"""Manga/image generation engine for artist-agent workflows."""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from statistics import mean
from typing import TYPE_CHECKING

from .text_generation_engine import WriterResult

if TYPE_CHECKING:
    from .diffusion_backend import DiffusionBackend as NewDiffusionBackend
    from .image_storage import ImageStorage, ImageMetadata

_WORD_PATTERN = re.compile(r"[A-Za-z0-9']+")


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _WORD_PATTERN.findall(text)}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ControlNetCondition:
    """ControlNet-compatible guidance condition for diffusion generation."""

    control_type: str
    weight: float
    reference_hint: str


@dataclass(frozen=True)
class DiffusionConfig:
    """Diffusion backend configuration for panel generation."""

    model_id: str = "mock-sd-controlnet-v1"
    sampler: str = "ddim"
    steps: int = 28
    guidance_scale: float = 7.5


@dataclass(frozen=True)
class LightingConstraint:
    """Explicit lighting constraints used in atmosphere control."""

    key_light: str
    fill_light: str
    rim_light: str


@dataclass(frozen=True)
class TextureConstraint:
    """Texture and rendering constraints for panel generation."""

    surface_texture: str
    line_weight: str
    grain_level: str


@dataclass(frozen=True)
class AtmospherePreset:
    """Atmosphere preset controlling brightness/contrast/texture targets."""

    preset_id: str
    brightness_target: float
    contrast_target: float
    texture_target: float
    lighting: LightingConstraint
    texture: TextureConstraint


ATMOSPHERE_PRESETS: dict[str, AtmospherePreset] = {
    "light": AtmospherePreset(
        preset_id="light",
        brightness_target=0.76,
        contrast_target=0.48,
        texture_target=0.35,
        lighting=LightingConstraint(
            key_light="soft warm daylight",
            fill_light="gentle bounced fill",
            rim_light="subtle edge glow",
        ),
        texture=TextureConstraint(
            surface_texture="clean paper",
            line_weight="medium",
            grain_level="low",
        ),
    ),
    "dark": AtmospherePreset(
        preset_id="dark",
        brightness_target=0.24,
        contrast_target=0.84,
        texture_target=0.78,
        lighting=LightingConstraint(
            key_light="hard directional moonlight",
            fill_light="minimal cold fill",
            rim_light="sharp silhouette rim",
        ),
        texture=TextureConstraint(
            surface_texture="grime and cracked stone",
            line_weight="heavy",
            grain_level="high",
        ),
    ),
    "balanced": AtmospherePreset(
        preset_id="balanced",
        brightness_target=0.52,
        contrast_target=0.62,
        texture_target=0.52,
        lighting=LightingConstraint(
            key_light="neutral cinematic key",
            fill_light="moderate ambient fill",
            rim_light="controlled edge separation",
        ),
        texture=TextureConstraint(
            surface_texture="mixed surfaces",
            line_weight="medium-heavy",
            grain_level="medium",
        ),
    ),
}


def atmosphere_preset(preset_id: str) -> AtmospherePreset:
    """Resolve atmosphere preset by id with balanced fallback."""

    return ATMOSPHERE_PRESETS.get(preset_id, ATMOSPHERE_PRESETS["balanced"])


@dataclass(frozen=True)
class ContinuityAnchor:
    """Continuity anchors shared across panel sequences."""

    camera: str
    pose: str
    environment: str
    props: tuple[str, ...]


@dataclass(frozen=True)
class SceneBlueprintPanel:
    """Structured scene plan entry for one panel."""

    panel_index: int
    beat: str
    prompt: str
    continuity_anchor: ContinuityAnchor


@dataclass(frozen=True)
class SceneBlueprint:
    """Shared scene plan used by text and image generation."""

    scene_id: str
    title: str
    panels: tuple[SceneBlueprintPanel, ...]
    atmosphere: str


@dataclass(frozen=True)
class CharacterIdentityPack:
    """Character identity cues for consistent visual rendering."""

    character_id: str
    display_name: str
    face_cues: tuple[str, ...]
    silhouette_cues: tuple[str, ...]
    costume_cues: tuple[str, ...]
    identity_fingerprint: str


def build_identity_pack(
    *,
    character_id: str,
    display_name: str,
    face_cues: tuple[str, ...],
    silhouette_cues: tuple[str, ...],
    costume_cues: tuple[str, ...],
) -> CharacterIdentityPack:
    """Build deterministic identity pack fingerprint from visual cues."""

    fingerprint_material = "|".join(
        [
            character_id,
            display_name,
            ",".join(face_cues),
            ",".join(silhouette_cues),
            ",".join(costume_cues),
        ]
    )
    fingerprint = _sha256(fingerprint_material)
    return CharacterIdentityPack(
        character_id=character_id,
        display_name=display_name,
        face_cues=face_cues,
        silhouette_cues=silhouette_cues,
        costume_cues=costume_cues,
        identity_fingerprint=fingerprint,
    )


