# Manga Story Extraction Strategy

## Overview

This document outlines the comprehensive strategy for extracting story content from manga volumes. The approach uses vision-capable LLMs to analyze every page, eliminating the need for separate OCR while ensuring complete narrative coverage.

## Core Principles

1. **Page-by-Page Analysis**: Every page is processed to ensure no content is missed
2. **Vision-First Approach**: LLM vision capabilities replace traditional OCR
3. **Incremental Processing**: Large volumes are processed in manageable chunks
4. **Data Resilience**: Multiple layers of storage and recovery mechanisms
5. **Quality Assurance**: Confidence scoring and manual review capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STORY EXTRACTION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Raw Pages  │───▶│ Page Chunker │───▶│ Vision LLM   │                  │
│  │  (webp/png)  │    │ (8-16 pages) │    │ (Gemini/etc) │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                   │                         │
│                                                   ▼                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Scene Graph │◀───│ Scene Merger │◀───│ Per-Page     │                  │
│  │  (SQLite)    │    │ (Deduplicate)│    │ JSON Output  │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Phase 1: Page Processing Strategy

### 1.1 Volume Analysis
Before extraction, analyze the volume to determine processing strategy:

```python
class VolumeAnalysis:
    page_count: int
    estimated_tokens: int  # Based on image sizes
    recommended_chunk_size: int  # 4-16 pages based on content density
    content_density: str  # "high" (text-heavy) / "medium" / "low" (action panels)
```

### 1.2 Chunking Strategy

| Volume Size | Chunk Size | Overlap | Strategy |
|-------------|------------|---------|----------|
| 1-50 pages | All pages | N/A | Single batch |
| 51-200 pages | 8 pages | 2 pages | Sequential with context carry |
| 201-500 pages | 12 pages | 3 pages | Parallel chunks + merge |
| 500+ pages | 16 pages | 4 pages | Parallel + hierarchical merge |

**Why overlap?** Ensures continuity between chunks. A scene spanning chunk boundaries is captured completely.

### 1.3 Vision Extraction Prompt

For each chunk, the LLM receives:

```
You are analyzing a sequence of manga pages. Extract the narrative content:

PAGES [X to Y] of [TITLE]:
[image 1]
[image 2]
...
[image N]

For each page, extract:
1. **Dialogue**: Character name + exact spoken text
2. **Narration**: Caption boxes, internal monologue
3. **Actions**: Key visual actions that advance the plot
4. **Setting**: Location, time of day if visually indicated
5. **Scene Boundaries**: Note where scenes begin/end

Output format:
{
  "pages": [
    {
      "page_number": N,
      "dialogue": [{"speaker": "Name", "text": "..."}],
      "narration": ["..."],
      "actions": ["..."],
      "setting": "...",
      "scene_start": true/false,
      "scene_end": true/false
    }
  ],
  "chunk_summary": "Brief narrative summary of these pages"
}
```

## Phase 2: Scene Synthesis

### 2.1 Page-Level Data Aggregation

After all chunks are processed, aggregate page data into continuous scenes:

```python
class SceneSynthesizer:
    def synthesize_scenes(self, page_data: list[PageData]) -> list[Scene]:
        scenes = []
        current_scene_pages = []
        
        for page in page_data:
            current_scene_pages.append(page)
            
            # Scene boundary detection
            if page.scene_end or self._is_scene_boundary(page):
                scene = self._create_scene(current_scene_pages)
                scenes.append(scene)
                current_scene_pages = []
        
        return scenes
```

### 2.2 Scene Enrichment

Each synthesized scene is enriched with:

```python
class Scene:
    scene_id: str
    title: str
    content: str  # Narrative prose version
    dialogue: list[DialogueLine]
    characters: list[str]  # Auto-extracted from dialogue
    page_start: int
    page_end: int
    mood: str  # Derived from dialogue tone + actions
    key_events: list[str]
    confidence_score: float  # LLM confidence
    
    # Provenance
    source_volume_id: str
    extraction_timestamp: str
    extraction_method: str  # "vision_gemini_2.0"
```

### 2.3 Scene Deduplication

When processing overlapping chunks, deduplicate scenes:

1. **Hash-based**: Content hash of key dialogue lines
2. **Semantic**: Embedding similarity for near-duplicate scenes
3. **Page-range**: Merge scenes covering same page ranges

## Phase 3: Storage Strategy

### 3.1 Multi-Layer Storage

```
Layer 1: Raw Extraction Cache (.loom/extractions/)
  - Raw LLM JSON responses (for recovery)
  - Page-by-page extraction results
  - Chunk metadata

Layer 2: Scene Database (.loom/graph.db)
  - GraphNode for each scene
  - GraphEdge linking scenes to manga
  - Scene metadata (characters, mood, etc.)

Layer 3: Event Store (.loom/events.db)
  - Extraction operation audit log
  - Before/after state for rollback
```

### 3.2 Raw Response Storage

Every LLM response is stored before parsing:

```python
class ExtractionCache:
    def save_raw_response(self, 
                          volume_id: str,
                          chunk_index: int,
                          response: str,
                          timestamp: str) -> str:
        """Save raw LLM response for recovery."""
        cache_path = f".loom/extractions/{volume_id}/chunk_{chunk_index}_{timestamp}.json"
        # Store with checksum for integrity
```

### 3.3 Incremental Persistence

During extraction, save progress every N pages:

```python
async def extract_with_checkpointing(volume_id, pages):
    for i, chunk in enumerate(chunk_pages(pages, chunk_size=8)):
        result = await extract_chunk(chunk)
        
        # Save checkpoint every 2 chunks
        if i % 2 == 0:
            await save_extraction_checkpoint(volume_id, i, results_so_far)
        
        # Resume capability
        if extraction_interrupted:
            results = await load_extraction_checkpoint(volume_id)
            continue_from = results.last_chunk_index
```

