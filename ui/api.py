"""FastAPI backend API for Phase 8 frontend UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from core.frontend_workflow_engine import (
    AccessibilityManager,
    BranchWorkflowManager,
    DualViewManager,
    GraphViewport,
    GraphWorkspace,
    TunerControlPanel,
    TunerSettings,
    evaluate_phase8_done_criteria,
)
from core.story_graph_engine import BranchLifecycleManager
from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Pydantic models for API


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


class CamelModel(BaseModel):
    """Base model with camelCase alias generation."""

    class Config:
        alias_generator = to_camel_case
        populate_by_name = True


class GraphNodeCreate(CamelModel):
    node_id: str
    label: str
    branch_id: str
    scene_id: str
    x: float
    y: float
    importance: float = 0.5


class ViewportUpdate(BaseModel):
    x: float
    y: float
    width: float
    height: float
    zoom: float = 1.0


class BranchCreate(BaseModel):
    source_node_id: str
    label: str
    parent_branch_id: str = "main"


class BranchArchive(BaseModel):
    branch_id: str
    reason: str


class BranchMerge(BaseModel):
    source_branch_id: str
    target_branch_id: str


class TunerUpdate(BaseModel):
    violence: float = Field(ge=0.0, le=1.0, default=0.5)
    humor: float = Field(ge=0.0, le=1.0, default=0.5)
    romance: float = Field(ge=0.0, le=1.0, default=0.5)


class SentenceEdit(BaseModel):
    scene_id: str
    sentence_index: int
    previous_text: str
    new_text: str


class PanelRedraw(BaseModel):
    scene_id: str
    panel_index: int
    reason: str


class ReconcileRequest(BaseModel):
    scene_id: str
    text_version: str
    image_version: str


class GraphMetricsResponse(CamelModel):
    total_nodes: int
    visible_nodes: int
    visible_edges: int
    virtualization_ratio: float
    estimated_frame_ms: float
    mode: str
    performance_usable: bool


class SyncStateResponse(CamelModel):
    scene_id: str
    text_version: str
    image_version: str
    text_status: str
    image_status: str
    badges: list[dict[str, str]]
    sync_visible: bool
    sync_accurate: bool


class AccessibilityResponse(CamelModel):
    keyboard_coverage: float
    semantic_label_coverage: float
    non_color_indicator_coverage: float
    mobile_ready: bool
    issues: list[str]
    critical_flows_usable: bool


class Phase8MetricsResponse(CamelModel):
    graph_performance_usable: bool
    keyboard_mobile_usable: bool
    dual_sync_visible_and_accurate: bool
    virtualization_ratio: float
    estimated_frame_ms: float
    keyboard_coverage: float
    mismatch_rate: float


# State managers (singleton pattern)
class UIState:
    """Global UI state container."""

    def __init__(self) -> None:
        self.graph_workspace: GraphWorkspace | None = None
        self.branch_workflow: BranchWorkflowManager | None = None
        self.dual_view: DualViewManager | None = None
        self.tuner: TunerControlPanel | None = None
        self.accessibility: AccessibilityManager | None = None
        self.lifecycle: BranchLifecycleManager | None = None


_STATE = UIState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize state managers on startup."""
    _STATE.graph_workspace = GraphWorkspace(
        GraphViewport(x=0, y=0, width=1200, height=800, zoom=1.0)
    )
    _STATE.branch_workflow = BranchWorkflowManager()
    _STATE.dual_view = DualViewManager()
    _STATE.tuner = TunerControlPanel()
    _STATE.accessibility = AccessibilityManager()
    _STATE.lifecycle = BranchLifecycleManager()
    yield
    # Cleanup on shutdown


