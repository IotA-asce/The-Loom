"""Diffusion backend abstraction layer for The Loom.

Provides unified interface for multiple image generation backends:
- Local Stable Diffusion (with optional ControlNet)
- Stability AI API
- Mock backend for testing
"""

from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DiffusionConfig:
    """Configuration for diffusion backend."""

    model_id: str = "runwayml/stable-diffusion-v1-5"
    scheduler: str = "ddim"
    steps: int = 28
    guidance_scale: float = 7.5
    height: int = 512
    width: int = 512

    # Optional ControlNet
    controlnet_model: str | None = None

    # Device configuration
    device: str = "auto"  # auto, cpu, cuda, mps

    # For API-based backends
    api_key: str | None = None
    base_url: str | None = None


@dataclass(frozen=True)
class ControlNetCondition:
    """ControlNet-compatible guidance condition."""

    control_type: str  # pose, depth, canny, etc.
    weight: float
    image_path: str | None = None  # Reference image for control


@dataclass(frozen=True)
class GenerationRequest:
    """Request for image generation."""

    prompt: str
    negative_prompt: str = ""
    seed: int = 42
    num_images: int = 1

    # ControlNet conditions
    controlnet_conditions: tuple[ControlNetCondition, ...] = ()

    # Override config per request
    steps: int | None = None
    guidance_scale: float | None = None
    height: int | None = None
    width: int | None = None


@dataclass(frozen=True)
class GenerationResult:
    """Result from image generation."""

    image_data: bytes  # PNG bytes
    prompt: str
    negative_prompt: str
    seed: int
    model_id: str
    generation_time_ms: float

    # Quality metrics
    brightness: float = 0.5
    contrast: float = 0.5

    # Metadata
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class ModelInfo:
    """Information about an available model."""

    model_id: str
    name: str
    description: str
    requires_auth: bool
    supports_controlnet: bool
    max_resolution: tuple[int, int]


class DiffusionBackend(ABC):
    """Abstract base class for diffusion backends."""

    def __init__(self, config: DiffusionConfig) -> None:
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate backend configuration."""
        pass

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> list[GenerationResult]:
        """Generate images from the request."""
        pass

    @abstractmethod
    async def get_available_models(self) -> list[ModelInfo]:
        """Get list of available models."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available (models loaded, API reachable)."""
        pass

    def _compute_hash(self, data: bytes) -> str:
        """Compute SHA256 hash of data."""
        return hashlib.sha256(data).hexdigest()


class MockDiffusionBackend(DiffusionBackend):
    """Mock backend for testing without GPU or API."""

    def _validate_config(self) -> None:
        pass

    async def generate(self, request: GenerationRequest) -> list[GenerationResult]:
        """Generate mock image data (random PNG bytes)."""
        import random
        import time

        start_time = time.time()
        results = []

        for i in range(request.num_images):
            # Create deterministic "image" based on seed and index
            seed = request.seed + i
            rng = random.Random(seed)

            # Generate random PNG-like bytes (not a real PNG, just mock data)
            # In reality this would be a real PNG, but for mock we'll create
            # a placeholder
            image_bytes = bytes([rng.randint(0, 255) for _ in range(1024)])

            # Mock quality metrics
            brightness = rng.uniform(0.3, 0.7)
            contrast = rng.uniform(0.4, 0.8)

            results.append(
                GenerationResult(
                    image_data=image_bytes,
                    prompt=request.prompt,
                    negative_prompt=request.negative_prompt,
                    seed=seed,
                    model_id=self.config.model_id,
                    generation_time_ms=(
                        (time.time() - start_time) * 1000 / request.num_images
                    ),
                    brightness=brightness,
                    contrast=contrast,
                )
            )

        return results

    async def get_available_models(self) -> list[ModelInfo]:
        """Get mock model list."""
        return [
            ModelInfo(
                model_id="mock-sd-v1-5",
                name="Mock Stable Diffusion v1.5",
                description="Mock backend for testing",
                requires_auth=False,
                supports_controlnet=True,
                max_resolution=(1024, 1024),
            )
        ]

    def is_available(self) -> bool:
        """Mock is always available."""
        return True