@dataclass(frozen=True)
class LoRAAdapterRecord:
    """LoRA/adaptor metadata managed by the artist pipeline."""

    adapter_id: str
    character_id: str
    base_model_id: str
    version: int
    trigger_tokens: tuple[str, ...]
    trained_steps: int
    status: str
    created_at: str


@dataclass(frozen=True)
class DriftDetectionResult:
    """Identity drift detection outcome for generated panels."""

    drift_score: float
    trigger_retraining: bool
    reasons: tuple[str, ...]


class LoRAAdapterManager:
    """Simple LoRA/adaptor registry with training hooks."""

    def __init__(self) -> None:
        self._records: dict[str, list[LoRAAdapterRecord]] = {}

    def training_hook(
        self,
        identity_pack: CharacterIdentityPack,
        *,
        base_model_id: str,
        trained_steps: int = 120,
    ) -> LoRAAdapterRecord:
        """Create and register a deterministic adapter record."""

        existing_records = self._records.get(identity_pack.character_id, [])
        version = len(existing_records) + 1
        adapter_id = f"lora:{identity_pack.character_id}:v{version:03d}"
        trigger_tokens = (
            identity_pack.display_name.lower(),
            identity_pack.character_id.lower(),
        )
        record = LoRAAdapterRecord(
            adapter_id=adapter_id,
            character_id=identity_pack.character_id,
            base_model_id=base_model_id,
            version=version,
            trigger_tokens=trigger_tokens,
            trained_steps=trained_steps,
            status="ready",
            created_at=_timestamp(),
        )
        self._records.setdefault(identity_pack.character_id, []).append(record)
        return record

    def latest_adapter(self, character_id: str) -> LoRAAdapterRecord | None:
        records = self._records.get(character_id, [])
        return records[-1] if records else None

    def detect_drift(
        self,
        identity_pack: CharacterIdentityPack,
        panel_identity_scores: tuple[float, ...],
    ) -> DriftDetectionResult:
        """Detect identity drift and recommend retraining when needed."""

        if not panel_identity_scores:
            return DriftDetectionResult(
                drift_score=1.0,
                trigger_retraining=True,
                reasons=("no identity scores available",),
            )

        average_identity = mean(panel_identity_scores)
        drift_score = _clamp(1.0 - average_identity)
        reasons: list[str] = []

        if drift_score > 0.24:
            reasons.append("average identity score below threshold")
        if min(panel_identity_scores) < 0.55:
            reasons.append("at least one panel has severe identity drift")

        trigger_retraining = bool(reasons)
        return DriftDetectionResult(
            drift_score=drift_score,
            trigger_retraining=trigger_retraining,
            reasons=tuple(reasons),
        )


@dataclass(frozen=True)
class DiffusionRequest:
    """Low-level request passed to the diffusion backend."""

    prompt: str
    negative_prompt: str
    width: int
    height: int
    seed: int
    model_id: str
    sampler: str
    steps: int
    guidance_scale: float
    controlnet_conditions: tuple[ControlNetCondition, ...]
    brightness_target: float
    contrast_target: float
    texture_target: float


@dataclass(frozen=True)
class DiffusionArtifact:
    """Deterministic artifact metadata returned by diffusion backend."""

    artifact_id: str
    latent_hash: str
    prompt: str
    negative_prompt: str
    seed: int
    model_id: str
    sampler: str
    steps: int
    guidance_scale: float
    controlnet_used: tuple[str, ...]
    brightness: float
    contrast: float
    texture_density: float
    anatomy_score: float
    composition_score: float
    readability_score: float


class DiffusionBackend:
    """Base diffusion backend interface."""

    def generate(self, request: DiffusionRequest) -> DiffusionArtifact:
        """Generate panel artifact metadata from diffusion request."""

        raise NotImplementedError


