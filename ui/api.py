"""FastAPI backend API for Phase 8 frontend UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
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
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# Pydantic models for API
class GraphNodeCreate(BaseModel):
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


class GraphMetricsResponse(BaseModel):
    total_nodes: int
    visible_nodes: int
    visible_edges: int
    virtualization_ratio: float
    estimated_frame_ms: float
    mode: str
    performance_usable: bool


class SyncStateResponse(BaseModel):
    scene_id: str
    text_version: str
    image_version: str
    text_status: str
    image_status: str
    badges: list[dict[str, str]]
    sync_visible: bool
    sync_accurate: bool


class AccessibilityResponse(BaseModel):
    keyboard_coverage: float
    semantic_label_coverage: float
    non_color_indicator_coverage: float
    mobile_ready: bool
    issues: list[str]
    critical_flows_usable: bool


class Phase8MetricsResponse(BaseModel):
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


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "phase": "8"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
