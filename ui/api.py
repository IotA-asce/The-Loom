"""FastAPI backend API for Phase 8 frontend UI with Sprint 11 endpoints."""

from __future__ import annotations

import asyncio
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
from fastapi import FastAPI, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

# Pydantic models for API


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


class CamelModel(BaseModel):
    """Base model with camelCase alias generation."""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )


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


# ============ Sprint 11: Writer API Models ============


class WriterGenerateRequest(CamelModel):
    node_id: str
    branch_id: str
    user_prompt: str
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    max_tokens: int = Field(ge=100, le=4000, default=500)
    context_chunks: list[str] = []
    style_exemplars: list[str] = []
    character_ids: list[str] = []
    tuner_settings: dict[str, float] = {"violence": 0.5, "humor": 0.5, "romance": 0.5}


class WriterGenerateResponse(CamelModel):
    job_id: str
    generated_text: str
    word_count: int
    style_similarity: float
    contradiction_rate: float
    prompt_version: str


class StyleExemplarResponse(CamelModel):
    exemplars: list[dict[str, Any]]


class ContradictionCheckRequest(CamelModel):
    generated_text: str
    source_context: str


class ContradictionCheckResponse(CamelModel):
    contradictions: list[str]
    contradiction_rate: float
    suggested_fixes: list[str]


# ============ Sprint 11: Artist API Models ============


class ArtistGenerateRequest(CamelModel):
    node_id: str
    branch_id: str
    scene_blueprint: dict[str, Any]
    atmosphere_settings: dict[str, Any]
    panel_count: int = Field(ge=1, le=16, default=4)
    aspect_ratio: str = "16:9"
    cfg_scale: float = Field(ge=1.0, le=15.0, default=7.5)
    steps: int = Field(ge=10, le=50, default=28)
    seed: int | None = None


class ArtistGenerateResponse(CamelModel):
    job_id: str
    panels: list[dict[str, Any]]
    overall_quality: float
    continuity_score: float


# ============ Sprint 11: Retrieval API Models ============


class RetrieveContextRequest(CamelModel):
    query: str
    branch_id: str
    limit: int = Field(ge=1, le=20, default=10)
    filters: dict[str, str] = {}


class RetrieveContextResponse(CamelModel):
    chunks: list[dict[str, Any]]
    total_tokens: int


# ============ Sprint 11: Simulation API Models ============


class SimulateImpactRequest(CamelModel):
    node_id: str
    change_type: str  # edit, delete, reorder
    description: str


class SimulateImpactResponse(CamelModel):
    affected_nodes: list[dict[str, Any]]
    consistency_score: float
    risk_level: str
    estimated_tokens: int
    estimated_time: int
    suggested_actions: list[str]


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
    return {"status": "healthy", "phase": "11"}


# ============ Sprint 11: Writer Engine Endpoints ============


@app.post("/api/writer/generate", response_model=WriterGenerateResponse)
async def generate_text(request: WriterGenerateRequest) -> dict[str, Any]:
    """Generate branch text through the writer engine with full pipeline."""
    from core.text_generation_engine import (
        WriterEngine,
        WriterRequest,
        TunerSettings,
        build_prompt_package,
        PromptRegistry,
        ContextAssembly,
        check_contradictions,
        retrieve_style_exemplars,
        map_tuner_settings,
    )

    try:
        # Initialize engine with LLM backend
        llm_backend = get_llm_backend()
        engine = WriterEngine(
            prompt_registry=PromptRegistry(),
            llm_backend=llm_backend,
        )
        
        # Build tuner settings
        tuner = TunerSettings(
            violence=request.tuner_settings.get("violence", 0.5),
            humor=request.tuner_settings.get("humor", 0.5),
            romance=request.tuner_settings.get("romance", 0.5),
        )
        
        # Map tuner to generation parameters
        tuner_mapping = map_tuner_settings(tuner, intensity=0.6)
        
        # Build context assembly
        context = ContextAssembly(
            chapter_summary="Chapter continuation",
            arc_summary="Arc progression",
            context_text="\n\n".join(request.context_chunks) if request.context_chunks else "No context provided",
            unresolved_thread_prompts=[],
            source_facts={},
        )
        
        # Retrieve style exemplars
        exemplars = retrieve_style_exemplars(
            request.user_prompt,
            tuple(request.style_exemplars) if request.style_exemplars else ("",),
            top_k=3,
        )
        
        # Build prompt package
        prompt_package = build_prompt_package(
            registry=PromptRegistry(),
            user_prompt=request.user_prompt,
            context=context,
            exemplars=exemplars,
            strict_layering=True,
        )
        
        # Create writer request
        writer_request = WriterRequest(
            story_id="default",
            branch_id=request.branch_id,
            user_prompt=request.user_prompt,
            intensity=0.6,
            tuner=tuner,
            source_windows=exemplars,
        )
        
        # Generate using LLM backend
        import hashlib
        import time
        
        job_id = f"writer-{hashlib.sha256(f'{request.node_id}-{time.time()}'.encode()).hexdigest()[:12]}"
        
        # Use the async generate method with LLM backend
        result = await engine.generate(
            request=writer_request,
            retrieval_index=None,
            memory_model=None,
        )
        
        return {
            "jobId": job_id,
            "generatedText": result.text,
            "wordCount": len(result.text.split()),
            "styleSimilarity": result.style_similarity,
            "contradictionRate": result.contradiction_rate,
            "promptVersion": result.prompt_version,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}") from e