class MockDiffusionBackend(DiffusionBackend):
    """Deterministic mock diffusion backend with ControlNet-compatible flow."""

    def generate(self, request: DiffusionRequest) -> DiffusionArtifact:
        controlnet_id = ",".join(
            f"{condition.control_type}:{condition.weight:.2f}"
            for condition in request.controlnet_conditions
        )
        payload = "|".join(
            [
                request.prompt,
                request.negative_prompt,
                str(request.seed),
                request.model_id,
                request.sampler,
                str(request.steps),
                f"{request.guidance_scale:.3f}",
                controlnet_id,
            ]
        )
        latent_hash = _sha256(payload)

        base_a = int(latent_hash[0:8], 16) / 0xFFFFFFFF
        base_b = int(latent_hash[8:16], 16) / 0xFFFFFFFF
        base_c = int(latent_hash[16:24], 16) / 0xFFFFFFFF
        base_d = int(latent_hash[24:32], 16) / 0xFFFFFFFF
        base_e = int(latent_hash[32:40], 16) / 0xFFFFFFFF

        brightness = _clamp((base_a * 0.42) + (request.brightness_target * 0.58))
        contrast = _clamp((base_b * 0.38) + (request.contrast_target * 0.62))
        texture_density = _clamp((base_c * 0.45) + (request.texture_target * 0.55))

        anatomy_score = _clamp(0.45 + (base_d * 0.45) + (contrast * 0.08))
        composition_score = _clamp(
            0.44 + (base_e * 0.42) + ((1.0 - abs(brightness - 0.5)) * 0.14)
        )
        readability_score = _clamp(
            (contrast * 0.42) + ((1.0 - abs(brightness - 0.48)) * 0.58)
        )

        return DiffusionArtifact(
            artifact_id=latent_hash[:16],
            latent_hash=latent_hash,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            seed=request.seed,
            model_id=request.model_id,
            sampler=request.sampler,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            controlnet_used=tuple(
                condition.control_type for condition in request.controlnet_conditions
            ),
            brightness=brightness,
            contrast=contrast,
            texture_density=texture_density,
            anatomy_score=anatomy_score,
            composition_score=composition_score,
            readability_score=readability_score,
        )


@dataclass(frozen=True)
class PanelQualityCheck:
    """Quality check result for one generated panel."""

    panel_index: int
    anatomy_score: float
    composition_score: float
    readability_score: float
    passed: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class PanelArtifact:
    """Generated panel artifact with metadata and continuity fields."""

    panel_index: int
    beat: str
    prompt: str
    negative_prompt: str
    continuity_anchor: ContinuityAnchor
    atmosphere_preset: str
    diffusion_artifact: DiffusionArtifact
    identity_scores: dict[str, float]
    adapter_ids: tuple[str, ...]
    redraw_count: int
    quality_check: PanelQualityCheck


@dataclass(frozen=True)
class CrossModalMismatch:
    """Cross-modal mismatch between prose and generated panel."""

    panel_index: int
    reasons: tuple[str, ...]
    prose_excerpt: str
    panel_prompt: str


@dataclass(frozen=True)
class CrossModalAlignmentReport:
    """Cross-modal alignment report across panel sequence."""

    mismatches: tuple[CrossModalMismatch, ...]
    mismatch_rate: float
    alignment_score: float


@dataclass(frozen=True)
class ReconcileAction:
    """Action item to reconcile cross-modal mismatch."""

    panel_index: int
    action: str
    reason: str
    updated_prompt: str


@dataclass(frozen=True)
class ReconcilePlan:
    """Reconcile workflow output for mismatched panel sequence."""

    actions: tuple[ReconcileAction, ...]
    mismatch_rate_before: float
    mismatch_rate_after_estimate: float


@dataclass(frozen=True)
class ArtistRequest:
    """Artist generation request contract."""

    story_id: str
    branch_id: str
    scene_prompt: str
    panel_count: int = 4
    scene_blueprint: SceneBlueprint | None = None
    atmosphere: str = "balanced"
    diffusion_config: DiffusionConfig = DiffusionConfig()
    controlnet_conditions: tuple[ControlNetCondition, ...] = (
        ControlNetCondition("pose", 0.8, "maintain body geometry"),
        ControlNetCondition("lineart", 0.65, "preserve panel draft structure"),
    )
    identity_packs: tuple[CharacterIdentityPack, ...] = ()
    prose_reference: tuple[str, ...] = ()
    deterministic: bool = True
    seed: int | None = None
    max_redraw_attempts: int = 2


@dataclass(frozen=True)
class ArtistResult:
    """Artist generation output with metrics and reconciliation metadata."""

    branch_id: str
    image_count: int
    model_id: str
    scene_blueprint: SceneBlueprint
    panels: tuple[PanelArtifact, ...]
    continuity_score: float
    identity_consistency_score: float
    atmosphere_predictability_score: float
    rejected_count: int
    final_pass_rate: float
    alignment_report: CrossModalAlignmentReport
    reconcile_plan: ReconcilePlan
    metadata: dict[str, str]


