"""Security and trust-boundary tests for ingestion."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import agents.archivist as archivist
import pytest

_PNG_HEADER = b"\x89PNG\r\n\x1a\n"
_JPEG_HEADER = b"\xff\xd8\xff\xe0"


def _write_fake_png(path: Path) -> None:
    path.write_bytes(_PNG_HEADER + b"fake-png-data")


def _write_fake_jpeg(path: Path) -> None:
    path.write_bytes(_JPEG_HEADER + b"fake-jpeg-data")


def test_image_folder_ingestion_uses_sandbox_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_fake_png(tmp_path / "page-1.png")
    called: dict[str, object] = {}

    def fake_runner(
        task_name: str,
        task_args: tuple[object, ...],
        timeout_seconds: float,
    ) -> archivist.IngestionReport:
        called["task_name"] = task_name
        called["task_args"] = task_args
        called["timeout_seconds"] = timeout_seconds
        return archivist.ingest_image_folder_pages(tmp_path, use_sandbox=False)

    monkeypatch.setattr(archivist, "_run_in_sandboxed_worker", fake_runner)

    report = archivist.ingest_image_folder_pages(tmp_path)

    assert called["task_name"] == "ingest_image_folder_pages"
    assert report.page_count == 1


def test_image_folder_ingestion_enforces_page_count_limit(tmp_path: Path) -> None:
    for index in range(3):
        _write_fake_png(tmp_path / f"page-{index}.png")

    policy = archivist.IngestionPolicy(max_page_count=2)
    with pytest.raises(
        archivist.IngestionSecurityError, match="page count exceeds limit"
    ):
        archivist.ingest_image_folder_pages(tmp_path, policy=policy, use_sandbox=False)


def test_image_folder_ingestion_validates_extension_signature_consistency(
    tmp_path: Path,
) -> None:
    _write_fake_jpeg(tmp_path / "page-1.png")

    with pytest.raises(archivist.IngestionSecurityError, match="signature check"):
        archivist.ingest_image_folder_pages(tmp_path, use_sandbox=False)


def test_cbz_ingestion_rejects_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.cbz"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as cbz_archive:
        cbz_archive.writestr("../page-1.png", _PNG_HEADER + b"panel")

    with pytest.raises(archivist.IngestionSecurityError, match="path traversal"):
        archivist.ingest_cbz_pages(archive_path, use_sandbox=False)


def test_cbz_ingestion_rejects_compression_ratio_abuse(tmp_path: Path) -> None:
    archive_path = tmp_path / "ratio.cbz"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as cbz_archive:
        cbz_archive.writestr("page-1.png", _PNG_HEADER + (b"A" * 40_000))

    strict_policy = archivist.IngestionPolicy(max_compression_ratio=2.0)
    with pytest.raises(archivist.IngestionSecurityError, match="compression ratio"):
        archivist.ingest_cbz_pages(
            archive_path,
            policy=strict_policy,
            use_sandbox=False,
        )


def test_cbz_ingestion_rejects_signature_mismatch(tmp_path: Path) -> None:
    archive_path = tmp_path / "not-a-zip.cbz"
    archive_path.write_bytes(b"plain-text-content")

    with pytest.raises(archivist.IngestionSecurityError, match="signature check"):
        archivist.ingest_cbz_pages(archive_path, use_sandbox=False)


def test_cbz_ingestion_enforces_worker_timeout(tmp_path: Path) -> None:
    archive_path = tmp_path / "pages.cbz"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as cbz_archive:
        cbz_archive.writestr("page-1.png", _PNG_HEADER + b"panel")

    short_timeout_policy = archivist.IngestionPolicy(worker_timeout_seconds=0.0)
    with pytest.raises(TimeoutError, match="exceeded timeout"):
        archivist.ingest_cbz_pages(archive_path, policy=short_timeout_policy)
