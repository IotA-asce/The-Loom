"""Tests for idempotent ingestion and near-duplicate detection."""

from __future__ import annotations

from pathlib import Path

import agents.archivist as archivist


def _create_png(path: Path, color: tuple[int, int, int]) -> None:
    image_module = __import__("PIL.Image", fromlist=["Image"])
    image = image_module.new("RGB", (320, 320), color)
    image.save(path, format="PNG")


def test_text_reingestion_is_idempotent_with_cache(tmp_path: Path) -> None:
    text_path = tmp_path / "story.txt"
    text_path.write_text("Chapter one\n\nA quiet street.", encoding="utf-8")

    cache = archivist.IngestionDedupeCache()
    first_report = archivist.ingest_text_document(
        text_path,
        use_sandbox=False,
        dedupe_cache=cache,
    )
    second_report = archivist.ingest_text_document(
        text_path,
        use_sandbox=False,
        dedupe_cache=cache,
    )

    assert first_report.source_hash
    assert second_report.source_hash == first_report.source_hash
    assert any("Source unchanged" in warning for warning in second_report.warnings)


def test_text_near_duplicate_detection_uses_chunk_signatures(tmp_path: Path) -> None:
    first_path = tmp_path / "a.txt"
    second_path = tmp_path / "b.txt"

    first_path.write_text("The corridor is silent and empty.", encoding="utf-8")
    second_path.write_text("The corridor is silent and almost empty.", encoding="utf-8")

    cache = archivist.IngestionDedupeCache()
    archivist.ingest_text_document(first_path, use_sandbox=False, dedupe_cache=cache)
    second_report = archivist.ingest_text_document(
        second_path,
        use_sandbox=False,
        dedupe_cache=cache,
    )

    assert any(
        "near-duplicate text source" in warning for warning in second_report.warnings
    )


def test_manga_reingestion_is_idempotent_with_cache(tmp_path: Path) -> None:
    _create_png(tmp_path / "page-1.png", (120, 60, 30))

    cache = archivist.IngestionDedupeCache()
    first_report = archivist.ingest_image_folder_pages(
        tmp_path,
        use_sandbox=False,
        dedupe_cache=cache,
    )
    second_report = archivist.ingest_image_folder_pages(
        tmp_path,
        use_sandbox=False,
        dedupe_cache=cache,
    )

    assert first_report.source_hash
    assert second_report.source_hash == first_report.source_hash
    assert any("Source unchanged" in warning for warning in second_report.warnings)


def test_manga_near_duplicate_detection_uses_perceptual_hash(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()

    _create_png(first_dir / "page-1.png", (120, 60, 30))
    _create_png(second_dir / "page-1.png", (122, 62, 28))

    cache = archivist.IngestionDedupeCache()
    archivist.ingest_image_folder_pages(
        first_dir, use_sandbox=False, dedupe_cache=cache
    )
    second_report = archivist.ingest_image_folder_pages(
        second_dir,
        use_sandbox=False,
        dedupe_cache=cache,
    )

    assert any(
        "near-duplicate page source" in warning for warning in second_report.warnings
    )