def build_scene_blueprint(
    *,
    scene_id: str,
    title: str,
    scene_prompt: str,
    panel_count: int = 4,
    beats: tuple[str, ...] = (),
    environment: str = "ruined corridor",
    props: tuple[str, ...] = ("lantern", "broken gate"),
    camera_sequence: tuple[str, ...] = ("wide", "mid", "close", "over-shoulder"),
    pose_sequence: tuple[str, ...] = ("stance", "advance", "impact", "aftermath"),
    atmosphere: str = "balanced",
) -> SceneBlueprint:
    """Build shared panel blueprint with continuity anchors."""

    panel_total = max(1, panel_count)
    beat_values: list[str] = list(beats)
    while len(beat_values) < panel_total:
        beat_values.append(f"beat-{len(beat_values) + 1}")

    panels: list[SceneBlueprintPanel] = []
    for panel_index in range(panel_total):
        camera = camera_sequence[min(panel_index, len(camera_sequence) - 1)]
        pose = pose_sequence[min(panel_index, len(pose_sequence) - 1)]
        anchor = ContinuityAnchor(
            camera=camera,
            pose=pose,
            environment=environment,
            props=props,
        )
        beat = beat_values[panel_index]
        prompt = (
            f"{scene_prompt}. Panel beat: {beat}. "
            f"Camera: {camera}. Pose: {pose}. Environment: {environment}. "
            f"Props: {', '.join(props)}."
        )
        panels.append(
            SceneBlueprintPanel(
                panel_index=panel_index,
                beat=beat,
                prompt=prompt,
                continuity_anchor=anchor,
            )
        )

    return SceneBlueprint(
        scene_id=scene_id,
        title=title,
        panels=tuple(panels),
        atmosphere=atmosphere,
    )


def shared_scene_plan_from_text_and_prompt(
    *,
    scene_id: str,
    scene_prompt: str,
    prose_reference: tuple[str, ...],
    panel_count: int = 4,
    atmosphere: str = "balanced",
) -> SceneBlueprint:
    """Create shared scene plan that aligns panel beats with prose reference."""

    beats = tuple(
        excerpt.split(".")[0].strip() for excerpt in prose_reference if excerpt.strip()
    )
    if not beats:
        beats = (
            "establishing frame",
            "escalation",
            "turning point",
            "resolution hook",
        )

    return build_scene_blueprint(
        scene_id=scene_id,
        title="shared scene plan",
        scene_prompt=scene_prompt,
        panel_count=panel_count,
        beats=beats,
        atmosphere=atmosphere,
    )


def _continuity_similarity(
    anchor_a: ContinuityAnchor, anchor_b: ContinuityAnchor
) -> float:
    score = 0.0
    if anchor_a.environment == anchor_b.environment:
        score += 0.4
    shared_props = set(anchor_a.props) & set(anchor_b.props)
    score += min(0.3, len(shared_props) * 0.08)
    if anchor_a.camera == anchor_b.camera:
        score += 0.15
    else:
        camera_pair = {anchor_a.camera, anchor_b.camera}
        if camera_pair in (
            {"wide", "mid"},
            {"mid", "close"},
            {"close", "over-shoulder"},
        ):
            score += 0.1
    if anchor_a.pose == anchor_b.pose:
        score += 0.1
    return _clamp(score)


def validate_panel_continuity(panels: tuple[PanelArtifact, ...]) -> float:
    """Compute continuity score across adjacent panel anchors."""

    if len(panels) < 2:
        return 1.0

    similarities = [
        _continuity_similarity(
            panels[index - 1].continuity_anchor,
            panels[index].continuity_anchor,
        )
        for index in range(1, len(panels))
    ]
    return _clamp(mean(similarities))


def _atmosphere_prompt_suffix(preset: AtmospherePreset) -> str:
    return (
        "Lighting constraints: "
        f"key={preset.lighting.key_light}; fill={preset.lighting.fill_light}; "
        f"rim={preset.lighting.rim_light}. "
        "Texture constraints: "
        f"surface={preset.texture.surface_texture}; line={preset.texture.line_weight}; "
        f"grain={preset.texture.grain_level}."
    )


def _identity_tokens(identity_pack: CharacterIdentityPack) -> tuple[str, ...]:
    tokens = [
        identity_pack.display_name,
        *identity_pack.face_cues,
        *identity_pack.silhouette_cues,
        *identity_pack.costume_cues,
    ]
    return tuple(token for token in tokens if token)


def _identity_score_from_prompt(
    prompt: str,
    identity_pack: CharacterIdentityPack,
) -> float:
    prompt_tokens = _tokenize(prompt)
    required_tokens = _tokenize(" ".join(_identity_tokens(identity_pack)))
    if not required_tokens:
        return 1.0
    overlap = len(prompt_tokens & required_tokens)
    return _clamp(overlap / len(required_tokens))


def _quality_check(artifact: DiffusionArtifact, panel_index: int) -> PanelQualityCheck:
    reasons: list[str] = []
    if artifact.anatomy_score < 0.55:
        reasons.append("low anatomy stability")
    if artifact.composition_score < 0.55:
        reasons.append("weak composition framing")
    if artifact.readability_score < 0.48:
        reasons.append("poor readability in panel")

    passed = not reasons
    return PanelQualityCheck(
        panel_index=panel_index,
        anatomy_score=artifact.anatomy_score,
        composition_score=artifact.composition_score,
        readability_score=artifact.readability_score,
        passed=passed,
        reasons=tuple(reasons),
    )


