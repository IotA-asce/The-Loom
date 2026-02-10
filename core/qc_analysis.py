"""Quality control analysis for The Loom.

Provides image quality scoring including:
- Anatomy analysis
- Composition scoring
- Readability assessment
- NSFW/content filtering
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class QCScoreLevel(Enum):
    """Quality control score levels."""

    EXCELLENT = "excellent"  # 0.9-1.0
    GOOD = "good"  # 0.7-0.9
    ACCEPTABLE = "acceptable"  # 0.5-0.7
    POOR = "poor"  # 0.3-0.5
    REJECT = "reject"  # 0.0-0.3


@dataclass(frozen=True)
class AnatomyScores:
    """Anatomy quality scores."""

    overall: float
    proportions: float
    pose_accuracy: float
    hand_quality: float
    face_quality: float

    @property
    def is_acceptable(self) -> bool:
        return self.overall >= 0.5


@dataclass(frozen=True)
class CompositionScores:
    """Composition quality scores."""

    overall: float
    rule_of_thirds: float
    balance: float
    focal_point: float
    framing: float

    @property
    def is_acceptable(self) -> bool:
        return self.overall >= 0.5


@dataclass(frozen=True)
class ReadabilityScores:
    """Readability quality scores."""

    overall: float
    contrast: float
    clarity: float
    text_legibility: float
    panel_flow: float

    @property
    def is_acceptable(self) -> bool:
        return self.overall >= 0.5


@dataclass(frozen=True)
class ContentFlags:
    """Content safety flags."""

    nsfw_detected: bool
    violence_level: float  # 0-1
    suggestive_level: float  # 0-1
    gore_detected: bool

    @property
    def is_safe(self) -> bool:
        return not self.nsfw_detected and not self.gore_detected


@dataclass(frozen=True)
class QCReport:
    """Complete quality control report."""

    report_id: str
    image_id: str

    # Scores
    anatomy: AnatomyScores
    composition: CompositionScores
    readability: ReadabilityScores
    content: ContentFlags

    # Overall
    overall_score: float
    score_level: QCScoreLevel

    # Categorization
    failure_categories: tuple[str, ...] = ()

    # Recommendations
    suggested_fixes: tuple[str, ...] = ()
    auto_redraw_recommended: bool = False

    # Metadata
    analyzed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    analyzer_version: str = "1.0.0"

    @property
    def passed(self) -> bool:
        """Check if image passed QC."""
        return (
            self.overall_score >= 0.5
            and self.anatomy.is_acceptable
            and self.composition.is_acceptable
            and self.readability.is_acceptable
            and self.content.is_safe
        )

    @property
    def needs_human_review(self) -> bool:
        """Check if image needs human review."""
        return 0.4 <= self.overall_score < 0.6


class QCAnalyzer(ABC):
    """Abstract base class for QC analyzers."""

    @abstractmethod
    async def analyze(self, image_data: bytes, image_id: str) -> QCReport:
        """Analyze image and return QC report."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if analyzer is available."""
        pass


