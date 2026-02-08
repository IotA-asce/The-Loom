"""Ingestion helpers for text and manga sources."""

from __future__ import annotations

import html
import importlib
import mimetypes
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path, PurePosixPath
from typing import Any, TypeVar
from zipfile import BadZipFile, ZipFile

_ReportT = TypeVar("_ReportT")

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
    ".epub": {"application/epub+zip", "application/zip"},
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".webp": {"image/webp"},
}

_EXPECTED_SIGNATURES_BY_EXTENSION: dict[str, set[str]] = {
    ".cbz": {"zip"},
    ".epub": {"zip"},
    ".pdf": {"pdf"},
    ".png": {"png"},
    ".jpg": {"jpeg"},
    ".jpeg": {"jpeg"},
    ".webp": {"webp"},
}

_SUPPORTED_TEXT_EXTENSIONS = {".txt", ".pdf", ".epub"}
_SUPPORTED_HTML_EXTENSIONS = {".xhtml", ".html", ".htm"}
_EPUB_HTML_MEDIA_TYPES = {"application/xhtml+xml", "text/html"}


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


@dataclass(frozen=True)
class TextChapter:
    """A parsed chapter extracted from text, PDF, or EPUB sources."""

    title: str
    content: str


@dataclass(frozen=True)
class TextIngestionReport:
    """Detailed parser output for textual ingestion workflows."""

    source_path: Path
    parser_used: str
    normalized_text: str
    chapters: tuple[TextChapter, ...]
    confidence: float
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


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


def _clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalize_text_content(raw_text: str) -> str:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _extract_text_from_html(html_content: str) -> str:
    stripped = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html_content)
    stripped = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", stripped)
    stripped = re.sub(r"(?i)</(p|div|h1|h2|h3|h4|h5|h6|li|br)>", "\n", stripped)
    stripped = re.sub(r"(?is)<[^>]+>", " ", stripped)
    stripped = html.unescape(stripped)
    stripped = re.sub(r"[ \t]+", " ", stripped)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped.strip()


def _extract_html_title(html_content: str, default_title: str) -> str:
    title_patterns = [
        r"(?is)<title[^>]*>(.*?)</title>",
        r"(?is)<h1[^>]*>(.*?)</h1>",
        r"(?is)<h2[^>]*>(.*?)</h2>",
    ]

    for pattern in title_patterns:
        match = re.search(pattern, html_content)
        if match:
            candidate = _extract_text_from_html(match.group(1)).strip()
            if candidate:
                return candidate

    return default_title


def _decode_text_bytes(raw_bytes: bytes) -> tuple[str, str, list[str]]:
    warnings: list[str] = []
    decode_plan = ["utf-8-sig", "utf-16", "utf-32", "cp1252", "latin-1"]

    for encoding in decode_plan:
        try:
            decoded = raw_bytes.decode(encoding)
            if encoding in {"cp1252", "latin-1"}:
                warnings.append(f"Decoded text using fallback encoding '{encoding}'.")
            return decoded, encoding, warnings
        except UnicodeDecodeError:
            continue

    decoded = raw_bytes.decode("utf-8", errors="replace")
    warnings.append("Decoded text with replacement characters due to unknown encoding.")
    return decoded, "utf-8-replace", warnings


def _validate_text_source(path: Path, policy: IngestionPolicy) -> None:
    _validate_file_size(path, policy)
    suffix = path.suffix.lower()

    if suffix not in _SUPPORTED_TEXT_EXTENSIONS:
        msg = f"Unsupported text source extension '{suffix}'."
        raise IngestionSecurityError(msg)

    guessed_mime, _ = mimetypes.guess_type(path.name)
    allowed_mime_types = _ALLOWED_MIME_TYPES.get(suffix, set())
    if (
        guessed_mime is not None
        and allowed_mime_types
        and guessed_mime not in allowed_mime_types
    ):
        msg = (
            f"File '{path.name}' has MIME '{guessed_mime}', "
            f"which does not match extension '{suffix}'."
        )
        raise IngestionSecurityError(msg)

    if suffix in {".pdf", ".epub"}:
        _validate_extension_mime_and_signature(path)


def _to_safe_member_path(base_dir: PurePosixPath, href: str) -> str:
    candidate = (base_dir / href).as_posix()
    member_path = PurePosixPath(candidate)

    if member_path.is_absolute() or ".." in member_path.parts:
        msg = f"EPUB member path '{href}' is unsafe."
        raise IngestionSecurityError(msg)

    return candidate