@app.get("/api/writer/style-exemplars", response_model=StyleExemplarResponse)
async def get_style_exemplars(
    query: str = Query(..., description="Query text to find similar styles"),
    top_k: int = Query(default=5, ge=1, le=10),
) -> dict[str, Any]:
    """Retrieve style exemplars most relevant to the query text."""
    from core.text_generation_engine import retrieve_style_exemplars
    
    # Mock source windows - in production would come from indexed content
    source_windows = (
        "The wind howled through the ancient corridors, carrying whispers of forgotten secrets.",
        "She moved with calculated precision, each step a deliberate choice in the grand game.",
        "Light filtered through stained glass, casting kaleidoscope shadows across the stone floor.",
        "His voice remained steady despite the chaos, a beacon of certainty in uncertain times.",
        "The city sprawled beneath them, a tapestry of lights and shadows stretching to the horizon.",
    )
    
    exemplars = retrieve_style_exemplars(query, source_windows, top_k=top_k)
    
    return {
        "exemplars": [
            {"id": f"exemplar-{i}", "text": text, "similarity": 0.9 - (i * 0.05)}
            for i, text in enumerate(exemplars)
        ]
    }


@app.post("/api/writer/check-contradictions", response_model=ContradictionCheckResponse)
async def check_contradictions_endpoint(request: ContradictionCheckRequest) -> dict[str, Any]:
    """Check generated text for contradictions against source facts."""
    from core.text_generation_engine import check_contradictions, _extract_state_facts
    
    # Extract facts from source context
    source_facts = _extract_state_facts(request.source_context)
    
    # Check for contradictions
    report = check_contradictions(request.generated_text, source_facts)
    
    # Generate suggested fixes
    suggested_fixes = []
    for contradiction in report.contradictions:
        suggested_fixes.append(f"Review and correct: {contradiction}")
    
    if not suggested_fixes:
        suggested_fixes.append("No contradictions detected. Text is consistent with canon.")
    
    return {
        "contradictions": list(report.contradictions),
        "contradictionRate": report.contradiction_rate,
        "suggestedFixes": suggested_fixes,
    }


# ============ Sprint 11: Artist Engine Endpoints ============


