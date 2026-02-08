"""Tests for phase-2 tone, style, and maturity profiling."""

from __future__ import annotations

import json
from pathlib import Path

from agents import archivist
from core.profile_engine import (
    MaturityOverride,
    ProfileRegistry,
    SceneLabelBenchmark,
    TextSceneCorrection,
    analyze_text_profile,
    analyze_visual_profile,
    build_maturity_profile,
    compute_tone_jitter_index,
    evaluate_scene_label_predictions,
)


def _create_checkerboard(path: Path, *, size: int = 120, block: int = 10) -> None:
    image_module = __import__("PIL.Image", fromlist=["Image"])
    image = image_module.new("RGB", (size, size), "white")
    pixels = image.load()

    for y_value in range(size):
        for x_value in range(size):
            is_dark = ((x_value // block) + (y_value // block)) % 2 == 0
            pixels[x_value, y_value] = (20, 20, 20) if is_dark else (235, 235, 235)

    image.save(path, format="PNG")


def _create_flat_image(
    path: Path, *, color: tuple[int, int, int], size: tuple[int, int]
) -> None:
    image_module = __import__("PIL.Image", fromlist=["Image"])
    image = image_module.new("RGB", size, color)
    image.save(path, format="PNG")


def test_text_profile_extracts_labels_uncertainty_shifts_and_peaks() -> None:
    text = (
        "They share warm tea and laugh together in a cozy kitchen.\n\n"
        "The blade tears flesh, blood sprays, and everyone screams in terror!\n\n"
        "They walk home quietly."
    )

    profile = analyze_text_profile(text, source_id="demo")

    assert len(profile.scenes) == 3
    assert profile.scenes[0].label_scores["wholesome"] > 0.4
    assert profile.scenes[1].label_scores["violence"] > 0.5
    assert profile.scenes[2].uncertainty > 0.45
    assert 1 in profile.abrupt_shift_indices
    assert 1 in profile.peak_intensity_indices


def test_visual_profile_uses_style_cues_and_aggregates(tmp_path: Path) -> None:
    _create_flat_image(tmp_path / "page-1.png", color=(240, 240, 240), size=(420, 620))
    _create_checkerboard(tmp_path / "page-2.png")
    _create_flat_image(tmp_path / "page-3.png", color=(18, 18, 18), size=(860, 420))

    ingestion_report = archivist.ingest_image_folder_pages(
        tmp_path,
        use_sandbox=False,
        idempotent=False,
    )
    visual_profile = analyze_visual_profile(
        ingestion_report.page_metadata,
        source_id="panels",
        scene_size=2,
        chapter_size=3,
    )

    assert len(visual_profile.panel_profiles) == 3
    assert len(visual_profile.scene_profiles) == 2
    assert len(visual_profile.chapter_profiles) == 1
    assert visual_profile.panel_profiles[1].line_density > 0.05
    assert visual_profile.panel_profiles[2].darkness > 0.8
    assert (
        "dark" in visual_profile.tone_distribution
        or "gritty" in visual_profile.tone_distribution
    )


def test_maturity_profile_smoothing_and_preset_mapping() -> None:
    text = (
        "A calm morning with kind words.\n\n"
        "The battle begins, blades clash, and blood runs cold!\n\n"
        "The nightmare lingers in his mind with paranoia and dread."
    )

    text_profile = analyze_text_profile(text, source_id="maturity")
    maturity_profile = build_maturity_profile(text_profile, None, smoothing_window=3)

    assert len(maturity_profile.raw_scores) == 3
    assert len(maturity_profile.smoothed_scores) == 3
    assert maturity_profile.maturity_band in {"all_ages", "teen", "mature", "explicit"}
    assert maturity_profile.preset.band == maturity_profile.maturity_band
    assert maturity_profile.tone_jitter_index <= compute_tone_jitter_index(
        maturity_profile.raw_scores
    )


def test_profile_registry_tracks_corrections_versions_and_override_audit(
    tmp_path: Path,
) -> None:
    _create_flat_image(tmp_path / "page-1.png", color=(235, 235, 235), size=(420, 620))
    _create_flat_image(tmp_path / "page-2.png", color=(22, 22, 22), size=(420, 620))

    ingestion_report = archivist.ingest_image_folder_pages(
        tmp_path,
        use_sandbox=False,
        idempotent=False,
    )
    visual_profile = analyze_visual_profile(
        ingestion_report.page_metadata, source_id="branch"
    )

    text_profile = analyze_text_profile(
        "A quiet day.\n\nA violent fight erupts with blood.",
        source_id="branch",
    )
    maturity_profile = build_maturity_profile(text_profile, visual_profile)

    registry = ProfileRegistry()
    version_1 = registry.create_initial_version(
        branch_id="branch-a",
        text_profile=text_profile,
        visual_profile=visual_profile,
        maturity_profile=maturity_profile,
        actor="system",
        reason="bootstrap",
    )

    version_2 = registry.apply_text_corrections(
        branch_id="branch-a",
        base_version_id=version_1.version_id,
        corrections=(
            TextSceneCorrection(
                scene_index=0,
                label_updates={"wholesome": 0.8},
                confidence_override=0.9,
                note="manual correction",
            ),
        ),
        actor="editor",
        reason="scene correction",
    )

    version_3 = registry.apply_maturity_override(
        branch_id="branch-a",
        base_version_id=version_2.version_id,
        override=MaturityOverride(
            target_band="mature",
            reason="keep intensity aligned with canon",
            actor="director",
        ),
    )

    versions = registry.get_branch_versions("branch-a")
    audit_events = registry.get_override_audit("branch-a")

    assert len(versions) == 3
    assert versions[1].parent_version_id == version_1.version_id
    assert versions[2].parent_version_id == version_2.version_id
    assert versions[2].maturity_profile.maturity_band == "mature"
    assert len(audit_events) == 1
    assert audit_events[0].version_id == version_3.version_id
    assert audit_events[0].actor == "director"


def test_benchmark_precision_recall_and_tone_jitter_thresholds() -> None:
    fixture_path = Path("tests/fixtures/golden/profile_benchmark_scenes.json")
    fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    scene_texts = [scene["text"] for scene in fixture_payload["scenes"]]
    benchmark = tuple(
        SceneLabelBenchmark(scene_index=index, labels=tuple(scene["labels"]))
        for index, scene in enumerate(fixture_payload["scenes"])
    )

    text_profile = analyze_text_profile("\n\n".join(scene_texts), source_id="benchmark")
    evaluation = evaluate_scene_label_predictions(text_profile, benchmark)
    maturity_profile = build_maturity_profile(text_profile, None)

    thresholds = fixture_payload["thresholds"]
    assert evaluation.precision >= thresholds["precision"]
    assert evaluation.recall >= thresholds["recall"]
    assert maturity_profile.tone_jitter_index <= thresholds["tone_jitter_tolerance"]