def _parse_txt_document(path: Path) -> TextIngestionReport:
    raw_bytes = path.read_bytes()
    decoded_text, encoding, warnings = _decode_text_bytes(raw_bytes)
    normalized_text = _normalize_text_content(decoded_text)

    confidence_map = {
        "utf-8-sig": 0.97,
        "utf-16": 0.93,
        "utf-32": 0.9,
        "cp1252": 0.78,
        "latin-1": 0.75,
        "utf-8-replace": 0.55,
    }
    confidence = confidence_map.get(encoding, 0.6)

    errors: list[str] = []
    if not normalized_text:
        errors.append("Text source did not contain readable content.")
        confidence = min(confidence, 0.2)

    chapters: tuple[TextChapter, ...]
    if normalized_text:
        chapter_title = path.stem.replace("_", " ").strip() or "Chapter 1"
        chapters = (TextChapter(title=chapter_title, content=normalized_text),)
    else:
        chapters = ()

    return TextIngestionReport(
        source_path=path,
        parser_used="txt",
        normalized_text=normalized_text,
        chapters=chapters,
        confidence=_clamp_confidence(confidence),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def _parse_pdf_with_pypdf(path: Path) -> tuple[str, int]:
    pypdf_module = importlib.import_module("pypdf")
    pdf_reader_cls = pypdf_module.PdfReader

    reader = pdf_reader_cls(str(path))
    extracted_pages: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        normalized_page_text = _normalize_text_content(page_text)
        if normalized_page_text:
            extracted_pages.append(normalized_page_text)

    combined_text = "\n\n".join(extracted_pages)
    return combined_text, len(reader.pages)


def _parse_pdf_with_fallback(path: Path) -> str:
    raw_bytes = path.read_bytes()
    string_literals = re.findall(rb"\(([^\(\)]{4,})\)", raw_bytes)
    decoded_segments: list[str] = []

    for segment in string_literals:
        decoded_segments.append(segment.decode("cp1252", errors="ignore").strip())

    fallback_text = "\n".join(segment for segment in decoded_segments if segment)
    if fallback_text:
        return _normalize_text_content(fallback_text)

    naive_text = raw_bytes.decode("latin-1", errors="ignore")
    extracted_blocks = re.findall(r"[A-Za-z][A-Za-z0-9 ,\.'!?\-]{5,}", naive_text)
    return _normalize_text_content("\n".join(extracted_blocks))


def _parse_pdf_document(path: Path, policy: IngestionPolicy) -> TextIngestionReport:
    warnings: list[str] = []
    errors: list[str] = []

    parser_used = "pdf-pypdf"
    confidence = 0.9

    try:
        normalized_text, page_count = _parse_pdf_with_pypdf(path)
        if page_count > policy.max_page_count:
            msg = (
                "PDF page count exceeds limit "
                f"({page_count} > {policy.max_page_count})."
            )
            raise IngestionSecurityError(msg)
    except Exception as primary_error:  # noqa: BLE001
        parser_used = "pdf-fallback"
        confidence = 0.5
        warnings.append(
            f"Primary PDF parser failed; used fallback extraction ({primary_error})."
        )
        normalized_text = _parse_pdf_with_fallback(path)

    if not normalized_text:
        errors.append("No extractable text found in PDF source.")
        confidence = min(confidence, 0.2)

    chapters = (
        (
            TextChapter(
                title=path.stem.replace("_", " ").strip() or "Document",
                content=normalized_text,
            ),
        )
        if normalized_text
        else ()
    )

    return TextIngestionReport(
        source_path=path,
        parser_used=parser_used,
        normalized_text=normalized_text,
        chapters=chapters,
        confidence=_clamp_confidence(confidence),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def _parse_epub_from_spine(epub_path: Path) -> tuple[list[TextChapter], list[str]]:
    warnings: list[str] = []

    with ZipFile(epub_path) as epub_archive:
        if "mimetype" in epub_archive.namelist():
            mimetype_payload = epub_archive.read("mimetype").decode(
                "utf-8", errors="ignore"
            )
            if "application/epub+zip" not in mimetype_payload:
                warnings.append("EPUB mimetype marker is missing or unexpected.")

        container_payload = epub_archive.read("META-INF/container.xml")
        container_root = ET.fromstring(container_payload)
        rootfile_node = container_root.find(".//{*}rootfile")
        if rootfile_node is None:
            msg = "EPUB container.xml is missing rootfile metadata."
            raise ValueError(msg)

        package_path = rootfile_node.attrib.get("full-path", "").strip()
        if not package_path:
            msg = "EPUB rootfile metadata is empty."
            raise ValueError(msg)

        package_payload = epub_archive.read(package_path)
        package_root = ET.fromstring(package_payload)
        package_base = PurePosixPath(package_path).parent

        manifest_map: dict[str, tuple[str, str]] = {}
        for item in package_root.findall(".//{*}manifest/{*}item"):
            item_id = item.attrib.get("id", "").strip()
            href = item.attrib.get("href", "").strip()
            media_type = item.attrib.get("media-type", "").strip()
            if item_id and href:
                manifest_map[item_id] = (href, media_type)

        chapter_nodes = package_root.findall(".//{*}spine/{*}itemref")
        chapters: list[TextChapter] = []

        for chapter_index, chapter_node in enumerate(chapter_nodes, start=1):
            id_ref = chapter_node.attrib.get("idref", "").strip()
            if not id_ref:
                continue

            manifest_item = manifest_map.get(id_ref)
            if manifest_item is None:
                warnings.append(
                    f"EPUB spine reference '{id_ref}' is missing from manifest."
                )
                continue

            href, media_type = manifest_item
            if media_type and media_type not in _EPUB_HTML_MEDIA_TYPES:
                continue

            member_path = _to_safe_member_path(package_base, href)
            html_payload = epub_archive.read(member_path)
            html_content = html_payload.decode("utf-8", errors="replace")
            chapter_text = _extract_text_from_html(html_content)

            if not chapter_text:
                continue

            chapter_title = _extract_html_title(
                html_content,
                default_title=f"Chapter {chapter_index}",
            )
            chapters.append(TextChapter(title=chapter_title, content=chapter_text))

    if not chapters:
        msg = "EPUB spine parsing produced no readable chapters."
        raise ValueError(msg)

    return chapters, warnings


def _parse_epub_fallback_scan(epub_path: Path) -> list[TextChapter]:
    with ZipFile(epub_path) as epub_archive:
        html_members = [
            member_name
            for member_name in epub_archive.namelist()
            if Path(member_name).suffix.lower() in _SUPPORTED_HTML_EXTENSIONS
        ]

        html_members.sort(key=_natural_sort_key)

        chapters: list[TextChapter] = []
        for chapter_index, member_name in enumerate(html_members, start=1):
            html_payload = epub_archive.read(member_name)
            html_content = html_payload.decode("utf-8", errors="replace")
            chapter_text = _extract_text_from_html(html_content)
            if not chapter_text:
                continue

            default_title = f"Chapter {chapter_index}"
            chapter_title = _extract_html_title(
                html_content, default_title=default_title
            )
            chapters.append(TextChapter(title=chapter_title, content=chapter_text))

    if not chapters:
        msg = "EPUB fallback scan found no readable HTML chapters."
        raise ValueError(msg)

    return chapters


def _parse_epub_document(path: Path) -> TextIngestionReport:
    warnings: list[str] = []
    errors: list[str] = []

    parser_used = "epub"
    confidence = 0.88

    try:
        chapters, spine_warnings = _parse_epub_from_spine(path)
        warnings.extend(spine_warnings)
    except Exception as spine_error:  # noqa: BLE001
        parser_used = "epub-fallback"
        confidence = 0.62
        warnings.append(
            f"EPUB spine parsing failed; used fallback scan ({spine_error})."
        )
        try:
            chapters = _parse_epub_fallback_scan(path)
        except Exception as fallback_error:  # noqa: BLE001
            chapters = []
            errors.append(
                "EPUB parsing failed for both primary and fallback paths: "
                f"{fallback_error}."
            )

    normalized_text = "\n\n".join(chapter.content for chapter in chapters)
    if not normalized_text:
        errors.append("No extractable text found in EPUB source.")
        confidence = min(confidence, 0.2)

    if warnings:
        confidence -= 0.05 * len(warnings)
    if errors:
        confidence -= 0.2

    return TextIngestionReport(
        source_path=path,
        parser_used=parser_used,
        normalized_text=normalized_text,
        chapters=tuple(chapters),
        confidence=_clamp_confidence(confidence),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def _ingest_text_document_worker(
    source_path: Path,
    policy: IngestionPolicy,
) -> TextIngestionReport:
    _validate_text_source(source_path, policy)

    suffix = source_path.suffix.lower()
    if suffix == ".txt":
        return _parse_txt_document(source_path)

    if suffix == ".pdf":
        return _parse_pdf_document(source_path, policy)

    if suffix == ".epub":
        return _parse_epub_document(source_path)

    msg = f"Unsupported text source extension '{suffix}'."
    raise IngestionSecurityError(msg)


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
    expected_type: type[_ReportT],
) -> _ReportT:
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
    if status == "ok" and isinstance(payload, expected_type):
        return payload

    if status == "error":
        raise IngestionSecurityError(str(payload))

    msg = f"Sandbox worker for '{task_name}' returned invalid payload."
    raise RuntimeError(msg)


_SANDBOX_TASKS: dict[str, Callable[[Path, IngestionPolicy], object]] = {
    "ingest_image_folder_pages": _ingest_image_folder_pages_worker,
    "ingest_cbz_pages": _ingest_cbz_pages_worker,
    "ingest_text_document": _ingest_text_document_worker,
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
            IngestionReport,
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
            IngestionReport,
        )

    return _ingest_cbz_pages_worker(archive_path, policy)


def ingest_text_document(
    source_path: Path,
    policy: IngestionPolicy = DEFAULT_INGESTION_POLICY,
    *,
    use_sandbox: bool = True,
) -> TextIngestionReport:
    """Parse and normalize `.txt`, `.pdf`, and `.epub` sources."""

    if not source_path.exists() or not source_path.is_file():
        return TextIngestionReport(
            source_path=source_path,
            parser_used="none",
            normalized_text="",
            chapters=(),
            confidence=0.0,
            warnings=("Text source does not exist.",),
            errors=("Missing source file.",),
        )

    if use_sandbox:
        return _run_in_sandboxed_worker(
            "ingest_text_document",
            (source_path, policy),
            policy.worker_timeout_seconds,
            TextIngestionReport,
        )

    return _ingest_text_document_worker(source_path, policy)
