"""Tests for text, PDF, and EPUB ingestion behavior."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import agents.archivist as archivist
import pytest


def _create_minimal_epub(epub_path: Path) -> None:
    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    package_opf = """<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Sample Book</dc:title>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>
"""

    chapter_html = """<html><head><title>Chapter One</title></head>
<body><h1>Chapter One</h1><p>The hallway is quiet.</p></body></html>
"""

    with ZipFile(epub_path, "w") as epub_archive:
        epub_archive.writestr(
            "mimetype", "application/epub+zip", compress_type=ZIP_STORED
        )
        epub_archive.writestr("META-INF/container.xml", container_xml)
        epub_archive.writestr("OPS/content.opf", package_opf)
        epub_archive.writestr(
            "OPS/chapter1.xhtml", chapter_html, compress_type=ZIP_DEFLATED
        )


def _create_epub_without_container(epub_path: Path) -> None:
    html_payload = (
        "<html><body><h1>Fallback Chapter</h1><p>Recovered.</p></body></html>"
    )
    with ZipFile(epub_path, "w", compression=ZIP_DEFLATED) as epub_archive:
        epub_archive.writestr("chapter-a.xhtml", html_payload)


def test_txt_ingestion_normalizes_encoding_and_newlines(tmp_path: Path) -> None:
    text_path = tmp_path / "story.txt"
    text_path.write_bytes("Line one\r\nLínea dos\r\n".encode("cp1252"))

    report = archivist.ingest_text_document(text_path, use_sandbox=False)

    assert report.parser_used == "txt"
    assert report.normalized_text == "Line one\nLínea dos"
    assert report.confidence < 0.9
    assert any("fallback encoding" in warning for warning in report.warnings)


def test_pdf_ingestion_uses_fallback_when_primary_parser_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "chapter.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n(Fallback extracted text)\n%%EOF")

    def failing_primary_parser(path: Path) -> tuple[str, int]:
        _ = path
        raise RuntimeError("simulated parser failure")

    monkeypatch.setattr(archivist, "_parse_pdf_with_pypdf", failing_primary_parser)

    report = archivist.ingest_text_document(pdf_path, use_sandbox=False)

    assert report.parser_used == "pdf-fallback"
    assert "Fallback extracted text" in report.normalized_text
    assert any("fallback extraction" in warning for warning in report.warnings)


def test_epub_ingestion_extracts_chapters_from_spine(tmp_path: Path) -> None:
    epub_path = tmp_path / "story.epub"
    _create_minimal_epub(epub_path)

    report = archivist.ingest_text_document(epub_path, use_sandbox=False)

    assert report.parser_used == "epub"
    assert len(report.chapters) == 1
    assert report.chapters[0].title == "Chapter One"
    assert "The hallway is quiet." in report.chapters[0].content
    assert report.confidence >= 0.8


def test_epub_ingestion_falls_back_when_container_is_missing(tmp_path: Path) -> None:
    epub_path = tmp_path / "fallback.epub"
    _create_epub_without_container(epub_path)

    report = archivist.ingest_text_document(epub_path, use_sandbox=False)

    assert report.parser_used == "epub-fallback"
    assert len(report.chapters) == 1
    assert "Recovered." in report.normalized_text
    assert any("fallback scan" in warning for warning in report.warnings)


def test_text_ingestion_reports_errors_for_non_readable_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n%%EOF")

    def empty_primary_parser(path: Path) -> tuple[str, int]:
        _ = path
        return "", 1

    monkeypatch.setattr(archivist, "_parse_pdf_with_pypdf", empty_primary_parser)
    monkeypatch.setattr(archivist, "_parse_pdf_with_fallback", lambda _path: "")

    report = archivist.ingest_text_document(pdf_path, use_sandbox=False)

    assert report.errors
    assert "No extractable text" in report.errors[0]
    assert report.confidence <= 0.2


def test_text_ingestion_rejects_unsupported_extension(tmp_path: Path) -> None:
    markdown_path = tmp_path / "notes.md"
    markdown_path.write_text("# Not supported")

    with pytest.raises(
        archivist.IngestionSecurityError, match="Unsupported text source"
    ):
        archivist.ingest_text_document(markdown_path, use_sandbox=False)