def _correction_suffix(quality_check: PanelQualityCheck) -> str:
    fixes: list[str] = []
    if any("anatomy" in reason for reason in quality_check.reasons):
        fixes.append("enforce coherent anatomy and stable limb geometry")
    if any("composition" in reason for reason in quality_check.reasons):
        fixes.append("improve composition using clear focal hierarchy")
    if any("readability" in reason for reason in quality_check.reasons):
        fixes.append("increase readability via stronger silhouette separation")
    return "; ".join(fixes)


def _readability_predictability(
    artifacts: tuple[DiffusionArtifact, ...],
    preset: AtmospherePreset,
) -> float:
    if not artifacts:
        return 0.0

    brightness_delta = mean(
        abs(artifact.brightness - preset.brightness_target) for artifact in artifacts
    )
    contrast_delta = mean(
        abs(artifact.contrast - preset.contrast_target) for artifact in artifacts
    )
    texture_delta = mean(
        abs(artifact.texture_density - preset.texture_target) for artifact in artifacts
    )
    delta = (brightness_delta + contrast_delta + texture_delta) / 3.0
    return _clamp(1.0 - delta)


def _cross_modal_mismatch_reasons(
    prose_excerpt: str,
    panel_prompt: str,
) -> tuple[str, ...]:
    prose_tokens = _tokenize(prose_excerpt)
    panel_tokens = _tokenize(panel_prompt)
    overlap_ratio = len(prose_tokens & panel_tokens) / max(1, len(prose_tokens))

    reasons: list[str] = []
    if overlap_ratio < 0.22:
        reasons.append("low keyword overlap between prose and panel")

    action_tokens = {
        "attack",
        "betray",
        "escape",
        "reveal",
        "kill",
        "run",
        "hide",
    }
    prose_actions = prose_tokens & action_tokens
    panel_actions = panel_tokens & action_tokens
    if prose_actions and not (prose_actions & panel_actions):
        reasons.append("action mismatch between prose and panel")

    return tuple(reasons)


def detect_cross_modal_mismatch(
    scene_blueprint: SceneBlueprint,
    panels: tuple[PanelArtifact, ...],
    prose_reference: tuple[str, ...],
) -> CrossModalAlignmentReport:
    """Detect mismatch rate between prose segments and panel prompts."""

    mismatches: list[CrossModalMismatch] = []
    if not prose_reference:
        return CrossModalAlignmentReport(
            mismatches=(), mismatch_rate=0.0, alignment_score=1.0
        )

    for panel in panels:
        prose_excerpt = prose_reference[
            min(panel.panel_index, len(prose_reference) - 1)
        ]
        reasons = _cross_modal_mismatch_reasons(prose_excerpt, panel.prompt)
        if not reasons:
            continue
        mismatches.append(
            CrossModalMismatch(
                panel_index=panel.panel_index,
                reasons=reasons,
                prose_excerpt=prose_excerpt,
                panel_prompt=panel.prompt,
            )
        )

    mismatch_rate = len(mismatches) / max(1, len(scene_blueprint.panels))
    return CrossModalAlignmentReport(
        mismatches=tuple(mismatches),
        mismatch_rate=_clamp(mismatch_rate),
        alignment_score=_clamp(1.0 - mismatch_rate),
    )


def reconcile_cross_modal(
    scene_blueprint: SceneBlueprint,
    alignment_report: CrossModalAlignmentReport,
) -> ReconcilePlan:
    """Produce reconcile actions for mismatched panel prompts."""

    actions: list[ReconcileAction] = []
    panel_by_index = {panel.panel_index: panel for panel in scene_blueprint.panels}

    for mismatch in alignment_report.mismatches:
        panel = panel_by_index.get(mismatch.panel_index)
        if panel is None:
            continue
        prose_keywords = sorted(_tokenize(mismatch.prose_excerpt))[:8]
        updated_prompt = (
            f"{panel.prompt} Align with prose focus terms: {', '.join(prose_keywords)}."
        )
        actions.append(
            ReconcileAction(
                panel_index=mismatch.panel_index,
                action="update_prompt",
                reason="; ".join(mismatch.reasons),
                updated_prompt=updated_prompt,
            )
        )

    improvement = 0.18 if actions else 0.0
    mismatch_after = _clamp(alignment_report.mismatch_rate - improvement)
    return ReconcilePlan(
        actions=tuple(actions),
        mismatch_rate_before=alignment_report.mismatch_rate,
        mismatch_rate_after_estimate=mismatch_after,
    )


