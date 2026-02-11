"""Graph persistence layer for The Loom.

Provides database storage for story graphs with:
- Node/edge CRUD operations
- Branch lineage tracking
- Version history
- Event sourcing
"""

from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GraphNode:
    """A node in the story graph."""

    node_id: str
    label: str
    branch_id: str
    scene_id: str
    x: float
    y: float
    importance: float = 0.5
    node_type: str = "scene"  # NEW: explicit type field (scene, chapter, beat, dialogue, manga)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "branch_id": self.branch_id,
            "scene_id": self.scene_id,
            "x": self.x,
            "y": self.y,
            "importance": self.importance,
            "node_type": self.node_type,
            "metadata": json.dumps(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphNode:
        metadata = data.get("metadata", "{}")
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        # Migrate node_type from metadata if not present
        node_type = data.get("node_type")
        if node_type is None and metadata:
            node_type = metadata.get("type")
        return cls(
            node_id=data["node_id"],
            label=data["label"],
            branch_id=data["branch_id"],
            scene_id=data["scene_id"],
            x=data["x"],
            y=data["y"],
            importance=data.get("importance", 0.5),
            node_type=node_type or "scene",
            metadata=metadata,
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass(frozen=True)
class GraphEdge:
    """An edge connecting two nodes."""

    edge_id: str
    source_id: str
    target_id: str
    label: str = ""
    edge_type: str = "default"  # default, branch, merge
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "label": self.label,
            "edge_type": self.edge_type,
            "weight": self.weight,
            "metadata": json.dumps(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphEdge:
        metadata = data.get("metadata", "{}")
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        return cls(
            edge_id=data["edge_id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            label=data.get("label", ""),
            edge_type=data.get("edge_type", "default"),
            weight=data.get("weight", 1.0),
            metadata=metadata,
            created_at=data["created_at"],
        )


@dataclass(frozen=True)
class BranchInfo:
    """Information about a story branch."""

    branch_id: str
    parent_branch_id: str | None
    source_node_id: str
    label: str
    status: str = "active"  # active, archived, merged
    lineage: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "parent_branch_id": self.parent_branch_id,
            "source_node_id": self.source_node_id,
            "label": self.label,
            "status": self.status,
            "lineage": json.dumps(self.lineage),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BranchInfo:
        lineage = data.get("lineage", "[]")
        if isinstance(lineage, str):
            lineage = json.loads(lineage)
        return cls(
            branch_id=data["branch_id"],
            parent_branch_id=data.get("parent_branch_id"),
            source_node_id=data["source_node_id"],
            label=data["label"],
            status=data.get("status", "active"),
            lineage=lineage,
            created_at=data["created_at"],
        )


class GraphPersistence(ABC):
    """Abstract base class for graph persistence."""

    @abstractmethod
    async def save_node(self, node: GraphNode) -> bool:
        """Save or update a node."""
        pass

    @abstractmethod
    async def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        pass

    @abstractmethod
    async def delete_node(self, node_id: str) -> bool:
        """Delete a node."""
        pass

    @abstractmethod
    async def save_edge(self, edge: GraphEdge) -> bool:
        """Save or update an edge."""
        pass

    @abstractmethod
    async def get_edge(self, edge_id: str) -> GraphEdge | None:
        """Get an edge by ID."""
        pass

    @abstractmethod
    async def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        pass

    @abstractmethod
    async def get_nodes_by_branch(self, branch_id: str) -> list[GraphNode]:
        """Get all nodes in a branch."""
        pass

    @abstractmethod
    async def get_all_nodes(self) -> list[GraphNode]:
        """Get all nodes."""
        pass

    @abstractmethod
    async def get_all_edges(self) -> list[GraphEdge]:
        """Get all edges."""
        pass

    @abstractmethod
    async def save_branch(self, branch: BranchInfo) -> bool:
        """Save or update a branch."""
        pass

    @abstractmethod
    async def get_branch(self, branch_id: str) -> BranchInfo | None:
        """Get a branch by ID."""
        pass

    @abstractmethod
    async def get_all_branches(self) -> list[BranchInfo]:
        """Get all branches."""
        pass

    @abstractmethod
    async def save_project(self, project_id: str, data: dict[str, Any]) -> bool:
        """Save entire project."""
        pass

    @abstractmethod
    async def load_project(self, project_id: str) -> dict[str, Any] | None:
        """Load entire project."""
        pass


class SQLiteGraphPersistence(GraphPersistence):
    """SQLite-based graph persistence."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or ".loom/graph.db"
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensure database exists with schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                branch_id TEXT NOT NULL,
                scene_id TEXT NOT NULL,
                x REAL DEFAULT 0,
                y REAL DEFAULT 0,
                importance REAL DEFAULT 0.5,
                node_type TEXT DEFAULT 'scene',
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Migration: Add node_type column if it doesn't exist (for existing databases)
        try:
            cursor.execute("SELECT node_type FROM nodes LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            cursor.execute("ALTER TABLE nodes ADD COLUMN node_type TEXT DEFAULT 'scene'")
            # Migrate existing nodes: extract type from metadata
            cursor.execute("SELECT node_id, metadata FROM nodes")
            for row in cursor.fetchall():
                node_id, metadata_str = row
                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    node_type = metadata.get("type", "scene")
                    cursor.execute(
                        "UPDATE nodes SET node_type = ? WHERE node_id = ?",
                        (node_type, node_id)
                    )
                except (json.JSONDecodeError, AttributeError):
                    pass
            conn.commit()

        # Edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                edge_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                label TEXT DEFAULT '',
                edge_type TEXT DEFAULT 'default',
                weight REAL DEFAULT 1.0,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES nodes(node_id),
                FOREIGN KEY (target_id) REFERENCES nodes(node_id)
            )
        """)

        # Branches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS branches (
                branch_id TEXT PRIMARY KEY,
                parent_branch_id TEXT,
                source_node_id TEXT NOT NULL,
                label TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                lineage TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_node_id) REFERENCES nodes(node_id)
            )
        """)

        # Projects table (for full export/import)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)

    async def save_node(self, node: GraphNode) -> bool:
        """Save or update a node."""
        import asyncio

        def _save():
            conn = self._get_connection()
            cursor = conn.cursor()

            data = node.to_dict()
            cursor.execute(
                """
                INSERT OR REPLACE INTO nodes 
                (node_id, label, branch_id, scene_id, x, y, importance, node_type, metadata, 
                 created_at, updated_at)
                VALUES (:node_id, :label, :branch_id, :scene_id, :x, :y, :importance, 
                        :node_type, :metadata, :created_at, :updated_at)
            """,
                data,
            )

            conn.commit()
            conn.close()
            return True

        return await asyncio.get_event_loop().run_in_executor(None, _save)

    async def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        import asyncio

        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
            row = cursor.fetchone()

            conn.close()

            if row is None:
                return None

            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row, strict=False))
            return GraphNode.from_dict(data)

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node."""
        import asyncio

        def _delete():
            conn = self._get_connection()
            cursor = conn.cursor()

            # Delete edges connected to this node
            cursor.execute(
                "DELETE FROM edges WHERE source_id = ? OR target_id = ?",
                (node_id, node_id),
            )

            # Delete node
            cursor.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
            deleted = cursor.rowcount > 0

            conn.commit()
            conn.close()
            return deleted

        return await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def save_edge(self, edge: GraphEdge) -> bool:
        """Save or update an edge."""
        import asyncio

        def _save():
            conn = self._get_connection()
            cursor = conn.cursor()

            data = edge.to_dict()
            cursor.execute(
                """
                INSERT OR REPLACE INTO edges 
                (edge_id, source_id, target_id, label, edge_type, weight, metadata, 
                 created_at)
                VALUES (:edge_id, :source_id, :target_id, :label, :edge_type, :weight, 
                        :metadata, :created_at)
            """,
                data,
            )

            conn.commit()
            conn.close()
            return True

        return await asyncio.get_event_loop().run_in_executor(None, _save)

    async def get_edge(self, edge_id: str) -> GraphEdge | None:
        """Get an edge by ID."""
        import asyncio

        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM edges WHERE edge_id = ?", (edge_id,))
            row = cursor.fetchone()

            conn.close()

            if row is None:
                return None

            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row, strict=False))
            return GraphEdge.from_dict(data)

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        import asyncio

        def _delete():
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM edges WHERE edge_id = ?", (edge_id,))
            deleted = cursor.rowcount > 0

            conn.commit()
            conn.close()
            return deleted

        return await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def get_nodes_by_branch(self, branch_id: str) -> list[GraphNode]:
        """Get all nodes in a branch."""
        import asyncio

        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM nodes WHERE branch_id = ?", (branch_id,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            nodes = []
            for row in rows:
                data = dict(zip(columns, row, strict=False))
                nodes.append(GraphNode.from_dict(data))

            conn.close()
            return nodes

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def get_all_nodes(self) -> list[GraphNode]:
        """Get all nodes."""
        import asyncio

        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM nodes")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            nodes = []
            for row in rows:
                data = dict(zip(columns, row, strict=False))
                nodes.append(GraphNode.from_dict(data))

            conn.close()
            return nodes

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def get_all_edges(self) -> list[GraphEdge]:
        """Get all edges."""
        import asyncio

        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM edges")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            edges = []
            for row in rows:
                data = dict(zip(columns, row, strict=False))
                edges.append(GraphEdge.from_dict(data))

            conn.close()
            return edges

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def save_branch(self, branch: BranchInfo) -> bool:
        """Save or update a branch."""
        import asyncio

        def _save():
            conn = self._get_connection()
            cursor = conn.cursor()

            data = branch.to_dict()
            cursor.execute(
                """
                INSERT OR REPLACE INTO branches 
                (branch_id, parent_branch_id, source_node_id, label, status, lineage, 
                 created_at)
                VALUES (:branch_id, :parent_branch_id, :source_node_id, :label, 
                        :status, :lineage, :created_at)
            """,
                data,
            )

            conn.commit()
            conn.close()
            return True

        return await asyncio.get_event_loop().run_in_executor(None, _save)

    async def get_branch(self, branch_id: str) -> BranchInfo | None:
        """Get a branch by ID."""
        import asyncio

        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM branches WHERE branch_id = ?", (branch_id,))
            row = cursor.fetchone()

            conn.close()

            if row is None:
                return None

            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row, strict=False))
            return BranchInfo.from_dict(data)

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def get_all_branches(self) -> list[BranchInfo]:
        """Get all branches."""
        import asyncio

        def _get():
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM branches")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            branches = []
            for row in rows:
                data = dict(zip(columns, row, strict=False))
                branches.append(BranchInfo.from_dict(data))

            conn.close()
            return branches

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def save_project(self, project_id: str, data: dict[str, Any]) -> bool:
        """Save entire project."""
        import asyncio

        def _save():
            conn = self._get_connection()
            cursor = conn.cursor()

            now = datetime.now(UTC).isoformat()
            cursor.execute(
                """
                INSERT OR REPLACE INTO projects 
                (project_id, data, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """,
                (project_id, json.dumps(data), now, now),
            )

            conn.commit()
            conn.close()
            return True

        return await asyncio.get_event_loop().run_in_executor(None, _save)

    async def load_project(self, project_id: str) -> dict[str, Any] | None:
        """Load entire project."""
        import asyncio

        def _load():
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM projects WHERE project_id = ?", (project_id,)
            )
            row = cursor.fetchone()

            conn.close()

            if row is None:
                return None

            return json.loads(row[0])

        return await asyncio.get_event_loop().run_in_executor(None, _load)


# Global persistence instance
_global_persistence: GraphPersistence | None = None


def get_graph_persistence() -> GraphPersistence:
    """Get or create global graph persistence."""
    global _global_persistence
    if _global_persistence is None:
        _global_persistence = SQLiteGraphPersistence()
    return _global_persistence


def set_graph_persistence(persistence: GraphPersistence) -> None:
    """Set global graph persistence."""
    global _global_persistence
    _global_persistence = persistence
