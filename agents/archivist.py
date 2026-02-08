"""Ingestion helpers for text and manga sources."""

from __future__ import annotations

import mimetypes
import re
from collections.abc import Callable
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile

SUPPORTED_MANGA_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
_NUMBER_PATTERN = re.compile(r"(\d+)")
_ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_JPEG_SIGNATURE = b"\xff\xd8\xff"
_PDF_SIGNATURE = b"%PDF-"
_WEBP_RIFF_SIGNATURE = b"RIFF"
_WEBP_FORMAT_MARKER = b"WEBP"

_ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    ".cbz": {
        "application/zip",
        "application/x-cbr",
        "application/x-cbz",
        "application/x-zip-compressed",
        "application/vnd.comicbook+zip",
    },
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".webp": {"image/webp"},
}

_EXPECTED_SIGNATURES_BY_EXTENSION: dict[str, set[str]] = {
    ".cbz": {"zip"},
    ".png": {"png"},
    ".jpg": {"jpeg"},
    ".jpeg": {"jpeg"},
    ".webp": {"webp"},
}


@dataclass(frozen=True)
class IngestionPolicy:
    """Security and resource limits used during ingestion."""

    max_file_size_bytes: int = 50 * 1024 * 1024
    max_page_count: int = 2_000
    max_archive_entry_count: int = 10_000
    max_archive_uncompressed_bytes: int = 500 * 1024 * 1024
    max_compression_ratio: float = 100.0
    worker_timeout_seconds: float = 10.0


DEFAULT_INGESTION_POLICY = IngestionPolicy()


class IngestionSecurityError(ValueError):
    """Raised when a source fails ingestion trust-boundary checks."""


@dataclass(frozen=True)
class IngestionReport:
    """Minimal ingestion status for a source."""

    source_path: Path
    page_count: int
    warnings: tuple[str, ...] = ()


def _sniff_binary_signature(file_header: bytes) -> str:
    if file_header.startswith(_PNG_SIGNATURE):
        return "png"
    if file_header.startswith(_JPEG_SIGNATURE):
        return "jpeg"
    if file_header.startswith(_PDF_SIGNATURE):
        return "pdf"
    if file_header.startswith(_ZIP_SIGNATURES):
        return "zip"
    if (
        file_header.startswith(_WEBP_RIFF_SIGNATURE)
        and file_header[8:12] == _WEBP_FORMAT_MARKER
    ):
        return "webp"
    return "unknown"


def _read_file_header(path: Path, length: int = 16) -> bytes:
    with path.open("rb") as file_handle:
        return file_handle.read(length)


def _validate_file_size(path: Path, policy: IngestionPolicy) -> None:
    file_size = path.stat().st_size
    if file_size > policy.max_file_size_bytes:
        msg = (
            f"File '{path.name}' exceeds max file size limit "
            f"({file_size} > {policy.max_file_size_bytes})."
        )
        raise IngestionSecurityError(msg)


def _validate_extension_mime_and_signature(path: Path) -> None:
    suffix = path.suffix.lower()
    expected_signatures = _EXPECTED_SIGNATURES_BY_EXTENSION.get(suffix)
    if expected_signatures is None:
        msg = f"Unsupported file extension '{suffix}'."
        raise IngestionSecurityError(msg)

    guessed_mime, _ = mimetypes.guess_type(path.name)
    allowed_mime_types = _ALLOWED_MIME_TYPES.get(suffix, set())
    if guessed_mime is not None and guessed_mime not in allowed_mime_types:
        msg = (
            f"File '{path.name}' has MIME '{guessed_mime}', "
            f"which does not match extension '{suffix}'."
        )
        raise IngestionSecurityError(msg)

    signature = _sniff_binary_signature(_read_file_header(path))
    if signature not in expected_signatures:
        msg = (
            f"File '{path.name}' failed signature check: expected "
            f"{sorted(expected_signatures)} but found '{signature}'."
        )
        raise IngestionSecurityError(msg)