## Phase 4: Quality Assurance

### 4.1 Confidence Scoring

Each extraction receives confidence scores:

| Metric | Source | Threshold |
|--------|--------|-----------|
| Text Clarity | Vision model | >0.7 |
| Dialogue Attribution | Speaker consistency | >0.8 |
| Scene Continuity | Cross-page narrative flow | >0.6 |
| Content Coverage | Pages with extracted text / total | >0.5 |

### 4.2 Validation Rules

```python
class ExtractionValidator:
    def validate(self, extraction: Scene) -> list[ValidationIssue]:
        issues = []
        
        # Rule: Scene must have content or dialogue
        if not extraction.content and not extraction.dialogue:
            issues.append(ValidationIssue.NO_CONTENT)
        
        # Rule: Page range must be valid
        if extraction.page_start > extraction.page_end:
            issues.append(ValidationIssue.INVALID_RANGE)
        
        # Rule: Characters should appear in dialogue
        for char in extraction.characters:
            if not any(d.speaker == char for d in extraction.dialogue):
                issues.append(ValidationIssue.ORPHAN_CHARACTER)
        
        return issues
```

### 4.3 Low-Confidence Flagging

Scenes below confidence threshold are flagged for review:

- Stored with `needs_review: true`
- Shown in UI with warning indicator
- Can be re-extracted with different settings

## Phase 5: UI/UX Considerations

### 5.1 Progress Visualization

```
Extracting "Dragon Ball Vol 1"...
[████████████░░░░░░░░] 62% - Processing pages 49-56

Phase: Vision Analysis
├─ Pages 1-8 ✓
├─ Pages 9-16 ✓
├─ Pages 17-24 ✓
├─ Pages 25-32 ✓
├─ Pages 33-40 ✓
├─ Pages 41-48 ✓
└─ Pages 49-56 ... ⏳

Estimated time remaining: 2m 15s
```

### 5.2 Extraction Settings

User-configurable options:

- **Detail Level**: "Summary" (faster) / "Standard" / "Detailed" (slower, more tokens)
- **Language**: Auto-detect / Specify source language
- **Character Names**: Pre-seed known character names for better attribution
- **Chunk Size**: Auto / 4 pages / 8 pages / 16 pages

### 5.3 Review Interface

Post-extraction review panel:

- Side-by-side: Original page ↔ Extracted scene
- Edit extracted dialogue inline
- Merge/split scenes manually
- Mark scenes as reviewed

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Implement page chunking with overlap
- [ ] Create vision extraction endpoint
- [ ] Add raw response caching
- [ ] Basic progress tracking

### Phase 2: Synthesis (Week 3-4)
- [ ] Scene synthesis from page data
- [ ] Scene deduplication logic
- [ ] Confidence scoring
- [ ] Validation rules

### Phase 3: Storage (Week 5-6)
- [ ] Multi-layer storage implementation
- [ ] Checkpoint/resume functionality
- [ ] Event logging
- [ ] Recovery tools

### Phase 4: UI (Week 7-8)
- [ ] Progress visualization
- [ ] Extraction settings panel
- [ ] Review interface
- [ ] Quality indicators

## Technical Specifications

### Token Budget Estimation

```python
def estimate_tokens(page_count: int, avg_image_size_kb: int) -> dict:
    """Estimate token usage for extraction."""
    
    # Vision tokens: ~256 tokens per image
    vision_tokens = page_count * 256
    
    # Output tokens: ~500 tokens per page of content
    output_tokens = page_count * 500
    
    # Chunking overhead: 10% for overlaps
    overhead = int((vision_tokens + output_tokens) * 0.1)
    
    return {
        "input_tokens": vision_tokens,
        "output_tokens": output_tokens,
        "overhead": overhead,
        "total": vision_tokens + output_tokens + overhead
    }
```

### Rate Limiting

- Max 4 concurrent chunk extractions
- 1-second delay between chunks to respect API limits
- Exponential backoff on rate limit errors

### Error Handling

| Error Type | Strategy |
|------------|----------|
| Vision API failure | Retry 3x, then mark chunk for manual review |
| JSON parse error | Save raw response, use fallback parsing |
| Timeout | Split chunk in half, retry |
| Content policy | Log and skip page, continue extraction |

## Migration from Current System

### Current → New Strategy

1. **Deprecate OCR-first approach**: Remove OCR dependency
2. **Migrate existing extractions**: Mark as "legacy_ocr" method
3. **Re-extraction option**: Allow users to re-extract with vision
4. **Data preservation**: Keep old scene nodes, create new ones with "_v2" suffix

---

## Appendix: Prompt Engineering

### Chunk Context Preservation

When processing chunks sequentially, carry context forward:

```python
context_carry = {
    "previous_chunk_summary": chunk_summary,
    "ongoing_scene": current_scene if not completed,
    "characters_introduced": list(characters),
    "current_setting": setting
}
```

### Character Consistency

Maintain a running list of characters seen so far:

```
Characters identified so far:
- Goku (spiky hair, orange gi)
- Bulma (blue hair, Capsule Corp outfit)

If you see these characters in subsequent pages, use these names consistently.
```

### Scene Boundary Detection

LLM is instructed to detect scene changes via:

- Setting change (new location, time jump)
- Character exit/entrance
- Narrative time skip
- Chapter boundaries (if visible)

---

*Last updated: 2026-02-10*
*Status: Draft - Awaiting Review*
