"""Tests for OCR baseline, fallback, and report storage."""

from __future__ import annotations

import json
from pathlib import Path

import agents.archivist as archivist
import pytest


def _create_test_image(path: Path) -> None:
    image_module = __import__("PIL.Image", fromlist=["Image"])
    image = image_module.new("RGB", (320, 180), "white")
    image.save(path, format="PNG")


def test_sidecar_ocr_fallback_extracts_regions(tmp_path: Path) -> None:
    page_path = tmp_path / "panel.png"
    _create_test_image(page_path)

    sidecar_path = page_path.with_suffix(f"{page_path.suffix}.ocr.txt")
    sidecar_path.write_text(
        "10,20,140,70|0.92|Narrator: The storm arrived.\n"
        "15,90,180,140|0.88|Who is there?\n",
        encoding="utf-8",
    )

    report = archivist.extract_ocr_from_manga_page(page_path)

    assert report.engine in {"sidecar", "ensemble-fallback"}
    assert len(report.regions) == 2
    assert report.regions[0].region_type == "narration"
    assert report.regions[1].region_type == "speech"
    assert report.regions[0].x1 == 10
    assert report.regions[0].confidence == pytest.approx(0.92)


def test_ocr_ensemble_prefers_higher_confidence_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page_path = tmp_path / "panel.png"
    _create_test_image(page_path)
    page_path.with_suffix(f"{page_path.suffix}.ocr.txt").write_text(
        "0,0,100,80|0.95|Narration: fallback text",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        archivist,
        "_run_primary_ocr_regions",
        lambda _path: [
            archivist.OcrRegion(
                x1=0,
                y1=0,
                x2=40,
                y2=20,
                text="primary",
                confidence=0.2,
                region_type="speech",
            )
        ],
    )

    report = archivist.extract_ocr_from_manga_page(page_path, min_confidence=0.6)

    assert report.engine == "ensemble-fallback"
    assert report.average_confidence > 0.9


def test_ocr_report_serialization_includes_coordinates(tmp_path: Path) -> None:
    page_path = tmp_path / "panel.png"
    _create_test_image(page_path)
    page_path.with_suffix(f"{page_path.suffix}.ocr.txt").write_text(
        "5,6,40,50|0.8|(I should run)",
        encoding="utf-8",
    )

    reports = archivist.extract_ocr_for_manga_pages([page_path])
    output_path = tmp_path / "ocr-report.json"
    archivist.save_ocr_reports(reports, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    region_payload = payload["pages"][0]["regions"][0]

    assert region_payload["x1"] == 5
    assert region_payload["y2"] == 50
    assert region_payload["confidence"] == pytest.approx(0.8)
    assert region_payload["region_type"] == "thought"
