"""Image storage and persistence for The Loom.

Handles saving, retrieving, and versioning generated images.
Supports local filesystem and cloud storage backends.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ImageMetadata:
    """Metadata for a stored image."""

    image_id: str
    original_filename: str
    content_type: str
    width: int
    height: int
    file_size_bytes: int

    # Generation metadata
    prompt: str = ""
    negative_prompt: str = ""
    seed: int = 0
    model_id: str = ""

    # Context
    story_id: str = ""
    branch_id: str = ""
    scene_id: str = ""
    panel_index: int | None = None

    # Versioning
    version: int = 1
    parent_version: str | None = None  # ID of previous version

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImageMetadata:
        """Create from dictionary."""
        # Filter only valid fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


@dataclass(frozen=True)
class StoredImage:
    """A stored image with metadata."""

    image_id: str
    metadata: ImageMetadata
    url: str  # Public or internal URL
    thumbnail_url: str | None = None


class ImageStorage(ABC):
    """Abstract base class for image storage backends."""

    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = base_path or "./generated_images"

    @abstractmethod
    async def save_image(
        self,
        image_data: bytes,
        metadata: ImageMetadata,
    ) -> StoredImage:
        """Save an image and return stored image info."""
        pass

    @abstractmethod
    async def get_image(self, image_id: str) -> bytes | None:
        """Get image data by ID."""
        pass

    @abstractmethod
    async def get_metadata(self, image_id: str) -> ImageMetadata | None:
        """Get image metadata by ID."""
        pass

    @abstractmethod
    async def delete_image(self, image_id: str) -> bool:
        """Delete an image. Returns True if deleted."""
        pass

    @abstractmethod
    async def list_images(
        self,
        story_id: str | None = None,
        branch_id: str | None = None,
        scene_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StoredImage]:
        """List images with optional filtering."""
        pass

    @abstractmethod
    async def create_new_version(
        self,
        image_id: str,
        new_image_data: bytes,
        updated_metadata: ImageMetadata | None = None,
    ) -> StoredImage | None:
        """Create a new version of an existing image."""
        pass

    @abstractmethod
    async def get_image_versions(self, image_id: str) -> list[StoredImage]:
        """Get all versions of an image."""
        pass

    def _generate_id(self, image_data: bytes, timestamp: str) -> str:
        """Generate unique image ID."""
        hash_input = f"{timestamp}:{len(image_data)}:{image_data[:100]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _get_image_hash(self, image_data: bytes) -> str:
        """Compute hash of image data."""
        return hashlib.sha256(image_data).hexdigest()


class LocalImageStorage(ImageStorage):
    """Local filesystem image storage."""

    def __init__(self, base_path: str | None = None) -> None:
        super().__init__(base_path)
        self._storage_path = Path(self.base_path)
        self._images_path = self._storage_path / "images"
        self._metadata_path = self._storage_path / "metadata"

        # Ensure directories exist
        self._images_path.mkdir(parents=True, exist_ok=True)
        self._metadata_path.mkdir(parents=True, exist_ok=True)

    def _get_image_path(self, image_id: str) -> Path:
        """Get filesystem path for image."""
        # Organize by first 2 chars of ID for better filesystem performance
        subdir = image_id[:2]
        return self._images_path / subdir / f"{image_id}.png"

    def _get_metadata_path(self, image_id: str) -> Path:
        """Get filesystem path for metadata."""
        subdir = image_id[:2]
        return self._metadata_path / subdir / f"{image_id}.json"

    async def save_image(
        self,
        image_data: bytes,
        metadata: ImageMetadata,
    ) -> StoredImage:
        """Save image to local filesystem."""
        import aiofiles

        # Create subdir if needed
        image_path = self._get_image_path(metadata.image_id)
        image_path.parent.mkdir(parents=True, exist_ok=True)

        # Save image
        async with aiofiles.open(image_path, "wb") as f:
            await f.write(image_data)

        # Save metadata
        metadata_path = self._get_metadata_path(metadata.image_id)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(metadata_path, "w") as f:
            await f.write(json.dumps(metadata.to_dict(), indent=2))

        return StoredImage(
            image_id=metadata.image_id,
            metadata=metadata,
            url=f"/api/images/{metadata.image_id}",
            thumbnail_url=None,  # Could generate thumbnails
        )

    async def get_image(self, image_id: str) -> bytes | None:
        """Get image data from filesystem."""
        import aiofiles

        image_path = self._get_image_path(image_id)

        if not image_path.exists():
            return None

        try:
            async with aiofiles.open(image_path, "rb") as f:
                return await f.read()
        except FileNotFoundError:
            return None

    async def get_metadata(self, image_id: str) -> ImageMetadata | None:
        """Get metadata from filesystem."""
        import aiofiles

        metadata_path = self._get_metadata_path(image_id)

        if not metadata_path.exists():
            return None

        try:
            async with aiofiles.open(metadata_path) as f:
                content = await f.read()
                data = json.loads(content)
                return ImageMetadata.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    async def delete_image(self, image_id: str) -> bool:
        """Delete image from filesystem."""
        image_path = self._get_image_path(image_id)
        metadata_path = self._get_metadata_path(image_id)

        deleted = False

        if image_path.exists():
            image_path.unlink()
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True

        return deleted

    async def list_images(
        self,
        story_id: str | None = None,
        branch_id: str | None = None,
        scene_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StoredImage]:
        """List images from filesystem."""
        images = []

        # Iterate through metadata files
        count = 0
        skip = 0

        for subdir in self._metadata_path.iterdir():
            if not subdir.is_dir():
                continue

            for metadata_file in subdir.glob("*.json"):
                if skip < offset:
                    skip += 1
                    continue

                if count >= limit:
                    break

                try:
                    metadata = await self.get_metadata(metadata_file.stem)
                    if metadata is None:
                        continue

                    # Apply filters
                    if story_id and metadata.story_id != story_id:
                        continue
                    if branch_id and metadata.branch_id != branch_id:
                        continue
                    if scene_id and metadata.scene_id != scene_id:
                        continue

                    images.append(
                        StoredImage(
                            image_id=metadata.image_id,
                            metadata=metadata,
                            url=f"/api/images/{metadata.image_id}",
                        )
                    )
                    count += 1

                except Exception:
                    continue

        return images

    async def create_new_version(
        self,
        image_id: str,
        new_image_data: bytes,
        updated_metadata: ImageMetadata | None = None,
    ) -> StoredImage | None:
        """Create new version of an image."""
        # Get existing metadata
        existing_metadata = await self.get_metadata(image_id)
        if existing_metadata is None:
            return None

        # Create new metadata
        new_metadata = updated_metadata or ImageMetadata(
            image_id=self._generate_id(new_image_data, datetime.now(UTC).isoformat()),
            original_filename=existing_metadata.original_filename,
            content_type=existing_metadata.content_type,
            width=existing_metadata.width,
            height=existing_metadata.height,
            file_size_bytes=len(new_image_data),
            prompt=existing_metadata.prompt,
            negative_prompt=existing_metadata.negative_prompt,
            seed=existing_metadata.seed,
            model_id=existing_metadata.model_id,
            story_id=existing_metadata.story_id,
            branch_id=existing_metadata.branch_id,
            scene_id=existing_metadata.scene_id,
            panel_index=existing_metadata.panel_index,
            version=existing_metadata.version + 1,
            parent_version=image_id,
        )

        # Save new version
        return await self.save_image(new_image_data, new_metadata)

    async def get_image_versions(self, image_id: str) -> list[StoredImage]:
        """Get all versions of an image."""
        # Get base image
        base_metadata = await self.get_metadata(image_id)
        if base_metadata is None:
            return []

        versions = []

        # Add base version
        versions.append(
            StoredImage(
                image_id=image_id,
                metadata=base_metadata,
                url=f"/api/images/{image_id}",
            )
        )

        # Find all images with this as parent
        # This is a simplified approach - in production, use a database
        for subdir in self._metadata_path.iterdir():
            if not subdir.is_dir():
                continue

            for metadata_file in subdir.glob("*.json"):
                try:
                    metadata = await self.get_metadata(metadata_file.stem)
                    if metadata and metadata.parent_version == image_id:
                        versions.append(
                            StoredImage(
                                image_id=metadata.image_id,
                                metadata=metadata,
                                url=f"/api/images/{metadata.image_id}",
                            )
                        )
                except Exception:
                    continue

        # Sort by version
        versions.sort(key=lambda x: x.metadata.version)

        return versions


# Global storage instance
_global_storage: ImageStorage | None = None


def get_image_storage() -> ImageStorage:
    """Get or create global image storage."""
    global _global_storage
    if _global_storage is None:
        _global_storage = LocalImageStorage()
    return _global_storage


def set_image_storage(storage: ImageStorage) -> None:
    """Set global image storage."""
    global _global_storage
    _global_storage = storage