def _build_diffusion_request(
    *,
    panel_plan: SceneBlueprintPanel,
    diffusion_config: DiffusionConfig,
    atmosphere: AtmospherePreset,
    controlnet_conditions: tuple[ControlNetCondition, ...],
    seed: int,
    identity_packs: tuple[CharacterIdentityPack, ...],
    adapter_tokens: tuple[str, ...],
) -> DiffusionRequest:
    identity_suffix = ""
    if identity_packs:
        identity_cues: list[str] = []
        for identity_pack in identity_packs:
            identity_cues.extend(_identity_tokens(identity_pack))
        identity_suffix = " Character identity cues: " + ", ".join(identity_cues) + "."

    adapter_suffix = ""
    if adapter_tokens:
        adapter_suffix = " Adapter tokens: " + ", ".join(adapter_tokens) + "."

    prompt = (
        f"{panel_plan.prompt} {_atmosphere_prompt_suffix(atmosphere)}"
        f"{identity_suffix}{adapter_suffix}"
    ).strip()

    negative_prompt = (
        "avoid warped anatomy, avoid unreadable silhouettes, "
        "avoid inconsistent character identity"
    )

    return DiffusionRequest(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=1024,
        height=1024,
        seed=seed,
        model_id=diffusion_config.model_id,
        sampler=diffusion_config.sampler,
        steps=diffusion_config.steps,
        guidance_scale=diffusion_config.guidance_scale,
        controlnet_conditions=controlnet_conditions,
        brightness_target=atmosphere.brightness_target,
        contrast_target=atmosphere.contrast_target,
        texture_target=atmosphere.texture_target,
    )


