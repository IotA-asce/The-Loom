"""Ingestion helpers for text and manga sources."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

SUPPORTED_MANGA_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
_NUMBER_PATTERN = re.compile(r"(\d+)")


@dataclass(frozen=True)
class IngestionReport:
    """Minimal ingestion status for a source."""

    source_path: Path
    page_count: int
    warnings: tuple[str, ...] = ()


def _natural_sort_key(value: str) -> tuple[object, ...]:
    parts = _NUMBER_PATTERN.split(value.lower())
    key: list[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return tuple(key)


def _is_supported_manga_page(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_MANGA_IMAGE_EXTENSIONS


def list_manga_image_pages(folder_path: Path) -> list[Path]:
    """Return naturally sorted manga image pages from a folder."""

    if not folder_path.exists() or not folder_path.is_dir():
        return []

    pages = [
        path
        for path in folder_path.iterdir()
        if path.is_file() and _is_supported_manga_page(path)
    ]
    return sorted(pages, key=lambda path: _natural_sort_key(path.name))


def ingest_image_folder_pages(folder_path: Path) -> IngestionReport:
    """Count supported pages for a loose-image manga folder."""

    pages = list_manga_image_pages(folder_path)
    warnings: list[str] = []
    if not pages:
        warnings.append("No supported manga image pages found.")

    return IngestionReport(
        source_path=folder_path, page_count=len(pages), warnings=tuple(warnings)
    )


def ingest_cbz_pages(archive_path: Path) -> IngestionReport:
    """Count supported pages in a CBZ archive."""

    warnings: list[str] = []
    if not archive_path.exists() or not archive_path.is_file():
        return IngestionReport(
            source_path=archive_path,
            page_count=0,
            warnings=("CBZ archive does not exist.",),
        )

    with ZipFile(archive_path) as cbz_archive:
        page_names = []
        for name in cbz_archive.namelist():
            suffix = Path(name).suffix.lower()
            if suffix in SUPPORTED_MANGA_IMAGE_EXTENSIONS:
                page_names.append(name)

    if not page_names:
        warnings.append("No supported page images found inside CBZ archive.")

    sorted_page_names = sorted(page_names, key=_natural_sort_key)
    return IngestionReport(
        source_path=archive_path,
        page_count=len(sorted_page_names),
        warnings=tuple(warnings),
    )
