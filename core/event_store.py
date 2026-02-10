"""Event sourcing layer for The Loom.

Provides audit logging and event replay for:
- Edit operations
- Graph mutations
- Generation jobs
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class EventType(Enum):
    """Types of events in the system."""
    # Graph events
    NODE_CREATED = "node_created"
    NODE_UPDATED = "node_updated"
    NODE_DELETED = "node_deleted"
    EDGE_CREATED = "edge_created"
    EDGE_DELETED = "edge_deleted"
    
    # Content events
    TEXT_EDITED = "text_edited"
    PANEL_REDRAWN = "panel_redrawn"
    PANEL_GENERATED = "panel_generated"
    
    # Branch events
    BRANCH_CREATED = "branch_created"
    BRANCH_MERGED = "branch_merged"
    BRANCH_ARCHIVED = "branch_archived"
    
    # System events
    PROJECT_SAVED = "project_saved"
    PROJECT_LOADED = "project_loaded"
    EXPORT_CREATED = "export_created"


@dataclass(frozen=True)
class Event:
    """An event in the event store."""
    event_id: str
    event_type: EventType
    aggregate_id: str  # Node ID, branch ID, etc.
    aggregate_type: str  # "node", "branch", "project"
    
    # Event data
    payload: dict[str, Any]
    
    # Metadata
    user_id: str | None = None
    session_id: str | None = None
    
    # Timestamps
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "payload": json.dumps(self.payload),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            payload=json.loads(data["payload"]),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            timestamp=data["timestamp"],
        )


class EventStore:
    """SQLite-based event store."""
    
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or ".loom/events.db"
        self._ensure_db()
    
    def _ensure_db(self) -> None:
        """Ensure database exists with schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                aggregate_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Indexes for efficient querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id, aggregate_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    async def append(self, event: Event) -> bool:
        """Append an event to the store."""
        import asyncio
        
        def _append():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            data = event.to_dict()
            cursor.execute("""
                INSERT INTO events 
                (event_id, event_type, aggregate_id, aggregate_type, payload, user_id, session_id, timestamp)
                VALUES (:event_id, :event_type, :aggregate_id, :aggregate_type, :payload, :user_id, :session_id, :timestamp)
            """, data)
            
            conn.commit()
            conn.close()
            return True
        
        return await asyncio.get_event_loop().run_in_executor(None, _append)
    
    async def get_events(
        self,
        aggregate_id: str | None = None,
        aggregate_type: str | None = None,
        event_type: EventType | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get events with optional filtering."""
        import asyncio
        
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if aggregate_id:
                query += " AND aggregate_id = ?"
                params.append(aggregate_id)
            
            if aggregate_type:
                query += " AND aggregate_type = ?"
                params.append(aggregate_type)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type.value)
            
            if since:
                query += " AND timestamp > ?"
                params.append(since)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            events = []
            for row in rows:
                data = dict(zip(columns, row))
                events.append(Event.from_dict(data))
            
            conn.close()
            return events
        
        return await asyncio.get_event_loop().run_in_executor(None, _get)
    
    async def get_events_for_aggregate(self, aggregate_id: str, aggregate_type: str) -> list[Event]:
        """Get all events for a specific aggregate (for replay)."""
        import asyncio
        
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM events 
                WHERE aggregate_id = ? AND aggregate_type = ?
                ORDER BY timestamp ASC
            """, (aggregate_id, aggregate_type))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            events = []
            for row in rows:
                data = dict(zip(columns, row))
                events.append(Event.from_dict(data))
            
            conn.close()
            return events
        
        return await asyncio.get_event_loop().run_in_executor(None, _get)
    
    async def get_audit_trail(
        self,
        aggregate_id: str,
        aggregate_type: str,
    ) -> list[dict[str, Any]]:
        """Get human-readable audit trail for an aggregate."""
        events = await self.get_events_for_aggregate(aggregate_id, aggregate_type)
        
        trail = []
        for event in events:
            entry = {
                "timestamp": event.timestamp,
                "action": event.event_type.value,
                "user": event.user_id or "system",
                "details": self._format_event_details(event),
            }
            trail.append(entry)
        
        return trail
    
    def _format_event_details(self, event: Event) -> str:
        """Format event details for human readability."""
        match event.event_type:
            case EventType.NODE_CREATED:
                return f"Created node '{event.payload.get('label', 'unnamed')}'"
            case EventType.NODE_UPDATED:
                changes = event.payload.get('changes', [])
                return f"Updated: {', '.join(changes)}"
            case EventType.NODE_DELETED:
                return "Deleted node"
            case EventType.TEXT_EDITED:
                return f"Edited text: {event.payload.get('edit_summary', 'changes made')}"
            case EventType.PANEL_GENERATED:
                return f"Generated panel with model {event.payload.get('model_id', 'unknown')}"
            case EventType.BRANCH_CREATED:
                return f"Created branch '{event.payload.get('label', 'unnamed')}'"
            case _:
                return str(event.payload)
    
    async def get_recent_activity(
        self,
        limit: int = 50,
        event_types: list[EventType] | None = None,
    ) -> list[Event]:
        """Get recent activity feed."""
        import asyncio
        
        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if event_types:
                placeholders = ','.join('?' * len(event_types))
                query = f"""
                    SELECT * FROM events 
                    WHERE event_type IN ({placeholders})
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                params = [et.value for et in event_types] + [limit]
            else:
                query = """
                    SELECT * FROM events 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                params = [limit]
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            events = []
            for row in rows:
                data = dict(zip(columns, row))
                events.append(Event.from_dict(data))
            
            conn.close()
            return events
        
        return await asyncio.get_event_loop().run_in_executor(None, _get)
    
    async def replay_aggregate(self, aggregate_id: str, aggregate_type: str) -> dict[str, Any] | None:
        """Replay all events for an aggregate to reconstruct state."""
        events = await self.get_events_for_aggregate(aggregate_id, aggregate_type)
        
        if not events:
            return None
        
        # Start with empty state
        state: dict[str, Any] = {
            "aggregate_id": aggregate_id,
            "aggregate_type": aggregate_type,
            "created_at": events[0].timestamp,
            "updated_at": events[-1].timestamp,
            "event_count": len(events),
        }
        
        # Apply each event
        for event in events:
            self._apply_event(state, event)
        
        return state
    
    def _apply_event(self, state: dict[str, Any], event: Event) -> None:
        """Apply an event to the state."""
        match event.event_type:
            case EventType.NODE_CREATED:
                state["label"] = event.payload.get("label")
                state["x"] = event.payload.get("x")
                state["y"] = event.payload.get("y")
                state["branch_id"] = event.payload.get("branch_id")
            
            case EventType.NODE_UPDATED:
                for key, value in event.payload.get("changes", {}).items():
                    state[key] = value
            
            case EventType.TEXT_EDITED:
                state["last_edit"] = {
                    "timestamp": event.timestamp,
                    "user": event.user_id,
                    "span": event.payload.get("span"),
                }
            
            case EventType.PANEL_GENERATED:
                if "panels" not in state:
                    state["panels"] = []
                state["panels"].append({
                    "panel_index": event.payload.get("panel_index"),
                    "image_id": event.payload.get("image_id"),
                    "generated_at": event.timestamp,
                })