def _validate_archive_member_path(member_name: str) -> None:
    normalized = member_name.replace("\\", "/")
    member_path = PurePosixPath(normalized)

    if member_path.is_absolute() or normalized.startswith("/"):
        msg = f"Archive member '{member_name}' uses an absolute path."
        raise IngestionSecurityError(msg)

    if ".." in member_path.parts:
        msg = f"Archive member '{member_name}' contains path traversal segments."
        raise IngestionSecurityError(msg)

    if member_path.parts:
        first_part = member_path.parts[0]
        if len(first_part) == 2 and first_part[1] == ":" and first_part[0].isalpha():
            msg = f"Archive member '{member_name}' contains a drive-prefixed path."
            raise IngestionSecurityError(msg)


def _validate_archive_limits(
    cbz_archive: ZipFile, policy: IngestionPolicy
) -> list[str]:
    entries = [entry for entry in cbz_archive.infolist() if not entry.is_dir()]
    if len(entries) > policy.max_archive_entry_count:
        msg = (
            "Archive entry count exceeds limit "
            f"({len(entries)} > {policy.max_archive_entry_count})."
        )
        raise IngestionSecurityError(msg)

    total_uncompressed_bytes = 0
    total_compressed_bytes = 0
    page_names: list[str] = []

    for entry in entries:
        _validate_archive_member_path(entry.filename)

        total_uncompressed_bytes += entry.file_size
        compressed_size = max(entry.compress_size, 1)
        total_compressed_bytes += compressed_size

        if entry.file_size > policy.max_file_size_bytes:
            msg = (
                f"Archive member '{entry.filename}' exceeds max file size limit "
                f"({entry.file_size} > {policy.max_file_size_bytes})."
            )
            raise IngestionSecurityError(msg)

        entry_compression_ratio = entry.file_size / compressed_size
        if entry_compression_ratio > policy.max_compression_ratio:
            msg = (
                f"Archive member '{entry.filename}' exceeds compression ratio limit "
                f"({entry_compression_ratio:.2f} > {policy.max_compression_ratio:.2f})."
            )
            raise IngestionSecurityError(msg)

        member_suffix = Path(entry.filename).suffix.lower()
        if member_suffix in SUPPORTED_MANGA_IMAGE_EXTENSIONS:
            with cbz_archive.open(entry) as member_file:
                member_signature = _sniff_binary_signature(member_file.read(16))

            expected_signatures = _EXPECTED_SIGNATURES_BY_EXTENSION[member_suffix]
            if member_signature not in expected_signatures:
                msg = (
                    f"Archive member '{entry.filename}' failed signature check: "
                    "expected "
                    f"{sorted(expected_signatures)} but found '{member_signature}'."
                )
                raise IngestionSecurityError(msg)

            page_names.append(entry.filename)

    if total_uncompressed_bytes > policy.max_archive_uncompressed_bytes:
        msg = (
            "Archive uncompressed size exceeds limit "
            f"({total_uncompressed_bytes} > {policy.max_archive_uncompressed_bytes})."
        )
        raise IngestionSecurityError(msg)

    archive_compression_ratio = total_uncompressed_bytes / max(
        total_compressed_bytes, 1
    )
    if archive_compression_ratio > policy.max_compression_ratio:
        msg = (
            "Archive compression ratio exceeds limit "
            f"({archive_compression_ratio:.2f} > {policy.max_compression_ratio:.2f})."
        )
        raise IngestionSecurityError(msg)

    if len(page_names) > policy.max_page_count:
        msg = (
            "Archive page count exceeds limit "
            f"({len(page_names)} > {policy.max_page_count})."
        )
        raise IngestionSecurityError(msg)

    return sorted(page_names, key=_natural_sort_key)


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


def _ingest_image_folder_pages_worker(
    folder_path: Path,
    policy: IngestionPolicy,
) -> IngestionReport:
    pages = list_manga_image_pages(folder_path)
    warnings: list[str] = []

    if len(pages) > policy.max_page_count:
        msg = (
            f"Image page count exceeds limit ({len(pages)} > {policy.max_page_count})."
        )
        raise IngestionSecurityError(msg)

    for page_path in pages:
        _validate_file_size(page_path, policy)
        _validate_extension_mime_and_signature(page_path)

    if not pages:
        warnings.append("No supported manga image pages found.")

    return IngestionReport(
        source_path=folder_path,
        page_count=len(pages),
        warnings=tuple(warnings),
    )