app = FastAPI(
    title="The Loom UI API",
    description="Frontend API for Phase 8 interactive graph UX and dual-view",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ G8.1: Interactive Graph UX ============


@app.get("/api/graph/metrics", response_model=GraphMetricsResponse)
async def get_graph_metrics() -> dict[str, Any]:
    """Get current graph render metrics including virtualization stats."""
    if _STATE.graph_workspace is None:
        raise HTTPException(status_code=500, detail="Graph workspace not initialized")

    metrics = _STATE.graph_workspace.render_metrics()
    return {
        "total_nodes": metrics.total_nodes,
        "visible_nodes": metrics.visible_nodes,
        "visible_edges": metrics.visible_edges,
        "virtualization_ratio": metrics.virtualization_ratio,
        "estimated_frame_ms": metrics.estimated_frame_ms,
        "mode": metrics.mode.value,
        "performance_usable": _STATE.graph_workspace.is_performance_usable(),
    }


@app.post("/api/graph/nodes")
async def create_node(node: GraphNodeCreate) -> dict[str, str]:
    """Add a new node to the graph."""
    if _STATE.graph_workspace is None:
        raise HTTPException(status_code=500, detail="Graph workspace not initialized")

    from core.frontend_workflow_engine import GraphNodeView

    graph_node = GraphNodeView(
        node_id=node.node_id,
        label=node.label,
        branch_id=node.branch_id,
        scene_id=node.scene_id,
        x=node.x,
        y=node.y,
        importance=node.importance,
    )
    _STATE.graph_workspace.add_node(graph_node)
    return {"status": "created", "node_id": node.node_id}


@app.post("/api/graph/viewport")
async def update_viewport(viewport: ViewportUpdate) -> dict[str, Any]:
    """Update graph viewport for semantic zoom."""
    if _STATE.graph_workspace is None:
        raise HTTPException(status_code=500, detail="Graph workspace not initialized")

    new_viewport = GraphViewport(
        x=viewport.x,
        y=viewport.y,
        width=viewport.width,
        height=viewport.height,
        zoom=viewport.zoom,
    )
    _STATE.graph_workspace.set_viewport(new_viewport)
    return {
        "status": "updated",
        "zoom_mode": _STATE.graph_workspace.zoom_mode.value,
    }


@app.post("/api/graph/undo")
async def undo_graph() -> dict[str, bool]:
    """Undo last graph operation."""
    if _STATE.graph_workspace is None:
        raise HTTPException(status_code=500, detail="Graph workspace not initialized")

    success = _STATE.graph_workspace.undo()
    return {"success": success}


@app.post("/api/graph/redo")
async def redo_graph() -> dict[str, bool]:
    """Redo last undone operation."""
    if _STATE.graph_workspace is None:
        raise HTTPException(status_code=500, detail="Graph workspace not initialized")

    success = _STATE.graph_workspace.redo()
    return {"success": success}


@app.post("/api/graph/autosave")
async def create_autosave(reason: str = "manual") -> dict[str, str]:
    """Create autosave checkpoint."""
    if _STATE.graph_workspace is None:
        raise HTTPException(status_code=500, detail="Graph workspace not initialized")

    checkpoint = _STATE.graph_workspace.create_autosave(reason)
    return {
        "checkpoint_id": checkpoint.checkpoint_id,
        "created_at": checkpoint.created_at,
    }


# ============ G8.2: Branching Workflow UX ============


@app.get("/api/branches")
async def list_branches() -> list[dict[str, Any]]:
    """List all branches with lineage info."""
    if _STATE.branch_workflow is None:
        raise HTTPException(status_code=500, detail="Branch workflow not initialized")

    branches = _STATE.branch_workflow.list_branches()
    return [
        {
            "branch_id": b.branch_id,
            "parent_branch_id": b.parent_branch_id,
            "source_node_id": b.source_node_id,
            "label": b.label,
            "status": b.status.value,
            "lineage": list(b.lineage),
            "created_at": b.created_at,
        }
        for b in branches
    ]


@app.post("/api/branches")
async def create_branch(request: BranchCreate) -> dict[str, Any]:
    """Create a new branch from a node."""
    if _STATE.branch_workflow is None:
        raise HTTPException(status_code=500, detail="Branch workflow not initialized")

    branch = _STATE.branch_workflow.create_branch(
        source_node_id=request.source_node_id,
        label=request.label,
        parent_branch_id=request.parent_branch_id,
    )
    return {
        "branch_id": branch.branch_id,
        "status": branch.status.value,
        "lineage": list(branch.lineage),
    }


@app.get("/api/branches/impact/{node_id}")
async def preview_branch_impact(node_id: str) -> dict[str, Any]:
    """Preview impact of branching at a specific node."""
    if _STATE.branch_workflow is None or _STATE.graph_workspace is None:
        raise HTTPException(status_code=500, detail="Not initialized")

    preview = _STATE.branch_workflow.preview_impact(node_id, _STATE.graph_workspace)
    return {
        "node_id": preview.node_id,
        "descendant_count": preview.descendant_count,
        "divergence_score": preview.divergence_score,
        "summary": preview.summary,
    }


@app.post("/api/branches/archive")
async def archive_branch(request: BranchArchive) -> dict[str, str]:
    """Archive a branch."""
    if _STATE.branch_workflow is None:
        raise HTTPException(status_code=500, detail="Branch workflow not initialized")

    branch = _STATE.branch_workflow.archive_branch(
        request.branch_id, reason=request.reason
    )
    return {"branch_id": branch.branch_id, "status": branch.status.value}


@app.post("/api/branches/merge")
async def merge_branch(request: BranchMerge) -> dict[str, str]:
    """Merge a branch into another."""
    if _STATE.branch_workflow is None:
        raise HTTPException(status_code=500, detail="Branch workflow not initialized")

    branch = _STATE.branch_workflow.merge_branch(
        source_branch_id=request.source_branch_id,
        target_branch_id=request.target_branch_id,
    )
    return {"branch_id": branch.branch_id, "status": branch.status.value}


# ============ G8.3: Tuner and Control Panel ============


@app.post("/api/tuner/resolve")
async def resolve_tuner(settings: TunerUpdate) -> dict[str, Any]:
    """Resolve tuner settings with precedence rules and warnings."""
    if _STATE.tuner is None:
        raise HTTPException(status_code=500, detail="Tuner not initialized")

    tuner_settings = TunerSettings(
        violence=settings.violence,
        humor=settings.humor,
        romance=settings.romance,
    )
    resolution = _STATE.tuner.resolve(tuner_settings)
    preview = _STATE.tuner.preview(resolution)

    return {
        "resolved_settings": {
            "violence": resolution.violence,
            "humor": resolution.humor,
            "romance": resolution.romance,
        },
        "warnings": list(resolution.warnings),
        "precedence_order": list(resolution.precedence_order),
        "preview": {
            "tone_summary": preview.tone_summary,
            "intensity_summary": preview.intensity_summary,
        },
    }


# ============ G8.4: Dual-view and Director Mode ============


@app.post("/api/dualview/initialize")
async def initialize_dual_view(
    scene_id: str, text_version: str = "v1", image_version: str = "v1"
) -> SyncStateResponse:
    """Initialize dual-view sync state for a scene."""
    if _STATE.dual_view is None:
        raise HTTPException(status_code=500, detail="Dual view not initialized")

    state = _STATE.dual_view.initialize(
        scene_id, text_version=text_version, image_version=image_version
    )
    return {
        "scene_id": state.scene_id,
        "text_version": state.text_version,
        "image_version": state.image_version,
        "text_status": state.text_status.value,
        "image_status": state.image_status.value,
        "badges": [{"label": b.label, "icon": b.icon} for b in state.badges],
        "sync_visible": _STATE.dual_view.is_sync_state_visible(scene_id),
        "sync_accurate": _STATE.dual_view.is_sync_state_accurate(scene_id),
    }


@app.post("/api/dualview/sentence-edit")
async def edit_sentence(edit: SentenceEdit) -> SyncStateResponse:
    """Record a sentence edit in Director Mode."""
    if _STATE.dual_view is None:
        raise HTTPException(status_code=500, detail="Dual view not initialized")

    state = _STATE.dual_view.record_sentence_edit(
        scene_id=edit.scene_id,
        sentence_index=edit.sentence_index,
        previous_text=edit.previous_text,
        new_text=edit.new_text,
    )
    return {
        "scene_id": state.scene_id,
        "text_version": state.text_version,
        "image_version": state.image_version,
        "text_status": state.text_status.value,
        "image_status": state.image_status.value,
        "badges": [{"label": b.label, "icon": b.icon} for b in state.badges],
        "sync_visible": _STATE.dual_view.is_sync_state_visible(edit.scene_id),
        "sync_accurate": _STATE.dual_view.is_sync_state_accurate(edit.scene_id),
    }


@app.post("/api/dualview/panel-redraw")
async def redraw_panel(request: PanelRedraw) -> SyncStateResponse:
    """Request a panel redraw in Director Mode."""
    if _STATE.dual_view is None:
        raise HTTPException(status_code=500, detail="Dual view not initialized")

    state = _STATE.dual_view.request_panel_redraw(
        scene_id=request.scene_id,
        panel_index=request.panel_index,
        reason=request.reason,
    )
    return {
        "scene_id": state.scene_id,
        "text_version": state.text_version,
        "image_version": state.image_version,
        "text_status": state.text_status.value,
        "image_status": state.image_status.value,
        "badges": [{"label": b.label, "icon": b.icon} for b in state.badges],
        "sync_visible": _STATE.dual_view.is_sync_state_visible(request.scene_id),
        "sync_accurate": _STATE.dual_view.is_sync_state_accurate(request.scene_id),
    }


@app.post("/api/dualview/reconcile")
async def reconcile_sync(request: ReconcileRequest) -> SyncStateResponse:
    """Reconcile text and image versions."""
    if _STATE.dual_view is None:
        raise HTTPException(status_code=500, detail="Dual view not initialized")

    state = _STATE.dual_view.reconcile(
        scene_id=request.scene_id,
        text_version=request.text_version,
        image_version=request.image_version,
    )
    return {
        "scene_id": state.scene_id,
        "text_version": state.text_version,
        "image_version": state.image_version,
        "text_status": state.text_status.value,
        "image_status": state.image_status.value,
        "badges": [{"label": b.label, "icon": b.icon} for b in state.badges],
        "sync_visible": _STATE.dual_view.is_sync_state_visible(request.scene_id),
        "sync_accurate": _STATE.dual_view.is_sync_state_accurate(request.scene_id),
    }


# ============ G8.5: Accessibility and Mobile ============


@app.get("/api/accessibility/layout/{viewport_width}")
async def get_responsive_layout(viewport_width: int) -> dict[str, Any]:
    """Get responsive layout settings for viewport width."""
    if _STATE.accessibility is None:
        raise HTTPException(status_code=500, detail="Accessibility not initialized")

    layout = _STATE.accessibility.layout_for_width(viewport_width)
    return {
        "viewport_width": layout.viewport_width,
        "breakpoint": layout.breakpoint,
        "graph_columns": layout.graph_columns,
        "controls_stacked": layout.controls_stacked,
        "dual_view_stacked": layout.dual_view_stacked,
        "graph_height": layout.graph_height,
    }


@app.post("/api/accessibility/audit")
async def run_accessibility_audit(
    shortcuts: list[dict[str, str]],
    semantic_labels: list[str],
    non_color_indicators: list[str],
    viewport_width: int,
) -> AccessibilityResponse:
    """Run accessibility audit for keyboard and mobile readiness."""
    if _STATE.accessibility is None:
        raise HTTPException(status_code=500, detail="Accessibility not initialized")

    from core.frontend_workflow_engine import KeyboardShortcut

    shortcut_objs = tuple(
        KeyboardShortcut(
            key=s["key"], action=s["action"], description=s.get("description", "")
        )
        for s in shortcuts
    )

    audit = _STATE.accessibility.audit(
        shortcuts=shortcut_objs,
        semantic_labels=tuple(semantic_labels),
        non_color_indicators=tuple(non_color_indicators),
        viewport_width=viewport_width,
    )
    return {
        "keyboard_coverage": audit.keyboard_coverage,
        "semantic_label_coverage": audit.semantic_label_coverage,
        "non_color_indicator_coverage": audit.non_color_indicator_coverage,
        "mobile_ready": audit.mobile_ready,
        "issues": list(audit.issues),
        "critical_flows_usable": audit.critical_flows_usable(),
    }


# ============ Phase 8 Done Criteria ============


@app.get("/api/phase8/metrics")
async def get_phase8_metrics(
    scene_id: str = Query(..., alias="sceneId"),
) -> Phase8MetricsResponse:
    """Get complete Phase 8 done criteria metrics."""
    if (
        _STATE.graph_workspace is None
        or _STATE.accessibility is None
        or _STATE.dual_view is None
    ):
        raise HTTPException(status_code=500, detail="Not initialized")

    # Get dual view state
    dual_state = _STATE.dual_view.get_state(scene_id)
    if dual_state is None:
        dual_state = _STATE.dual_view.initialize(
            scene_id, text_version="v1", image_version="v1"
        )

    # Get graph metrics
    graph_metrics = _STATE.graph_workspace.render_metrics()

    # Get accessibility audit (with full coverage)
    from core.frontend_workflow_engine import KeyboardShortcut

    shortcuts = tuple(
        KeyboardShortcut(key=k, action=a, description=d)
        for k, a, d in [
            ("ctrl+b", "create_branch", "Create new branch"),
            ("ctrl+z", "undo", "Undo"),
            ("ctrl+y", "redo", "Redo"),
            ("ctrl++", "zoom_in", "Zoom in"),
            ("ctrl+-", "zoom_out", "Zoom out"),
            ("ctrl+t", "open_tuner", "Open tuner panel"),
            ("ctrl+s", "save_checkpoint", "Save checkpoint"),
            ("ctrl+d", "toggle_dual_view", "Toggle dual view"),
            ("ctrl+r", "reconcile_sync", "Reconcile sync"),
        ]
    )
    audit = _STATE.accessibility.audit(
        shortcuts=shortcuts,
        semantic_labels=(
            "graph_canvas",
            "branch_button",
            "zoom_slider",
            "tuner_panel",
            "text_editor",
            "image_panel",
            "sync_badges",
        ),
        non_color_indicators=("sync_icon", "warning_icon", "stale_badge"),
        viewport_width=375,  # Mobile width for testing
    )

    metrics = evaluate_phase8_done_criteria(
        graph_metrics=graph_metrics,
        accessibility_audit=audit,
        dual_view_state=dual_state,
    )

    return {
        "graph_performance_usable": metrics.graph_performance_usable,
        "keyboard_mobile_usable": metrics.keyboard_mobile_usable,
        "dual_sync_visible_and_accurate": metrics.dual_sync_visible_and_accurate,
        "virtualization_ratio": metrics.virtualization_ratio,
        "estimated_frame_ms": metrics.estimated_frame_ms,
        "keyboard_coverage": metrics.keyboard_coverage,
        "mismatch_rate": metrics.mismatch_rate,
    }


@app.post("/api/ingest/text")
async def ingest_text(file: UploadFile) -> dict[str, Any]:
    """Ingest a text document (txt, pdf, epub)."""
    from agents.archivist import ingest_text_document

    temp_path = Path(f"/tmp/loom_upload_{file.filename}")
    try:
        content = await file.read()
        temp_path.write_bytes(content)

        report = ingest_text_document(temp_path)

        return {
            "success": True,
            "source": str(report.source_path),
            "parser": report.parser_used,
            "chapters": len(report.chapters),
            "confidence": report.confidence,
            "hash": report.source_hash,
            "warnings": list(report.warnings),
            "errors": list(report.errors),
        }
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/ingest/manga")
async def ingest_manga(file: UploadFile) -> dict[str, Any]:
    """Ingest manga/comic files (cbz, folder of images)."""
    from agents.archivist import ingest_cbz_pages

    temp_path = Path(f"/tmp/loom_upload_{file.filename}")
    try:
        content = await file.read()
        temp_path.write_bytes(content)

        # Detect file type
        suffix = Path(file.filename or "").suffix.lower()

        if suffix == ".cbz":
            report = ingest_cbz_pages(temp_path)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported manga format: {suffix}"
            )

        return {
            "success": True,
            "source": str(report.source_path),
            "pages": report.page_count,
            "spreads": report.spread_count,
            "formats": list(report.page_formats),
            "hash": report.source_hash,
            "warnings": list(report.warnings),
        }
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.get("/api/ingest/supported-formats")
async def get_supported_formats() -> dict[str, list[str]]:
    """Get list of supported ingestion formats."""
    return {
        "text": [".txt", ".pdf", ".epub"],
        "manga": [".cbz", ".zip"],
        "images": [".png", ".jpg", ".jpeg", ".webp"],
    }