class LocalDiffusionBackend(DiffusionBackend):
    """Local Stable Diffusion backend using diffusers library."""

    def __init__(self, config: DiffusionConfig) -> None:
        super().__init__(config)
        self._pipeline: Any | None = None
        self._controlnet_pipeline: Any | None = None

    def _validate_config(self) -> None:
        if self.config.device == "auto":
            import torch

            if torch.cuda.is_available():
                object.__setattr__(self.config, "device", "cuda")
            elif torch.backends.mps.is_available():
                object.__setattr__(self.config, "device", "mps")
            else:
                object.__setattr__(self.config, "device", "cpu")

    def _get_pipeline(self) -> Any:
        """Lazy load diffusion pipeline."""
        if self._pipeline is None:
            try:
                import torch
                from diffusers import StableDiffusionPipeline
            except ImportError as e:
                raise ImportError(
                    "diffusers not installed. Run: pip install diffusers "
                    "transformers accelerate"
                ) from e

            # Load pipeline
            self._pipeline = StableDiffusionPipeline.from_pretrained(
                self.config.model_id,
                torch_dtype=(
                    torch.float16 if self.config.device == "cuda" else torch.float32
                ),
                safety_checker=None,  # Disable safety checker for speed
            )
            self._pipeline = self._pipeline.to(self.config.device)

            # Enable optimizations
            if self.config.device == "cuda":
                self._pipeline.enable_attention_slicing()

        return self._pipeline

    def _get_controlnet_pipeline(self, controlnet_type: str) -> Any:
        """Lazy load ControlNet pipeline."""
        if self._controlnet_pipeline is None:
            try:
                import torch
                from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
            except ImportError as e:
                raise ImportError(
                    "diffusers not installed. Run: pip install diffusers "
                    "transformers accelerate"
                ) from e

            # Map control type to model
            controlnet_models = {
                "pose": "lllyasviel/sd-controlnet-openpose",
                "canny": "lllyasviel/sd-controlnet-canny",
                "depth": "lllyasviel/sd-controlnet-depth",
            }

            model_id = controlnet_models.get(controlnet_type)
            if model_id is None:
                raise ValueError(f"Unknown ControlNet type: {controlnet_type}")

            controlnet = ControlNetModel.from_pretrained(
                model_id,
                torch_dtype=(
                    torch.float16 if self.config.device == "cuda" else torch.float32
                ),
            )

            self._controlnet_pipeline = (
                StableDiffusionControlNetPipeline.from_pretrained(
                    self.config.model_id,
                    controlnet=controlnet,
                    torch_dtype=(
                        torch.float16 if self.config.device == "cuda" else torch.float32
                    ),
                    safety_checker=None,
                )
            )
            self._controlnet_pipeline = self._controlnet_pipeline.to(self.config.device)

        return self._controlnet_pipeline

    async def generate(self, request: GenerationRequest) -> list[GenerationResult]:
        """Generate images using local Stable Diffusion."""
        import asyncio
        import time
        from io import BytesIO

        loop = asyncio.get_event_loop()
        start_time = time.time()

        # Determine which pipeline to use
        has_controlnet = len(request.controlnet_conditions) > 0

        if has_controlnet:
            # Use ControlNet (only first condition for simplicity)
            condition = request.controlnet_conditions[0]
            pipeline = self._get_controlnet_pipeline(condition.control_type)

            # Load control image
            control_image = None
            if condition.image_path and os.path.exists(condition.image_path):
                from PIL import Image

                control_image = Image.open(condition.image_path).convert("RGB")
        else:
            pipeline = self._get_pipeline()
            control_image = None

        # Generate in executor to not block
        def _generate():
            generator = None
            try:
                import torch

                generator = torch.Generator(device=self.config.device).manual_seed(
                    request.seed
                )
            except Exception:
                pass

            kwargs = {
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "num_inference_steps": request.steps or self.config.steps,
                "guidance_scale": request.guidance_scale or self.config.guidance_scale,
                "height": request.height or self.config.height,
                "width": request.width or self.config.width,
                "num_images_per_prompt": request.num_images,
                "generator": generator,
            }

            if control_image is not None:
                kwargs["image"] = control_image

            output = pipeline(**kwargs)
            return output.images

        images = await loop.run_in_executor(None, _generate)

        # Convert to bytes
        results = []
        for i, image in enumerate(images):
            img_bytes = BytesIO()
            image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Estimate brightness/contrast
            import numpy as np

            img_array = np.array(image.convert("L"))
            brightness = float(np.mean(img_array)) / 255.0
            contrast = float(np.std(img_array)) / 128.0

            results.append(
                GenerationResult(
                    image_data=img_bytes.getvalue(),
                    prompt=request.prompt,
                    negative_prompt=request.negative_prompt,
                    seed=request.seed + i,
                    model_id=self.config.model_id,
                    generation_time_ms=(time.time() - start_time) * 1000 / len(images),
                    brightness=brightness,
                    contrast=contrast,
                )
            )

        return results

    async def get_available_models(self) -> list[ModelInfo]:
        """Get available local models."""
        return [
            ModelInfo(
                model_id="runwayml/stable-diffusion-v1-5",
                name="Stable Diffusion v1.5",
                description="Standard SD model, good general performance",
                requires_auth=False,
                supports_controlnet=True,
                max_resolution=(512, 512),
            ),
            ModelInfo(
                model_id="stabilityai/stable-diffusion-2-1",
                name="Stable Diffusion v2.1",
                description="Improved SD model",
                requires_auth=False,
                supports_controlnet=True,
                max_resolution=(768, 768),
            ),
        ]

    def is_available(self) -> bool:
        """Check if diffusers is installed."""
        try:
            import diffusers  # noqa: F401
            import torch  # noqa: F401

            return True
        except ImportError:
            return False