def _ingest_cbz_pages_worker(
    archive_path: Path,
    policy: IngestionPolicy,
) -> IngestionReport:
    warnings: list[str] = []
    _validate_file_size(archive_path, policy)
    _validate_extension_mime_and_signature(archive_path)

    try:
        with ZipFile(archive_path) as cbz_archive:
            sorted_page_names = _validate_archive_limits(cbz_archive, policy)
    except BadZipFile as error:
        msg = f"CBZ archive '{archive_path.name}' is invalid: {error}."
        raise IngestionSecurityError(msg) from error

    if not sorted_page_names:
        warnings.append("No supported page images found inside CBZ archive.")

    return IngestionReport(
        source_path=archive_path,
        page_count=len(sorted_page_names),
        warnings=tuple(warnings),
    )


def _sandbox_worker_entry(
    task_name: str,
    task_args: tuple[Any, ...],
    result_queue: Any,
) -> None:
    try:
        task = _SANDBOX_TASKS[task_name]
        report = task(*task_args)
        result_queue.put(("ok", report))
    except Exception as error:  # noqa: BLE001
        result_queue.put(("error", f"{type(error).__name__}: {error}"))


def _run_in_sandboxed_worker(
    task_name: str,
    task_args: tuple[Any, ...],
    timeout_seconds: float,
) -> IngestionReport:
    context = get_context("spawn")
    result_queue = context.Queue()
    worker = context.Process(
        target=_sandbox_worker_entry,
        args=(task_name, task_args, result_queue),
    )

    worker.start()
    worker.join(timeout_seconds)

    if worker.is_alive():
        worker.terminate()
        worker.join()
        msg = f"Sandbox worker for '{task_name}' exceeded timeout ({timeout_seconds}s)."
        raise TimeoutError(msg)

    if result_queue.empty():
        msg = (
            f"Sandbox worker for '{task_name}' returned no result "
            f"(exit_code={worker.exitcode})."
        )
        raise RuntimeError(msg)

    status, payload = result_queue.get()
    if status == "ok" and isinstance(payload, IngestionReport):
        return payload

    if status == "error":
        raise IngestionSecurityError(str(payload))

    msg = f"Sandbox worker for '{task_name}' returned invalid payload."
    raise RuntimeError(msg)


_SANDBOX_TASKS: dict[str, Callable[[Path, IngestionPolicy], IngestionReport]] = {
    "ingest_image_folder_pages": _ingest_image_folder_pages_worker,
    "ingest_cbz_pages": _ingest_cbz_pages_worker,
}


def ingest_image_folder_pages(
    folder_path: Path,
    policy: IngestionPolicy = DEFAULT_INGESTION_POLICY,
    *,
    use_sandbox: bool = True,
) -> IngestionReport:
    """Count supported pages for a loose-image manga folder."""

    if not folder_path.exists() or not folder_path.is_dir():
        return IngestionReport(
            source_path=folder_path,
            page_count=0,
            warnings=("Image folder does not exist.",),
        )

    if use_sandbox:
        return _run_in_sandboxed_worker(
            "ingest_image_folder_pages",
            (folder_path, policy),
            policy.worker_timeout_seconds,
        )

    return _ingest_image_folder_pages_worker(folder_path, policy)


def ingest_cbz_pages(
    archive_path: Path,
    policy: IngestionPolicy = DEFAULT_INGESTION_POLICY,
    *,
    use_sandbox: bool = True,
) -> IngestionReport:
    """Count supported pages in a CBZ archive."""

    if not archive_path.exists() or not archive_path.is_file():
        return IngestionReport(
            source_path=archive_path,
            page_count=0,
            warnings=("CBZ archive does not exist.",),
        )

    if use_sandbox:
        return _run_in_sandboxed_worker(
            "ingest_cbz_pages",
            (archive_path, policy),
            policy.worker_timeout_seconds,
        )

    return _ingest_cbz_pages_worker(archive_path, policy)