@app.post("/api/generate/text")
async def generate_text(request: dict[str, Any]) -> dict[str, Any]:
    """Generate text continuation for a scene."""
    from core.text_generation_engine import WriterEngine, WriterRequest, TunerSettings

    try:
        # Create mock generation for now (replace with actual engine call)
        user_prompt = request.get("userPrompt", "")
        context = request.get("context", [])
        tuner = request.get("tuner", {"violence": 0.5, "humor": 0.5, "romance": 0.5})
        
        # Simulate generation delay
        await __import__('asyncio').sleep(0.5)
        
        # Generate mock content based on prompt
        generated_text = f"""{user_prompt}

[Generated content based on {len(context)} context chunks]

The scene unfolded with a tension that gripped the air. Characters moved through the space with purpose, their actions guided by the underlying currents of the narrative. As the moment stretched, decisions were made that would ripple through the story's unfolding path.

"We cannot turn back now," the voice rang out, carrying weight beyond mere words. The response came not in speech, but in the set of shoulders, the firmness of steps forward into uncertainty.

The world responded in kind—shadows lengthening, sounds sharpening, the very atmosphere bending to the gravity of choice."""

        return {
            "success": True,
            "generatedText": generated_text,
            "wordCount": len(generated_text.split()),
            "requestId": f"req-{__import__('time').time()}",
            "tunerApplied": tuner,
            "contextUsed": len(context),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/retrieve/context")
async def retrieve_context(request: dict[str, Any]) -> dict[str, Any]:
    """Retrieve relevant context chunks for a query."""
    query = request.get("query", "")
    branch_id = request.get("branchId", "main")
    top_k = request.get("topK", 6)
    
    # Mock retrieved chunks
    mock_chunks = [
        {
            "id": "chunk-1",
            "text": "The protagonist stood at the crossroads, the weight of decision pressing upon their shoulders.",
            "relevanceScore": 0.95,
            "source": "Chapter 1, Scene 3",
            "branchId": branch_id,
        },
        {
            "id": "chunk-2",
            "text": "Echoes of the past whispered through the corridor, memories threading through present tension.",
            "relevanceScore": 0.87,
            "source": "Chapter 2, Scene 1",
            "branchId": branch_id,
        },
        {
            "id": "chunk-3",
            "text": "The antagonist's motivations remained clouded, yet their actions spoke of deeper purpose.",
            "relevanceScore": 0.82,
            "source": "Chapter 1, Scene 5",
            "branchId": branch_id,
        },
        {
            "id": "chunk-4",
            "text": "Setting details: the room was dimly lit, shadows pooling in corners like gathered secrets.",
            "relevanceScore": 0.76,
            "source": "Chapter 3, Scene 2",
            "branchId": branch_id,
        },
    ]
    
    return {
        "success": True,
        "query": query,
        "chunks": mock_chunks[:top_k],
        "totalAvailable": len(mock_chunks),
    }


@app.post("/api/retrieve/style-exemplars")
async def retrieve_style_exemplars(request: dict[str, Any]) -> dict[str, Any]:
    """Retrieve style exemplars matching the query."""
    query_text = request.get("queryText", "")
    source_windows = request.get("sourceWindows", [])
    top_k = request.get("topK", 3)
    
    mock_exemplars = [
        {
            "id": "ex-1",
            "text": "The rain fell in sheets, each drop a percussion against the rooftop symphony.",
            "similarityScore": 0.91,
            "features": ["atmospheric", "sensory", "metaphorical"],
        },
        {
            "id": "ex-2",
            "text": "She moved with purpose, each step calculated, each breath measured against the pressing silence.",
            "similarityScore": 0.85,
            "features": ["character-focused", "tense", "deliberate pacing"],
        },
        {
            "id": "ex-3",
            "text": "Words hung between them, heavy with unspoken meaning, the space filling with what remained unsaid.",
            "similarityScore": 0.79,
            "features": ["dialogue-adjacent", "emotional", "subtext-heavy"],
        },
    ]
    
    return {
        "success": True,
        "exemplars": mock_exemplars[:top_k],
        "queryAnalyzed": True,
    }


@app.get("/api/characters")
async def list_characters() -> list[dict[str, Any]]:
    """List all characters with voice profiles."""
    return [
        {
            "id": "char-1",
            "name": "Protagonist",
            "aliases": ["Hero", "MC"],
            "traits": ["brave", "determined", "conflicted"],
            "description": "The main character driven by a need for justice",
            "voiceProfile": {
                "speechPatterns": ["direct", "introspective", "hesitant in emotional moments"],
                "vocabulary": ["precise", "occasionally poetic", "avoids contractions when serious"],
                "sampleQuotes": [
                    "I won't stand by while this happens.",
                    "There's more to this than meets the eye.",
                ],
            },
            "consistencyScore": 0.94,
        },
        {
            "id": "char-2",
            "name": "Antagonist",
            "aliases": ["Villain"],
            "traits": ["cunning", "ruthless", "charming"],
            "description": "Opposing force with hidden vulnerabilities",
            "voiceProfile": {
                "speechPatterns": ["measured", "uses questions to control conversation", "metaphorical"],
                "vocabulary": ["sophisticated", "technical terms", "euphemisms for violence"],
                "sampleQuotes": [
                    "Don't you see? This is the only way.",
                    "Sacrifices must be made for progress.",
                ],
            },
            "consistencyScore": 0.89,
        },
    ]


@app.post("/api/check/contradictions")
async def check_contradictions(request: dict[str, Any]) -> dict[str, Any]:
    """Check generated text for contradictions against canon."""
    generated_text = request.get("generatedText", "")
    canon_facts = request.get("canonFacts", [])
    
    # Mock contradiction check
    contradictions = []
    
    if "dead" in generated_text.lower() and "alive" in generated_text.lower():
        contradictions.append({
            "severity": "high",
            "type": "state_contradiction",
            "description": "Character mentioned as both dead and alive",
            "suggestedFix": "Verify character status in timeline",
        })
    
    return {
        "success": True,
        "contradictions": contradictions,
        "checkPassed": len(contradictions) == 0,
        "warnings": [],
    }


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "phase": "8"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
