"""Manga storage module for The Loom.

Provides persistent storage for imported manga volumes with:
- Manga metadata (title, page count, source hash)
- Page information (dimensions, format, OCR text)
- Association with graph nodes
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MangaPage:
    """A single page in a manga volume."""

    page_number: int
    format_name: str
    width: int
    height: int
    content_hash: str
    ocr_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "format_name": self.format_name,
            "width": self.width,
            "height": self.height,
            "content_hash": self.content_hash,
            "ocr_text": self.ocr_text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MangaPage:
        return cls(
            page_number=data["page_number"],
            format_name=data["format_name"],
            width=data["width"],
            height=data["height"],
            content_hash=data["content_hash"],
            ocr_text=data.get("ocr_text", ""),
        )


@dataclass(frozen=True)
class MangaVolume:
    """A manga volume with metadata and pages."""

    volume_id: str
    title: str
    source_path: str
    page_count: int
    source_hash: str
    pages: tuple[MangaPage, ...] = ()
    graph_node_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "volume_id": self.volume_id,
            "title": self.title,
            "source_path": self.source_path,
            "page_count": self.page_count,
            "source_hash": self.source_hash,
            "pages": [p.to_dict() for p in self.pages],
            "graph_node_id": self.graph_node_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MangaVolume:
        pages = tuple(MangaPage.from_dict(p) for p in data.get("pages", []))
        return cls(
            volume_id=data["volume_id"],
            title=data["title"],
            source_path=data["source_path"],
            page_count=data["page_count"],
            source_hash=data["source_hash"],
            pages=pages,
            graph_node_id=data.get("graph_node_id"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


class MangaStorage:
    """SQLite-based storage for manga volumes."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or ".loom/manga.db"
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensure database exists with schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Volumes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manga_volumes (
                volume_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_path TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                source_hash TEXT NOT NULL,
                graph_node_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Pages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manga_pages (
                page_id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume_id TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                format_name TEXT NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                ocr_text TEXT DEFAULT '',
                FOREIGN KEY (volume_id) REFERENCES manga_volumes(volume_id) ON DELETE CASCADE,
                UNIQUE(volume_id, page_number)
            )
        """)

        # Index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_manga_pages_volume 
            ON manga_pages(volume_id)
        """)

        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)

    def save_volume(self, volume: MangaVolume) -> bool:
        """Save or update a manga volume."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Insert or replace volume
            cursor.execute("""
                INSERT OR REPLACE INTO manga_volumes 
                (volume_id, title, source_path, page_count, source_hash, graph_node_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                volume.volume_id,
                volume.title,
                volume.source_path,
                volume.page_count,
                volume.source_hash,
                volume.graph_node_id,
                volume.created_at,
                volume.updated_at,
            ))

            # Delete existing pages for this volume
            cursor.execute("DELETE FROM manga_pages WHERE volume_id = ?", (volume.volume_id,))

            # Insert pages
            for page in volume.pages:
                cursor.execute("""
                    INSERT INTO manga_pages 
                    (volume_id, page_number, format_name, width, height, content_hash, ocr_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    volume.volume_id,
                    page.page_number,
                    page.format_name,
                    page.width,
                    page.height,
                    page.content_hash,
                    page.ocr_text,
                ))

            conn.commit()
            return True
        except Exception as e:
            print(f"Failed to save manga volume: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_volume(self, volume_id: str) -> MangaVolume | None:
        """Get a volume by ID with all pages."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get volume
            cursor.execute("""
                SELECT volume_id, title, source_path, page_count, source_hash, 
                       graph_node_id, created_at, updated_at
                FROM manga_volumes WHERE volume_id = ?
            """, (volume_id,))

            row = cursor.fetchone()
            if not row:
                return None

            # Get pages
            cursor.execute("""
                SELECT page_number, format_name, width, height, content_hash, ocr_text
                FROM manga_pages WHERE volume_id = ? ORDER BY page_number
            """, (volume_id,))

            pages = tuple(
                MangaPage(
                    page_number=pr[0],
                    format_name=pr[1],
                    width=pr[2],
                    height=pr[3],
                    content_hash=pr[4],
                    ocr_text=pr[5],
                )
                for pr in cursor.fetchall()
            )

            return MangaVolume(
                volume_id=row[0],
                title=row[1],
                source_path=row[2],
                page_count=row[3],
                source_hash=row[4],
                pages=pages,
                graph_node_id=row[5],
                created_at=row[6],
                updated_at=row[7],
            )
        finally:
            conn.close()

    def get_page(self, volume_id: str, page_number: int) -> MangaPage | None:
        """Get a specific page by volume ID and page number."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT page_number, format_name, width, height, content_hash, ocr_text
                FROM manga_pages WHERE volume_id = ? AND page_number = ?
            """, (volume_id, page_number))

            row = cursor.fetchone()
            if not row:
                return None

            return MangaPage(
                page_number=row[0],
                format_name=row[1],
                width=row[2],
                height=row[3],
                content_hash=row[4],
                ocr_text=row[5],
            )
        finally:
            conn.close()

    def get_volume_source_path(self, volume_id: str) -> str | None:
        """Get the source path for a volume."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT source_path FROM manga_volumes WHERE volume_id = ?",
                (volume_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def get_all_volumes(self, limit: int = 100, offset: int = 0) -> list[MangaVolume]:
        """Get all volumes (without pages for listing)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT volume_id, title, source_path, page_count, source_hash, 
                       graph_node_id, created_at, updated_at
                FROM manga_volumes
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            return [
                MangaVolume(
                    volume_id=row[0],
                    title=row[1],
                    source_path=row[2],
                    page_count=row[3],
                    source_hash=row[4],
                    pages=(),  # Don't load pages for listing
                    graph_node_id=row[5],
                    created_at=row[6],
                    updated_at=row[7],
                )
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def delete_volume(self, volume_id: str) -> bool:
        """Delete a volume and its pages."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM manga_volumes WHERE volume_id = ?", (volume_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Failed to delete manga volume: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_volume_by_hash(self, source_hash: str) -> MangaVolume | None:
        """Get a volume by its source hash (for deduplication)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT volume_id FROM manga_volumes WHERE source_hash = ?
            """, (source_hash,))

            row = cursor.fetchone()
            if row:
                return self.get_volume(row[0])
            return None
        finally:
            conn.close()


# Global instance
_manga_storage: MangaStorage | None = None


def get_manga_storage(db_path: str | None = None) -> MangaStorage:
    """Get or create global manga storage instance."""
    global _manga_storage
    if _manga_storage is None or db_path is not None:
        _manga_storage = MangaStorage(db_path)
    return _manga_storage
