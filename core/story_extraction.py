"""Manga story extraction using vision-capable LLMs.

This module implements the page-by-page vision extraction strategy
as defined in docs/STORY_EXTRACTION_STRATEGY.md.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Literal

from core.llm_backend import LLMBackend, LLMRequest, LLMMessage


@dataclass(frozen=True)
class PageData:
    """Extracted data from a single manga page."""
    
    page_number: int
    dialogue: list[dict[str, str]] = field(default_factory=list)
    narration: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    setting: str = ""
    scene_start: bool = False
    scene_end: bool = False
    confidence: float = 0.0


@dataclass(frozen=True)
class Scene:
    """A synthesized scene from multiple pages."""
    
    scene_id: str
    title: str
    content: str  # Narrative prose
    dialogue: list[dict[str, str]] = field(default_factory=list)
    characters: list[str] = field(default_factory=list)
    page_start: int = 1
    page_end: int = 1
    mood: str = "neutral"
    key_events: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    source_volume_id: str = ""
    extraction_timestamp: str = ""


@dataclass(frozen=True)
class ValidationIssue:
    """Validation issue for extracted content."""
    
    code: str
    message: str
    severity: Literal["warning", "error"] = "warning"


class PageChunker:
    """Chunks manga pages with overlap for processing."""
    
    CHUNK_SIZES = {
        "small": 50,    # 1-50 pages: process all at once
        "medium": 8,    # 51-200 pages: 8-page chunks
        "large": 12,    # 201-500 pages: 12-page chunks
        "xlarge": 16,   # 500+ pages: 16-page chunks
    }
    
    OVERLAPS = {
        "small": 0,
        "medium": 2,
        "large": 3,
        "xlarge": 4,
    }
    
    @classmethod
    def determine_strategy(cls, page_count: int) -> tuple[int, int]:
        """Determine chunk size and overlap based on page count.
        
        Returns:
            Tuple of (chunk_size, overlap)
        """
        if page_count <= 50:
            return (page_count, 0)  # Process all at once
        elif page_count <= 200:
            return (cls.CHUNK_SIZES["medium"], cls.OVERLAPS["medium"])
        elif page_count <= 500:
            return (cls.CHUNK_SIZES["large"], cls.OVERLAPS["large"])
        else:
            return (cls.CHUNK_SIZES["xlarge"], cls.OVERLAPS["xlarge"])
    
    @classmethod
    def chunk_pages(
        cls,
        image_paths: list[Path],
        chunk_size: int,
        overlap: int
    ) -> list[list[tuple[int, Path]]]:
        """Create overlapping chunks of pages.
        
        Args:
            image_paths: Sorted list of image paths
            chunk_size: Number of pages per chunk
            overlap: Number of pages to overlap between chunks
            
        Returns:
            List of chunks, each containing (page_number, path) tuples
        """
        if len(image_paths) <= chunk_size:
            return [[(i + 1, path) for i, path in enumerate(image_paths)]]
        
        chunks = []
        step = chunk_size - overlap
        
        for start_idx in range(0, len(image_paths), step):
            end_idx = min(start_idx + chunk_size, len(image_paths))
            chunk = [
                (start_idx + i + 1, path)
                for i, path in enumerate(image_paths[start_idx:end_idx])
            ]
            chunks.append(chunk)
            
            # Don't create a chunk that's just overlap
            if end_idx >= len(image_paths):
                break
        
        return chunks


class ExtractionCache:
    """Caches raw extraction responses for recovery."""
    
    def __init__(self, cache_dir: str | None = None) -> None:
        self.cache_dir = Path(cache_dir or ".loom/extractions")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_volume_dir(self, volume_id: str) -> Path:
        """Get cache directory for a volume."""
        volume_dir = self.cache_dir / volume_id
        volume_dir.mkdir(exist_ok=True)
        return volume_dir
    
    def save_raw_response(
        self,
        volume_id: str,
        chunk_index: int,
        response: str,
        timestamp: str,
        checksum: str | None = None
    ) -> str:
        """Save raw LLM response for recovery.
        
        Returns:
            Path to saved file
        """
        volume_dir = self._get_volume_dir(volume_id)
        filename = f"chunk_{chunk_index:04d}_{timestamp}.json"
        filepath = volume_dir / filename
        
        data = {
            "volume_id": volume_id,
            "chunk_index": chunk_index,
            "timestamp": timestamp,
            "response": response,
            "checksum": checksum or hashlib.sha256(response.encode()).hexdigest()[:16],
        }
        
        filepath.write_text(json.dumps(data, indent=2))
        return str(filepath)
    
    def load_raw_response(self, volume_id: str, chunk_index: int) -> dict | None:
        """Load cached raw response."""
        volume_dir = self._get_volume_dir(volume_id)
        
        # Find files matching this chunk
        pattern = f"chunk_{chunk_index:04d}_*.json"
        matches = list(volume_dir.glob(pattern))
        
        if not matches:
            return None
        
        # Return most recent
        latest = max(matches, key=lambda p: p.stat().st_mtime)
        return json.loads(latest.read_text())
    
    def get_extraction_status(self, volume_id: str) -> dict:
        """Get extraction status for resumption."""
        volume_dir = self._get_volume_dir(volume_id)
        
        if not volume_dir.exists():
            return {"completed_chunks": [], "last_chunk": -1}
        
        chunks = sorted(volume_dir.glob("chunk_*.json"))
        completed = [
            int(c.stem.split("_")[1])
            for c in chunks
        ]
        
        return {
            "completed_chunks": completed,
            "last_chunk": max(completed) if completed else -1,
        }
    
    def clear_cache(self, volume_id: str) -> None:
        """Clear extraction cache for a volume."""
        volume_dir = self._get_volume_dir(volume_id)
        if volume_dir.exists():
            for f in volume_dir.glob("*.json"):
                f.unlink()


class VisionExtractor:
    """Extracts text from manga pages using vision-capable LLMs."""
    
    def __init__(self, llm_backend: LLMBackend) -> None:
        self.llm = llm_backend
        self.cache = ExtractionCache()
    
    async def extract_chunk(
        self,
        volume_id: str,
        chunk_index: int,
        chunk: list[tuple[int, Path]],
        volume_title: str,
        context_carry: dict | None = None,
    ) -> dict[str, Any]:
        """Extract content from a chunk of pages.
        
        Args:
            volume_id: Manga volume ID
            chunk_index: Index of this chunk
            chunk: List of (page_number, image_path) tuples
            volume_title: Title of the manga
            context_carry: Context from previous chunk (for continuity)
            
        Returns:
            Parsed extraction result with pages, dialogue, etc.
        """
        from datetime import datetime, UTC
        import asyncio
        from PIL import Image
        import io
        
        timestamp = datetime.now(UTC).isoformat()
        
        # Load and resize images
        images = []
        for page_num, img_path in chunk:
            try:
                with Image.open(img_path) as img:
                    # Resize to reduce tokens
                    max_size = (1024, 1024)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Save to bytes
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    images.append(buffer.getvalue())
            except Exception as e:
                print(f"Failed to process image {img_path}: {e}")
                continue
        
        if not images:
            return {"pages": [], "chunk_summary": "", "error": "No images loaded"}
        
        # Build context section if carrying forward
        context_section = ""
        if context_carry:
            context_section = f"""
