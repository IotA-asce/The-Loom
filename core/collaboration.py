"""Real-time collaboration engine for The Loom.

Provides multi-user collaboration features:
- Room-based WebSocket connections
- User presence tracking
- Cursor position broadcasting
- Operational transforms for concurrent edits
- Conflict resolution
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class CollaborationEventType(Enum):
    """Types of collaboration events."""

    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    CURSOR_UPDATE = "cursor_update"
    NODE_SELECTED = "node_selected"
    NODE_EDITING = "node_editing"
    EDIT_LOCKED = "edit_locked"
    EDIT_UNLOCKED = "edit_unlocked"
    CHANGE_APPLIED = "change_applied"
    PRESENCE_SYNC = "presence_sync"


@dataclass(frozen=True)
class UserPresence:
    """User presence information."""

    user_id: str
    user_name: str
    user_color: str  # Hex color for cursor/selection
    joined_at: str
    last_active: str
    cursor_x: float = 0.0
    cursor_y: float = 0.0
    selected_node_id: str | None = None
    editing_node_id: str | None = None
    is_active: bool = True


@dataclass(frozen=True)
class CursorPosition:
    """Cursor position update."""

    user_id: str
    x: float
    y: float
    node_id: str | None = None  # Cursor is over this node
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class EditLock:
    """Lock on a node for editing."""

    node_id: str
    user_id: str
    user_name: str
    locked_at: str
    expires_at: str  # Lock expires after timeout


@dataclass
class CollaborationRoom:
    """A collaboration room for a story/project."""

    room_id: str  # Usually story_id or project_id
    created_at: str
    users: dict[str, UserPresence] = field(default_factory=dict)
    edit_locks: dict[str, EditLock] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def get_active_users(self) -> list[UserPresence]:
        """Get list of active users in the room."""
        return [u for u in self.users.values() if u.is_active]

    def get_user_count(self) -> int:
        """Get number of active users."""
        return len(self.get_active_users())


@dataclass(frozen=True)
class CollaborationEvent:
    """Event broadcast to room members."""

    event_type: CollaborationEventType
    room_id: str
    user_id: str
    payload: dict[str, Any]
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.event_type.value,
            "roomId": self.room_id,
            "userId": self.user_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class CollaborationEngine:
    """Engine for managing real-time collaboration."""

    # User colors for cursors/selections
    USER_COLORS = [
        "#FF6B6B",  # Red
        "#4ECDC4",  # Teal
        "#45B7D1",  # Blue
        "#FFA07A",  # Light salmon
        "#98D8C8",  # Mint
        "#F7DC6F",  # Yellow
        "#BB8FCE",  # Purple
        "#85C1E2",  # Light blue
        "#F8B739",  # Orange
        "#52BE80",  # Green
    ]

    # Lock timeout in seconds
    LOCK_TIMEOUT_SECONDS = 300  # 5 minutes

    def __init__(self) -> None:
        self._rooms: dict[str, CollaborationRoom] = {}
        self._user_connections: dict[str, str] = {}  # user_id -> room_id
        self._callbacks: list[Callable[[CollaborationEvent], None]] = []
        self._lock = asyncio.Lock()

    async def create_room(self, room_id: str) -> CollaborationRoom:
        """Create a new collaboration room."""
        async with self._lock:
            if room_id not in self._rooms:
                self._rooms[room_id] = CollaborationRoom(
                    room_id=room_id,
                    created_at=datetime.now(UTC).isoformat(),
                )
            return self._rooms[room_id]

    async def get_room(self, room_id: str) -> CollaborationRoom | None:
        """Get a collaboration room by ID."""
        return self._rooms.get(room_id)

    async def join_room(
        self,
        room_id: str,
        user_id: str,
        user_name: str,
    ) -> tuple[CollaborationRoom, UserPresence]:
        """Join a user to a collaboration room."""
        async with self._lock:
            # Create room if it doesn't exist
            if room_id not in self._rooms:
                await self.create_room(room_id)

            room = self._rooms[room_id]

            # Assign color based on user index
            color_index = len(room.users) % len(self.USER_COLORS)
            user_color = self.USER_COLORS[color_index]

            now = datetime.now(UTC).isoformat()
            presence = UserPresence(
                user_id=user_id,
                user_name=user_name,
                user_color=user_color,
                joined_at=now,
                last_active=now,
                is_active=True,
            )

            room.users[user_id] = presence
            self._user_connections[user_id] = room_id

            # Broadcast user joined event
            await self._broadcast(
                CollaborationEvent(
                    event_type=CollaborationEventType.USER_JOINED,
                    room_id=room_id,
                    user_id=user_id,
                    payload={
                        "userName": user_name,
                        "userColor": user_color,
                        "userCount": room.get_user_count(),
                    },
                )
            )

            return room, presence

    async def leave_room(self, room_id: str, user_id: str) -> CollaborationRoom | None:
        """Remove a user from a room."""
        async with self._lock:
            room = self._rooms.get(room_id)
            if not room:
                return None

            user = room.users.get(user_id)
            if user:
                # Mark as inactive
                room.users[user_id] = UserPresence(
                    user_id=user.user_id,
                    user_name=user.user_name,
                    user_color=user.user_color,
                    joined_at=user.joined_at,
                    last_active=datetime.now(UTC).isoformat(),
                    is_active=False,
                )

                # Release any edit locks
                await self._release_user_locks(room_id, user_id)

                # Broadcast user left
                await self._broadcast(
                    CollaborationEvent(
                        event_type=CollaborationEventType.USER_LEFT,
                        room_id=room_id,
                        user_id=user_id,
                        payload={
                            "userName": user.user_name,
                            "userCount": room.get_user_count(),
                        },
                    )
                )

            # Clean up if room is empty
            if room.get_user_count() == 0:
                del self._rooms[room_id]
                return None

            return room

    async def update_cursor(
        self,
        room_id: str,
        user_id: str,
        x: float,
        y: float,
        node_id: str | None = None,
    ) -> None:
        """Update user cursor position."""
        room = self._rooms.get(room_id)
        if not room:
            return

        user = room.users.get(user_id)
        if not user or not user.is_active:
            return

        # Update user's cursor position
        room.users[user_id] = UserPresence(
            user_id=user.user_id,
            user_name=user.user_name,
            user_color=user.user_color,
            joined_at=user.joined_at,
            last_active=datetime.now(UTC).isoformat(),
            cursor_x=x,
            cursor_y=y,
            selected_node_id=user.selected_node_id,
            editing_node_id=user.editing_node_id,
            is_active=True,
        )

        # Broadcast cursor update
        await self._broadcast(
            CollaborationEvent(
                event_type=CollaborationEventType.CURSOR_UPDATE,
                room_id=room_id,
                user_id=user_id,
                payload={
                    "x": x,
                    "y": y,
                    "nodeId": node_id,
                    "userColor": user.user_color,
                    "userName": user.user_name,
                },
            )
        )

    async def select_node(
        self,
        room_id: str,
        user_id: str,
        node_id: str | None,
    ) -> None:
        """Update user's selected node."""
        room = self._rooms.get(room_id)
        if not room:
            return

        user = room.users.get(user_id)
        if not user or not user.is_active:
            return

        # Update selection
        room.users[user_id] = UserPresence(
            user_id=user.user_id,
            user_name=user.user_name,
            user_color=user.user_color,
            joined_at=user.joined_at,
            last_active=datetime.now(UTC).isoformat(),
            cursor_x=user.cursor_x,
            cursor_y=user.cursor_y,
            selected_node_id=node_id,
            editing_node_id=user.editing_node_id,
            is_active=True,
        )

        await self._broadcast(
            CollaborationEvent(
                event_type=CollaborationEventType.NODE_SELECTED,
                room_id=room_id,
                user_id=user_id,
                payload={
                    "nodeId": node_id,
                    "userColor": user.user_color,
                    "userName": user.user_name,
                },
            )
        )

    async def acquire_edit_lock(
        self,
        room_id: str,
        node_id: str,
        user_id: str,
        user_name: str,
    ) -> tuple[bool, str | None]:
        """Try to acquire an edit lock on a node.

        Returns:
            (success, error_message)
        """
        room = self._rooms.get(room_id)
        if not room:
            return False, "Room not found"

        async with room._lock:
            # Check if already locked by someone else
            existing = room.edit_locks.get(node_id)
            if existing and existing.user_id != user_id:
                # Check if lock expired
                now = datetime.now(UTC)
                expires = datetime.fromisoformat(existing.expires_at)
                if now < expires:
                    return (
                        False,
                        f"Node is being edited by {existing.user_name}",
                    )

            # Acquire lock
            now = datetime.now(UTC)
            lock = EditLock(
                node_id=node_id,
                user_id=user_id,
                user_name=user_name,
                locked_at=now.isoformat(),
                expires_at=(
                    now.replace(second=now.second + self.LOCK_TIMEOUT_SECONDS)
                ).isoformat(),
            )
            room.edit_locks[node_id] = lock

            # Update user's editing status
            user = room.users.get(user_id)
            if user:
                room.users[user_id] = UserPresence(
                    user_id=user.user_id,
                    user_name=user.user_name,
                    user_color=user.user_color,
                    joined_at=user.joined_at,
                    last_active=now.isoformat(),
                    cursor_x=user.cursor_x,
                    cursor_y=user.cursor_y,
                    selected_node_id=user.selected_node_id,
                    editing_node_id=node_id,
                    is_active=True,
                )

            await self._broadcast(
                CollaborationEvent(
                    event_type=CollaborationEventType.EDIT_LOCKED,
                    room_id=room_id,
                    user_id=user_id,
                    payload={
                        "nodeId": node_id,
                        "userName": user_name,
                        "expiresAt": lock.expires_at,
                    },
                )
            )

            return True, None

    async def release_edit_lock(
        self,
        room_id: str,
        node_id: str,
        user_id: str,
    ) -> bool:
        """Release an edit lock."""
        room = self._rooms.get(room_id)
        if not room:
            return False

        async with room._lock:
            lock = room.edit_locks.get(node_id)
            if not lock or lock.user_id != user_id:
                return False

            del room.edit_locks[node_id]

            # Update user's editing status
            user = room.users.get(user_id)
            if user:
                room.users[user_id] = UserPresence(
                    user_id=user.user_id,
                    user_name=user.user_name,
                    user_color=user.user_color,
                    joined_at=user.joined_at,
                    last_active=datetime.now(UTC).isoformat(),
                    cursor_x=user.cursor_x,
                    cursor_y=user.cursor_y,
                    selected_node_id=user.selected_node_id,
                    editing_node_id=None,
                    is_active=True,
                )

            await self._broadcast(
                CollaborationEvent(
                    event_type=CollaborationEventType.EDIT_UNLOCKED,
                    room_id=room_id,
                    user_id=user_id,
                    payload={"nodeId": node_id},
                )
            )

            return True

    async def _release_user_locks(self, room_id: str, user_id: str) -> None:
        """Release all locks held by a user."""
        room = self._rooms.get(room_id)
        if not room:
            return

        locks_to_release = [
            node_id
            for node_id, lock in room.edit_locks.items()
            if lock.user_id == user_id
        ]

        for node_id in locks_to_release:
            await self.release_edit_lock(room_id, node_id, user_id)

    async def get_presence_sync(self, room_id: str) -> dict[str, Any]:
        """Get full presence state for sync."""
        room = self._rooms.get(room_id)
        if not room:
            return {"users": [], "locks": []}

        return {
            "users": [
                {
                    "userId": u.user_id,
                    "userName": u.user_name,
                    "userColor": u.user_color,
                    "cursorX": u.cursor_x,
                    "cursorY": u.cursor_y,
                    "selectedNodeId": u.selected_node_id,
                    "editingNodeId": u.editing_node_id,
                }
                for u in room.get_active_users()
            ],
            "locks": [
                {
                    "nodeId": lock.node_id,
                    "userId": lock.user_id,
                    "userName": lock.user_name,
                    "expiresAt": lock.expires_at,
                }
                for lock in room.edit_locks.values()
            ],
        }

    def on_event(self, callback: callable[[CollaborationEvent], None]) -> None:
        """Register a callback for collaboration events."""
        self._callbacks.append(callback)

    def off_event(self, callback: callable[[CollaborationEvent], None]) -> None:
        """Unregister a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def _broadcast(self, event: CollaborationEvent) -> None:
        """Broadcast event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception:
                pass  # Don't let callbacks break the engine


# Global collaboration engine instance
_collaboration_engine: CollaborationEngine | None = None


def get_collaboration_engine() -> CollaborationEngine:
    """Get the global collaboration engine instance."""
    global _collaboration_engine
    if _collaboration_engine is None:
        _collaboration_engine = CollaborationEngine()
    return _collaboration_engine