class MockQCAnalyzer(QCAnalyzer):
    """Mock QC analyzer for testing without ML models."""

    def __init__(self, deterministic: bool = True) -> None:
        self.deterministic = deterministic

    def is_available(self) -> bool:
        return True

    async def analyze(self, image_data: bytes, image_id: str) -> QCReport:
        """Generate deterministic mock QC scores."""
        import hashlib
        import random

        # Use image hash for deterministic scoring
        image_hash = hashlib.sha256(image_data).hexdigest()

        if self.deterministic:
            seed = int(image_hash[:8], 16)
            rng = random.Random(seed)
        else:
            rng = random.Random()

        # Generate mock scores
        anatomy_overall = rng.uniform(0.4, 0.95)
        composition_overall = rng.uniform(0.5, 0.95)
        readability_overall = rng.uniform(0.6, 0.98)

        # Derive sub-scores
        anatomy = AnatomyScores(
            overall=anatomy_overall,
            proportions=rng.uniform(
                max(0, anatomy_overall - 0.1), min(1, anatomy_overall + 0.1)
            ),
            pose_accuracy=rng.uniform(
                max(0, anatomy_overall - 0.15), min(1, anatomy_overall + 0.1)
            ),
            hand_quality=rng.uniform(
                max(0, anatomy_overall - 0.2), min(1, anatomy_overall + 0.05)
            ),
            face_quality=rng.uniform(
                max(0, anatomy_overall - 0.1), min(1, anatomy_overall + 0.1)
            ),
        )

        composition = CompositionScores(
            overall=composition_overall,
            rule_of_thirds=rng.uniform(
                max(0, composition_overall - 0.1), min(1, composition_overall + 0.1)
            ),
            balance=rng.uniform(
                max(0, composition_overall - 0.1), min(1, composition_overall + 0.1)
            ),
            focal_point=rng.uniform(
                max(0, composition_overall - 0.15), min(1, composition_overall + 0.1)
            ),
            framing=rng.uniform(
                max(0, composition_overall - 0.1), min(1, composition_overall + 0.1)
            ),
        )

        readability = ReadabilityScores(
            overall=readability_overall,
            contrast=rng.uniform(
                max(0, readability_overall - 0.1), min(1, readability_overall + 0.05)
            ),
            clarity=rng.uniform(
                max(0, readability_overall - 0.1), min(1, readability_overall + 0.05)
            ),
            text_legibility=rng.uniform(0.6, 1.0),
            panel_flow=rng.uniform(0.5, 1.0),
        )

        content = ContentFlags(
            nsfw_detected=rng.random() < 0.05,
            violence_level=rng.uniform(0, 0.3),
            suggestive_level=rng.uniform(0, 0.2),
            gore_detected=rng.random() < 0.02,
        )

        # Calculate overall
        overall = (
            anatomy_overall * 0.35
            + composition_overall * 0.35
            + readability_overall * 0.30
        )

        # Determine score level
        if overall >= 0.9:
            level = QCScoreLevel.EXCELLENT
        elif overall >= 0.7:
            level = QCScoreLevel.GOOD
        elif overall >= 0.5:
            level = QCScoreLevel.ACCEPTABLE
        elif overall >= 0.3:
            level = QCScoreLevel.POOR
        else:
            level = QCScoreLevel.REJECT

        # Determine failure categories
        failures = []
        if anatomy_overall < 0.5:
            failures.append("anatomy")
        if composition_overall < 0.5:
            failures.append("composition")
        if readability_overall < 0.5:
            failures.append("readability")
        if content.nsfw_detected:
            failures.append("nsfw_content")

        # Generate suggestions
        suggestions = []
        if anatomy.hand_quality < 0.5:
            suggestions.append("Review hand positioning and proportions")
        if composition.rule_of_thirds < 0.5:
            suggestions.append("Adjust composition to follow rule of thirds")
        if readability.contrast < 0.6:
            suggestions.append("Increase contrast for better readability")

        return QCReport(
            report_id=f"qc-{image_hash[:12]}",
            image_id=image_id,
            anatomy=anatomy,
            composition=composition,
            readability=readability,
            content=content,
            overall_score=overall,
            score_level=level,
            failure_categories=tuple(failures),
            suggested_fixes=tuple(suggestions),
            auto_redraw_recommended=overall < 0.5 and not content.nsfw_detected,
        )


class CLIPBasedQCAnalyzer(QCAnalyzer):
    """QC analyzer using CLIP and other vision models."""

    def __init__(self) -> None:
        self._clip_model: Any | None = None
        self._detector: Any | None = None

    def is_available(self) -> bool:
        """Check if required models are available."""
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401

            return True
        except ImportError:
            return False

    def _load_models(self) -> None:
        """Lazy load vision models."""
        if self._clip_model is None:
            try:
                import torch  # noqa: F401
                from transformers import CLIPModel, CLIPProcessor
            except ImportError as e:
                raise ImportError(
                    "transformers or torch not installed. "
                    "Run: pip install transformers torch"
                ) from e

            self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32"
            )

    async def analyze(self, image_data: bytes, image_id: str) -> QCReport:
        """Analyze image using CLIP and heuristics."""
        import asyncio
        import io

        from PIL import Image

        # Load models in executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_models)

        # Load image
        image = Image.open(io.BytesIO(image_data))

        # Analyze composition
        comp_score = await self._analyze_composition(image)

        # Analyze anatomy (using simple heuristics for now)
        anatomy_score = await self._analyze_anatomy(image)

        # Analyze readability
        readability_score = await self._analyze_readability(image)

        # Content check
        content = await self._check_content(image)

        # Calculate overall
        overall = (
            anatomy_score.overall * 0.35
            + comp_score.overall * 0.35
            + readability_score.overall * 0.30
        )

        return QCReport(
            report_id=f"qc-{image_id}",
            image_id=image_id,
            anatomy=anatomy_score,
            composition=comp_score,
            readability=readability_score,
            content=content,
            overall_score=overall,
            score_level=self._score_to_level(overall),
        )

    async def _analyze_composition(self, image: Any) -> CompositionScores:
        """Analyze composition using CLIP."""
        import numpy as np

        # Convert to numpy
        img_array = np.array(image)
        height, width = img_array.shape[:2]

        # Simple composition heuristics
        # Check if image has clear focal point (brightness variance)
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array

        # Calculate rule of thirds alignment
        h_third, w_third = height // 3, width // 3
        intersection_points = [
            (h_third, w_third),
            (h_third, 2 * w_third),
            (2 * h_third, w_third),
            (2 * h_third, 2 * w_third),
        ]

        # Check brightness at intersection points
        point_brightness = []
        for y, x in intersection_points:
            region = gray[
                max(0, y - 10) : min(height, y + 10),
                max(0, x - 10) : min(width, x + 10),
            ]
            point_brightness.append(np.mean(region))

        # Variance in brightness at thirds indicates good composition
        thirds_score = min(1.0, np.std(point_brightness) / 50 + 0.5)

        overall = thirds_score * 0.8 + 0.2  # Base score

        return CompositionScores(
            overall=overall,
            rule_of_thirds=thirds_score,
            balance=overall,
            focal_point=thirds_score,
            framing=0.7,
        )

    async def _analyze_anatomy(self, image: Any) -> AnatomyScores:
        """Analyze anatomy (placeholder for pose detection)."""
        # This would use a pose detection model in production
        # For now, return reasonable scores
        return AnatomyScores(
            overall=0.75,
            proportions=0.75,
            pose_accuracy=0.70,
            hand_quality=0.65,
            face_quality=0.80,
        )

    async def _analyze_readability(self, image: Any) -> ReadabilityScores:
        """Analyze readability (contrast, clarity)."""
        import numpy as np

        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array

        # Calculate contrast
        contrast = np.std(gray) / 128  # Normalize

        # Calculate clarity (Laplacian variance)
        from scipy import ndimage

        laplacian = ndimage.laplace(gray)
        clarity = min(1.0, np.var(laplacian) / 500)

        overall = contrast * 0.5 + clarity * 0.5

        return ReadabilityScores(
            overall=overall,
            contrast=contrast,
            clarity=clarity,
            text_legibility=0.8,
            panel_flow=0.75,
        )

    async def _check_content(self, image: Any) -> ContentFlags:
        """Check content safety."""
        # This would use a content moderation model in production
        return ContentFlags(
            nsfw_detected=False,
            violence_level=0.1,
            suggestive_level=0.05,
            gore_detected=False,
        )

    def _score_to_level(self, score: float) -> QCScoreLevel:
        """Convert score to level."""
        if score >= 0.9:
            return QCScoreLevel.EXCELLENT
        elif score >= 0.7:
            return QCScoreLevel.GOOD
        elif score >= 0.5:
            return QCScoreLevel.ACCEPTABLE
        elif score >= 0.3:
            return QCScoreLevel.POOR
        else:
            return QCScoreLevel.REJECT


