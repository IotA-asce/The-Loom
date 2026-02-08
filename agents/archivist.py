"""Ingestion helpers for text and manga sources."""

from __future__ import annotations

import difflib
import hashlib
import html
import importlib
import io
import json
import math
import mimetypes
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from multiprocessing import get_context
from pathlib import Path, PurePosixPath
from typing import Any, TypeVar, cast
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
    source_hash: str = ""
    spread_count: int = 0
    page_formats: tuple[str, ...] = ()
    page_hashes: tuple[str, ...] = ()
    page_metadata: tuple[MangaPageMetadata, ...] = ()


@dataclass(frozen=True)
class MangaPageMetadata:
    """Normalized metadata captured for a manga page."""

    source_ref: str
    width: int
    height: int
    format_name: str
    original_mode: str
    normalized_mode: str
    has_alpha: bool
    is_spread: bool
    content_hash: str
    normalized_hash: str
    perceptual_hash: str
    mean_brightness: float
    contrast: float
    line_density: float
    texture_entropy: float
    composition_balance: float


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
    source_hash: str = ""
    chunk_hashes: tuple[str, ...] = ()
    chunk_signatures: tuple[str, ...] = ()


@dataclass(frozen=True)
class OcrRegion:
    """Detected OCR region and dialogue classification."""

    x1: int
    y1: int
    x2: int
    y2: int
    text: str
    confidence: float
    region_type: str


@dataclass(frozen=True)
class OcrPageReport:
    """OCR output for a single manga page."""

    source_path: Path
    engine: str
    regions: tuple[OcrRegion, ...]
    average_confidence: float
    warnings: tuple[str, ...] = ()


@dataclass
class IngestionDedupeCache:
    """In-memory cache for idempotent ingestion and dedupe tracking."""

    source_fingerprints: dict[str, str] = field(default_factory=dict)
    source_reports: dict[str, object] = field(default_factory=dict)
    chunk_hash_index: dict[str, set[str]] = field(default_factory=dict)
    chunk_signature_index: dict[str, set[str]] = field(default_factory=dict)
    page_hash_index: dict[str, set[str]] = field(default_factory=dict)
    page_perceptual_index: dict[str, set[str]] = field(default_factory=dict)
    source_texts: dict[str, str] = field(default_factory=dict)


DEFAULT_INGESTION_DEDUPE_CACHE = IngestionDedupeCache()


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


def _hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _compute_file_hash(path: Path) -> str:
    hash_builder = hashlib.sha256()
    with path.open("rb") as file_handle:
        while True:
            chunk = file_handle.read(1024 * 1024)
            if not chunk:
                break
            hash_builder.update(chunk)
    return hash_builder.hexdigest()


def _compute_folder_hash(folder_path: Path) -> str:
    hash_builder = hashlib.sha256()
    page_paths = list_manga_image_pages(folder_path)

    for page_path in page_paths:
        hash_builder.update(page_path.name.encode("utf-8"))
        hash_builder.update(page_path.stat().st_size.to_bytes(8, signed=False))
        hash_builder.update(_compute_file_hash(page_path).encode("ascii"))

    return hash_builder.hexdigest()


def _load_pillow_modules() -> tuple[Any, Any]:
    image_module = importlib.import_module("PIL.Image")
    image_ops_module = importlib.import_module("PIL.ImageOps")
    return image_module, image_ops_module


def _compute_perceptual_hash(pillow_image: Any) -> str:
    grayscale = pillow_image.convert("L").resize((8, 8))
    pixels = list(grayscale.tobytes())
    mean_value = sum(pixels) / len(pixels)
    bits = ["1" if pixel >= mean_value else "0" for pixel in pixels]
    value = int("".join(bits), 2)
    return f"{value:016x}"