class StabilityAIBackend(DiffusionBackend):
    """Stability AI API backend for cloud image generation."""

    API_BASE_URL = "https://api.stability.ai/v2beta"

    def __init__(self, config: DiffusionConfig) -> None:
        super().__init__(config)
        self._client: Any | None = None

    def _validate_config(self) -> None:
        if not self.config.api_key:
            # Try to get from environment
            api_key = os.environ.get("STABILITY_API_KEY")
            if api_key:
                object.__setattr__(self.config, "api_key", api_key)
            else:
                raise ValueError(
                    "Stability AI API key required. Set STABILITY_API_KEY."
                )

    def _get_headers(self) -> dict[str, str]:
        """Get API headers."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    async def generate(self, request: GenerationRequest) -> list[GenerationResult]:
        """Generate images using Stability AI API."""
        import time

        import aiohttp

        start_time = time.time()

        # Map to Stability AI engine
        engine_id = "stable-diffusion-v1-6"

        url = f"{self.API_BASE_URL}/stable-image/generate/sd3"

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Accept": "image/*",
        }

        # For SD3, use simpler endpoint
        # For Ultra/Core, use different endpoints
        data = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "seed": request.seed,
            "output_format": "png",
        }

        results = []

        async with aiohttp.ClientSession() as session:
            for i in range(request.num_images):
                if i > 0:
                    data["seed"] = request.seed + i

                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        image_data = await response.read()

                        results.append(
                            GenerationResult(
                                image_data=image_data,
                                prompt=request.prompt,
                                negative_prompt=request.negative_prompt,
                                seed=request.seed + i,
                                model_id=engine_id,
                                generation_time_ms=(
                                    (time.time() - start_time)
                                    * 1000
                                    / request.num_images
                                ),
                            )
                        )
                    else:
                        error_text = await response.text()
                        raise RuntimeError(f"Stability AI API error: {error_text}")

        return results

    async def get_available_models(self) -> list[ModelInfo]:
        """Get available Stability AI models."""
        return [
            ModelInfo(
                model_id="sd3-large",
                name="Stable Diffusion 3 Large",
                description="High quality generation",
                requires_auth=True,
                supports_controlnet=False,
                max_resolution=(1024, 1024),
            ),
            ModelInfo(
                model_id="sd3-medium",
                name="Stable Diffusion 3 Medium",
                description="Balanced quality and speed",
                requires_auth=True,
                supports_controlnet=False,
                max_resolution=(1024, 1024),
            ),
        ]

    def is_available(self) -> bool:
        """Check if API key is set."""
        return bool(self.config.api_key)


class DiffusionBackendFactory:
    """Factory for creating diffusion backends."""

    _backends: dict[str, type[DiffusionBackend]] = {
        "mock": MockDiffusionBackend,
        "local": LocalDiffusionBackend,
        "stability": StabilityAIBackend,
    }

    @classmethod
    def create(
        cls,
        backend_type: str | None = None,
        config: DiffusionConfig | None = None,
    ) -> DiffusionBackend:
        """Create backend from type and config."""
        if backend_type is None:
            # Auto-detect
            if os.environ.get("STABILITY_API_KEY"):
                backend_type = "stability"
            else:
                try:
                    import diffusers  # noqa: F401

                    backend_type = "local"
                except ImportError:
                    backend_type = "mock"

        backend_class = cls._backends.get(backend_type)
        if backend_class is None:
            raise ValueError(f"Unknown backend type: {backend_type}")

        if config is None:
            config = DiffusionConfig()

        return backend_class(config)

    @classmethod
    def register_backend(cls, name: str, backend_class: type[DiffusionBackend]) -> None:
        """Register a custom backend."""
        cls._backends[name] = backend_class

    @classmethod
    def get_available_backends(cls) -> list[dict[str, Any]]:
        """Get list of available backends."""
        backends = []

        # Mock (always available)
        backends.append(
            {
                "id": "mock",
                "name": "Mock (Testing)",
                "available": True,
            }
        )

        # Local (requires diffusers)
        try:
            import diffusers  # noqa: F401
            import torch

            backends.append(
                {
                    "id": "local",
                    "name": "Local Stable Diffusion",
                    "available": True,
                    "device": "cuda" if torch.cuda.is_available() else "cpu",
                }
            )
        except ImportError:
            backends.append(
                {
                    "id": "local",
                    "name": "Local Stable Diffusion",
                    "available": False,
                    "reason": (
                        "diffusers not installed. Run: pip install diffusers "
                        "transformers accelerate"
                    ),
                }
            )

        # Stability AI (requires API key)
        if os.environ.get("STABILITY_API_KEY"):
            backends.append(
                {
                    "id": "stability",
                    "name": "Stability AI API",
                    "available": True,
                }
            )
        else:
            backends.append(
                {
                    "id": "stability",
                    "name": "Stability AI API",
                    "available": False,
                    "reason": "STABILITY_API_KEY not set",
                }
            )

        return backends


# Global backend instance
_global_backend: DiffusionBackend | None = None


def get_diffusion_backend() -> DiffusionBackend:
    """Get or create global diffusion backend."""
    global _global_backend
    if _global_backend is None:
        _global_backend = DiffusionBackendFactory.create()
    return _global_backend


def set_diffusion_backend(backend: DiffusionBackend) -> None:
    """Set global diffusion backend."""
    global _global_backend
    _global_backend = backend
