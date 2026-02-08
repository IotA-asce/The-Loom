"""Tests for manga page ingestion normalization and spread detection."""

from __future__ import annotations

import io
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import agents.archivist as archivist


def _save_image(
    path: Path, *, mode: str, size: tuple[int, int], image_format: str
) -> None:
    image_module = __import__("PIL.Image", fromlist=["Image"])
    image = image_module.new(mode, size, (255, 0, 0, 180) if "A" in mode else 120)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format=image_format)


def _image_bytes(*, mode: str, size: tuple[int, int], image_format: str) -> bytes:
    image_module = __import__("PIL.Image", fromlist=["Image"])
    image = image_module.new(mode, size, (255, 0, 0, 180) if "A" in mode else 120)
    payload = io.BytesIO()
    image.save(payload, format=image_format)
    return payload.getvalue()


def test_folder_ingestion_normalizes_modes_and_detects_spreads(tmp_path: Path) -> None:
    _save_image(
        tmp_path / "page-2.webp", mode="RGBA", size=(640, 420), image_format="WEBP"
    )
    _save_image(tmp_path / "page-1.jpg", mode="L", size=(400, 700), image_format="JPEG")

    report = archivist.ingest_image_folder_pages(
        tmp_path, use_sandbox=False, idempotent=False
    )

    assert report.page_count == 2
    assert report.spread_count == 1
    assert set(report.page_formats) == {"jpeg", "webp"}
    assert len(report.page_hashes) == 2

    first_page, second_page = report.page_metadata
    assert first_page.source_ref.endswith("page-1.jpg")
    assert first_page.normalized_mode == "RGB"
    assert second_page.has_alpha is True
    assert second_page.is_spread is True


def test_cbz_ingestion_collects_metadata_and_spread_count(tmp_path: Path) -> None:
    archive_path = tmp_path / "panels.cbz"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as cbz_archive:
        cbz_archive.writestr(
            "01.png", _image_bytes(mode="RGB", size=(300, 500), image_format="PNG")
        )
        cbz_archive.writestr(
            "02.png", _image_bytes(mode="RGBA", size=(900, 400), image_format="PNG")
        )

    report = archivist.ingest_cbz_pages(
        archive_path, use_sandbox=False, idempotent=False
    )

    assert report.page_count == 2
    assert report.spread_count == 1
    assert report.page_formats == ("png",)
    assert len(report.page_metadata) == 2
    assert report.page_metadata[1].is_spread is True


def test_folder_ingestion_supports_png_jpg_jpeg_webp(tmp_path: Path) -> None:
    _save_image(
        tmp_path / "page-1.png", mode="RGB", size=(300, 400), image_format="PNG"
    )
    _save_image(
        tmp_path / "page-2.jpg", mode="RGB", size=(300, 400), image_format="JPEG"
    )
    _save_image(
        tmp_path / "page-3.jpeg", mode="RGB", size=(300, 400), image_format="JPEG"
    )
    _save_image(
        tmp_path / "page-4.webp", mode="RGB", size=(300, 400), image_format="WEBP"
    )

    report = archivist.ingest_image_folder_pages(
        tmp_path, use_sandbox=False, idempotent=False
    )

    assert report.page_count == 4
    assert set(report.page_formats) == {"jpeg", "png", "webp"}