Context from previous pages:
- Previous summary: {context_carry.get('previous_chunk_summary', 'N/A')}
- Ongoing scene: {context_carry.get('ongoing_scene', 'None')}
- Characters so far: {', '.join(context_carry.get('characters_introduced', []))}
- Current setting: {context_carry.get('current_setting', 'Unknown')}
"""
        
        # Build prompt
        start_page = chunk[0][0]
        end_page = chunk[-1][0]
        
        prompt = f"""Analyze pages {start_page}-{end_page} of "{volume_title}".

{context_section}

For each page, extract:
1. **Dialogue**: Character name + exact spoken text (if speaker is unclear, use "Unknown")
2. **Narration**: Caption boxes, internal monologue, sound effects with meaning
3. **Actions**: Key visual actions that advance the plot
4. **Setting**: Location, time of day if visually indicated
5. **Scene Boundaries**: Mark where scenes begin/end (scene changes = new location, time jump, major event)

Output valid JSON only:
{{
  "pages": [
    {{
      "page_number": {start_page},
      "dialogue": [{{"speaker": "Name", "text": "Dialogue text"}}],
      "narration": ["Narration text"],
      "actions": ["Action description"],
      "setting": "Location description",
      "scene_start": false,
      "scene_end": false
    }}
  ],
  "chunk_summary": "Brief narrative summary of these pages",
  "characters_seen": ["List", "Of", "Characters"],
  "setting": "Current setting at end of chunk",
  "ongoing_scene": "Description of incomplete scene (if any)"
}}"""
        
        # Call LLM with vision
        try:
            response = await self.llm.generate_from_images(
                images=images,
                prompt=prompt,
                temperature=0.2,
                max_tokens=4000,
            )
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Cache raw response
            self.cache.save_raw_response(
                volume_id=volume_id,
                chunk_index=chunk_index,
                response=response_text,
                timestamp=timestamp,
            )
            
            # Parse JSON
            result = self._parse_extraction_response(response_text)
            result["_metadata"] = {
                "chunk_index": chunk_index,
                "timestamp": timestamp,
                "pages": [p[0] for p in chunk],
            }
            
            return result
            
        except Exception as e:
            print(f"Vision extraction failed for chunk {chunk_index}: {e}")
            return {
                "pages": [],
                "chunk_summary": "",
                "error": str(e),
                "_metadata": {
                    "chunk_index": chunk_index,
                    "timestamp": timestamp,
                    "pages": [p[0] for p in chunk],
                }
            }
    
    def _parse_extraction_response(self, response_text: str) -> dict:
        """Parse LLM response, handling markdown code blocks."""
        # Strip markdown
        cleaned = response_text.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # Find JSON
        start = cleaned.find('{')
        end = cleaned.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = cleaned[start:end]
            return json.loads(json_str)
        
        # Fallback: try parsing entire cleaned text
        return json.loads(cleaned)
    
    async def extract_volume(
        self,
        volume_id: str,
        image_paths: list[Path],
        volume_title: str,
        progress_callback: callable | None = None,
    ) -> AsyncIterator[dict]:
        """Extract all pages from a volume with progress updates.
        
        Yields:
            Progress updates and results for each chunk
        """
        # Determine chunking strategy
        chunk_size, overlap = PageChunker.determine_strategy(len(image_paths))
        
        # Create chunks
        chunks = PageChunker.chunk_pages(image_paths, chunk_size, overlap)
        
        # Check for existing progress
        status = self.cache.get_extraction_status(volume_id)
        start_chunk = status["last_chunk"] + 1
        
        if start_chunk > 0 and progress_callback:
            await progress_callback({
                "phase": "resume",
                "message": f"Resuming from chunk {start_chunk}",
                "progress": int((start_chunk / len(chunks)) * 25),
            })
        
        # Process chunks
        context_carry = None
        all_results = []
        
        for i, chunk in enumerate(chunks):
            if i < start_chunk:
                # Load from cache
                cached = self.cache.load_raw_response(volume_id, i)
                if cached:
                    result = self._parse_extraction_response(cached["response"])
                    result["_metadata"] = {
                        "chunk_index": i,
                        "timestamp": cached["timestamp"],
                        "pages": [p[0] for p in chunk],
                        "from_cache": True,
                    }
                else:
                    result = {"pages": [], "error": "Cache miss"}
            else:
                # Extract fresh
                if progress_callback:
                    await progress_callback({
                        "phase": "vision",
                        "message": f"Processing pages {chunk[0][0]}-{chunk[-1][0]}...",
                        "progress": int((i / len(chunks)) * 25) + 25,
                    })
                
                result = await self.extract_chunk(
                    volume_id=volume_id,
                    chunk_index=i,
                    chunk=chunk,
                    volume_title=volume_title,
                    context_carry=context_carry,
                )
                
                # Update context for next chunk
                context_carry = {
                    "previous_chunk_summary": result.get("chunk_summary", ""),
                    "ongoing_scene": result.get("ongoing_scene", ""),
                    "characters_introduced": result.get("characters_seen", []),
                    "current_setting": result.get("setting", ""),
                }
            
            all_results.append(result)
            yield {
                "type": "chunk_complete",
                "chunk_index": i,
                "total_chunks": len(chunks),
                "result": result,
            }
        
        yield {
            "type": "extraction_complete",
            "total_chunks": len(chunks),
            "all_results": all_results,
        }


class SceneSynthesizer:
    """Synthesizes scenes from page-level extraction data."""
    
    def __init__(self) -> None:
        pass
    
    def synthesize_scenes(
        self,
        page_data: list[PageData],
        volume_id: str,
    ) -> list[Scene]:
        """Aggregate page data into continuous scenes.
        
        Args:
            page_data: List of PageData from all chunks
            volume_id: Source volume ID
            
        Returns:
            List of synthesized Scene objects
        """
        from datetime import datetime, UTC
        import uuid
        
        scenes = []
        current_scene_pages: list[PageData] = []
        
        for page in page_data:
            current_scene_pages.append(page)
            
            # Scene boundary detection
            if page.scene_end or self._is_scene_boundary(page, current_scene_pages):
                scene = self._create_scene(
                    current_scene_pages,
                    volume_id,
                    str(uuid.uuid4())[:12],
                    datetime.now(UTC).isoformat(),
                )
                scenes.append(scene)
                current_scene_pages = []
        
        # Don't forget final scene
        if current_scene_pages:
            scene = self._create_scene(
                current_scene_pages,
                volume_id,
                str(uuid.uuid4())[:12],
                datetime.now(UTC).isoformat(),
            )
            scenes.append(scene)
        
        return scenes
    
    def _is_scene_boundary(self, page: PageData, context: list[PageData]) -> bool:
        """Detect if this page marks a scene boundary."""
        # Explicit marker from LLM
        if page.scene_start and len(context) > 1:
            return True
        
        # Setting change
        if len(context) > 1:
            prev_setting = context[-2].setting if len(context) > 1 else ""
            if page.setting and prev_setting and page.setting != prev_setting:
                return True
        
        return False
    
    def _create_scene(
        self,
        pages: list[PageData],
        volume_id: str,
        scene_id: str,
        timestamp: str,
    ) -> Scene:
        """Create a Scene from a list of pages."""
        # Collect all dialogue
        all_dialogue = []
        for p in pages:
            all_dialogue.extend(p.dialogue)
        
        # Extract unique characters
        characters = list(set(
            d.get("speaker", "Unknown")
            for d in all_dialogue
            if d.get("speaker") != "Unknown"
        ))
        
        # Build narrative content
        narration_parts = []
        for p in pages:
            narration_parts.extend(p.narration)
            narration_parts.extend(p.actions)
        
        content = " ".join(narration_parts)
        
        # Determine mood from dialogue and actions
        mood = self._detect_mood(pages)
        
        # Key events from actions
        key_events = []
        for p in pages:
            key_events.extend(p.actions)
        
        # Calculate confidence
        confidence = sum(p.confidence for p in pages) / len(pages) if pages else 0
        
        # Generate title
        title = self._generate_scene_title(pages, characters)
        
        return Scene(
            scene_id=f"scene_{scene_id}",
            title=title,
            content=content[:2000],  # Limit length
            dialogue=all_dialogue[:20],  # Limit dialogue entries
            characters=characters[:10],  # Limit character list
            page_start=pages[0].page_number,
            page_end=pages[-1].page_number,
            mood=mood,
            key_events=key_events[:10],
            confidence_score=round(confidence, 2),
            source_volume_id=volume_id,
            extraction_timestamp=timestamp,
        )
    
    def _detect_mood(self, pages: list[PageData]) -> str:
        """Detect scene mood from content."""
        # Simple keyword-based detection
        all_text = " ".join(
            p.setting + " " + " ".join(p.actions) + " ".join(p.narration)
            for p in pages
        ).lower()
        
        mood_keywords = {
            "tense": ["fight", "battle", "danger", "escape", "chase", "attack"],
            "peaceful": ["calm", "relax", "sleep", "peace", "quiet", "rest"],
            "romantic": ["love", "kiss", "heart", "date", " confession"],
            "mysterious": ["secret", "mystery", "unknown", "shadow", "dark"],
            "joyful": ["happy", "laugh", "smile", "celebrate", "victory"],
            "sad": ["cry", "tears", "death", "loss", "goodbye", "sad"],
        }
        
        scores = {
            mood: sum(1 for kw in keywords if kw in all_text)
            for mood, keywords in mood_keywords.items()
        }
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return "neutral"
    
    def _generate_scene_title(self, pages: list[PageData], characters: list[str]) -> str:
        """Generate a title for the scene."""
        if not pages:
            return "Untitled Scene"
        
        # Use setting if available
        settings = [p.setting for p in pages if p.setting]
        if settings:
            return f"Scene at {settings[0][:30]}"
        
        # Use characters
        if characters:
            if len(characters) <= 2:
                return f"{', '.join(characters[:2])}"
            else:
                return f"{characters[0]} and Others"
        
        # Fallback to page numbers
        return f"Pages {pages[0].page_number}-{pages[-1].page_number}"
    
    def deduplicate_scenes(self, scenes: list[Scene]) -> list[Scene]:
        """Remove duplicate scenes based on page ranges."""
        seen_ranges: set[tuple[int, int]] = set()
        unique: list[Scene] = []
        
        for scene in scenes:
            key = (scene.page_start, scene.page_end)
            if key not in seen_ranges:
                seen_ranges.add(key)
                unique.append(scene)
        
        return unique


class ExtractionValidator:
    """Validates extracted scenes for quality."""
    
    VALIDATION_RULES = {
        "NO_CONTENT": ("Scene has no content or dialogue", "error"),
        "INVALID_RANGE": ("Page range is invalid (start > end)", "error"),
        "ORPHAN_CHARACTER": ("Character mentioned but has no dialogue", "warning"),
        "LOW_CONFIDENCE": ("Scene confidence below threshold", "warning"),
        "NO_CHARACTERS": ("No characters identified", "warning"),
        "SINGLE_PAGE": ("Scene is only one page (might be incomplete)", "info"),
    }
    
    def __init__(self, confidence_threshold: float = 0.5) -> None:
        self.confidence_threshold = confidence_threshold
    
    def validate(self, scene: Scene) -> list[ValidationIssue]:
        """Validate a scene and return list of issues."""
        issues = []
        
        # Rule: Must have content or dialogue
        if not scene.content.strip() and not scene.dialogue:
            issues.append(ValidationIssue(
                code="NO_CONTENT",
                message=self.VALIDATION_RULES["NO_CONTENT"][0],
                severity="error",
            ))
        
        # Rule: Valid page range
        if scene.page_start > scene.page_end:
            issues.append(ValidationIssue(
                code="INVALID_RANGE",
                message=self.VALIDATION_RULES["INVALID_RANGE"][0],
                severity="error",
            ))
        
        # Rule: Low confidence
        if scene.confidence_score < self.confidence_threshold:
            issues.append(ValidationIssue(
                code="LOW_CONFIDENCE",
                message=f"{self.VALIDATION_RULES['LOW_CONFIDENCE'][0]} ({scene.confidence_score:.2f})",
                severity="warning",
            ))
        
        # Rule: Characters should have dialogue
        dialogue_speakers = {d.get("speaker", "") for d in scene.dialogue}
        for char in scene.characters:
            if char not in dialogue_speakers:
                issues.append(ValidationIssue(
                    code="ORPHAN_CHARACTER",
                    message=f"{self.VALIDATION_RULES['ORPHAN_CHARACTER'][0]}: {char}",
                    severity="warning",
                ))
        
        # Rule: No characters
        if not scene.characters:
            issues.append(ValidationIssue(
                code="NO_CHARACTERS",
                message=self.VALIDATION_RULES["NO_CHARACTERS"][0],
                severity="warning",
            ))
        
        return issues
    
    def calculate_overall_confidence(
        self,
        scenes: list[Scene],
        issues: list[list[ValidationIssue]],
    ) -> dict[str, float]:
        """Calculate overall extraction confidence metrics."""
        if not scenes:
            return {"overall": 0.0, "coverage": 0.0, "quality": 0.0}
        
        # Average scene confidence
        avg_confidence = sum(s.confidence_score for s in scenes) / len(scenes)
        
        # Error rate
        error_count = sum(
            1 for issue_list in issues
            for i in issue_list if i.severity == "error"
        )
        error_rate = error_count / len(scenes) if scenes else 0
        
        # Coverage (pages covered / total pages)
        # This is calculated separately and passed in
        
        return {
            "overall": round(avg_confidence * (1 - error_rate), 2),
            "quality": round(avg_confidence, 2),
            "error_rate": round(error_rate, 2),
        }


class StoryExtractionPipeline:
    """Main pipeline coordinating extraction, synthesis, and storage."""
    
    def __init__(self, llm_backend: LLMBackend) -> None:
        self.extractor = VisionExtractor(llm_backend)
        self.synthesizer = SceneSynthesizer()
        self.validator = ExtractionValidator()
        self.cache = ExtractionCache()
    
    async def extract(
        self,
        volume_id: str,
        image_paths: list[Path],
        volume_title: str,
        progress_callback: callable | None = None,
    ) -> dict[str, Any]:
        """Run full extraction pipeline.
        
        Returns:
            Dict with scenes, validation results, and metadata
        """
        # Phase 1: Vision extraction
        all_page_data: list[PageData] = []
        
        async for update in self.extractor.extract_volume(
            volume_id, image_paths, volume_title, progress_callback
        ):
            if update["type"] == "chunk_complete":
                # Convert chunk result to PageData
                for page in update["result"].get("pages", []):
                    page_data = PageData(
                        page_number=page.get("page_number", 0),
                        dialogue=page.get("dialogue", []),
                        narration=page.get("narration", []),
                        actions=page.get("actions", []),
                        setting=page.get("setting", ""),
                        scene_start=page.get("scene_start", False),
                        scene_end=page.get("scene_end", False),
                        confidence=0.8,  # Default confidence
                    )
                    all_page_data.append(page_data)
        
        if progress_callback:
            await progress_callback({
                "phase": "synthesis",
                "message": "Synthesizing scenes from page data...",
                "progress": 60,
            })
        
        # Phase 2: Scene synthesis
        scenes = self.synthesizer.synthesize_scenes(all_page_data, volume_id)
        scenes = self.synthesizer.deduplicate_scenes(scenes)
        
        if progress_callback:
            await progress_callback({
                "phase": "validation",
                "message": "Validating extracted scenes...",
                "progress": 75,
            })
        
        # Phase 3: Validation
        all_issues = [self.validator.validate(s) for s in scenes]
        confidence_metrics = self.validator.calculate_overall_confidence(scenes, all_issues)
        
        # Flag low-confidence scenes
        for i, scene in enumerate(scenes):
            if any(issue.severity == "error" for issue in all_issues[i]):
                # Mark for review
                scene.metadata["needs_review"] = True
        
        if progress_callback:
            await progress_callback({
                "phase": "complete",
                "message": f"Extraction complete! {len(scenes)} scenes created.",
                "progress": 100,
            })
        
        return {
            "scenes": scenes,
            "issues": all_issues,
            "confidence": confidence_metrics,
            "total_pages": len(all_page_data),
            "extraction_method": "vision_v2",
        }
