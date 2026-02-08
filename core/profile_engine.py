"""Tone, style, and maturity profiling engine for The Loom."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from statistics import mean
from typing import Any

_POSITIVE_WORDS = {
    "kind",
    "gentle",
    "warm",
    "hope",
    "hopeful",
    "smile",
    "laugh",
    "friend",
    "peace",
    "joy",
    "happy",
    "safe",
    "calm",
    "bright",
    "love",
}

_NEGATIVE_WORDS = {
    "fear",
    "terror",
    "hate",
    "blood",
    "gore",
    "pain",
    "death",
    "kill",
    "dark",
    "nightmare",
    "dread",
    "rage",
    "scream",
    "despair",
    "alone",
}

_TEXT_LABEL_LEXICONS: dict[str, set[str]] = {
    "violence": {
        "blood",
        "gore",
        "kill",
        "stab",
        "slash",
        "wound",
        "fight",
        "battle",
        "attack",
        "corpse",
        "blade",
        "bone",
    },
    "romance": {
        "love",
        "kiss",
        "heart",
        "embrace",
        "desire",
        "date",
        "romance",
        "affection",
    },
    "humor": {
        "joke",
        "laugh",
        "funny",
        "smirk",
        "gag",
        "comic",
        "giggle",
        "chuckle",
    },
    "horror": {
        "horror",
        "dread",
        "nightmare",
        "haunt",
        "ghost",
        "monster",
        "void",
        "scream",
        "ominous",
    },
    "wholesome": {
        "kind",
        "gentle",
        "warm",
        "friend",
        "family",
        "safe",
        "cozy",
        "comfort",
        "smile",
    },
    "psychological": {
        "mind",
        "memory",
        "paranoia",
        "hallucination",
        "obsession",
        "anxiety",
        "madness",
        "identity",
        "control",
    },
}

_LABEL_KEYS = tuple(_TEXT_LABEL_LEXICONS.keys())


@dataclass(frozen=True)
class SceneTextProfile:
    """Scene-level textual tone signals."""

    scene_index: int
    text: str
    label_scores: dict[str, float]
    sentiment_score: float
    intensity_score: float
    confidence: float
    uncertainty: float
    abrupt_shift: bool = False
    peak_intensity: bool = False

    def predicted_labels(self, threshold: float = 0.18) -> tuple[str, ...]:
        labels = [
            label for label, score in self.label_scores.items() if score >= threshold
        ]
        return tuple(sorted(labels))


@dataclass(frozen=True)
class TextProfileResult:
    """Text profile report with scene-level and aggregate metrics."""

    source_id: str
    scenes: tuple[SceneTextProfile, ...]
    label_averages: dict[str, float]
    abrupt_shift_indices: tuple[int, ...]
    peak_intensity_indices: tuple[int, ...]
    uncertainty_mean: float


@dataclass(frozen=True)
class PanelVisualProfile:
    """Panel-level visual tone classification."""

    panel_index: int
    source_ref: str
    tone_label: str
    darkness: float
    grit: float
    brightness: float
    contrast: float
    line_density: float
    texture_entropy: float
    composition_balance: float
    confidence: float


@dataclass(frozen=True)
class VisualAggregateProfile:
    """Aggregated visual profile for a scene or chapter chunk."""

    aggregate_index: int
    start_panel_index: int
    end_panel_index: int
    dominant_tone: str
    avg_darkness: float
    avg_grit: float
    avg_brightness: float
    avg_contrast: float
    avg_line_density: float
    avg_texture_entropy: float
    avg_composition_balance: float
    confidence: float


@dataclass(frozen=True)
class VisualProfileResult:
    """Visual profile report containing panel and aggregate level signals."""

    source_id: str
    panel_profiles: tuple[PanelVisualProfile, ...]
    scene_profiles: tuple[VisualAggregateProfile, ...]
    chapter_profiles: tuple[VisualAggregateProfile, ...]
    tone_distribution: dict[str, float]


@dataclass(frozen=True)
class GenerationPreset:
    """Generation controls derived from maturity band selection."""

    band: str
    temperature: float
    top_p: float
    style_strength: float
    violence_bias: float
    humor_bias: float
    romance_bias: float


@dataclass(frozen=True)
class MaturityOverride:
    """Optional user override for maturity score or band."""

    target_band: str | None = None
    target_score: float | None = None
    reason: str = ""
    actor: str = "user"


@dataclass(frozen=True)
class MaturityProfile:
    """Maturity spectrum output with smoothing and generation preset mapping."""

    raw_scores: tuple[float, ...]
    smoothed_scores: tuple[float, ...]
    final_score: float
    maturity_band: str
    preset: GenerationPreset
    tone_jitter_index: float
    override_applied: bool = False
    override_reason: str | None = None
    override_actor: str | None = None


@dataclass(frozen=True)
class TextSceneCorrection:
    """Human correction for one scene profile."""

    scene_index: int
    label_updates: dict[str, float] = field(default_factory=dict)
    sentiment_override: float | None = None
    intensity_override: float | None = None
    confidence_override: float | None = None
    note: str = ""


@dataclass(frozen=True)
class ProfileChangeRecord:
    """Change provenance for profile version transitions."""

    change_type: str
    actor: str
    reason: str
    timestamp: str
    details: dict[str, str]


@dataclass(frozen=True)
class ProfileVersionRecord:
    """Versioned profile snapshot for one branch."""

    branch_id: str
    version_id: str
    parent_version_id: str | None
    created_at: str
    created_by: str
    text_profile: TextProfileResult
    visual_profile: VisualProfileResult
    maturity_profile: MaturityProfile
    change_records: tuple[ProfileChangeRecord, ...]


@dataclass(frozen=True)
class ProfileOverrideAudit:
    """Audit event for explicit maturity override operations."""

    branch_id: str
    version_id: str
    actor: str
    reason: str
    previous_band: str
    new_band: str
    timestamp: str


@dataclass(frozen=True)
class LabelEvaluation:
    """Precision/recall summary for benchmark scene labels."""

    precision: float
    recall: float
    f1: float
    true_positive: int
    false_positive: int
    false_negative: int


@dataclass(frozen=True)
class SceneLabelBenchmark:
    """Expected labels for one scene index in benchmark tests."""

    scene_index: int
    labels: tuple[str, ...]


_BAND_PRESETS: dict[str, GenerationPreset] = {
    "all_ages": GenerationPreset(
        band="all_ages",
        temperature=0.55,
        top_p=0.85,
        style_strength=0.45,
        violence_bias=0.1,
        humor_bias=0.55,
        romance_bias=0.35,
    ),
    "teen": GenerationPreset(
        band="teen",
        temperature=0.65,
        top_p=0.88,
        style_strength=0.6,
        violence_bias=0.35,
        humor_bias=0.4,
        romance_bias=0.45,
    ),
    "mature": GenerationPreset(
        band="mature",
        temperature=0.72,
        top_p=0.9,
        style_strength=0.78,
        violence_bias=0.6,
        humor_bias=0.25,
        romance_bias=0.5,
    ),
    "explicit": GenerationPreset(
        band="explicit",
        temperature=0.8,
        top_p=0.92,
        style_strength=0.92,
        violence_bias=0.85,
        humor_bias=0.15,
        romance_bias=0.55,
    ),
}


def _clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _tokenize(scene_text: str) -> list[str]:
    return [
        token.lower()
        for token in __import__("re").findall(r"[A-Za-z0-9']+", scene_text)
    ]


def _score_label(tokens: list[str], label: str) -> float:
    lexicon = _TEXT_LABEL_LEXICONS[label]
    if not tokens:
        return 0.0

    hit_count = sum(1 for token in tokens if token in lexicon)
    normalized_score = hit_count / max(1.0, len(tokens) * 0.12)
    return _clamp(normalized_score)


def _sentiment_score(tokens: list[str]) -> float:
    if not tokens:
        return 0.0

    positive_hits = sum(1 for token in tokens if token in _POSITIVE_WORDS)
    negative_hits = sum(1 for token in tokens if token in _NEGATIVE_WORDS)

    if positive_hits == 0 and negative_hits == 0:
        return 0.0

    return _clamp(
        (positive_hits - negative_hits) / max(1, positive_hits + negative_hits),
        min_value=-1.0,
        max_value=1.0,
    )


def _intensity_score(scene_text: str, label_scores: dict[str, float]) -> float:
    exclamation_count = scene_text.count("!")
    question_count = scene_text.count("?")
    words = scene_text.split()
    uppercase_words = [word for word in words if len(word) > 2 and word.isupper()]

    punctuation_energy = _clamp(exclamation_count * 0.2 + question_count * 0.1)
    uppercase_energy = _clamp(len(uppercase_words) / max(1.0, len(words) * 0.25))

    lexical_energy = max(
        label_scores.get("violence", 0.0),
        label_scores.get("horror", 0.0),
        label_scores.get("psychological", 0.0),
        label_scores.get("romance", 0.0) * 0.45,
        label_scores.get("humor", 0.0) * 0.3,
    )

    return _clamp(
        lexical_energy * 0.5 + punctuation_energy * 0.3 + uppercase_energy * 0.2
    )


def _confidence_score(
    tokens: list[str],
    label_scores: dict[str, float],
    sentiment_score: float,
    intensity_score: float,
) -> float:
    if not tokens:
        return 0.0

    dominant_signal = max(
        max(label_scores.values(), default=0.0),
        abs(sentiment_score),
        intensity_score,
    )
    length_factor = _clamp(len(tokens) / 14.0)

    return _clamp(0.2 + dominant_signal * 0.55 + length_factor * 0.25)


def _split_into_scenes(raw_text: str) -> list[str]:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    scene_candidates = [scene.strip() for scene in normalized.split("\n\n")]
    return [scene for scene in scene_candidates if scene]


def _annotate_scene_transitions(
    scenes: list[SceneTextProfile],
) -> tuple[list[SceneTextProfile], tuple[int, ...], tuple[int, ...]]:
    abrupt_shift_indices: list[int] = []

    for index in range(1, len(scenes)):
        previous_scene = scenes[index - 1]
        current_scene = scenes[index]

        sentiment_delta = abs(
            current_scene.sentiment_score - previous_scene.sentiment_score
        )
        intensity_delta = abs(
            current_scene.intensity_score - previous_scene.intensity_score
        )

        if (
            sentiment_delta >= 0.6
            or intensity_delta >= 0.45
            or (sentiment_delta + intensity_delta) >= 0.8
        ):
            abrupt_shift_indices.append(index)

    peak_intensity_indices: list[int] = []
    if scenes:
        intensity_values = [scene.intensity_score for scene in scenes]
        sorted_values = sorted(intensity_values)
        percentile_index = int((len(sorted_values) - 1) * 0.85)
        peak_threshold = max(0.58, sorted_values[percentile_index])

        for index, scene in enumerate(scenes):
            if scene.intensity_score >= peak_threshold:
                peak_intensity_indices.append(index)

        if not peak_intensity_indices:
            max_intensity = max(intensity_values)
            for index, scene in enumerate(scenes):
                if scene.intensity_score == max_intensity:
                    peak_intensity_indices.append(index)

    annotated_scenes = [
        replace(
            scene,
            abrupt_shift=(scene.scene_index in abrupt_shift_indices),
            peak_intensity=(scene.scene_index in peak_intensity_indices),
        )
        for scene in scenes
    ]

    return (
        annotated_scenes,
        tuple(abrupt_shift_indices),
        tuple(peak_intensity_indices),
    )


def _aggregate_label_averages(scenes: list[SceneTextProfile]) -> dict[str, float]:
    if not scenes:
        return {label: 0.0 for label in _LABEL_KEYS}

    averages: dict[str, float] = {}
    for label in _LABEL_KEYS:
        label_values = [scene.label_scores.get(label, 0.0) for scene in scenes]
        averages[label] = _clamp(mean(label_values))

    return averages


def analyze_text_profile(
    raw_text: str, *, source_id: str = "text"
) -> TextProfileResult:
    """Build scene-level text profile with labels, uncertainty, and shift markers."""

    scene_texts = _split_into_scenes(raw_text)
    scene_profiles: list[SceneTextProfile] = []

    for scene_index, scene_text in enumerate(scene_texts):
        tokens = _tokenize(scene_text)
        label_scores = {label: _score_label(tokens, label) for label in _LABEL_KEYS}
        sentiment_score = _sentiment_score(tokens)
        intensity_score = _intensity_score(scene_text, label_scores)
        confidence = _confidence_score(
            tokens, label_scores, sentiment_score, intensity_score
        )
        uncertainty = _clamp(1.0 - confidence)

        scene_profiles.append(
            SceneTextProfile(
                scene_index=scene_index,
                text=scene_text,
                label_scores=label_scores,
                sentiment_score=sentiment_score,
                intensity_score=intensity_score,
                confidence=confidence,
                uncertainty=uncertainty,
            )
        )

    annotated_scenes, abrupt_shift_indices, peak_intensity_indices = (
        _annotate_scene_transitions(scene_profiles)
    )
    uncertainty_mean = (
        _clamp(mean(scene.uncertainty for scene in annotated_scenes))
        if annotated_scenes
        else 1.0
    )

    return TextProfileResult(
        source_id=source_id,
        scenes=tuple(annotated_scenes),
        label_averages=_aggregate_label_averages(annotated_scenes),
        abrupt_shift_indices=abrupt_shift_indices,
        peak_intensity_indices=peak_intensity_indices,
        uncertainty_mean=uncertainty_mean,
    )


def analyze_text_ingestion_report(text_report: Any) -> TextProfileResult:
    """Build text profile directly from archivist text-ingestion output."""

    return analyze_text_profile(
        text_report.normalized_text,
        source_id=str(text_report.source_path),
    )


def _panel_tone_label(
    darkness: float,
    grit: float,
    brightness: float,
    contrast: float,
    composition_balance: float,
) -> tuple[str, float]:
    if darkness >= 0.78 and brightness <= 0.25:
        return "dark", _clamp(0.72 + darkness * 0.2)

    brightness_center = _clamp(1.0 - (abs(brightness - 0.5) * 2.0))
    contrast_center = _clamp(1.0 - (abs(contrast - 0.5) * 2.0))

    candidates = {
        "dark": darkness * 0.55 + grit * 0.3 + contrast * 0.15,
        "gritty": grit * 0.55 + darkness * 0.25 + contrast * 0.2,
        "light": brightness * 0.6 + composition_balance * 0.25 + (1.0 - grit) * 0.15,
        "balanced": brightness_center * 0.5
        + composition_balance * 0.2
        + contrast_center * 0.3,
    }

    ranked = sorted(candidates.items(), key=lambda item: item[1], reverse=True)
    top_label, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = _clamp(0.4 + (top_score - second_score) * 1.2)
    return top_label, confidence


def _aggregate_visual_chunk(
    chunk: list[PanelVisualProfile],
    aggregate_index: int,
) -> VisualAggregateProfile:
    tone_counts: dict[str, int] = {}
    for panel in chunk:
        tone_counts[panel.tone_label] = tone_counts.get(panel.tone_label, 0) + 1

    dominant_tone = max(tone_counts.items(), key=lambda item: item[1])[0]

    return VisualAggregateProfile(
        aggregate_index=aggregate_index,
        start_panel_index=chunk[0].panel_index,
        end_panel_index=chunk[-1].panel_index,
        dominant_tone=dominant_tone,
        avg_darkness=_clamp(mean(panel.darkness for panel in chunk)),
        avg_grit=_clamp(mean(panel.grit for panel in chunk)),
        avg_brightness=_clamp(mean(panel.brightness for panel in chunk)),
        avg_contrast=_clamp(mean(panel.contrast for panel in chunk)),
        avg_line_density=_clamp(mean(panel.line_density for panel in chunk)),
        avg_texture_entropy=_clamp(mean(panel.texture_entropy for panel in chunk)),
        avg_composition_balance=_clamp(
            mean(panel.composition_balance for panel in chunk)
        ),
        confidence=_clamp(mean(panel.confidence for panel in chunk)),
    )


def _chunk_panels(
    panel_profiles: list[PanelVisualProfile],
    chunk_size: int,
) -> tuple[VisualAggregateProfile, ...]:
    if chunk_size <= 0:
        msg = "Chunk size must be positive."
        raise ValueError(msg)

    chunks: list[VisualAggregateProfile] = []
    for start_index in range(0, len(panel_profiles), chunk_size):
        chunk = panel_profiles[start_index : start_index + chunk_size]
        if not chunk:
            continue
        chunks.append(_aggregate_visual_chunk(chunk, aggregate_index=len(chunks)))

    return tuple(chunks)


def analyze_visual_profile(
    page_metadata: tuple[Any, ...],
    *,
    source_id: str = "visual",
    scene_size: int = 4,
    chapter_size: int = 24,
) -> VisualProfileResult:
    """Build panel-level and aggregate visual tone profile from page metadata."""

    panel_profiles: list[PanelVisualProfile] = []
    for panel_index, metadata in enumerate(page_metadata):
        brightness = _clamp(float(metadata.mean_brightness))
        contrast = _clamp(float(metadata.contrast))
        line_density = _clamp(float(metadata.line_density))
        texture_entropy = _clamp(float(metadata.texture_entropy))
        composition_balance = _clamp(float(metadata.composition_balance))
        darkness = _clamp(1.0 - brightness)
        grit = _clamp(line_density * 0.35 + texture_entropy * 0.35 + contrast * 0.3)

        tone_label, confidence = _panel_tone_label(
            darkness,
            grit,
            brightness,
            contrast,
            composition_balance,
        )

        panel_profiles.append(
            PanelVisualProfile(
                panel_index=panel_index,
                source_ref=str(metadata.source_ref),
                tone_label=tone_label,
                darkness=darkness,
                grit=grit,
                brightness=brightness,
                contrast=contrast,
                line_density=line_density,
                texture_entropy=texture_entropy,
                composition_balance=composition_balance,
                confidence=confidence,
            )
        )

    scene_profiles = (
        _chunk_panels(panel_profiles, chunk_size=scene_size) if panel_profiles else ()
    )
    chapter_profiles = (
        _chunk_panels(panel_profiles, chunk_size=chapter_size) if panel_profiles else ()
    )

    tone_distribution: dict[str, float] = {}
    if panel_profiles:
        total_panels = len(panel_profiles)
        for tone in {panel.tone_label for panel in panel_profiles}:
            tone_distribution[tone] = _clamp(
                sum(1 for panel in panel_profiles if panel.tone_label == tone)
                / total_panels
            )

    return VisualProfileResult(
        source_id=source_id,
        panel_profiles=tuple(panel_profiles),
        scene_profiles=scene_profiles,
        chapter_profiles=chapter_profiles,
        tone_distribution=tone_distribution,
    )


def _smooth_scores(scores: list[float], window: int) -> tuple[float, ...]:
    if not scores:
        return ()

    if window <= 1:
        return tuple(scores)

    smoothed: list[float] = []
    for index in range(len(scores)):
        start_index = max(0, index - window + 1)
        segment = scores[start_index : index + 1]
        smoothed.append(_clamp(mean(segment)))
    return tuple(smoothed)


def compute_tone_jitter_index(scores: tuple[float, ...]) -> float:
    """Compute mean adjacent score delta; lower means smoother tone progression."""

    if len(scores) < 2:
        return 0.0

    deltas = [abs(scores[index] - scores[index - 1]) for index in range(1, len(scores))]
    return _clamp(mean(deltas))


def _band_for_score(score: float) -> str:
    if score < 0.2:
        return "all_ages"
    if score < 0.45:
        return "teen"
    if score < 0.7:
        return "mature"
    return "explicit"


def build_maturity_profile(
    text_profile: TextProfileResult,
    visual_profile: VisualProfileResult | None,
    *,
    smoothing_window: int = 3,
    override: MaturityOverride | None = None,
) -> MaturityProfile:
    """Create maturity spectrum scores and map to generation presets."""

    raw_scores: list[float] = []
    visual_scenes = visual_profile.scene_profiles if visual_profile is not None else ()

    for scene_index, scene in enumerate(text_profile.scenes):
        text_component = (
            scene.label_scores.get("violence", 0.0) * 0.35
            + scene.label_scores.get("horror", 0.0) * 0.22
            + scene.label_scores.get("psychological", 0.0) * 0.18
            + scene.label_scores.get("romance", 0.0) * 0.1
            + scene.intensity_score * 0.15
        )

        visual_component = 0.0
        if visual_scenes:
            visual_scene = visual_scenes[min(scene_index, len(visual_scenes) - 1)]
            visual_component = (
                visual_scene.avg_darkness * 0.45
                + visual_scene.avg_grit * 0.35
                + visual_scene.avg_contrast * 0.2
            )

        raw_scores.append(_clamp(text_component * 0.7 + visual_component * 0.3))

    smoothed_scores = _smooth_scores(raw_scores, window=smoothing_window)
    final_score = _clamp(mean(smoothed_scores)) if smoothed_scores else 0.0
    maturity_band = _band_for_score(final_score)

    override_applied = False
    override_reason: str | None = None
    override_actor: str | None = None

    if override is not None:
        override_applied = True
        override_reason = override.reason or "manual override"
        override_actor = override.actor

        if override.target_score is not None:
            final_score = _clamp(override.target_score)
            maturity_band = _band_for_score(final_score)

        if override.target_band is not None:
            maturity_band = override.target_band

    preset = _BAND_PRESETS.get(maturity_band, _BAND_PRESETS["teen"])
    jitter_index = compute_tone_jitter_index(smoothed_scores)

    return MaturityProfile(
        raw_scores=tuple(raw_scores),
        smoothed_scores=smoothed_scores,
        final_score=final_score,
        maturity_band=maturity_band,
        preset=preset,
        tone_jitter_index=jitter_index,
        override_applied=override_applied,
        override_reason=override_reason,
        override_actor=override_actor,
    )


def apply_text_corrections(
    text_profile: TextProfileResult,
    corrections: tuple[TextSceneCorrection, ...],
) -> TextProfileResult:
    """Apply human scene corrections and recompute profile aggregates."""

    scenes = list(text_profile.scenes)
    scene_by_index = {scene.scene_index: scene for scene in scenes}

    for correction in corrections:
        scene = scene_by_index.get(correction.scene_index)
        if scene is None:
            continue

        updated_label_scores = dict(scene.label_scores)
        for label, value in correction.label_updates.items():
            updated_label_scores[label] = _clamp(value)

        updated_scene = replace(
            scene,
            label_scores=updated_label_scores,
            sentiment_score=(
                _clamp(correction.sentiment_override, min_value=-1.0, max_value=1.0)
                if correction.sentiment_override is not None
                else scene.sentiment_score
            ),
            intensity_score=(
                _clamp(correction.intensity_override)
                if correction.intensity_override is not None
                else scene.intensity_score
            ),
            confidence=(
                _clamp(correction.confidence_override)
                if correction.confidence_override is not None
                else scene.confidence
            ),
            uncertainty=(
                _clamp(1.0 - _clamp(correction.confidence_override))
                if correction.confidence_override is not None
                else scene.uncertainty
            ),
        )

        scene_by_index[correction.scene_index] = updated_scene

    ordered_scenes = [scene_by_index[index] for index in sorted(scene_by_index.keys())]
    annotated_scenes, abrupt_shift_indices, peak_indices = _annotate_scene_transitions(
        ordered_scenes
    )

    uncertainty_mean = (
        _clamp(mean(scene.uncertainty for scene in annotated_scenes))
        if annotated_scenes
        else 1.0
    )

    return TextProfileResult(
        source_id=text_profile.source_id,
        scenes=tuple(annotated_scenes),
        label_averages=_aggregate_label_averages(annotated_scenes),
        abrupt_shift_indices=abrupt_shift_indices,
        peak_intensity_indices=peak_indices,
        uncertainty_mean=uncertainty_mean,
    )


def evaluate_scene_label_predictions(
    text_profile: TextProfileResult,
    benchmarks: tuple[SceneLabelBenchmark, ...],
    *,
    threshold: float = 0.18,
) -> LabelEvaluation:
    """Evaluate predicted scene labels against benchmark annotations."""

    benchmark_map = {
        benchmark.scene_index: set(benchmark.labels) for benchmark in benchmarks
    }

    true_positive = 0
    false_positive = 0
    false_negative = 0

    for scene in text_profile.scenes:
        expected_labels = benchmark_map.get(scene.scene_index)
        if expected_labels is None:
            continue

        predicted_labels = set(scene.predicted_labels(threshold=threshold))
        true_positive += len(predicted_labels & expected_labels)
        false_positive += len(predicted_labels - expected_labels)
        false_negative += len(expected_labels - predicted_labels)

    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else 0.0
    )
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return LabelEvaluation(
        precision=_clamp(precision),
        recall=_clamp(recall),
        f1=_clamp(f1),
        true_positive=true_positive,
        false_positive=false_positive,
        false_negative=false_negative,
    )


class ProfileRegistry:
    """Versioned registry for profile reports, corrections, and overrides."""

    def __init__(self) -> None:
        self._versions_by_branch: dict[str, list[ProfileVersionRecord]] = {}
        self._override_audit_events: list[ProfileOverrideAudit] = []

    def _next_version_id(self, branch_id: str) -> str:
        version_count = len(self._versions_by_branch.get(branch_id, [])) + 1
        return f"{branch_id}:v{version_count:04d}"

    def _timestamp(self) -> str:
        return datetime.now(UTC).isoformat()

    def create_initial_version(
        self,
        *,
        branch_id: str,
        text_profile: TextProfileResult,
        visual_profile: VisualProfileResult,
        maturity_profile: MaturityProfile,
        actor: str = "system",
        reason: str = "initial profiling",
    ) -> ProfileVersionRecord:
        version = ProfileVersionRecord(
            branch_id=branch_id,
            version_id=self._next_version_id(branch_id),
            parent_version_id=None,
            created_at=self._timestamp(),
            created_by=actor,
            text_profile=text_profile,
            visual_profile=visual_profile,
            maturity_profile=maturity_profile,
            change_records=(
                ProfileChangeRecord(
                    change_type="initial",
                    actor=actor,
                    reason=reason,
                    timestamp=self._timestamp(),
                    details={"source": text_profile.source_id},
                ),
            ),
        )
        self._versions_by_branch.setdefault(branch_id, []).append(version)
        return version

    def _get_version(self, branch_id: str, version_id: str) -> ProfileVersionRecord:
        for version in self._versions_by_branch.get(branch_id, []):
            if version.version_id == version_id:
                return version
        msg = f"Version '{version_id}' not found for branch '{branch_id}'."
        raise KeyError(msg)

    def latest_version(self, branch_id: str) -> ProfileVersionRecord:
        versions = self._versions_by_branch.get(branch_id, [])
        if not versions:
            msg = f"No versions found for branch '{branch_id}'."
            raise KeyError(msg)
        return versions[-1]

    def apply_text_corrections(
        self,
        *,
        branch_id: str,
        base_version_id: str,
        corrections: tuple[TextSceneCorrection, ...],
        actor: str,
        reason: str,
    ) -> ProfileVersionRecord:
        base_version = self._get_version(branch_id, base_version_id)
        updated_text_profile = apply_text_corrections(
            base_version.text_profile, corrections
        )
        updated_maturity = build_maturity_profile(
            updated_text_profile,
            base_version.visual_profile,
        )

        version = ProfileVersionRecord(
            branch_id=branch_id,
            version_id=self._next_version_id(branch_id),
            parent_version_id=base_version.version_id,
            created_at=self._timestamp(),
            created_by=actor,
            text_profile=updated_text_profile,
            visual_profile=base_version.visual_profile,
            maturity_profile=updated_maturity,
            change_records=(
                ProfileChangeRecord(
                    change_type="text_correction",
                    actor=actor,
                    reason=reason,
                    timestamp=self._timestamp(),
                    details={"correction_count": str(len(corrections))},
                ),
            ),
        )
        self._versions_by_branch.setdefault(branch_id, []).append(version)
        return version

    def apply_maturity_override(
        self,
        *,
        branch_id: str,
        base_version_id: str,
        override: MaturityOverride,
    ) -> ProfileVersionRecord:
        base_version = self._get_version(branch_id, base_version_id)
        updated_maturity = build_maturity_profile(
            base_version.text_profile,
            base_version.visual_profile,
            override=override,
        )

        version = ProfileVersionRecord(
            branch_id=branch_id,
            version_id=self._next_version_id(branch_id),
            parent_version_id=base_version.version_id,
            created_at=self._timestamp(),
            created_by=override.actor,
            text_profile=base_version.text_profile,
            visual_profile=base_version.visual_profile,
            maturity_profile=updated_maturity,
            change_records=(
                ProfileChangeRecord(
                    change_type="maturity_override",
                    actor=override.actor,
                    reason=override.reason,
                    timestamp=self._timestamp(),
                    details={
                        "target_band": override.target_band or "",
                        "target_score": (
                            f"{override.target_score:.3f}"
                            if override.target_score is not None
                            else ""
                        ),
                    },
                ),
            ),
        )

        previous_band = base_version.maturity_profile.maturity_band
        new_band = updated_maturity.maturity_band
        self._override_audit_events.append(
            ProfileOverrideAudit(
                branch_id=branch_id,
                version_id=version.version_id,
                actor=override.actor,
                reason=override.reason,
                previous_band=previous_band,
                new_band=new_band,
                timestamp=self._timestamp(),
            )
        )

        self._versions_by_branch.setdefault(branch_id, []).append(version)
        return version

    def get_branch_versions(self, branch_id: str) -> tuple[ProfileVersionRecord, ...]:
        return tuple(self._versions_by_branch.get(branch_id, []))

    def get_override_audit(self, branch_id: str) -> tuple[ProfileOverrideAudit, ...]:
        events = [
            event
            for event in self._override_audit_events
            if event.branch_id == branch_id
        ]
        return tuple(events)