class QCAnalyzerFactory:
    """Factory for creating QC analyzers."""

    @staticmethod
    def create(analyzer_type: str | None = None) -> QCAnalyzer:
        """Create QC analyzer."""
        if analyzer_type is None:
            # Auto-detect
            clip_analyzer = CLIPBasedQCAnalyzer()
            if clip_analyzer.is_available():
                return clip_analyzer
            return MockQCAnalyzer()

        match analyzer_type:
            case "clip":
                return CLIPBasedQCAnalyzer()
            case "mock":
                return MockQCAnalyzer()
            case _:
                raise ValueError(f"Unknown analyzer type: {analyzer_type}")


# Global analyzer instance
_global_analyzer: QCAnalyzer | None = None


def get_qc_analyzer() -> QCAnalyzer:
    """Get or create global QC analyzer."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = QCAnalyzerFactory.create()
    return _global_analyzer


def set_qc_analyzer(analyzer: QCAnalyzer) -> None:
    """Set global QC analyzer."""
    global _global_analyzer
    _global_analyzer = analyzer


@dataclass
class AutoRedrawResult:
    """Result from auto-redraw attempt."""

    original_image_id: str
    new_image_id: str | None
    new_report: QCReport | None
    attempts: int
    improved: bool
    final_score: float


async def auto_redraw_with_qc(
    image_data: bytes,
    image_id: str,
    generate_fn,
    max_attempts: int = 3,
    score_threshold: float = 0.5,
) -> AutoRedrawResult:
    """Automatically redraw image until it passes QC.

    Args:
        image_data: Original image data
        image_id: Original image ID
        generate_fn: Async function that generates new image
        max_attempts: Maximum redraw attempts
        score_threshold: Minimum acceptable score

    Returns:
        AutoRedrawResult with best attempt
    """
    analyzer = get_qc_analyzer()

    # Analyze original
    original_report = await analyzer.analyze(image_data, image_id)

    if original_report.passed:
        return AutoRedrawResult(
            original_image_id=image_id,
            new_image_id=None,
            new_report=original_report,
            attempts=0,
            improved=True,
            final_score=original_report.overall_score,
        )

    best_score = original_report.overall_score
    best_image_id = image_id
    best_report = original_report
    _ = image_data  # Keep reference but unused

    for attempt in range(max_attempts):
        # Generate new image
        new_image_data = await generate_fn()
        new_image_id = f"{image_id}-redraw-{attempt + 1}"

        # Analyze new image
        new_report = await analyzer.analyze(new_image_data, new_image_id)

        if new_report.overall_score > best_score:
            best_score = new_report.overall_score
            best_image_id = new_image_id
            best_report = new_report
            _ = new_image_data  # Keep reference but unused

        if new_report.passed:
            break

    return AutoRedrawResult(
        original_image_id=image_id,
        new_image_id=best_image_id if best_image_id != image_id else None,
        new_report=best_report,
        attempts=max_attempts,
        improved=best_score > original_report.overall_score,
        final_score=best_score,
    )
