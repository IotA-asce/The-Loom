"""Storage layer for story extraction with checkpointing and event logging.

Phase 3 of the story extraction strategy.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ExtractionEventType(Enum):
    """Types of extraction events."""
    
    EXTRACTION_STARTED = "extraction_started"
    CHUNK_COMPLETED = "chunk_completed"
    CHUNK_FAILED = "chunk_failed"
    SYNTHESIS_STARTED = "synthesis_started"
    SCENE_CREATED = "scene_created"
    VALIDATION_COMPLETED = "validation_completed"
    EXTRACTION_COMPLETED = "extraction_completed"
    EXTRACTION_FAILED = "extraction_failed"
    CHECKPOINT_SAVED = "checkpoint_saved"
    RECOVERY_ATTEMPTED = "recovery_attempted"


@dataclass
class ExtractionCheckpoint:
    """Checkpoint for resuming extraction."""
    
    volume_id: str
    chunk_index: int
    total_chunks: int
    pages_processed: int
    total_pages: int
    intermediate_results: list[dict] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    context_carry: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "volume_id": self.volume_id,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "pages_processed": self.pages_processed,
            "total_pages": self.total_pages,
            "intermediate_results": self.intermediate_results,
            "timestamp": self.timestamp,
            "context_carry": self.context_carry,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtractionCheckpoint:
        return cls(
            volume_id=data["volume_id"],
            chunk_index=data["chunk_index"],
            total_chunks=data["total_chunks"],
            pages_processed=data["pages_processed"],
            total_pages=data["total_pages"],
            intermediate_results=data.get("intermediate_results", []),
            timestamp=data["timestamp"],
            context_carry=data.get("context_carry", {}),
        )


@dataclass
class ExtractionEvent:
    """An event in the extraction process."""
    
    event_id: str
    event_type: ExtractionEventType
    volume_id: str
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "volume_id": self.volume_id,
            "payload": json.dumps(self.payload),
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtractionEvent:
        return cls(
            event_id=data["event_id"],
            event_type=ExtractionEventType(data["event_type"]),
            volume_id=data["volume_id"],
            payload=json.loads(data["payload"]),
            timestamp=data["timestamp"],
        )


@dataclass
class ExtractionSession:
    """Complete extraction session record."""
    
    session_id: str
    volume_id: str
    volume_title: str
    status: str  # "running", "completed", "failed", "paused"
    total_pages: int
    pages_processed: int = 0
    chunks_completed: int = 0
    total_chunks: int = 0
    scenes_created: int = 0
    confidence_score: float = 0.0
    settings: dict = field(default_factory=dict)
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    error_message: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "volume_id": self.volume_id,
            "volume_title": self.volume_title,
            "status": self.status,
            "total_pages": self.total_pages,
            "pages_processed": self.pages_processed,
            "chunks_completed": self.chunks_completed,
            "total_chunks": self.total_chunks,
            "scenes_created": self.scenes_created,
            "confidence_score": self.confidence_score,
            "settings": json.dumps(self.settings),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtractionSession:
        return cls(
            session_id=data["session_id"],
            volume_id=data["volume_id"],
            volume_title=data["volume_title"],
            status=data["status"],
            total_pages=data["total_pages"],
            pages_processed=data["pages_processed"],
            chunks_completed=data["chunks_completed"],
            total_chunks=data["total_chunks"],
            scenes_created=data["scenes_created"],
            confidence_score=data["confidence_score"],
            settings=json.loads(data["settings"]),
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            error_message=data.get("error_message"),
        )


class ExtractionStorage:
    """SQLite-based storage for extraction data."""
    
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or ".loom/extractions.db"
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """Ensure database schema exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction_sessions (
                session_id TEXT PRIMARY KEY,
                volume_id TEXT NOT NULL,
                volume_title TEXT NOT NULL,
                status TEXT NOT NULL,
                total_pages INTEGER NOT NULL,
                pages_processed INTEGER DEFAULT 0,
                chunks_completed INTEGER DEFAULT 0,
                total_chunks INTEGER DEFAULT 0,
                scenes_created INTEGER DEFAULT 0,
                confidence_score REAL DEFAULT 0.0,
                settings TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                error_message TEXT
            )
        """)
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                volume_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Checkpoints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction_checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                volume_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                total_chunks INTEGER NOT NULL,
                data TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_volume 
            ON extraction_sessions(volume_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_volume 
            ON extraction_events(volume_id, timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_volume 
            ON extraction_checkpoints(volume_id, chunk_index)
        """)
        
        conn.commit()
        conn.close()
    
    # Session Management
    
    def create_session(
        self,
        session_id: str,
        volume_id: str,
        volume_title: str,
        total_pages: int,
        settings: dict | None = None,
    ) -> ExtractionSession:
        """Create a new extraction session."""
        session = ExtractionSession(
            session_id=session_id,
            volume_id=volume_id,
            volume_title=volume_title,
            status="running",
            total_pages=total_pages,
            settings=settings or {},
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO extraction_sessions 
            (session_id, volume_id, volume_title, status, total_pages, settings, started_at)
            VALUES (:session_id, :volume_id, :volume_title, :status, :total_pages, :settings, :started_at)
            """,
            session.to_dict(),
        )
        
        conn.commit()
        conn.close()
        
        return session
    
    def update_session(self, session: ExtractionSession) -> None:
        """Update an existing session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE extraction_sessions SET
                status = :status,
                pages_processed = :pages_processed,
                chunks_completed = :chunks_completed,
                total_chunks = :total_chunks,
                scenes_created = :scenes_created,
                confidence_score = :confidence_score,
                completed_at = :completed_at,
                error_message = :error_message
            WHERE session_id = :session_id
            """,
            session.to_dict(),
        )
        
        conn.commit()
        conn.close()
    
    def get_session(self, session_id: str) -> ExtractionSession | None:
        """Get a session by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM extraction_sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        return ExtractionSession.from_dict(data)
    
    def get_latest_session(self, volume_id: str) -> ExtractionSession | None:
        """Get the most recent session for a volume."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM extraction_sessions 
            WHERE volume_id = ? 
            ORDER BY started_at DESC 
            LIMIT 1
            """,
            (volume_id,),
        )
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        return ExtractionSession.from_dict(data)
    
    def list_sessions(self, volume_id: str | None = None) -> list[ExtractionSession]:
        """List extraction sessions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if volume_id:
            cursor.execute(
                "SELECT * FROM extraction_sessions WHERE volume_id = ? ORDER BY started_at DESC",
                (volume_id,),
            )
        else:
            cursor.execute("SELECT * FROM extraction_sessions ORDER BY started_at DESC")
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        return [ExtractionSession.from_dict(dict(zip(columns, row))) for row in rows]
    
    # Event Logging
    
    def log_event(
        self,
        event_id: str,
        event_type: ExtractionEventType,
        volume_id: str,
        payload: dict[str, Any],
    ) -> ExtractionEvent:
        """Log an extraction event."""
        event = ExtractionEvent(
            event_id=event_id,
            event_type=event_type,
            volume_id=volume_id,
            payload=payload,
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO extraction_events 
            (event_id, event_type, volume_id, payload, timestamp)
            VALUES (:event_id, :event_type, :volume_id, :payload, :timestamp)
            """,
            event.to_dict(),
        )
        
        conn.commit()
        conn.close()
        
        return event
    
    def get_events(
        self,
        volume_id: str,
        event_type: ExtractionEventType | None = None,
        limit: int = 100,
    ) -> list[ExtractionEvent]:
        """Get events for a volume."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if event_type:
            cursor.execute(
                """
                SELECT * FROM extraction_events 
                WHERE volume_id = ? AND event_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (volume_id, event_type.value, limit),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM extraction_events 
                WHERE volume_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (volume_id, limit),
            )
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        return [ExtractionEvent.from_dict(dict(zip(columns, row))) for row in rows]
    
    # Checkpointing
    
    def save_checkpoint(self, checkpoint: ExtractionCheckpoint) -> None:
        """Save an extraction checkpoint."""
        checkpoint_id = f"{checkpoint.volume_id}_{checkpoint.chunk_index}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO extraction_checkpoints 
            (checkpoint_id, volume_id, chunk_index, total_chunks, data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                checkpoint_id,
                checkpoint.volume_id,
                checkpoint.chunk_index,
                checkpoint.total_chunks,
                json.dumps(checkpoint.to_dict()),
                checkpoint.timestamp,
            ),
        )
        
        conn.commit()
        conn.close()
    
    def load_checkpoint(self, volume_id: str, chunk_index: int) -> ExtractionCheckpoint | None:
        """Load a checkpoint."""
        checkpoint_id = f"{volume_id}_{chunk_index}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT data FROM extraction_checkpoints WHERE checkpoint_id = ?",
            (checkpoint_id,),
        )
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        return ExtractionCheckpoint.from_dict(json.loads(row[0]))
    
    def get_latest_checkpoint(self, volume_id: str) -> ExtractionCheckpoint | None:
        """Get the most recent checkpoint for a volume."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT data FROM extraction_checkpoints 
            WHERE volume_id = ?
            ORDER BY chunk_index DESC
            LIMIT 1
            """,
            (volume_id,),
        )
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        return ExtractionCheckpoint.from_dict(json.loads(row[0]))
    
    def clear_checkpoints(self, volume_id: str) -> None:
        """Clear all checkpoints for a volume."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM extraction_checkpoints WHERE volume_id = ?",
            (volume_id,),
        )
        
        conn.commit()
        conn.close()
    
    # Recovery
    
    def get_recovery_status(self, volume_id: str) -> dict[str, Any]:
        """Get status for resuming extraction."""
        session = self.get_latest_session(volume_id)
        checkpoint = self.get_latest_checkpoint(volume_id)
        
        if session is None:
            return {
                "can_resume": False,
                "reason": "No previous extraction found",
            }
        
        if session.status == "completed":
            return {
                "can_resume": False,
                "reason": "Extraction already completed",
                "session": session,
            }
        
        if session.status == "failed":
            return {
                "can_resume": True,
                "resume_from_chunk": checkpoint.chunk_index if checkpoint else 0,
                "session": session,
                "warning": "Previous extraction failed",
            }
        
        if checkpoint:
            return {
                "can_resume": True,
                "resume_from_chunk": checkpoint.chunk_index + 1,
                "pages_processed": checkpoint.pages_processed,
                "total_pages": checkpoint.total_pages,
                "session": session,
            }
        
        return {
            "can_resume": False,
            "reason": "No checkpoint found",
            "session": session,
        }


class ExtractionRecovery:
    """Tools for recovering from failed extractions."""
    
    def __init__(self, storage: ExtractionStorage) -> None:
        self.storage = storage
    
    def analyze_failure(self, volume_id: str) -> dict[str, Any]:
        """Analyze why an extraction failed."""
        events = self.storage.get_events(volume_id)
        session = self.storage.get_latest_session(volume_id)
        
        if not events:
            return {
                "found_failure": False,
                "message": "No events found for this volume",
            }
        
        # Find failure event
        failure_events = [e for e in events if e.event_type == ExtractionEventType.EXTRACTION_FAILED]
        chunk_failures = [e for e in events if e.event_type == ExtractionEventType.CHUNK_FAILED]
        
        analysis = {
            "found_failure": len(failure_events) > 0,
            "total_events": len(events),
            "chunk_failures": len(chunk_failures),
            "failure_events": [
                {
                    "timestamp": e.timestamp,
                    "error": e.payload.get("error", "Unknown error"),
                    "chunk_index": e.payload.get("chunk_index"),
                }
                for e in failure_events[:3]  # Last 3 failures
            ],
        }
        
        if session:
            analysis["session_status"] = session.status
            analysis["progress"] = f"{session.pages_processed}/{session.total_pages} pages"
        
        # Recommend recovery strategy
        if chunk_failures:
            failed_chunks = {e.payload.get("chunk_index") for e in chunk_failures}
            analysis["recommendation"] = f"Retry chunks: {sorted(failed_chunks)}"
        elif failure_events:
            analysis["recommendation"] = "Full retry recommended"
        else:
            analysis["recommendation"] = "Resume from last checkpoint"
        
        return analysis
    
    def prepare_retry(
        self,
        volume_id: str,
        retry_failed_only: bool = True,
    ) -> dict[str, Any]:
        """Prepare a retry plan."""
        status = self.storage.get_recovery_status(volume_id)
        events = self.storage.get_events(volume_id)
        
        if not status.get("can_resume"):
            return {
                "can_retry": False,
                "reason": status.get("reason"),
            }
        
        session = status["session"]
        
        if retry_failed_only:
            # Find failed chunks
            chunk_failures = [
                e for e in events 
                if e.event_type == ExtractionEventType.CHUNK_FAILED
            ]
            failed_chunks = {e.payload.get("chunk_index") for e in chunk_failures}
            
            return {
                "can_retry": True,
                "strategy": "failed_chunks_only",
                "failed_chunks": sorted(failed_chunks),
                "total_chunks": session.total_chunks if session else 0,
                "session_id": session.session_id if session else None,
            }
        else:
            # Full retry
            return {
                "can_retry": True,
                "strategy": "full_retry",
                "start_from_chunk": 0,
                "total_chunks": session.total_chunks if session else 0,
                "session_id": session.session_id if session else None,
            }


# Global storage instance
_extraction_storage: ExtractionStorage | None = None


def get_extraction_storage() -> ExtractionStorage:
    """Get global extraction storage instance."""
    global _extraction_storage
    if _extraction_storage is None:
        _extraction_storage = ExtractionStorage()
    return _extraction_storage
