"""Artist agent interface backed by the image-generation engine."""

from __future__ import annotations

from core.image_generation_engine import (
    ArtistRequest,
    ArtistResult,
    DiffusionBackend,
    LoRAAdapterManager,
    generate_manga_sequence,
)


def generate_manga_panels(
    request: ArtistRequest,
    *,
    backend: DiffusionBackend | None = None,
    adapter_manager: LoRAAdapterManager | None = None,
) -> ArtistResult:
    """Generate manga panels with continuity, QC, and alignment safeguards."""

    return generate_manga_sequence(
        request,
        backend=backend,
        adapter_manager=adapter_manager,
    )


__all__ = [
    "ArtistRequest",
    "ArtistResult",
    "generate_manga_panels",
]