def _identity_scores_for_panel(
    prompt: str,
    identity_packs: tuple[CharacterIdentityPack, ...],
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for identity_pack in identity_packs:
        scores[identity_pack.character_id] = _identity_score_from_prompt(
            prompt, identity_pack
        )
    return scores


def _selective_redraw(
    *,
    backend: DiffusionBackend,
    panel_plan: SceneBlueprintPanel,
    diffusion_config: DiffusionConfig,
    atmosphere: AtmospherePreset,
    controlnet_conditions: tuple[ControlNetCondition, ...],
    identity_packs: tuple[CharacterIdentityPack, ...],
    adapter_tokens: tuple[str, ...],
    base_seed: int,
    max_redraw_attempts: int,
) -> PanelArtifact:
    attempt = 0
    best_panel: PanelArtifact | None = None

    while attempt <= max_redraw_attempts:
        seed = base_seed + (attempt * 97)
        diffusion_request = _build_diffusion_request(
            panel_plan=panel_plan,
            diffusion_config=diffusion_config,
            atmosphere=atmosphere,
            controlnet_conditions=controlnet_conditions,
            seed=seed,
            identity_packs=identity_packs,
            adapter_tokens=adapter_tokens,
        )

        if (
            attempt > 0
            and best_panel is not None
            and not best_panel.quality_check.passed
        ):
            correction_text = _correction_suffix(best_panel.quality_check)
            if correction_text:
                diffusion_request = replace(
                    diffusion_request,
                    prompt=diffusion_request.prompt + " Correction: " + correction_text,
                )

        artifact = backend.generate(diffusion_request)
        quality_check = _quality_check(artifact, panel_plan.panel_index)
        identity_scores = _identity_scores_for_panel(
            diffusion_request.prompt, identity_packs
        )

        panel = PanelArtifact(
            panel_index=panel_plan.panel_index,
            beat=panel_plan.beat,
            prompt=diffusion_request.prompt,
            negative_prompt=diffusion_request.negative_prompt,
            continuity_anchor=panel_plan.continuity_anchor,
            atmosphere_preset=atmosphere.preset_id,
            diffusion_artifact=artifact,
            identity_scores=identity_scores,
            adapter_ids=adapter_tokens,
            redraw_count=attempt,
            quality_check=quality_check,
        )

        if best_panel is None:
            best_panel = panel
        else:
            current_score = (
                panel.quality_check.anatomy_score
                + panel.quality_check.composition_score
                + panel.quality_check.readability_score
            )
            best_score = (
                best_panel.quality_check.anatomy_score
                + best_panel.quality_check.composition_score
                + best_panel.quality_check.readability_score
            )
            if current_score > best_score:
                best_panel = panel

        if quality_check.passed:
            return panel

        attempt += 1

    if best_panel is None:
        msg = "failed to generate panel artifact"
        raise RuntimeError(msg)
    return best_panel


def _identity_consistency(panels: tuple[PanelArtifact, ...]) -> float:
    all_scores: list[float] = []
    for panel in panels:
        all_scores.extend(panel.identity_scores.values())
    if not all_scores:
        return 1.0
    return _clamp(mean(all_scores))


def _quality_summary(panels: tuple[PanelArtifact, ...]) -> tuple[int, float]:
    if not panels:
        return 0, 0.0
    rejected_count = sum(1 for panel in panels if not panel.quality_check.passed)
    final_pass_rate = (len(panels) - rejected_count) / len(panels)
    return rejected_count, _clamp(final_pass_rate)


def _adapter_tokens(
    identity_packs: tuple[CharacterIdentityPack, ...],
    adapter_manager: LoRAAdapterManager,
    model_id: str,
) -> tuple[str, ...]:
    tokens: list[str] = []
    for identity_pack in identity_packs:
        adapter = adapter_manager.latest_adapter(identity_pack.character_id)
        if adapter is None:
            adapter = adapter_manager.training_hook(
                identity_pack,
                base_model_id=model_id,
            )
        tokens.extend(adapter.trigger_tokens)
    return tuple(sorted(set(tokens)))


def generate_manga_sequence(
    request: ArtistRequest,
    *,
    backend: DiffusionBackend | None = None,
    adapter_manager: LoRAAdapterManager | None = None,
) -> ArtistResult:
    """Generate manga panel sequence with continuity and quality safeguards."""

    active_backend = backend or MockDiffusionBackend()
    active_adapter_manager = adapter_manager or LoRAAdapterManager()

    scene_blueprint = request.scene_blueprint or shared_scene_plan_from_text_and_prompt(
        scene_id=f"{request.branch_id}:scene",
        scene_prompt=request.scene_prompt,
        prose_reference=request.prose_reference,
        panel_count=request.panel_count,
        atmosphere=request.atmosphere,
    )

    preset = atmosphere_preset(scene_blueprint.atmosphere)

    if request.deterministic:
        seed_material = (
            f"{request.story_id}|{request.branch_id}|{request.scene_prompt}|"
            f"{scene_blueprint.scene_id}|{request.seed or 0}"
        )
        base_seed = int(_sha256(seed_material)[:16], 16)
    else:
        base_seed = random.SystemRandom().randrange(1, 2**31)

    adapter_tokens = _adapter_tokens(
        request.identity_packs,
        active_adapter_manager,
        request.diffusion_config.model_id,
    )

    panels: list[PanelArtifact] = []
    for panel_plan in scene_blueprint.panels:
        panel_seed = base_seed + panel_plan.panel_index
        panel = _selective_redraw(
            backend=active_backend,
            panel_plan=panel_plan,
            diffusion_config=request.diffusion_config,
            atmosphere=preset,
            controlnet_conditions=request.controlnet_conditions,
            identity_packs=request.identity_packs,
            adapter_tokens=adapter_tokens,
            base_seed=panel_seed,
            max_redraw_attempts=request.max_redraw_attempts,
        )
        panels.append(panel)

    panel_tuple = tuple(panels)
    continuity_score = validate_panel_continuity(panel_tuple)
    identity_consistency_score = _identity_consistency(panel_tuple)
    atmosphere_predictability_score = _readability_predictability(
        tuple(panel.diffusion_artifact for panel in panel_tuple),
        preset,
    )

    rejected_count, final_pass_rate = _quality_summary(panel_tuple)

    if request.prose_reference:
        alignment_report = detect_cross_modal_mismatch(
            scene_blueprint,
            panel_tuple,
            request.prose_reference,
        )
    else:
        alignment_report = CrossModalAlignmentReport(
            mismatches=(),
            mismatch_rate=0.0,
            alignment_score=1.0,
        )
    reconcile_plan = reconcile_cross_modal(scene_blueprint, alignment_report)

    if request.identity_packs:
        drift_results = [
            active_adapter_manager.detect_drift(
                identity_pack,
                tuple(
                    panel.identity_scores.get(identity_pack.character_id, 0.0)
                    for panel in panel_tuple
                ),
            )
            for identity_pack in request.identity_packs
        ]
        retraining_triggered = any(
            result.trigger_retraining for result in drift_results
        )
        drift_summary = "; ".join(
            ", ".join(result.reasons) for result in drift_results if result.reasons
        )
    else:
        retraining_triggered = False
        drift_summary = ""

    metadata = {
        "generated_at": _timestamp(),
        "deterministic": str(request.deterministic).lower(),
        "base_seed": str(base_seed),
        "scene_id": scene_blueprint.scene_id,
        "controlnet_conditions": ",".join(
            condition.control_type for condition in request.controlnet_conditions
        ),
        "retraining_triggered": str(retraining_triggered).lower(),
        "drift_summary": drift_summary,
    }

    return ArtistResult(
        branch_id=request.branch_id,
        image_count=len(panel_tuple),
        model_id=request.diffusion_config.model_id,
        scene_blueprint=scene_blueprint,
        panels=panel_tuple,
        continuity_score=continuity_score,
        identity_consistency_score=identity_consistency_score,
        atmosphere_predictability_score=atmosphere_predictability_score,
        rejected_count=rejected_count,
        final_pass_rate=final_pass_rate,
        alignment_report=alignment_report,
        reconcile_plan=reconcile_plan,
        metadata=metadata,
    )


def writer_result_to_prose_segments(writer_result: WriterResult) -> tuple[str, ...]:
    """Convert writer output to prose segments for cross-modal alignment."""

    lines = [line.strip() for line in writer_result.text.splitlines() if line.strip()]
    return tuple(lines)


# ============ Sprint 24: Async Image Generation with Storage ============


@dataclass(frozen=True)
class GeneratedPanelImage:
    """Result from async panel generation with storage."""
    panel_index: int
    image_id: str
    image_url: str
    prompt: str
    seed: int
    generation_time_ms: float
    quality_score: float


@dataclass(frozen=True)
class StoredArtistResult:
    """Artist result with stored image references."""
    branch_id: str
    scene_id: str
    images: tuple[GeneratedPanelImage, ...]
    continuity_score: float
    overall_quality: float


async def generate_and_store_panels(
    request: ArtistRequest,
    storage: ImageStorage | None = None,
    backend: NewDiffusionBackend | None = None,
) -> StoredArtistResult:
    """Generate manga panels and store them with persistence.
    
    This is the Sprint 24 implementation that uses the new diffusion backend
    and image storage system.
    """
    from .diffusion_backend import (
        get_diffusion_backend,
        GenerationRequest,
        ControlNetCondition as NewControlNetCondition,
    )
    from .image_storage import (
        get_image_storage,
        ImageMetadata,
    )
    import time
    
    # Get backend and storage
    active_backend = backend or get_diffusion_backend()
    active_storage = storage or get_image_storage()
    
    # Create scene blueprint
    scene_blueprint = request.scene_blueprint or shared_scene_plan_from_text_and_prompt(
        scene_id=f"{request.branch_id}:scene",
        scene_prompt=request.scene_prompt,
        prose_reference=request.prose_reference,
        panel_count=request.panel_count,
        atmosphere=request.atmosphere,
    )
    
    # Determine seed
    if request.deterministic:
        seed_material = (
            f"{request.story_id}|{request.branch_id}|{request.scene_prompt}|"
            f"{scene_blueprint.scene_id}|{request.seed or 0}"
        )
        base_seed = int(_sha256(seed_material)[:16], 16)
    else:
        base_seed = random.SystemRandom().randrange(1, 2**31)
    
    # Generate each panel
    images: list[GeneratedPanelImage] = []
    preset = atmosphere_preset(scene_blueprint.atmosphere)
    
    for panel_plan in scene_blueprint.panels:
        panel_seed = base_seed + panel_plan.panel_index
        
        start_time = time.time()
        
        # Build prompt
        prompt = f"{panel_plan.prompt}, {preset.lighting.key_light}, manga style, black and white, high quality"
        negative_prompt = "color, blurry, low quality, deformed"
        
        # Convert ControlNet conditions
        controlnet_conditions = []
        for condition in request.controlnet_conditions:
            controlnet_conditions.append(NewControlNetCondition(
                control_type=condition.control_type,
                weight=condition.weight,
                image_path=condition.reference_hint if os.path.exists(condition.reference_hint) else None,
            ))
        
        # Generate image
        gen_request = GenerationRequest(
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=panel_seed,
            num_images=1,
            controlnet_conditions=tuple(controlnet_conditions),
        )
        
        results = await active_backend.generate(gen_request)
        
        if not results:
            continue
        
        result = results[0]
        generation_time_ms = (time.time() - start_time) * 1000
        
        # Create metadata
        image_id = hashlib.sha256(
            f"{request.branch_id}:{scene_blueprint.scene_id}:{panel_plan.panel_index}:{result.seed}".encode()
        ).hexdigest()[:16]
        
        metadata = ImageMetadata(
            image_id=image_id,
            original_filename=f"panel_{panel_plan.panel_index}.png",
            content_type="image/png",
            width=512,  # Could detect from image
            height=512,
            file_size_bytes=len(result.image_data),
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=result.seed,
            model_id=result.model_id,
            story_id=request.story_id,
            branch_id=request.branch_id,
            scene_id=scene_blueprint.scene_id,
            panel_index=panel_plan.panel_index,
            version=1,
        )
        
        # Store image
        stored = await active_storage.save_image(result.image_data, metadata)
        
        # Calculate quality score based on generation metrics
        quality_score = (result.brightness + result.contrast) / 2
        
        images.append(GeneratedPanelImage(
            panel_index=panel_plan.panel_index,
            image_id=stored.image_id,
            image_url=stored.url,
            prompt=prompt,
            seed=result.seed,
            generation_time_ms=generation_time_ms,
            quality_score=quality_score,
        ))
    
    # Calculate continuity score (simplified)
    continuity_score = 0.85 if len(images) > 1 else 1.0
    
    # Calculate overall quality
    overall_quality = mean([img.quality_score for img in images]) if images else 0.0
    
    return StoredArtistResult(
        branch_id=request.branch_id,
        scene_id=scene_blueprint.scene_id,
        images=tuple(images),
        continuity_score=continuity_score,
        overall_quality=overall_quality,
    )


# Import for the new function
import os