def _compute_visual_feature_signals(
    pillow_image: Any,
) -> tuple[float, float, float, float, float]:
    grayscale = pillow_image.convert("L")
    width, height = grayscale.size
    pixel_values = list(grayscale.tobytes())

    if not pixel_values:
        return 0.0, 0.0, 0.0, 0.0, 1.0

    mean_brightness = sum(pixel_values) / (len(pixel_values) * 255.0)

    variance = sum(
        (value - (mean_brightness * 255.0)) ** 2 for value in pixel_values
    ) / len(pixel_values)
    contrast = _clamp((variance**0.5) / 128.0)

    edge_hits = 0
    edge_samples = 0
    for y_value in range(height):
        row_offset = y_value * width
        for x_value in range(width):
            current = pixel_values[row_offset + x_value]
            if x_value + 1 < width:
                right = pixel_values[row_offset + x_value + 1]
                edge_samples += 1
                if abs(current - right) >= 18:
                    edge_hits += 1
            if y_value + 1 < height:
                down = pixel_values[row_offset + width + x_value]
                edge_samples += 1
                if abs(current - down) >= 18:
                    edge_hits += 1

    line_density = _clamp(edge_hits / max(1, edge_samples))

    histogram = [0] * 256
    for value in pixel_values:
        histogram[value] += 1

    entropy = 0.0
    total_pixels = len(pixel_values)
    for bucket_count in histogram:
        if bucket_count == 0:
            continue
        probability = bucket_count / total_pixels
        entropy -= probability * (math.log2(probability))

    texture_entropy = _clamp(entropy / 8.0)

    half_width = max(1, width // 2)
    half_height = max(1, height // 2)

    left_pixels = [
        pixel_values[y * width + x] for y in range(height) for x in range(half_width)
    ]
    right_pixels = [
        pixel_values[y * width + x]
        for y in range(height)
        for x in range(half_width, width)
    ]
    top_pixels = [
        pixel_values[y * width + x] for y in range(half_height) for x in range(width)
    ]
    bottom_pixels = [
        pixel_values[y * width + x]
        for y in range(half_height, height)
        for x in range(width)
    ]

    left_mean = sum(left_pixels) / max(1, len(left_pixels))
    right_mean = sum(right_pixels) / max(1, len(right_pixels))
    top_mean = sum(top_pixels) / max(1, len(top_pixels))
    bottom_mean = sum(bottom_pixels) / max(1, len(bottom_pixels))

    horizontal_balance = 1.0 - min(1.0, abs(left_mean - right_mean) / 255.0)
    vertical_balance = 1.0 - min(1.0, abs(top_mean - bottom_mean) / 255.0)
    composition_balance = _clamp((horizontal_balance + vertical_balance) / 2.0)

    return (
        _clamp(mean_brightness),
        contrast,
        line_density,
        texture_entropy,
        composition_balance,
    )


def _hamming_distance(hash_a: str, hash_b: str) -> int:
    integer_a = int(hash_a, 16)
    integer_b = int(hash_b, 16)
    xor_value = integer_a ^ integer_b
    return xor_value.bit_count()


def _image_has_alpha(pillow_image: Any) -> bool:
    mode = pillow_image.mode
    if mode in {"RGBA", "LA"}:
        return True
    if mode == "P" and "transparency" in pillow_image.info:
        return True
    return False


def _normalize_image_mode(pillow_image: Any) -> Any:
    has_alpha = _image_has_alpha(pillow_image)
    if has_alpha:
        image_module, _ = _load_pillow_modules()
        rgba_image = pillow_image.convert("RGBA")
        background_image = image_module.new(
            "RGBA", rgba_image.size, (255, 255, 255, 255)
        )
        background_image.alpha_composite(rgba_image)
        return background_image.convert("RGB")

    if pillow_image.mode != "RGB":
        return pillow_image.convert("RGB")

    return pillow_image


def _analyze_manga_page_bytes(
    image_bytes: bytes,
    source_ref: str,
    spread_ratio_threshold: float = 1.35,
) -> MangaPageMetadata:
    image_module, image_ops_module = _load_pillow_modules()
    source_hash = _hash_bytes(image_bytes)

    with image_module.open(io.BytesIO(image_bytes)) as raw_image:
        image_format = (raw_image.format or "unknown").lower()
        oriented_image = image_ops_module.exif_transpose(raw_image)
        original_mode = oriented_image.mode
        has_alpha = _image_has_alpha(oriented_image)
        normalized_image = _normalize_image_mode(oriented_image)
        width, height = normalized_image.size
        normalized_mode = normalized_image.mode
        spread_ratio = width / max(height, 1)
        is_spread = spread_ratio >= spread_ratio_threshold
        perceptual_hash = _compute_perceptual_hash(normalized_image)
        (
            mean_brightness,
            contrast,
            line_density,
            texture_entropy,
            composition_balance,
        ) = _compute_visual_feature_signals(normalized_image)

        normalized_buffer = io.BytesIO()
        normalized_image.save(normalized_buffer, format="PNG")
        normalized_bytes = normalized_buffer.getvalue()

    normalized_hash = _hash_bytes(normalized_bytes)

    return MangaPageMetadata(
        source_ref=source_ref,
        width=width,
        height=height,
        format_name=image_format,
        original_mode=original_mode,
        normalized_mode=normalized_mode,
        has_alpha=has_alpha,
        is_spread=is_spread,
        content_hash=source_hash,
        normalized_hash=normalized_hash,
        perceptual_hash=perceptual_hash,
        mean_brightness=mean_brightness,
        contrast=contrast,
        line_density=line_density,
        texture_entropy=texture_entropy,
        composition_balance=composition_balance,
    )


def _compute_text_chunk_hashes(
    normalized_text: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    chunks = [chunk.strip() for chunk in normalized_text.split("\n\n") if chunk.strip()]

    chunk_hashes: list[str] = []
    chunk_signatures: list[str] = []
    for chunk in chunks:
        chunk_hashes.append(_hash_bytes(chunk.encode("utf-8")))
        token_candidates = re.findall(r"[a-zA-Z0-9']+", chunk.lower())
        unique_tokens = sorted(set(token_candidates))[:40]
        signature_seed = " ".join(unique_tokens)
        chunk_signatures.append(_hash_bytes(signature_seed.encode("utf-8")))

    return tuple(chunk_hashes), tuple(chunk_signatures)


def _append_warning(report: IngestionReport, warning: str) -> IngestionReport:
    return replace(report, warnings=(*report.warnings, warning))


def _append_text_warning(
    report: TextIngestionReport, warning: str
) -> TextIngestionReport:
    return replace(report, warnings=(*report.warnings, warning))


def _cache_key(path: Path) -> str:
    return str(path.resolve())


def _apply_text_dedupe(
    report: TextIngestionReport,
    cache: IngestionDedupeCache,
) -> TextIngestionReport:
    source_key = _cache_key(report.source_path)
    source_hash = _compute_file_hash(report.source_path)
    cached_hash = cache.source_fingerprints.get(source_key)
    cached_report = cache.source_reports.get(source_key)

    if cached_hash == source_hash and isinstance(cached_report, TextIngestionReport):
        return _append_text_warning(
            cached_report,
            "Source unchanged; returning cached text ingestion report.",
        )

    chunk_hashes, chunk_signatures = _compute_text_chunk_hashes(report.normalized_text)
    near_duplicate_sources: set[str] = set()
    for chunk_signature in chunk_signatures:
        near_duplicate_sources.update(
            cache.chunk_signature_index.get(chunk_signature, set())
        )

    for known_source, known_text in cache.source_texts.items():
        similarity = difflib.SequenceMatcher(
            None,
            report.normalized_text,
            known_text,
        ).ratio()
        if similarity >= 0.85:
            near_duplicate_sources.add(known_source)

    near_duplicate_sources.discard(source_key)

    enriched_report = replace(
        report,
        source_hash=source_hash,
        chunk_hashes=chunk_hashes,
        chunk_signatures=chunk_signatures,
    )

    if near_duplicate_sources:
        enriched_report = _append_text_warning(
            enriched_report,
            f"Detected {len(near_duplicate_sources)} near-duplicate text source(s).",
        )

    cache.source_fingerprints[source_key] = source_hash
    cache.source_reports[source_key] = enriched_report

    for chunk_hash in chunk_hashes:
        cache.chunk_hash_index.setdefault(chunk_hash, set()).add(source_key)

    for chunk_signature in chunk_signatures:
        cache.chunk_signature_index.setdefault(chunk_signature, set()).add(source_key)

    cache.source_texts[source_key] = report.normalized_text

    return enriched_report


def _apply_page_dedupe(
    report: IngestionReport,
    source_hash: str,
    cache: IngestionDedupeCache,
) -> IngestionReport:
    source_key = _cache_key(report.source_path)
    cached_hash = cache.source_fingerprints.get(source_key)
    cached_report = cache.source_reports.get(source_key)

    if cached_hash == source_hash and isinstance(cached_report, IngestionReport):
        return _append_warning(
            cached_report,
            "Source unchanged; returning cached manga ingestion report.",
        )

    near_duplicate_sources: set[str] = set()
    for page in report.page_metadata:
        near_duplicate_sources.update(
            cache.page_hash_index.get(page.normalized_hash, set())
        )

        for cached_phash, source_keys in cache.page_perceptual_index.items():
            if _hamming_distance(page.perceptual_hash, cached_phash) <= 6:
                near_duplicate_sources.update(source_keys)

    near_duplicate_sources.discard(source_key)

    enriched_report = replace(report, source_hash=source_hash)
    if near_duplicate_sources:
        enriched_report = _append_warning(
            enriched_report,
            f"Detected {len(near_duplicate_sources)} near-duplicate page source(s).",
        )

    cache.source_fingerprints[source_key] = source_hash
    cache.source_reports[source_key] = enriched_report

    for page in report.page_metadata:
        cache.page_hash_index.setdefault(page.normalized_hash, set()).add(source_key)
        cache.page_perceptual_index.setdefault(page.perceptual_hash, set()).add(
            source_key
        )

    return enriched_report


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
    page_metadata: list[MangaPageMetadata] = []

    if len(pages) > policy.max_page_count:
        msg = (
            f"Image page count exceeds limit ({len(pages)} > {policy.max_page_count})."
        )
        raise IngestionSecurityError(msg)

    for page_path in pages:
        _validate_file_size(page_path, policy)
        _validate_extension_mime_and_signature(page_path)

        page_bytes = page_path.read_bytes()
        metadata = _analyze_manga_page_bytes(page_bytes, source_ref=str(page_path))
        page_metadata.append(metadata)

    if not pages:
        warnings.append("No supported manga image pages found.")

    spread_count = sum(1 for metadata in page_metadata if metadata.is_spread)
    page_formats = tuple(sorted({metadata.format_name for metadata in page_metadata}))
    page_hashes = tuple(metadata.normalized_hash for metadata in page_metadata)

    return IngestionReport(
        source_path=folder_path,
        page_count=len(pages),
        warnings=tuple(warnings),
        spread_count=spread_count,
        page_formats=page_formats,
        page_hashes=page_hashes,
        page_metadata=tuple(page_metadata),
    )


def _ingest_cbz_pages_worker(
    archive_path: Path,
    policy: IngestionPolicy,
) -> IngestionReport:
    warnings: list[str] = []
    page_metadata: list[MangaPageMetadata] = []
    _validate_file_size(archive_path, policy)
    _validate_extension_mime_and_signature(archive_path)

    try:
        with ZipFile(archive_path) as cbz_archive:
            sorted_page_names = _validate_archive_limits(cbz_archive, policy)

            for page_name in sorted_page_names:
                with cbz_archive.open(page_name) as member_file:
                    page_bytes = member_file.read()

                metadata = _analyze_manga_page_bytes(page_bytes, source_ref=page_name)
                page_metadata.append(metadata)
    except BadZipFile as error:
        msg = f"CBZ archive '{archive_path.name}' is invalid: {error}."
        raise IngestionSecurityError(msg) from error

    if not sorted_page_names:
        warnings.append("No supported page images found inside CBZ archive.")

    spread_count = sum(1 for metadata in page_metadata if metadata.is_spread)
    page_formats = tuple(sorted({metadata.format_name for metadata in page_metadata}))
    page_hashes = tuple(metadata.normalized_hash for metadata in page_metadata)

    return IngestionReport(
        source_path=archive_path,
        page_count=len(sorted_page_names),
        warnings=tuple(warnings),
        spread_count=spread_count,
        page_formats=page_formats,
        page_hashes=page_hashes,
        page_metadata=tuple(page_metadata),
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


def _classify_dialogue_region(text: str) -> str:
    normalized_text = text.strip().lower()

    narration_prefixes = ("narrator:", "narration:", "[narration]")
    if normalized_text.startswith(narration_prefixes):
        return "narration"

    if normalized_text.startswith("(") and normalized_text.endswith(")"):
        return "thought"

    return "speech"


def _page_dimensions(image_path: Path) -> tuple[int, int]:
    image_module, image_ops_module = _load_pillow_modules()
    with image_module.open(image_path) as raw_image:
        normalized_image = image_ops_module.exif_transpose(raw_image)
        return cast(tuple[int, int], normalized_image.size)


def _parse_sidecar_ocr_regions(image_path: Path) -> list[OcrRegion]:
    sidecar_path = image_path.with_suffix(f"{image_path.suffix}.ocr.txt")
    if not sidecar_path.exists() or not sidecar_path.is_file():
        return []

    page_width, page_height = _page_dimensions(image_path)
    regions: list[OcrRegion] = []

    for line in sidecar_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue

        # Format: x1,y1,x2,y2|confidence|text
        parts = line.split("|", maxsplit=2)
        if len(parts) == 3 and "," in parts[0]:
            coordinate_values = [value.strip() for value in parts[0].split(",")]
            if len(coordinate_values) == 4:
                try:
                    x1, y1, x2, y2 = [int(value) for value in coordinate_values]
                    confidence = _clamp_confidence(float(parts[1]))
                    text = parts[2].strip()
                    if text:
                        regions.append(
                            OcrRegion(
                                x1=x1,
                                y1=y1,
                                x2=x2,
                                y2=y2,
                                text=text,
                                confidence=confidence,
                                region_type=_classify_dialogue_region(text),
                            )
                        )
                        continue
                except ValueError:
                    pass

        regions.append(
            OcrRegion(
                x1=0,
                y1=0,
                x2=page_width,
                y2=page_height,
                text=line,
                confidence=0.65,
                region_type=_classify_dialogue_region(line),
            )
        )

    return regions


def _run_primary_ocr_regions(image_path: Path) -> list[OcrRegion]:
    pytesseract_module = importlib.import_module("pytesseract")
    image_module, image_ops_module = _load_pillow_modules()

    with image_module.open(image_path) as raw_image:
        image = image_ops_module.exif_transpose(raw_image)
        ocr_data = pytesseract_module.image_to_data(
            image,
            output_type=pytesseract_module.Output.DICT,
        )

    regions: list[OcrRegion] = []
    total_entries = len(ocr_data.get("text", []))
    for index in range(total_entries):
        text_value = str(ocr_data["text"][index]).strip()
        if not text_value:
            continue

        try:
            confidence = _clamp_confidence(float(ocr_data["conf"][index]) / 100.0)
        except (TypeError, ValueError):
            confidence = 0.0

        x1 = int(ocr_data["left"][index])
        y1 = int(ocr_data["top"][index])
        width = int(ocr_data["width"][index])
        height = int(ocr_data["height"][index])

        regions.append(
            OcrRegion(
                x1=x1,
                y1=y1,
                x2=x1 + width,
                y2=y1 + height,
                text=text_value,
                confidence=confidence,
                region_type=_classify_dialogue_region(text_value),
            )
        )

    return regions


def _average_ocr_confidence(regions: list[OcrRegion]) -> float:
    if not regions:
        return 0.0
    return sum(region.confidence for region in regions) / len(regions)


def extract_ocr_from_manga_page(
    image_path: Path,
    *,
    min_confidence: float = 0.6,
    use_ensemble: bool = True,
) -> OcrPageReport:
    """Extract OCR regions for one page with fallback support."""

    warnings: list[str] = []

    primary_regions: list[OcrRegion] = []
    try:
        primary_regions = _run_primary_ocr_regions(image_path)
    except Exception as error:  # noqa: BLE001
        warnings.append(f"Primary OCR unavailable; fallback used ({error}).")

    primary_confidence = _average_ocr_confidence(primary_regions)
    fallback_regions: list[OcrRegion] = []

    should_try_fallback = (not primary_regions) or (primary_confidence < min_confidence)
    if should_try_fallback:
        fallback_regions = _parse_sidecar_ocr_regions(image_path)
        if fallback_regions and primary_regions:
            warnings.append("Primary OCR confidence low; combined with fallback OCR.")

    if use_ensemble and primary_regions and fallback_regions:
        if _average_ocr_confidence(fallback_regions) > primary_confidence:
            selected_regions = fallback_regions
            engine = "ensemble-fallback"
        else:
            selected_regions = primary_regions
            engine = "ensemble-primary"
    elif fallback_regions:
        selected_regions = fallback_regions
        engine = "sidecar"
    elif primary_regions:
        selected_regions = primary_regions
        engine = "pytesseract"
    else:
        selected_regions = []
        engine = "none"
        warnings.append("No OCR text extracted from this page.")

    return OcrPageReport(
        source_path=image_path,
        engine=engine,
        regions=tuple(selected_regions),
        average_confidence=_clamp_confidence(_average_ocr_confidence(selected_regions)),
        warnings=tuple(warnings),
    )


def extract_ocr_for_manga_pages(
    page_paths: list[Path],
    *,
    min_confidence: float = 0.6,
    use_ensemble: bool = True,
) -> tuple[OcrPageReport, ...]:
    """Extract OCR reports for a batch of manga pages."""

    reports = [
        extract_ocr_from_manga_page(
            page_path,
            min_confidence=min_confidence,
            use_ensemble=use_ensemble,
        )
        for page_path in page_paths
    ]
    return tuple(reports)


def save_ocr_reports(reports: tuple[OcrPageReport, ...], output_path: Path) -> None:
    """Store OCR reports as JSON with coordinates and confidence values."""

    payload = {
        "pages": [
            {
                "source_path": str(report.source_path),
                "engine": report.engine,
                "average_confidence": report.average_confidence,
                "warnings": list(report.warnings),
                "regions": [
                    {
                        "x1": region.x1,
                        "y1": region.y1,
                        "x2": region.x2,
                        "y2": region.y2,
                        "text": region.text,
                        "confidence": region.confidence,
                        "region_type": region.region_type,
                    }
                    for region in report.regions
                ],
            }
            for report in reports
        ]
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
    idempotent: bool = True,
    dedupe_cache: IngestionDedupeCache = DEFAULT_INGESTION_DEDUPE_CACHE,
) -> IngestionReport:
    """Count supported pages for a loose-image manga folder."""

    if not folder_path.exists() or not folder_path.is_dir():
        return IngestionReport(
            source_path=folder_path,
            page_count=0,
            warnings=("Image folder does not exist.",),
        )

    if use_sandbox:
        report = _run_in_sandboxed_worker(
            "ingest_image_folder_pages",
            (folder_path, policy),
            policy.worker_timeout_seconds,
            IngestionReport,
        )
    else:
        report = _ingest_image_folder_pages_worker(folder_path, policy)

    source_hash = _compute_folder_hash(folder_path)
    if idempotent:
        return _apply_page_dedupe(report, source_hash, dedupe_cache)

    return replace(report, source_hash=source_hash)


def ingest_cbz_pages(
    archive_path: Path,
    policy: IngestionPolicy = DEFAULT_INGESTION_POLICY,
    *,
    use_sandbox: bool = True,
    idempotent: bool = True,
    dedupe_cache: IngestionDedupeCache = DEFAULT_INGESTION_DEDUPE_CACHE,
) -> IngestionReport:
    """Count supported pages in a CBZ archive."""

    if not archive_path.exists() or not archive_path.is_file():
        return IngestionReport(
            source_path=archive_path,
            page_count=0,
            warnings=("CBZ archive does not exist.",),
        )

    if use_sandbox:
        report = _run_in_sandboxed_worker(
            "ingest_cbz_pages",
            (archive_path, policy),
            policy.worker_timeout_seconds,
            IngestionReport,
        )
    else:
        report = _ingest_cbz_pages_worker(archive_path, policy)

    source_hash = _compute_file_hash(archive_path)
    if idempotent:
        return _apply_page_dedupe(report, source_hash, dedupe_cache)

    return replace(report, source_hash=source_hash)


def ingest_text_document(
    source_path: Path,
    policy: IngestionPolicy = DEFAULT_INGESTION_POLICY,
    *,
    use_sandbox: bool = True,
    idempotent: bool = True,
    dedupe_cache: IngestionDedupeCache = DEFAULT_INGESTION_DEDUPE_CACHE,
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
        report = _run_in_sandboxed_worker(
            "ingest_text_document",
            (source_path, policy),
            policy.worker_timeout_seconds,
            TextIngestionReport,
        )
    else:
        report = _ingest_text_document_worker(source_path, policy)

    if idempotent:
        return _apply_text_dedupe(report, dedupe_cache)

    source_hash = _compute_file_hash(source_path)
    chunk_hashes, chunk_signatures = _compute_text_chunk_hashes(report.normalized_text)
    return replace(
        report,
        source_hash=source_hash,
        chunk_hashes=chunk_hashes,
        chunk_signatures=chunk_signatures,
    )