# Global event store instance
_global_event_store: EventStore | None = None


def get_event_store() -> EventStore:
    """Get or create global event store."""
    global _global_event_store
    if _global_event_store is None:
        _global_event_store = EventStore()
    return _global_event_store


def set_event_store(store: EventStore) -> None:
    """Set global event store."""
    global _global_event_store
    _global_event_store = store


# Helper functions for common events

async def log_node_created(node_id: str, label: str, x: float, y: float, branch_id: str, user_id: str | None = None) -> None:
    """Log node creation event."""
    import hashlib
    import time
    
    event = Event(
        event_id=f"evt-{hashlib.sha256(f'{node_id}-{time.time()}'.encode()).hexdigest()[:12]}",
        event_type=EventType.NODE_CREATED,
        aggregate_id=node_id,
        aggregate_type="node",
        payload={"label": label, "x": x, "y": y, "branch_id": branch_id},
        user_id=user_id,
    )
    
    await get_event_store().append(event)


async def log_node_updated(node_id: str, changes: dict[str, Any], user_id: str | None = None) -> None:
    """Log node update event."""
    import hashlib
    import time
    
    event = Event(
        event_id=f"evt-{hashlib.sha256(f'{node_id}-{time.time()}'.encode()).hexdigest()[:12]}",
        event_type=EventType.NODE_UPDATED,
        aggregate_id=node_id,
        aggregate_type="node",
        payload={"changes": changes},
        user_id=user_id,
    )
    
    await get_event_store().append(event)


async def log_text_edited(scene_id: str, span: dict[str, Any], edit_summary: str, user_id: str | None = None) -> None:
    """Log text edit event."""
    import hashlib
    import time
    
    event = Event(
        event_id=f"evt-{hashlib.sha256(f'{scene_id}-{time.time()}'.encode()).hexdigest()[:12]}",
        event_type=EventType.TEXT_EDITED,
        aggregate_id=scene_id,
        aggregate_type="scene",
        payload={"span": span, "edit_summary": edit_summary},
        user_id=user_id,
    )
    
    await get_event_store().append(event)


async def log_panel_generated(scene_id: str, panel_index: int, image_id: str, model_id: str, user_id: str | None = None) -> None:
    """Log panel generation event."""
    import hashlib
    import time
    
    event = Event(
        event_id=f"evt-{hashlib.sha256(f'{image_id}-{time.time()}'.encode()).hexdigest()[:12]}",
        event_type=EventType.PANEL_GENERATED,
        aggregate_id=scene_id,
        aggregate_type="scene",
        payload={"panel_index": panel_index, "image_id": image_id, "model_id": model_id},
        user_id=user_id,
    )
    
    await get_event_store().append(event)


async def log_branch_created(branch_id: str, label: str, parent_branch_id: str | None, source_node_id: str, user_id: str | None = None) -> None:
    """Log branch creation event."""
    import hashlib
    import time
    
    event = Event(
        event_id=f"evt-{hashlib.sha256(f'{branch_id}-{time.time()}'.encode()).hexdigest()[:12]}",
        event_type=EventType.BRANCH_CREATED,
        aggregate_id=branch_id,
        aggregate_type="branch",
        payload={"label": label, "parent_branch_id": parent_branch_id, "source_node_id": source_node_id},
        user_id=user_id,
    )
    
    await get_event_store().append(event)
