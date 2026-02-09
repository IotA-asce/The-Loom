"""Tests for phase-6 manga/image generation goals."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from agents.artist import generate_manga_panels
from core.image_generation_engine import (
    ArtistRequest,
    CharacterIdentityPack,
    DiffusionArtifact,
    DiffusionRequest,
    LoRAAdapterManager,
    MockDiffusionBackend,
    build_identity_pack,
    build_scene_blueprint,
    generate_manga_sequence,
    shared_scene_plan_from_text_and_prompt,
)


def _identity_packs() -> tuple[CharacterIdentityPack, ...]:
    mina_pack = build_identity_pack(
        character_id="mina",
        display_name="Mina",
        face_cues=("scar under left eye", "sharp jawline"),
        silhouette_cues=("short coat", "lean frame"),
        costume_cues=("ashen cloak", "steel gauntlet"),
    )
    arin_pack = build_identity_pack(
        character_id="arin",
        display_name="Arin",
        face_cues=("brow cut", "narrow eyes"),
        silhouette_cues=("broad shoulders", "long coat"),
        costume_cues=("red sash", "map satchel"),
    )
    return (mina_pack, arin_pack)


def test_g61_artist_contract_controlnet_and_deterministic_metadata() -> None:
    request = ArtistRequest(
        story_id="artist-story",
        branch_id="main",
        scene_prompt="Mina and Arin confront the eclipse cult at Ash Gate.",
        deterministic=True,
        seed=44,
    )

    first = generate_manga_panels(request)
    second = generate_manga_panels(request)

    assert first.image_count == 4
    assert first.image_count == second.image_count
    assert first.model_id == request.diffusion_config.model_id
    assert first.metadata["base_seed"] == second.metadata["base_seed"]

    first_ids = [panel.diffusion_artifact.artifact_id for panel in first.panels]
    second_ids = [panel.diffusion_artifact.artifact_id for panel in second.panels]
    assert first_ids == second_ids

    for panel in first.panels:
        assert set(panel.diffusion_artifact.controlnet_used) >= {"pose", "lineart"}


def test_g62_scene_blueprint_continuity_and_anchor_validation() -> None:
    blueprint = build_scene_blueprint(
        scene_id="scene:ash-gate",
        title="Ash Gate Clash",
        scene_prompt="Arin and Mina breach the gate under siren alarms",
        panel_count=4,
        beats=("setup", "advance", "impact", "fallout"),
        environment="ash gate courtyard",
        props=("ash key", "broken banner", "gate chain"),
    )

    request = ArtistRequest(
        story_id="artist-story",
        branch_id="main",
        scene_prompt="unused because blueprint provided",
        scene_blueprint=blueprint,
        deterministic=True,
        seed=12,
    )
    result = generate_manga_sequence(request)

    assert len(result.panels) == 4
    assert result.continuity_score >= 0.72
    assert all(
        panel.continuity_anchor.environment == "ash gate courtyard"
        for panel in result.panels
    )
    assert all("ash key" in panel.continuity_anchor.props for panel in result.panels)


def test_g63_atmosphere_presets_and_readability() -> None:
    light_request = ArtistRequest(
        story_id="artist-story",
        branch_id="main",
        scene_prompt="A dawn recon at the harbor",
        atmosphere="light",
        deterministic=True,
        seed=9,
    )
    dark_request = ArtistRequest(
        story_id="artist-story",
        branch_id="main",
        scene_prompt="A midnight assault inside flooded ruins",
        atmosphere="dark",
        deterministic=True,
        seed=9,
    )

    light_result = generate_manga_sequence(light_request)
    dark_result = generate_manga_sequence(dark_request)

    light_brightness = sum(
        panel.diffusion_artifact.brightness for panel in light_result.panels
    ) / len(light_result.panels)
    dark_brightness = sum(
        panel.diffusion_artifact.brightness for panel in dark_result.panels
    ) / len(dark_result.panels)
    dark_contrast = sum(
        panel.diffusion_artifact.contrast for panel in dark_result.panels
    ) / len(dark_result.panels)
    light_contrast = sum(
        panel.diffusion_artifact.contrast for panel in light_result.panels
    ) / len(light_result.panels)

    assert light_brightness > dark_brightness
    assert dark_contrast > light_contrast
    assert dark_result.atmosphere_predictability_score >= 0.7
    assert light_result.atmosphere_predictability_score >= 0.7


def test_g64_identity_pack_lora_hooks_and_drift_detection_triggers() -> None:
    adapter_manager = LoRAAdapterManager()
    request = ArtistRequest(
        story_id="artist-story",
        branch_id="main",
        scene_prompt="Mina guards Arin while moving through smoke",
        identity_packs=_identity_packs(),
        deterministic=True,
        seed=7,
    )

    result = generate_manga_sequence(request, adapter_manager=adapter_manager)
    mina_adapter = adapter_manager.latest_adapter("mina")
    arin_adapter = adapter_manager.latest_adapter("arin")

    assert mina_adapter is not None
    assert arin_adapter is not None
    assert result.identity_consistency_score >= 0.65

    forced_drift = adapter_manager.detect_drift(
        _identity_packs()[0],
        (0.35, 0.42, 0.38, 0.4),
    )
    assert forced_drift.trigger_retraining is True


def test_g65_quality_guardrails_and_selective_redraw_loop() -> None:
    class FlakyBackend(MockDiffusionBackend):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def generate(self, request: DiffusionRequest) -> DiffusionArtifact:
            self.calls += 1
            artifact = super().generate(request)
            if self.calls % 2 == 1:
                return replace(
                    artifact,
                    anatomy_score=0.32,
                    composition_score=0.34,
                    readability_score=0.3,
                )
            return artifact

    backend = FlakyBackend()
    request = ArtistRequest(
        story_id="artist-story",
        branch_id="main",
        scene_prompt="The corridor battle escalates with shattered pillars",
        deterministic=True,
        seed=21,
        max_redraw_attempts=1,
    )
    result = generate_manga_sequence(request, backend=backend)

    assert backend.calls > request.panel_count
    assert any(panel.redraw_count > 0 for panel in result.panels)
    assert 0.0 <= result.final_pass_rate <= 1.0


def test_g66_cross_modal_alignment_and_reconcile_workflow() -> None:
    prose_reference = (
        "Mina crashes through the harbor gate under thunder and sparks.",
        "Arin drags the injured scout behind a broken crane.",
        "The eclipse cult fires from the watchtower while smoke rises.",
        "They retreat toward the archive tunnel with the ash key.",
    )

    mismatched_request = ArtistRequest(
        story_id="artist-story",
        branch_id="main",
        scene_prompt="A quiet tea gathering in a bright meadow",
        scene_blueprint=build_scene_blueprint(
            scene_id="scene:mismatch",
            title="Mismatch",
            scene_prompt="Tea ceremony under clear sky",
            beats=(
                "pouring tea quietly",
                "sharing pastries",
                "laughing at old stories",
                "watching birds over the field",
            ),
            environment="sunlit meadow",
            props=("tea set", "pastry tray", "picnic cloth"),
        ),
        prose_reference=prose_reference,
        deterministic=True,
        seed=33,
    )
    mismatched_result = generate_manga_sequence(mismatched_request)

    shared_blueprint = shared_scene_plan_from_text_and_prompt(
        scene_id="scene:shared",
        scene_prompt="Harbor assault with retreat through archive tunnel",
        prose_reference=prose_reference,
    )
    aligned_request = ArtistRequest(
        story_id="artist-story",
        branch_id="main",
        scene_prompt="ignored by provided blueprint",
        scene_blueprint=shared_blueprint,
        prose_reference=prose_reference,
        deterministic=True,
        seed=33,
    )
    aligned_result = generate_manga_sequence(aligned_request)

    assert mismatched_result.alignment_report.mismatch_rate > 0.0
    assert mismatched_result.reconcile_plan.actions
    assert (
        aligned_result.alignment_report.mismatch_rate
        <= mismatched_result.alignment_report.mismatch_rate
    )
    assert (
        aligned_result.reconcile_plan.mismatch_rate_after_estimate
        <= aligned_result.reconcile_plan.mismatch_rate_before
    )


def test_phase6_done_criteria_thresholds_hold() -> None:
    thresholds = json.loads(
        Path("tests/fixtures/golden/artist_generation_thresholds.json").read_text(
            encoding="utf-8"
        )
    )

    prose_reference = (
        "Mina breaches the gate while Arin signals the retreat path.",
        "The cult surges through smoke and the tower siren fails.",
        "They clash at the archive steps beneath shattered lanterns.",
        "Arin and Mina secure the ash key before dawn.",
    )
    blueprint = shared_scene_plan_from_text_and_prompt(
        scene_id="scene:threshold",
        scene_prompt="Gate breach and archive retreat under siege",
        prose_reference=prose_reference,
        atmosphere="dark",
    )

    request = ArtistRequest(
        story_id="artist-story",
        branch_id="main",
        scene_prompt="ignored by blueprint",
        scene_blueprint=blueprint,
        prose_reference=prose_reference,
        identity_packs=_identity_packs(),
        atmosphere="dark",
        deterministic=True,
        seed=52,
    )
    result = generate_manga_sequence(request)

    assert result.continuity_score >= thresholds["min_continuity_score"]
    assert result.identity_consistency_score >= thresholds["min_identity_consistency"]
    assert (
        result.atmosphere_predictability_score
        >= thresholds["min_atmosphere_predictability"]
    )
    assert (
        result.alignment_report.mismatch_rate
        <= thresholds["max_cross_modal_mismatch_rate"]
    )