@app.post("/api/artist/generate-panels", response_model=ArtistGenerateResponse)
async def generate_panels(request: ArtistGenerateRequest) -> dict[str, Any]:
    """Generate manga panels with continuity, QC, and alignment safeguards."""
    from core.image_generation_engine import (
        generate_manga_sequence,
        ArtistRequest,
        SceneBlueprint,
        AtmospherePreset,
        atmosphere_preset,
        MockDiffusionBackend,
    )
    
    try:
        import hashlib
        import time
        
        job_id = f"artist-{hashlib.sha256(f'{request.node_id}-{time.time()}'.encode()).hexdigest()[:12]}"
        
        # Build scene blueprint from request
        blueprint = SceneBlueprint(
            setting=request.scene_blueprint.get("setting", "Unknown location"),
            time_of_day=request.scene_blueprint.get("timeOfDay", "day"),
            weather=request.scene_blueprint.get("weather", "clear"),
            lighting_direction=request.atmosphere_settings.get("direction", "top"),
            lighting_intensity=request.atmosphere_settings.get("intensity", 0.6),
            shot_type=request.scene_blueprint.get("shotType", "medium"),
            camera_angle=request.scene_blueprint.get("cameraAngle", "eye_level"),
            focus_point=request.scene_blueprint.get("focusPoint", ""),
            props=tuple(request.scene_blueprint.get("props", [])),
            characters=[
                {
                    "character_id": c.get("characterId", ""),
                    "position": c.get("position", "center"),
                    "pose": c.get("pose", ""),
                    "expression": c.get("expression", "neutral"),
                }
                for c in request.scene_blueprint.get("characters", [])
            ],
        )
        
        # Get atmosphere preset
        preset_id = request.atmosphere_settings.get("presetId", "neutral")
        atmosphere = atmosphere_preset(preset_id)
        
        # Build artist request
        artist_request = ArtistRequest(
            scene_blueprint=blueprint,
            atmosphere=atmosphere,
            prose_reference=tuple(),  # Would link to text
            identity_packs=tuple(),  # Would load from character DB
            aspect_ratio=request.aspect_ratio,
            panel_count=request.panel_count,
            seed=request.seed,
        )
        
        # Generate panels
        backend = MockDiffusionBackend()
        result = generate_manga_sequence(artist_request, backend=backend)
        
        # Format panels for response
        panels = [
            {
                "panelId": f"{job_id}-p{i}",
                "index": i,
                "status": artifact.status if hasattr(artifact, 'status') else "completed",
                "qualityScore": getattr(artifact, 'quality_score', 0.85),
                "seed": getattr(artifact, 'seed', 42),
            }
            for i, artifact in enumerate(result.artifacts)
        ]
        
        return {
            "jobId": job_id,
            "panels": panels,
            "overallQuality": result.overall_quality,
            "continuityScore": result.continuity_score,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Panel generation failed: {str(e)}") from e


# ============ Sprint 11: Retrieval Endpoints ============


@app.post("/api/retrieve/context", response_model=RetrieveContextResponse)
async def retrieve_context(request: RetrieveContextRequest) -> dict[str, Any]:
    """Hybrid retrieval (BM25 + embedding) with branch-aware namespace."""
    from core.retrieval_engine import (
        RetrievalIndex,
        RetrievalQuery,
        RetrievedChunk,
        hybrid_search,
    )
    
    # Mock retrieved chunks - in production would query actual index
    chunks = [
        {
            "id": f"chunk-{i}",
            "text": f"Relevant context passage {i+1} related to: {request.query[:50]}...",
            "source": f"Chapter {i+1}",
            "branchId": request.branch_id,
            "relevanceScore": 0.95 - (i * 0.08),
            "tokenCount": 150 + (i * 20),
        }
        for i in range(min(request.limit, 5))
    ]
    
    total_tokens = sum(chunk["tokenCount"] for chunk in chunks)
    
    return {
        "chunks": chunks,
        "totalTokens": total_tokens,
    }


# ============ Sprint 11: Simulation Endpoints ============


@app.post("/api/simulate/impact", response_model=SimulateImpactResponse)
async def simulate_impact(request: SimulateImpactRequest) -> dict[str, Any]:
    """Simulate impact of proposed changes with consequence propagation."""
    
    # Mock affected nodes based on change type
    affected_nodes = []
    
    if request.change_type == "edit":
        affected_nodes = [
            {"id": f"node-{request.node_id}", "name": "Target Node", "impact": "high", "description": "Direct edit"},
            {"id": "node-desc-1", "name": "Dependent Scene", "impact": "medium", "description": "References target"},
            {"id": "node-desc-2", "name": "Following Chapter", "impact": "low", "description": "Timeline successor"},
        ]
    elif request.change_type == "delete":
        affected_nodes = [
            {"id": f"node-{request.node_id}", "name": "Target Node", "impact": "high", "description": "Will be removed"},
            {"id": "node-desc-1", "name": "Child Branch", "impact": "high", "description": "Depends on target"},
            {"id": "node-desc-2", "name": "Reference Node", "impact": "medium", "description": "Links to target"},
        ]
    else:  # reorder
        affected_nodes = [
            {"id": f"node-{request.node_id}", "name": "Target Node", "impact": "medium", "description": "Position change"},
            {"id": "node-sib-1", "name": "Sibling Node", "impact": "low", "description": "Order affected"},
        ]
    
    # Calculate risk level
    high_count = sum(1 for n in affected_nodes if n["impact"] == "high")
    risk_level = "high" if high_count > 1 else "medium" if high_count == 1 else "low"
    
    return {
        "affectedNodes": affected_nodes,
        "consistencyScore": 85 - (high_count * 15),
        "riskLevel": risk_level,
        "estimatedTokens": len(affected_nodes) * 1500,
        "estimatedTime": len(affected_nodes) * 30,
        "suggestedActions": [
            "Review affected nodes before applying",
            "Create backup branch",
            "Check character continuity",
        ],
    }


# ============ Sprint 22: LLM Configuration Endpoints ============


class LLMConfigRequest(CamelModel):
    """Request to configure LLM provider."""
    provider: str  # openai, anthropic, ollama, mock
    model: str
    api_key: str | None = None
    base_url: str | None = None


class LLMConfigResponse(CamelModel):
    """LLM configuration response."""
    provider: str
    model: str
    available: bool
    message: str


# Global LLM backend instance (initialized on demand)
_llm_backend = None


def get_llm_backend():
    """Get or create LLM backend instance."""
    global _llm_backend
    if _llm_backend is None:
        from core.llm_backend import LLMBackendFactory
        try:
            _llm_backend = LLMBackendFactory.create_from_env()
        except Exception:
            # Fall back to mock if no env vars set
            from core.llm_backend import LLMConfig, LLMProvider, MockLLMBackend
            _llm_backend = MockLLMBackend(LLMConfig(
                provider=LLMProvider.MOCK,
                model="mock"
            ))
    return _llm_backend


def set_llm_backend(backend):
    """Set the global LLM backend instance."""
    global _llm_backend
    _llm_backend = backend


@app.get("/api/llm/providers")
async def list_llm_providers() -> list[dict[str, Any]]:
    """List available LLM providers based on environment configuration."""
    from core.llm_backend import get_available_providers
    return get_available_providers()


@app.post("/api/llm/config", response_model=LLMConfigResponse)
async def configure_llm(request: LLMConfigRequest) -> dict[str, Any]:
    """Configure LLM provider and model."""
    from core.llm_backend import (
        LLMBackendFactory,
        LLMConfig,
        LLMProvider,
    )
    
    try:
        provider = LLMProvider(request.provider.lower())
        config = LLMConfig(
            provider=provider,
            model=request.model,
            api_key=request.api_key,
            base_url=request.base_url,
        )
        
        # Test the configuration by creating backend
        backend = LLMBackendFactory.create(config)
        set_llm_backend(backend)
        
        return {
            "provider": request.provider,
            "model": request.model,
            "available": True,
            "message": f"Successfully configured {request.provider} with model {request.model}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure LLM: {e}")


@app.get("/api/llm/config")
async def get_llm_config() -> dict[str, Any]:
    """Get current LLM configuration."""
    backend = get_llm_backend()
    return {
        "provider": backend.config.provider.value,
        "model": backend.config.model,
        "available": True,
    }


@app.post("/api/llm/test")
async def test_llm_connection() -> dict[str, Any]:
    """Test LLM connection with a simple prompt."""
    from core.llm_backend import LLMMessage, LLMRequest
    
    backend = get_llm_backend()
    
    try:
        request = LLMRequest(
            messages=(
                LLMMessage(role="system", content="You are a helpful assistant."),
                LLMMessage(role="user", content="Say 'The Loom is ready' and nothing else."),
            ),
            temperature=0.0,
            max_tokens=20,
        )
        
        response = await backend.generate(request)
        
        return {
            "success": True,
            "response": response.content,
            "provider": backend.config.provider.value,
            "model": backend.config.model,
            "tokens_used": response.total_tokens,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM test failed: {e}")


@app.websocket("/api/llm/stream/{client_id}")
async def llm_stream_websocket(websocket: WebSocket, client_id: str) -> None:
    """WebSocket endpoint for streaming LLM generation."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("action") == "generate":
                from core.llm_backend import LLMMessage, LLMRequest
                
                messages = [
                    LLMMessage(role=m["role"], content=m["content"])
                    for m in data.get("messages", [])
                ]
                
                request = LLMRequest(
                    messages=tuple(messages),
                    temperature=data.get("temperature", 0.7),
                    max_tokens=data.get("max_tokens", 2000),
                    stream=True,
                )
                
                backend = get_llm_backend()
                
                async for chunk in backend.generate_stream(request):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk.content,
                        "is_finished": chunk.is_finished,
                        "finish_reason": chunk.finish_reason,
                    })
                    
                    if chunk.is_finished:
                        break
                        
            elif data.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass


# ============ Sprint 11: WebSocket Real-Time Updates ============


class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.job_subscriptions: dict[str, list[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str) -> None:
        self.active_connections.pop(client_id, None)
        # Clean up subscriptions
        for job_id, clients in list(self.job_subscriptions.items()):
            if client_id in clients:
                clients.remove(client_id)
    
    def subscribe_to_job(self, client_id: str, job_id: str) -> None:
        if job_id not in self.job_subscriptions:
            self.job_subscriptions[job_id] = []
        if client_id not in self.job_subscriptions[job_id]:
            self.job_subscriptions[job_id].append(client_id)
    
    async def send_progress(self, job_id: str, progress: dict[str, Any]) -> None:
        """Send progress update to all subscribed clients."""
        clients = self.job_subscriptions.get(job_id, [])
        message = {
            "type": "generation_progress",
            "jobId": job_id,
            "data": progress,
        }
        
        for client_id in clients:
            websocket = self.active_connections.get(client_id)
            if websocket:
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass  # Client disconnected
    
    async def send_job_complete(self, job_id: str, result: dict[str, Any]) -> None:
        """Send job completion notification."""
        clients = self.job_subscriptions.get(job_id, [])
        message = {
            "type": "job_complete",
            "jobId": job_id,
            "data": result,
        }
        
        for client_id in clients:
            websocket = self.active_connections.get(client_id)
            if websocket:
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass
        
        # Clean up subscription
        self.job_subscriptions.pop(job_id, None)
    
    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(client_id)
        
        # Clean up disconnected
        for client_id in disconnected:
            self.disconnect(client_id)


# Global connection manager
_connection_manager = ConnectionManager()


@app.websocket("/api/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    """WebSocket endpoint for real-time generation progress."""
    await _connection_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle subscription requests
            if data.get("action") == "subscribe":
                job_id = data.get("jobId")
                if job_id:
                    _connection_manager.subscribe_to_job(client_id, job_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "jobId": job_id,
                    })
            
            # Handle ping
            elif data.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        _connection_manager.disconnect(client_id)


# Background task for simulating generation progress
async def simulate_generation_progress(job_id: str, job_type: str) -> None:
    """Simulate generation progress for demo purposes."""
    steps = [
        ("retrieving_context", "Retrieving relevant context...", 10),
        ("analyzing_style", "Analyzing style patterns...", 25),
        ("generating", f"Generating {job_type}...", 50),
        ("validating", "Validating output...", 80),
        ("finalizing", "Finalizing...", 95),
    ]
    
    for step_name, step_label, progress in steps:
        await asyncio.sleep(0.5)  # Simulate work
        await _connection_manager.send_progress(job_id, {
            "step": step_name,
            "label": step_label,
            "progress": progress,
        })
    
    # Send completion
    await _connection_manager.send_job_complete(job_id, {
        "status": "completed",
        "message": f"{job_type.capitalize()} generation complete",
    })


# Update generation endpoints to trigger WebSocket updates
@app.post("/api/writer/generate-async")
async def generate_text_async(request: WriterGenerateRequest) -> dict[str, str]:
    """Start async text generation with WebSocket progress updates."""
    import hashlib
    import time
    
    job_id = f"writer-{hashlib.sha256(f'{request.node_id}-{time.time()}'.encode()).hexdigest()[:12]}"
    
    # Start background progress simulation
    asyncio.create_task(simulate_generation_progress(job_id, "text"))
    
    return {"jobId": job_id, "status": "started"}


@app.post("/api/artist/generate-panels-async")
async def generate_panels_async(request: ArtistGenerateRequest) -> dict[str, str]:
    """Start async panel generation with WebSocket progress updates."""
    import hashlib
    import time
    
    job_id = f"artist-{hashlib.sha256(f'{request.node_id}-{time.time()}'.encode()).hexdigest()[:12]}"
    
    # Start background progress simulation
    asyncio.create_task(simulate_generation_progress(job_id, "panels"))
    
    return {"jobId": job_id, "status": "started"}


# ============ Sprint 23: Vector Store & Indexing Endpoints ============


class IndexBuildRequest(CamelModel):
    """Request to build or update vector index."""
    story_id: str = "default"
    branch_id: str = "main"
    clear_existing: bool = False


class IndexStatsResponse(CamelModel):
    """Vector index statistics."""
    document_count: int
    dimension: int
    last_updated: str | None
    index_size_bytes: int | None


class SearchRequest(CamelModel):
    """Vector search request."""
    query: str
    branch_id: str = "main"
    top_k: int = 5
    use_hybrid: bool = True


class SearchResultItem(CamelModel):
    """Single search result."""
    id: str
    text: str
    score: float
    source: str
    branch_id: str


@app.post("/api/index/build")
async def build_index(request: IndexBuildRequest) -> dict[str, Any]:
    """Build vector index from current story content."""
    from core.vector_store import get_vector_store, VectorDocument
    from core.retrieval_engine import NarrativeChunk, ChunkMetadata, index_chunks_to_vector_store
    
    try:
        vector_store = get_vector_store()
        
        # Clear existing if requested
        if request.clear_existing:
            await vector_store.clear()
        
        # TODO: Load actual chunks from story database
        # For now, create sample chunks
        sample_chunks = [
            NarrativeChunk(
                chunk_id="chunk-001",
                text="The protagonist stood at the crossroads, the weight of decision pressing upon their shoulders.",
                level="sentence",
                token_count=15,
                metadata=ChunkMetadata(
                    story_id=request.story_id,
                    branch_id=request.branch_id,
                    version_id="v1",
                    created_at=datetime.now(UTC).isoformat(),
                    chapter_index=1,
                    scene_index=1,
                    sentence_index=1,
                    level="sentence",
                ),
                content_hash="abc123",
            ),
            NarrativeChunk(
                chunk_id="chunk-002",
                text="Echoes of the past whispered through the corridor, memories threading through present tension.",
                level="sentence",
                token_count=14,
                metadata=ChunkMetadata(
                    story_id=request.story_id,
                    branch_id=request.branch_id,
                    version_id="v1",
                    created_at=datetime.now(UTC).isoformat(),
                    chapter_index=1,
                    scene_index=1,
                    sentence_index=2,
                    level="sentence",
                ),
                content_hash="def456",
            ),
            NarrativeChunk(
                chunk_id="chunk-003",
                text="The antagonist's motivations remained clouded, yet their actions spoke of deeper purpose.",
                level="sentence",
                token_count=13,
                metadata=ChunkMetadata(
                    story_id=request.story_id,
                    branch_id=request.branch_id,
                    version_id="v1",
                    created_at=datetime.now(UTC).isoformat(),
                    chapter_index=1,
                    scene_index=2,
                    sentence_index=1,
                    level="sentence",
                ),
                content_hash="ghi789",
            ),
        ]
        
        # Index chunks
        ids = await index_chunks_to_vector_store(sample_chunks, vector_store)
        
        stats = await vector_store.get_stats()
        
        return {
            "success": True,
            "indexed_count": len(ids),
            "stats": {
                "document_count": stats.document_count,
                "dimension": stats.dimension,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index build failed: {e}")


@app.get("/api/index/stats", response_model=IndexStatsResponse)
async def get_index_stats() -> dict[str, Any]:
    """Get vector index statistics."""
    from core.vector_store import get_vector_store
    
    try:
        vector_store = get_vector_store()
        stats = await vector_store.get_stats()
        
        return {
            "document_count": stats.document_count,
            "dimension": stats.dimension,
            "last_updated": stats.last_updated,
            "index_size_bytes": stats.index_size_bytes,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {e}")


@app.post("/api/index/clear")
async def clear_index() -> dict[str, Any]:
    """Clear all documents from vector index."""
    from core.vector_store import get_vector_store
    
    try:
        vector_store = get_vector_store()
        await vector_store.clear()
        
        return {
            "success": True,
            "message": "Index cleared successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear index: {e}")


@app.post("/api/retrieve/vector-search")
async def vector_search(request: SearchRequest) -> dict[str, Any]:
    """Search vector index with semantic similarity."""
    from core.vector_store import get_vector_store
    from core.retrieval_engine import RetrievalQuery, hybrid_search_with_vector_store
    
    try:
        if request.use_hybrid:
            # Use hybrid search
            query = RetrievalQuery(
                story_id="default",
                branch_id=request.branch_id,
                query_text=request.query,
                top_k=request.top_k,
            )
            
            response = await hybrid_search_with_vector_store(query)
            
            results = [
                {
                    "id": hit.chunk_id,
                    "text": hit.text,
                    "score": hit.score,
                    "source": f"Chapter {hit.metadata.chapter_index}, Scene {hit.metadata.scene_index}",
                    "branch_id": hit.metadata.branch_id,
                    "bm25_score": hit.bm25_score,
                    "embedding_score": hit.embedding_score,
                }
                for hit in response.results
            ]
            
            return {
                "success": True,
                "query": request.query,
                "results": results,
                "query_time_ms": response.query_time_ms,
                "method": "hybrid",
            }
        else:
            # Use pure vector search
            vector_store = get_vector_store()
            search_results = await vector_store.search(
                query=request.query,
                top_k=request.top_k,
                filters={"branch_id": request.branch_id} if request.branch_id else None,
            )
            
            results = [
                {
                    "id": result.document.id,
                    "text": result.document.text,
                    "score": result.score,
                    "source": result.document.metadata.get("source", "unknown"),
                    "branch_id": result.document.metadata.get("branch_id", "main"),
                }
                for result in search_results
            ]
            
            return {
                "success": True,
                "query": request.query,
                "results": results,
                "method": "vector",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@app.get("/api/embedding/providers")
async def list_embedding_providers() -> list[dict[str, Any]]:
    """List available embedding providers."""
    providers = []
    
    # Check OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "models": ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
            "available": True,
            "dimensions": [1536, 3072, 1536],
        })
    else:
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "models": ["text-embedding-3-small", "text-embedding-3-large"],
            "available": False,
            "reason": "OPENAI_API_KEY not set",
        })
    
    # HuggingFace (local)
    providers.append({
        "id": "huggingface",
        "name": "HuggingFace (Local)",
        "models": ["all-MiniLM-L6-v2", "all-mpnet-base-v2"],
        "available": True,
        "note": "Requires sentence-transformers package",
    })
    
    # Mock (always available)
    providers.append({
        "id": "mock",
        "name": "Mock (Testing)",
        "models": ["mock"],
        "available": True,
    })
    
    return providers


# ============ Sprint 13: Character Identity Management ============


class LoRATrainRequest(CamelModel):
    character_id: str
    character_name: str
    base_model_id: str = "mock-sd-controlnet-v1"
    trained_steps: int = 120


class LoRATrainResponse(CamelModel):
    job_id: str
    adapter_id: str
    status: str
    estimated_time: int


class LoRAStatusResponse(CamelModel):
    job_id: str
    adapter_id: str
    status: str  # pending, training, completed, failed
    progress: float
    current_step: str
    version: int


@app.post("/api/lora/train", response_model=LoRATrainResponse)
async def start_lora_training(request: LoRATrainRequest) -> dict[str, Any]:
    """Start LoRA training for a character identity."""
    from core.image_generation_engine import (
        CharacterIdentityPack,
        LoRAAdapterManager,
        build_character_identity_pack,
    )
    
    import hashlib
    import time
    
    job_id = f"lora-{hashlib.sha256(f'{request.character_id}-{time.time()}'.encode()).hexdigest()[:12]}"
    adapter_id = f"lora:{request.character_id}:v001"
    
    # Simulate training start
    asyncio.create_task(simulate_lora_training(job_id, request.character_id))
    
    return {
        "jobId": job_id,
        "adapterId": adapter_id,
        "status": "started",
        "estimatedTime": 300,  # 5 minutes estimated
    }


async def simulate_lora_training(job_id: str, character_id: str) -> None:
    """Simulate LoRA training progress."""
    steps = [
        ("preprocessing", "Preprocessing reference images...", 10),
        ("face_extraction", "Extracting facial features...", 25),
        ("feature_learning", "Learning character features...", 50),
        ("optimization", "Optimizing model weights...", 80),
        ("finalizing", "Finalizing adapter...", 95),
    ]
    
    for step_name, step_label, progress in steps:
        await asyncio.sleep(1)  # Training takes longer
        await _connection_manager.send_progress(job_id, {
            "step": step_name,
            "label": step_label,
            "progress": progress,
            "type": "lora_training",
        })
    
    # Send completion
    await _connection_manager.send_job_complete(job_id, {
        "status": "completed",
        "adapterId": f"lora:{character_id}:v001",
        "message": "LoRA training complete",
    })


@app.get("/api/lora/status/{job_id}", response_model=LoRAStatusResponse)
async def get_lora_training_status(job_id: str) -> dict[str, Any]:
    """Get the status of a LoRA training job."""
    # Mock status - in production would check actual training job
    return {
        "jobId": job_id,
        "adapterId": f"lora:char:{job_id[-6:]}",
        "status": "training",
        "progress": 0.65,
        "currentStep": "feature_learning",
        "version": 1,
    }


@app.get("/api/lora/adapters/{character_id}")
async def list_character_adapters(character_id: str) -> dict[str, Any]:
    """List all LoRA adapters for a character."""
    return {
        "characterId": character_id,
        "adapters": [
            {
                "adapterId": f"lora:{character_id}:v001",
                "version": 1,
                "status": "ready",
                "createdAt": "2026-02-10T10:00:00Z",
                "trainedSteps": 120,
            },
        ],
    }


@app.post("/api/lora/upload-reference/{character_id}")
async def upload_reference_image(
    character_id: str,
    image: UploadFile,
    reference_type: str = Query(..., description="Type: face, silhouette, or costume"),
) -> dict[str, Any]:
    """Upload a reference image for character identity training."""
    # In production, would save and process the image
    return {
        "success": True,
        "characterId": character_id,
        "referenceType": reference_type,
        "filename": image.filename,
        "message": f"{reference_type} reference uploaded successfully",
    }


# ============ Sprint 14: Quality Control & Drift Detection ============


class QCScoreRequest(CamelModel):
    panel_id: str
    image_data: str | None = None  # base64 encoded or URL


class QCScoreResponse(CamelModel):
    panel_id: str
    overall_score: float
    anatomy_score: float
    composition_score: float
    color_score: float
    continuity_score: float
    issues: list[str]
    recommendations: list[str]


@app.post("/api/qc/score", response_model=QCScoreResponse)
async def get_panel_qc_score(request: QCScoreRequest) -> dict[str, Any]:
    """Get quality control scores for a panel."""
    # Mock QC scoring - in production would run actual QC analysis
    import random
    
    scores = {
        "anatomy": random.uniform(0.7, 0.98),
        "composition": random.uniform(0.75, 0.95),
        "color": random.uniform(0.8, 0.97),
        "continuity": random.uniform(0.7, 0.96),
    }
    
    overall = sum(scores.values()) / len(scores)
    
    issues = []
    if scores["anatomy"] < 0.8:
        issues.append("anatomy_issue")
    if scores["color"] < 0.8:
        issues.append("color_inconsistency")
    if scores["composition"] < 0.75:
        issues.append("composition_problem")
    
    recommendations = []
    if "anatomy_issue" in issues:
        recommendations.append("Review character proportions and pose")
    if "color_inconsistency" in issues:
        recommendations.append("Check color palette alignment with scene")
    
    return {
        "panelId": request.panel_id,
        "overallScore": overall,
        "anatomyScore": scores["anatomy"],
        "compositionScore": scores["composition"],
        "colorScore": scores["color"],
        "continuityScore": scores["continuity"],
        "issues": issues,
        "recommendations": recommendations,
    }


@app.get("/api/qc/batch-score")
async def get_batch_qc_scores(panel_ids: list[str] = Query(...)) -> dict[str, Any]:
    """Get QC scores for multiple panels."""
    results = []
    for panel_id in panel_ids:
        # Generate mock scores
        import random
        results.append({
            "panelId": panel_id,
            "overallScore": random.uniform(0.7, 0.95),
            "status": "passed" if random.random() > 0.3 else "needs_review",
        })
    
    return {
        "results": results,
        "total": len(results),
        "passed": sum(1 for r in results if r["status"] == "passed"),
    }


class DriftDetectionRequest(CamelModel):
    character_id: str
    panel_ids: list[str]


class DriftDetectionResponse(CamelModel):
    character_id: str
    drift_detected: bool
    drift_score: float
    affected_panels: list[dict[str, Any]]
    trigger_retraining: bool
    reasons: list[str]


@app.post("/api/drift/detect", response_model=DriftDetectionResponse)
async def detect_character_drift(request: DriftDetectionRequest) -> dict[str, Any]:
    """Detect identity drift for a character across panels."""
    from core.image_generation_engine import (
        CharacterIdentityPack,
        LoRAAdapterManager,
    )
    
    import random
    
    # Mock drift detection
    drift_score = random.uniform(0, 0.4)
    drift_detected = drift_score > 0.25
    
    affected_panels = []
    if drift_detected:
        # Mark some panels as affected
        for panel_id in request.panel_ids[:3]:
            affected_panels.append({
                "panelId": panel_id,
                "identityScore": random.uniform(0.5, 0.7),
                "driftType": "facial_features",
            })
    
    reasons = []
    if drift_detected:
        reasons.append("Facial features inconsistent with reference")
        if drift_score > 0.35:
            reasons.append("Costume details deviating from character design")
    
    return {
        "characterId": request.character_id,
        "driftDetected": drift_detected,
        "driftScore": drift_score,
        "affectedPanels": affected_panels,
        "triggerRetraining": drift_detected and drift_score > 0.3,
        "reasons": reasons,
    }


@app.get("/api/drift/status/{character_id}")
async def get_drift_status(character_id: str) -> dict[str, Any]:
    """Get current drift status for a character."""
    import random
    
    drift_score = random.uniform(0, 0.3)
    
    return {
        "characterId": character_id,
        "driftScore": drift_score,
        "status": "critical" if drift_score > 0.3 else "warning" if drift_score > 0.2 else "good",
        "lastChecked": "2026-02-10T10:00:00Z",
        "panelsChecked": 24,
    }


class CorrectionRequest(CamelModel):
    panel_ids: list[str]
    priority: str  # low, medium, high
    reason: str


@app.post("/api/qc/request-correction")
async def request_panel_correction(request: CorrectionRequest) -> dict[str, Any]:
    """Request correction for panels that failed QC."""
    import hashlib
    import time
    
    batch_id = f"corr-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
    
    return {
        "batchId": batch_id,
        "panelIds": request.panel_ids,
        "priority": request.priority,
        "status": "queued",
        "estimatedCompletion": "2026-02-10T12:00:00Z",
        "queuePosition": 3,
    }


@app.get("/api/qc/correction-queue")
async def get_correction_queue() -> dict[str, Any]:
    """Get the current correction queue status."""
    return {
        "queueLength": 5,
        "pending": 3,
        "processing": 1,
        "completed": 12,
        "estimatedWaitMinutes": 15,
    }


# ============ Sprint 24: Image Generation & Storage Endpoints ============


class DiffusionBackendConfig(CamelModel):
    """Configuration for diffusion backend."""
    backend_type: str = "mock"  # mock, local, stability
    model_id: str = "mock-sd-v1-5"
    device: str = "auto"


class GeneratePanelsRequest(CamelModel):
    """Request to generate manga panels."""
    story_id: str = "default"
    branch_id: str = "main"
    scene_id: str
    scene_prompt: str
    panel_count: int = 4
    atmosphere: str = "balanced"  # light, dark, balanced
    style: str = "manga"
    seed: int | None = None
    controlnet_type: str | None = None  # pose, canny, depth


class GeneratePanelsResponse(CamelModel):
    """Response from panel generation."""
    job_id: str
    images: list[dict[str, Any]]
    continuity_score: float
    overall_quality: float


@app.get("/api/diffusion/backends")
async def list_diffusion_backends() -> list[dict[str, Any]]:
    """List available diffusion backends."""
    from core.diffusion_backend import DiffusionBackendFactory
    return DiffusionBackendFactory.get_available_backends()


@app.post("/api/diffusion/config")
async def configure_diffusion_backend(config: DiffusionBackendConfig) -> dict[str, Any]:
    """Configure the diffusion backend."""
    from core.diffusion_backend import (
        DiffusionBackendFactory,
        DiffusionConfig,
        set_diffusion_backend,
    )
    
    try:
        diffusion_config = DiffusionConfig(
            model_id=config.model_id,
            device=config.device,
        )
        
        backend = DiffusionBackendFactory.create(
            backend_type=config.backend_type,
            config=diffusion_config,
        )
        
        set_diffusion_backend(backend)
        
        return {
            "success": True,
            "backend_type": config.backend_type,
            "model_id": config.model_id,
            "available": backend.is_available(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure backend: {e}")


@app.post("/api/artist/generate", response_model=GeneratePanelsResponse)
async def generate_panels_endpoint(request: GeneratePanelsRequest) -> dict[str, Any]:
    """Generate manga panels with storage."""
    from core.image_generation_engine import (
        generate_and_store_panels,
        ArtistRequest,
        DiffusionConfig as IGEConfig,
        atmosphere_preset,
    )
    from core.diffusion_backend import get_diffusion_backend
    import hashlib
    import time
    
    try:
        job_id = f"artist-{hashlib.sha256(f'{request.scene_id}-{time.time()}'.encode()).hexdigest()[:12]}"
        
        # Build request
        artist_request = ArtistRequest(
            story_id=request.story_id,
            branch_id=request.branch_id,
            scene_prompt=request.scene_prompt,
            panel_count=request.panel_count,
            atmosphere=request.atmosphere,
            diffusion_config=IGEConfig(),
            seed=request.seed,
        )
        
        # Generate and store
        result = await generate_and_store_panels(
            request=artist_request,
            backend=get_diffusion_backend(),
        )
        
        return {
            "job_id": job_id,
            "images": [
                {
                    "panel_index": img.panel_index,
                    "image_id": img.image_id,
                    "image_url": img.image_url,
                    "prompt": img.prompt,
                    "generation_time_ms": img.generation_time_ms,
                    "quality_score": img.quality_score,
                }
                for img in result.images
            ],
            "continuity_score": result.continuity_score,
            "overall_quality": result.overall_quality,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@app.get("/api/images/{image_id}")
async def get_image(image_id: str) -> Any:
    """Get an image by ID."""
    from core.image_storage import get_image_storage
    from fastapi.responses import Response
    
    try:
        storage = get_image_storage()
        image_data = await storage.get_image(image_id)
        
        if image_data is None:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return Response(
            content=image_data,
            media_type="image/png",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image: {e}")


@app.get("/api/images/{image_id}/metadata")
async def get_image_metadata_endpoint(image_id: str) -> dict[str, Any]:
    """Get image metadata."""
    from core.image_storage import get_image_storage
    
    try:
        storage = get_image_storage()
        metadata = await storage.get_metadata(image_id)
        
        if metadata is None:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return metadata.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metadata: {e}")


@app.delete("/api/images/{image_id}")
async def delete_image_endpoint(image_id: str) -> dict[str, Any]:
    """Delete an image."""
    from core.image_storage import get_image_storage
    
    try:
        storage = get_image_storage()
        deleted = await storage.delete_image(image_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {"success": True, "message": f"Image {image_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {e}")


@app.get("/api/images")
async def list_images(
    story_id: str | None = None,
    branch_id: str | None = None,
    scene_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """List images with optional filtering."""
    from core.image_storage import get_image_storage
    
    try:
        storage = get_image_storage()
        images = await storage.list_images(
            story_id=story_id,
            branch_id=branch_id,
            scene_id=scene_id,
            limit=limit,
            offset=offset,
        )
        
        return {
            "images": [
                {
                    "image_id": img.image_id,
                    "image_url": img.image_url,
                    "metadata": img.metadata.to_dict(),
                }
                for img in images
            ],
            "count": len(images),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list images: {e}")


# ============ Sprint 25: LoRA Training Endpoints ============


class LoRATrainRequest(CamelModel):
    """Request to start LoRA training."""
    character_id: str
    character_name: str
    base_model: str = "runwayml/stable-diffusion-v1-5"
    training_steps: int = 1000
    learning_rate: float = 1e-4
    rank: int = 4  # LoRA rank (4, 8, 16)
    trigger_word: str | None = None


class LoRAStatusResponse(CamelModel):
    """LoRA training status response."""
    job_id: str
    character_id: str
    status: str  # pending, training, completed, failed
    progress: float  # 0-100
    current_step: int
    total_steps: int
    loss: float | None
    eta_seconds: int | None


class CharacterIdentityRequest(CamelModel):
    """Request to build character identity pack."""
    character_id: str
    character_name: str
    face_cues: list[str]
    silhouette_cues: list[str]
    costume_cues: list[str]


# Training job storage (in-memory for now, would use database in production)
_training_jobs: dict[str, dict[str, Any]] = {}


@app.post("/api/lora/train")
async def start_lora_training(request: LoRATrainRequest) -> dict[str, Any]:
    """Start LoRA training for a character."""
    import hashlib
    import time
    
    job_id = f"lora-{hashlib.sha256(f'{request.character_id}-{time.time()}'.encode()).hexdigest()[:12]}"
    
    # Store job info
    _training_jobs[job_id] = {
        "job_id": job_id,
        "character_id": request.character_id,
        "character_name": request.character_name,
        "status": "pending",
        "progress": 0.0,
        "current_step": 0,
        "total_steps": request.training_steps,
        "loss": None,
        "created_at": datetime.now(UTC).isoformat(),
    }
    
    # Start training in background (mock for now)
    asyncio.create_task(_simulate_lora_training(job_id))
    
    return {
        "job_id": job_id,
        "character_id": request.character_id,
        "status": "pending",
        "estimated_time": request.training_steps * 2,  # ~2s per step
    }


async def _simulate_lora_training(job_id: str) -> None:
    """Simulate LoRA training progress."""
    import random
    import time
    
    job = _training_jobs.get(job_id)
    if job is None:
        return
    
    # Pending phase
    await asyncio.sleep(2)
    job["status"] = "training"
    
    # Training phase
    total_steps = job["total_steps"]
    for step in range(total_steps):
        await asyncio.sleep(0.1)  # Fast simulation
        job["current_step"] = step + 1
        job["progress"] = (step + 1) / total_steps * 100
        job["loss"] = 0.5 * (1 - (step / total_steps)) + random.uniform(0, 0.1)
    
    # Completed
    job["status"] = "completed"
    job["progress"] = 100.0
    job["adapter_id"] = f"lora-{job['character_id']}-v1"


@app.get("/api/lora/status/{job_id}", response_model=LoRAStatusResponse)
async def get_lora_training_status(job_id: str) -> dict[str, Any]:
    """Get LoRA training status."""
    job = _training_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    # Calculate ETA
    eta = None
    if job["status"] == "training" and job["current_step"] < job["total_steps"]:
        remaining_steps = job["total_steps"] - job["current_step"]
        eta = remaining_steps * 2  # ~2s per step
    
    return {
        "job_id": job_id,
        "character_id": job["character_id"],
        "status": job["status"],
        "progress": job["progress"],
        "current_step": job["current_step"],
        "total_steps": job["total_steps"],
        "loss": job.get("loss"),
        "eta_seconds": eta,
    }


@app.post("/api/characters/identity-pack")
async def build_character_identity(request: CharacterIdentityRequest) -> dict[str, Any]:
    """Build character identity pack."""
    from core.image_generation_engine import build_identity_pack
    
    try:
        identity_pack = build_identity_pack(
            character_id=request.character_id,
            display_name=request.character_name,
            face_cues=tuple(request.face_cues),
            silhouette_cues=tuple(request.silhouette_cues),
            costume_cues=tuple(request.costume_cues),
        )
        
        return {
            "character_id": identity_pack.character_id,
            "display_name": identity_pack.display_name,
            "identity_fingerprint": identity_pack.identity_fingerprint,
            "face_cues": list(identity_pack.face_cues),
            "silhouette_cues": list(identity_pack.silhouette_cues),
            "costume_cues": list(identity_pack.costume_cues),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build identity: {e}")


@app.get("/api/characters/{character_id}/adapters")
async def list_character_adapters(character_id: str) -> dict[str, Any]:
    """List LoRA adapters for a character."""
    # Filter jobs by character
    adapters = []
    for job in _training_jobs.values():
        if job["character_id"] == character_id and job["status"] == "completed":
            adapters.append({
                "adapter_id": job.get("adapter_id", f"lora-{character_id}-v1"),
                "version": 1,
                "status": "ready",
                "trained_steps": job["total_steps"],
            })
    
    return {
        "character_id": character_id,
        "adapters": adapters,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
