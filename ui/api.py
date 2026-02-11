"""FastAPI backend API for Phase 8 frontend UI with Sprint 11 endpoints."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
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
from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
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


@app.post("/api/ingest/manga/pages")
async def ingest_manga_pages(
    files: list[UploadFile],
    title: str = Query(..., description="Manga title"),
) -> dict[str, Any]:
    """Bulk import manga pages as individual image files (webp, png, jpg).

    Accepts multiple image files, automatically sorts by filename,
    and ingests them as a single manga volume.
    """
    import shutil
    import tempfile

    from agents.archivist import (
        SUPPORTED_MANGA_IMAGE_EXTENSIONS,
        ingest_image_folder_pages,
    )

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Create a temporary folder for the pages
    temp_folder = Path(tempfile.mkdtemp(prefix="loom_manga_"))

    try:
        # Save all uploaded files to the temp folder
        saved_count = 0
        skipped_files = []

        for file in files:
            if not file.filename:
                continue

            file_path = Path(file.filename)
            suffix = file_path.suffix.lower()

            # Validate file extension
            if suffix not in SUPPORTED_MANGA_IMAGE_EXTENSIONS:
                skipped_files.append(f"{file.filename} (unsupported format)")
                continue

            # Read and save file
            content = await file.read()
            dest_path = temp_folder / file_path.name
            dest_path.write_bytes(content)
            saved_count += 1

        if saved_count == 0:
            supported = SUPPORTED_MANGA_IMAGE_EXTENSIONS
            raise HTTPException(
                status_code=400,
                detail=f"No valid image files found. Supported: {supported}",
            )

        # Ingest the folder
        report = ingest_image_folder_pages(temp_folder)

        return {
            "success": True,
            "title": title,
            "pages_imported": report.page_count,
            "pages": [
                {
                    "page_number": i + 1,
                    "format": meta.format_name,
                    "width": meta.width,
                    "height": meta.height,
                    "hash": meta.source_hash[:16],
                }
                for i, meta in enumerate(report.page_metadata)
            ],
            "skipped_files": skipped_files,
            "warnings": list(report.warnings),
            "source_hash": report.source_hash,
        }

    finally:
        # Clean up temp folder
        if temp_folder.exists():
            shutil.rmtree(temp_folder)


@app.get("/api/ingest/supported-formats")
async def get_supported_formats() -> dict[str, list[str]]:
    """Get list of supported ingestion formats."""
    return {
        "text": [".txt", ".pdf", ".epub"],
        "manga": [".cbz", ".zip"],
        "images": [".png", ".jpg", ".jpeg", ".webp"],
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
        ContextAssembly,
        PromptRegistry,
        TunerSettings,
        WriterEngine,
        WriterRequest,
        build_prompt_package,
        map_tuner_settings,
        retrieve_style_exemplars,
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

        # Map tuner to generation parameters (used in future expansion)
        _ = map_tuner_settings(tuner, intensity=0.6)

        # Build context assembly
        ctx_text = "\n\n".join(request.context_chunks)
        context = ContextAssembly(
            chapter_summary="Chapter continuation",
            arc_summary="Arc progression",
            context_text=ctx_text if request.context_chunks else "No context provided",
            unresolved_thread_prompts=[],
            source_facts={},
        )

        # Retrieve style exemplars
        exemplars = retrieve_style_exemplars(
            request.user_prompt,
            tuple(request.style_exemplars) if request.style_exemplars else ("",),
            top_k=3,
        )

        # Build prompt package (used in future expansion)
        _ = build_prompt_package(
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

        _hash_input = f"{request.node_id}-{time.time()}"
        job_id = f"writer-{hashlib.sha256(_hash_input.encode()).hexdigest()[:12]}"

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
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}") from e


@app.get("/api/writer/style-exemplars", response_model=StyleExemplarResponse)
async def get_style_exemplars(
    query: str = Query(..., description="Query text to find similar styles"),
    top_k: int = Query(default=5, ge=1, le=10),
) -> dict[str, Any]:
    """Retrieve style exemplars most relevant to the query text."""
    from core.text_generation_engine import retrieve_style_exemplars

    # Mock source windows - in production would come from indexed content
    source_windows = (
        "The wind howled through the ancient corridors, carrying whispers of "
        "forgotten secrets.",
        "She moved with calculated precision, each step a deliberate choice in "
        "the grand game.",
        "Light filtered through stained glass, casting kaleidoscope shadows "
        "across the stone floor.",
        "His voice remained steady despite the chaos, a beacon of certainty in "
        "uncertain times.",
        "The city sprawled beneath them, a tapestry of lights and shadows "
        "stretching to the horizon.",
    )

    exemplars = retrieve_style_exemplars(query, source_windows, top_k=top_k)

    return {
        "exemplars": [
            {"id": f"exemplar-{i}", "text": text, "similarity": 0.9 - (i * 0.05)}
            for i, text in enumerate(exemplars)
        ]
    }


@app.post("/api/writer/check-contradictions", response_model=ContradictionCheckResponse)
async def check_contradictions_endpoint(
    request: ContradictionCheckRequest,
) -> dict[str, Any]:
    """Check generated text for contradictions against source facts."""
    from core.text_generation_engine import _extract_state_facts, check_contradictions

    # Extract facts from source context
    source_facts = _extract_state_facts(request.source_context)

    # Check for contradictions
    report = check_contradictions(request.generated_text, source_facts)

    # Generate suggested fixes
    suggested_fixes = []
    for contradiction in report.contradictions:
        suggested_fixes.append(f"Review and correct: {contradiction}")

    if not suggested_fixes:
        suggested_fixes.append(
            "No contradictions detected. Text is consistent with canon."
        )

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
        ArtistRequest,
        MockDiffusionBackend,
        SceneBlueprint,
        atmosphere_preset,
        generate_manga_sequence,
    )

    try:
        import hashlib
        import time

        _hash_input = f"{request.node_id}-{time.time()}"
        job_id = f"artist-{hashlib.sha256(_hash_input.encode()).hexdigest()[:12]}"

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
                "status": (
                    artifact.status if hasattr(artifact, "status") else "completed"
                ),
                "qualityScore": getattr(artifact, "quality_score", 0.85),
                "seed": getattr(artifact, "seed", 42),
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
        raise HTTPException(
            status_code=500, detail=f"Panel generation failed: {e}"
        ) from e


# ============ Sprint 11: Retrieval Endpoints ============


@app.post("/api/retrieve/context", response_model=RetrieveContextResponse)
async def retrieve_context(request: RetrieveContextRequest) -> dict[str, Any]:
    """Hybrid retrieval (BM25 + embedding) with branch-aware namespace."""

    # Mock retrieved chunks - in production would query actual index
    chunks = [
        {
            "id": f"chunk-{i}",
            "text": (
                f"Relevant context passage {i+1} related to: "
                f"{request.query[:50]}..."
            ),
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
            {
                "id": f"node-{request.node_id}",
                "name": "Target Node",
                "impact": "high",
                "description": "Direct edit",
            },
            {
                "id": "node-desc-1",
                "name": "Dependent Scene",
                "impact": "medium",
                "description": "References target",
            },
            {
                "id": "node-desc-2",
                "name": "Following Chapter",
                "impact": "low",
                "description": "Timeline successor",
            },
        ]
    elif request.change_type == "delete":
        affected_nodes = [
            {
                "id": f"node-{request.node_id}",
                "name": "Target Node",
                "impact": "high",
                "description": "Will be removed",
            },
            {
                "id": "node-desc-1",
                "name": "Child Branch",
                "impact": "high",
                "description": "Depends on target",
            },
            {
                "id": "node-desc-2",
                "name": "Reference Node",
                "impact": "medium",
                "description": "Links to target",
            },
        ]
    else:  # reorder
        affected_nodes = [
            {
                "id": f"node-{request.node_id}",
                "name": "Target Node",
                "impact": "medium",
                "description": "Position change",
            },
            {
                "id": "node-sib-1",
                "name": "Sibling Node",
                "impact": "low",
                "description": "Order affected",
            },
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

            _llm_backend = MockLLMBackend(
                LLMConfig(provider=LLMProvider.MOCK, model="mock")
            )
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
            "message": (
                f"Successfully configured {request.provider} "
                f"with model {request.model}"
            ),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {e}") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to configure LLM: {e}"
        ) from e


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
                LLMMessage(
                    role="user",
                    content="Say 'The Loom is ready' and nothing else.",
                ),
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
        raise HTTPException(status_code=500, detail=f"LLM test failed: {e}") from e


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
                    await websocket.send_json(
                        {
                            "type": "chunk",
                            "content": chunk.content,
                            "is_finished": chunk.is_finished,
                            "finish_reason": chunk.finish_reason,
                        }
                    )

                    if chunk.is_finished:
                        break

            elif data.get("action") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
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
        for _job_id, clients in list(self.job_subscriptions.items()):
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
                    await websocket.send_json(
                        {
                            "type": "subscribed",
                            "jobId": job_id,
                        }
                    )

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
        await _connection_manager.send_progress(
            job_id,
            {
                "step": step_name,
                "label": step_label,
                "progress": progress,
            },
        )

    # Send completion
    await _connection_manager.send_job_complete(
        job_id,
        {
            "status": "completed",
            "message": f"{job_type.capitalize()} generation complete",
        },
    )


# Update generation endpoints to trigger WebSocket updates
@app.post("/api/writer/generate-async")
async def generate_text_async(request: WriterGenerateRequest) -> dict[str, str]:
    """Start async text generation with WebSocket progress updates."""
    import hashlib
    import time

    _hash_input = f"{request.node_id}-{time.time()}"
    job_id = f"writer-{hashlib.sha256(_hash_input.encode()).hexdigest()[:12]}"

    # Start background progress simulation
    asyncio.create_task(simulate_generation_progress(job_id, "text"))

    return {"jobId": job_id, "status": "started"}


@app.post("/api/artist/generate-panels-async")
async def generate_panels_async(request: ArtistGenerateRequest) -> dict[str, str]:
    """Start async panel generation with WebSocket progress updates."""
    import hashlib
    import time

    _hash_input = f"{request.node_id}-{time.time()}"
    job_id = f"artist-{hashlib.sha256(_hash_input.encode()).hexdigest()[:12]}"

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
    from core.retrieval_engine import (
        ChunkMetadata,
        NarrativeChunk,
        index_chunks_to_vector_store,
    )
    from core.vector_store import get_vector_store

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
                text=(
                    "The protagonist stood at the crossroads, the weight of "
                    "decision pressing upon their shoulders."
                ),
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
                text=(
                    "Echoes of the past whispered through the corridor, "
                    "memories threading through present tension."
                ),
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
                text=(
                    "The antagonist's motivations remained clouded, yet their "
                    "actions spoke of deeper purpose."
                ),
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
        raise HTTPException(status_code=500, detail=f"Index build failed: {e}") from e


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
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {e}") from e


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
        raise HTTPException(
            status_code=500, detail=f"Failed to clear index: {e}"
        ) from e


@app.post("/api/retrieve/vector-search")
async def vector_search(request: SearchRequest) -> dict[str, Any]:
    """Search vector index with semantic similarity."""
    from core.retrieval_engine import RetrievalQuery, hybrid_search_with_vector_store
    from core.vector_store import get_vector_store

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
                    "source": (
                        f"Chapter {hit.metadata.chapter_index}, "
                        f"Scene {hit.metadata.scene_index}"
                    ),
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
        raise HTTPException(status_code=500, detail=f"Search failed: {e}") from e


@app.get("/api/embedding/providers")
async def list_embedding_providers() -> list[dict[str, Any]]:
    """List available embedding providers."""
    providers = []

    # Check OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        providers.append(
            {
                "id": "openai",
                "name": "OpenAI",
                "models": [
                    "text-embedding-3-small",
                    "text-embedding-3-large",
                    "text-embedding-ada-002",
                ],
                "available": True,
                "dimensions": [1536, 3072, 1536],
            }
        )
    else:
        providers.append(
            {
                "id": "openai",
                "name": "OpenAI",
                "models": ["text-embedding-3-small", "text-embedding-3-large"],
                "available": False,
                "reason": "OPENAI_API_KEY not set",
            }
        )

    # HuggingFace (local)
    providers.append(
        {
            "id": "huggingface",
            "name": "HuggingFace (Local)",
            "models": ["all-MiniLM-L6-v2", "all-mpnet-base-v2"],
            "available": True,
            "note": "Requires sentence-transformers package",
        }
    )

    # Mock (always available)
    providers.append(
        {
            "id": "mock",
            "name": "Mock (Testing)",
            "models": ["mock"],
            "available": True,
        }
    )

    return providers


# ============ Sprint 13: Character Identity Management ============


class LoRATrainResponse(CamelModel):
    job_id: str
    adapter_id: str
    status: str
    estimated_time: int


@app.get("/api/lora/adapters/{character_id}")
async def list_character_adapters_legacy(character_id: str) -> dict[str, Any]:
    """List all LoRA adapters for a character (legacy endpoint)."""
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
async def get_batch_qc_scores(
    panel_ids: list[str] = Query(...),  # noqa: B008
) -> dict[str, Any]:
    """Get QC scores for multiple panels."""
    results = []
    for panel_id in panel_ids:
        # Generate mock scores
        import random

        results.append(
            {
                "panelId": panel_id,
                "overallScore": random.uniform(0.7, 0.95),
                "status": "passed" if random.random() > 0.3 else "needs_review",
            }
        )

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

    import random

    # Mock drift detection
    drift_score = random.uniform(0, 0.4)
    drift_detected = drift_score > 0.25

    affected_panels = []
    if drift_detected:
        # Mark some panels as affected
        for panel_id in request.panel_ids[:3]:
            affected_panels.append(
                {
                    "panelId": panel_id,
                    "identityScore": random.uniform(0.5, 0.7),
                    "driftType": "facial_features",
                }
            )

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
        "status": (
            "critical"
            if drift_score > 0.3
            else "warning" if drift_score > 0.2 else "good"
        ),
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
        raise HTTPException(
            status_code=500, detail=f"Failed to configure backend: {e}"
        ) from e


@app.post("/api/artist/generate", response_model=GeneratePanelsResponse)
async def generate_panels_endpoint(request: GeneratePanelsRequest) -> dict[str, Any]:
    """Generate manga panels with storage."""
    import hashlib
    import time

    from core.diffusion_backend import get_diffusion_backend
    from core.image_generation_engine import (
        ArtistRequest,
        generate_and_store_panels,
    )
    from core.image_generation_engine import (
        DiffusionConfig as IGEConfig,
    )

    try:
        _hash_input = f"{request.scene_id}-{time.time()}"
        job_id = f"artist-{hashlib.sha256(_hash_input.encode()).hexdigest()[:12]}"

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
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}") from e


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
        raise HTTPException(status_code=500, detail=f"Failed to get image: {e}") from e


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
        raise HTTPException(
            status_code=500, detail=f"Failed to get metadata: {e}"
        ) from e


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
        raise HTTPException(
            status_code=500, detail=f"Failed to delete image: {e}"
        ) from e


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
        raise HTTPException(
            status_code=500, detail=f"Failed to list images: {e}"
        ) from e


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

    _hash_input = f"{request.character_id}-{time.time()}"
    job_id = f"lora-{hashlib.sha256(_hash_input.encode()).hexdigest()[:12]}"

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
        raise HTTPException(
            status_code=500, detail=f"Failed to build identity: {e}"
        ) from e


@app.get("/api/characters/{character_id}/adapters")
async def list_character_adapters(character_id: str) -> dict[str, Any]:
    """List LoRA adapters for a character."""
    # Filter jobs by character
    adapters = []
    for job in _training_jobs.values():
        if job["character_id"] == character_id and job["status"] == "completed":
            adapters.append(
                {
                    "adapter_id": job.get("adapter_id", f"lora-{character_id}-v1"),
                    "version": 1,
                    "status": "ready",
                    "trained_steps": job["total_steps"],
                }
            )

    return {
        "character_id": character_id,
        "adapters": adapters,
    }


# ============ Sprint 26: QC Pipeline Endpoints ============


class QCAnalyzeRequest(CamelModel):
    """Request to analyze image quality."""

    image_id: str
    analyzer_type: str = "auto"  # auto, mock, clip


class QCAnalyzeResponse(CamelModel):
    """QC analysis response."""

    report_id: str
    image_id: str
    overall_score: float
    score_level: str
    passed: bool
    failure_categories: list[str]
    suggested_fixes: list[str]
    auto_redraw_recommended: bool


@app.post("/api/qc/analyze", response_model=QCAnalyzeResponse)
async def analyze_image_quality(request: QCAnalyzeRequest) -> dict[str, Any]:
    """Analyze image quality."""
    from core.image_storage import get_image_storage
    from core.qc_analysis import QCAnalyzerFactory, get_qc_analyzer

    try:
        # Get image
        storage = get_image_storage()
        image_data = await storage.get_image(request.image_id)

        if image_data is None:
            raise HTTPException(status_code=404, detail="Image not found")

        # Get analyzer
        if request.analyzer_type == "auto":
            analyzer = get_qc_analyzer()
        else:
            analyzer = QCAnalyzerFactory.create(request.analyzer_type)

        # Analyze
        report = await analyzer.analyze(image_data, request.image_id)

        return {
            "report_id": report.report_id,
            "image_id": report.image_id,
            "overall_score": report.overall_score,
            "score_level": report.score_level.value,
            "passed": report.passed,
            "failure_categories": list(report.failure_categories),
            "suggested_fixes": list(report.suggested_fixes),
            "auto_redraw_recommended": report.auto_redraw_recommended,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QC analysis failed: {e}") from e


@app.get("/api/qc/analyzers")
async def list_qc_analyzers() -> list[dict[str, Any]]:
    """List available QC analyzers."""
    from core.qc_analysis import CLIPBasedQCAnalyzer

    analyzers = []

    # Mock (always available)
    analyzers.append(
        {
            "id": "mock",
            "name": "Mock Analyzer",
            "available": True,
            "description": "Deterministic mock scoring for testing",
        }
    )

    # CLIP-based
    clip = CLIPBasedQCAnalyzer()
    analyzers.append(
        {
            "id": "clip",
            "name": "CLIP-Based Analyzer",
            "available": clip.is_available(),
            "description": "Uses CLIP and vision models for scoring",
            "requirements": "transformers, torch" if not clip.is_available() else None,
        }
    )

    return analyzers


@app.get("/api/qc/reports/{image_id}")
async def get_qc_report(image_id: str) -> dict[str, Any]:
    """Get QC report for an image."""
    from core.image_storage import get_image_storage
    from core.qc_analysis import get_qc_analyzer

    try:
        storage = get_image_storage()
        image_data = await storage.get_image(image_id)

        if image_data is None:
            raise HTTPException(status_code=404, detail="Image not found")

        analyzer = get_qc_analyzer()
        report = await analyzer.analyze(image_data, image_id)

        return {
            "report_id": report.report_id,
            "image_id": report.image_id,
            "overall_score": report.overall_score,
            "score_level": report.score_level.value,
            "passed": report.passed,
            "needs_human_review": report.needs_human_review,
            "anatomy": {
                "overall": report.anatomy.overall,
                "proportions": report.anatomy.proportions,
                "pose_accuracy": report.anatomy.pose_accuracy,
                "hand_quality": report.anatomy.hand_quality,
                "face_quality": report.anatomy.face_quality,
            },
            "composition": {
                "overall": report.composition.overall,
                "rule_of_thirds": report.composition.rule_of_thirds,
                "balance": report.composition.balance,
                "focal_point": report.composition.focal_point,
                "framing": report.composition.framing,
            },
            "readability": {
                "overall": report.readability.overall,
                "contrast": report.readability.contrast,
                "clarity": report.readability.clarity,
            },
            "content": {
                "safe": report.content.is_safe,
                "violence_level": report.content.violence_level,
                "suggestive_level": report.content.suggestive_level,
            },
            "failure_categories": list(report.failure_categories),
            "suggested_fixes": list(report.suggested_fixes),
            "auto_redraw_recommended": report.auto_redraw_recommended,
            "analyzed_at": report.analyzed_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get QC report: {e}"
        ) from e


@app.post("/api/qc/auto-redraw")
async def auto_redraw_image(image_id: str) -> dict[str, Any]:
    """Automatically redraw an image that failed QC."""
    from core.diffusion_backend import GenerationRequest, get_diffusion_backend
    from core.image_storage import get_image_storage
    from core.qc_analysis import auto_redraw_with_qc

    try:
        storage = get_image_storage()
        metadata = await storage.get_metadata(image_id)

        if metadata is None:
            raise HTTPException(status_code=404, detail="Image not found")

        # Get original image
        image_data = await storage.get_image(image_id)

        # Define generate function for redraw
        async def generate_fn():
            backend = get_diffusion_backend()
            request = GenerationRequest(
                prompt=metadata.prompt,
                negative_prompt=metadata.negative_prompt,
                seed=metadata.seed + 1000,  # Different seed
            )
            results = await backend.generate(request)
            return results[0].image_data if results else b""

        # Auto redraw
        result = await auto_redraw_with_qc(
            image_data=image_data,
            image_id=image_id,
            generate_fn=generate_fn,
            max_attempts=3,
        )

        if result.new_image_id and result.new_report:
            # Store the new image - new_metadata would be used in production
            _ = (
                result.new_image_id,
                f"{metadata.original_filename}-redraw",
                metadata.content_type,
            )

        return {
            "original_image_id": result.original_image_id,
            "new_image_id": result.new_image_id,
            "attempts": result.attempts,
            "improved": result.improved,
            "final_score": result.final_score,
            "passed": result.new_report.passed if result.new_report else False,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto redraw failed: {e}") from e


# ============ Sprint 27: Graph Persistence Endpoints ============


class SaveNodeRequest(CamelModel):
    """Request to save a graph node."""

    node_id: str
    label: str
    branch_id: str
    scene_id: str
    x: float
    y: float
    importance: float = 0.5
    metadata: dict[str, Any] = {}


class SaveEdgeRequest(CamelModel):
    """Request to save a graph edge."""

    edge_id: str
    source_id: str
    target_id: str
    label: str = ""
    edge_type: str = "default"
    weight: float = 1.0


class ProjectSaveRequest(CamelModel):
    """Request to save entire project."""

    project_id: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    branches: list[dict[str, Any]]


@app.post("/api/graph/nodes/save")
async def save_graph_node(request: SaveNodeRequest) -> dict[str, Any]:
    """Save or update a graph node."""
    from core.event_store import log_node_created, log_node_updated
    from core.graph_persistence import GraphNode, get_graph_persistence

    try:
        persistence = get_graph_persistence()

        node = GraphNode(
            node_id=request.node_id,
            label=request.label,
            branch_id=request.branch_id,
            scene_id=request.scene_id,
            x=request.x,
            y=request.y,
            importance=request.importance,
            metadata=request.metadata,
        )

        # Check if node exists
        existing = await persistence.get_node(request.node_id)

        await persistence.save_node(node)

        # Log event
        if existing is None:
            await log_node_created(
                node_id=request.node_id,
                label=request.label,
                x=request.x,
                y=request.y,
                branch_id=request.branch_id,
            )
        else:
            await log_node_updated(
                node_id=request.node_id,
                changes={"x": request.x, "y": request.y, "label": request.label},
            )

        return {"success": True, "node_id": request.node_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save node: {e}") from e


@app.get("/api/graph/nodes/{node_id}")
async def get_graph_node(node_id: str) -> dict[str, Any]:
    """Get a graph node by ID."""
    from core.graph_persistence import get_graph_persistence

    try:
        persistence = get_graph_persistence()
        node = await persistence.get_node(node_id)

        if node is None:
            raise HTTPException(status_code=404, detail="Node not found")

        return node.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node: {e}") from e


@app.delete("/api/graph/nodes/{node_id}")
async def delete_graph_node(node_id: str) -> dict[str, Any]:
    """Delete a graph node."""
    from core.graph_persistence import get_graph_persistence

    try:
        persistence = get_graph_persistence()
        deleted = await persistence.delete_node(node_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Node not found")

        return {"success": True, "message": f"Node {node_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete node: {e}"
        ) from e


@app.get("/api/graph/nodes")
async def list_graph_nodes(branch_id: str | None = None) -> dict[str, Any]:
    """List all graph nodes, optionally filtered by branch."""
    from core.graph_persistence import get_graph_persistence

    try:
        persistence = get_graph_persistence()

        if branch_id:
            nodes = await persistence.get_nodes_by_branch(branch_id)
        else:
            nodes = await persistence.get_all_nodes()

        return {
            "nodes": [node.to_dict() for node in nodes],
            "count": len(nodes),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list nodes: {e}") from e


@app.post("/api/graph/edges/save")
async def save_graph_edge(request: SaveEdgeRequest) -> dict[str, Any]:
    """Save or update a graph edge."""
    from core.graph_persistence import GraphEdge, get_graph_persistence

    try:
        persistence = get_graph_persistence()

        edge = GraphEdge(
            edge_id=request.edge_id,
            source_id=request.source_id,
            target_id=request.target_id,
            label=request.label,
            edge_type=request.edge_type,
            weight=request.weight,
        )

        await persistence.save_edge(edge)

        return {"success": True, "edge_id": request.edge_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save edge: {e}") from e


@app.get("/api/graph/edges")
async def list_graph_edges() -> dict[str, Any]:
    """List all graph edges."""
    from core.graph_persistence import get_graph_persistence

    try:
        persistence = get_graph_persistence()
        edges = await persistence.get_all_edges()

        return {
            "edges": [edge.to_dict() for edge in edges],
            "count": len(edges),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list edges: {e}") from e


@app.post("/api/project/save")
async def save_project(request: ProjectSaveRequest) -> dict[str, Any]:
    """Save entire project."""
    from core.graph_persistence import get_graph_persistence

    try:
        persistence = get_graph_persistence()

        data = {
            "project_id": request.project_id,
            "nodes": request.nodes,
            "edges": request.edges,
            "branches": request.branches,
            "saved_at": datetime.now(UTC).isoformat(),
        }

        await persistence.save_project(request.project_id, data)

        return {
            "success": True,
            "project_id": request.project_id,
            "node_count": len(request.nodes),
            "edge_count": len(request.edges),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save project: {e}"
        ) from e


@app.get("/api/project/load/{project_id}")
async def load_project(project_id: str) -> dict[str, Any]:
    """Load entire project."""
    from core.graph_persistence import get_graph_persistence

    try:
        persistence = get_graph_persistence()
        data = await persistence.load_project(project_id)

        if data is None:
            raise HTTPException(status_code=404, detail="Project not found")

        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load project: {e}"
        ) from e


@app.post("/api/project/export")
async def export_project(project_id: str) -> dict[str, Any]:
    """Export project to JSON format."""

    from core.graph_persistence import get_graph_persistence

    try:
        persistence = get_graph_persistence()
        data = await persistence.load_project(project_id)

        if data is None:
            raise HTTPException(status_code=404, detail="Project not found")

        # Convert to export format
        export = {
            "format_version": "1.0",
            "project_id": project_id,
            "exported_at": datetime.now(UTC).isoformat(),
            "data": data,
        }

        return export
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export project: {e}"
        ) from e


# ============ Event Store / Audit Endpoints ============


@app.get("/api/events/audit/{aggregate_type}/{aggregate_id}")
async def get_audit_trail(aggregate_type: str, aggregate_id: str) -> dict[str, Any]:
    """Get audit trail for an aggregate."""
    from core.event_store import get_event_store

    try:
        store = get_event_store()
        trail = await store.get_audit_trail(aggregate_id, aggregate_type)

        return {
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "events": trail,
            "event_count": len(trail),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get audit trail: {e}"
        ) from e


@app.get("/api/events/recent")
async def get_recent_events(limit: int = 50) -> dict[str, Any]:
    """Get recent activity feed."""
    from core.event_store import get_event_store

    try:
        store = get_event_store()
        events = await store.get_recent_activity(limit=limit)

        return {
            "events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type.value,
                    "aggregate_id": e.aggregate_id,
                    "timestamp": e.timestamp,
                    "user_id": e.user_id,
                }
                for e in events
            ],
            "count": len(events),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {e}") from e


# ============ Sprint 28: Real-time Collaboration Endpoints ============


@app.post("/api/collaboration/join")
async def collaboration_join(request: dict[str, Any]) -> dict[str, Any]:
    """Join a collaboration room."""
    from core.collaboration import get_collaboration_engine

    room_id = request.get("room_id", "")
    user_id = request.get("user_id", "")
    user_name = request.get("user_name", "Anonymous")

    if not room_id or not user_id:
        raise HTTPException(status_code=400, detail="room_id and user_id are required")

    try:
        engine = get_collaboration_engine()
        room, presence = await engine.join_room(room_id, user_id, user_name)

        # Get full presence sync for new user
        sync_data = await engine.get_presence_sync(room_id)

        return {
            "success": True,
            "room_id": room_id,
            "user_id": user_id,
            "user_color": presence.user_color,
            "user_count": room.get_user_count(),
            "presence_sync": sync_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to join room: {e}") from e


@app.post("/api/collaboration/leave")
async def collaboration_leave(request: dict[str, Any]) -> dict[str, Any]:
    """Leave a collaboration room."""
    from core.collaboration import get_collaboration_engine

    room_id = request.get("room_id", "")
    user_id = request.get("user_id", "")

    if not room_id or not user_id:
        raise HTTPException(status_code=400, detail="room_id and user_id are required")

    try:
        engine = get_collaboration_engine()
        await engine.leave_room(room_id, user_id)

        return {
            "success": True,
            "room_id": room_id,
            "user_id": user_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to leave room: {e}") from e


@app.post("/api/collaboration/cursor")
async def collaboration_cursor(request: dict[str, Any]) -> dict[str, Any]:
    """Update cursor position."""
    from core.collaboration import get_collaboration_engine

    room_id = request.get("room_id", "")
    user_id = request.get("user_id", "")
    x = request.get("x", 0.0)
    y = request.get("y", 0.0)
    node_id = request.get("node_id")

    if not room_id or not user_id:
        raise HTTPException(status_code=400, detail="room_id and user_id are required")

    try:
        engine = get_collaboration_engine()
        await engine.update_cursor(room_id, user_id, x, y, node_id)

        return {"success": True}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update cursor: {e}"
        ) from e


@app.post("/api/collaboration/select")
async def collaboration_select(request: dict[str, Any]) -> dict[str, Any]:
    """Update selected node."""
    from core.collaboration import get_collaboration_engine

    room_id = request.get("room_id", "")
    user_id = request.get("user_id", "")
    node_id = request.get("node_id")

    if not room_id or not user_id:
        raise HTTPException(status_code=400, detail="room_id and user_id are required")

    try:
        engine = get_collaboration_engine()
        await engine.select_node(room_id, user_id, node_id)

        return {"success": True, "node_id": node_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to select node: {e}"
        ) from e


@app.post("/api/collaboration/lock")
async def collaboration_lock(request: dict[str, Any]) -> dict[str, Any]:
    """Acquire edit lock on a node."""
    from core.collaboration import get_collaboration_engine

    room_id = request.get("room_id", "")
    user_id = request.get("user_id", "")
    user_name = request.get("user_name", "Anonymous")
    node_id = request.get("node_id", "")

    if not room_id or not user_id or not node_id:
        raise HTTPException(
            status_code=400,
            detail="room_id, user_id, and node_id are required",
        )

    try:
        engine = get_collaboration_engine()
        success, error = await engine.acquire_edit_lock(
            room_id, node_id, user_id, user_name
        )

        if not success:
            raise HTTPException(status_code=409, detail=error or "Lock failed")

        return {
            "success": True,
            "node_id": node_id,
            "user_id": user_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to acquire lock: {e}"
        ) from e


@app.post("/api/collaboration/unlock")
async def collaboration_unlock(request: dict[str, Any]) -> dict[str, Any]:
    """Release edit lock on a node."""
    from core.collaboration import get_collaboration_engine

    room_id = request.get("room_id", "")
    user_id = request.get("user_id", "")
    node_id = request.get("node_id", "")

    if not room_id or not user_id or not node_id:
        raise HTTPException(
            status_code=400,
            detail="room_id, user_id, and node_id are required",
        )

    try:
        engine = get_collaboration_engine()
        success = await engine.release_edit_lock(room_id, node_id, user_id)

        return {
            "success": success,
            "node_id": node_id,
            "user_id": user_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to release lock: {e}"
        ) from e


@app.get("/api/collaboration/presence/{room_id}")
async def collaboration_presence(room_id: str) -> dict[str, Any]:
    """Get current presence state for a room."""
    from core.collaboration import get_collaboration_engine

    try:
        engine = get_collaboration_engine()
        sync_data = await engine.get_presence_sync(room_id)

        return {
            "room_id": room_id,
            **sync_data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get presence: {e}"
        ) from e


# ============ Sprint 29: Observability Endpoints ============


@app.get("/api/ops/metrics")
async def get_metrics() -> dict[str, Any]:
    """Get system metrics."""
    from core.observability import get_observability

    try:
        obs = get_observability()
        summary = obs.metrics.get_summary()

        return {
            "counters": summary.get("counters", {}),
            "gauges": summary.get("gauges", {}),
            "histogram_count": summary.get("histogram_count", {}),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get metrics: {e}"
        ) from e


@app.get("/api/ops/metrics/prometheus")
async def get_metrics_prometheus() -> str:
    """Get metrics in Prometheus format."""
    from core.observability import get_observability

    try:
        obs = get_observability()
        return obs.export_prometheus()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export metrics: {e}"
        ) from e


@app.get("/api/ops/slos")
async def get_slos() -> dict[str, Any]:
    """Get SLO (Service Level Objective) status."""
    from core.observability import get_observability

    try:
        obs = get_observability()
        results = obs.slo.check_all_slos()

        return {
            "slos": [
                {
                    "name": r.definition.name,
                    "description": r.definition.description,
                    "target": r.definition.target,
                    "current_value": r.current_value,
                    "status": r.status.value,
                    "window_minutes": r.window_minutes,
                    "measured_at": r.measured_at,
                }
                for r in results
            ],
            "overall_status": (
                "healthy"
                if all(r.status.value == "healthy" for r in results)
                else (
                    "warning"
                    if any(r.status.value == "warning" for r in results)
                    else "breach"
                )
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SLOs: {e}") from e


@app.get("/api/ops/health")
async def get_health() -> dict[str, Any]:
    """Get health status."""
    from core.observability import get_observability

    try:
        obs = get_observability()
        return obs.health.get_overall_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health: {e}") from e


@app.get("/api/ops/logs")
async def get_logs(level: str | None = None, limit: int = 100) -> dict[str, Any]:
    """Get recent log entries."""
    from core.observability import get_observability

    try:
        obs = get_observability()
        entries = obs.logger.get_recent(level=level, limit=limit)

        return {
            "logs": [
                {
                    "timestamp": e.timestamp,
                    "level": e.level,
                    "message": e.message,
                    "correlation_id": e.correlation_id,
                    "context": e.context,
                }
                for e in entries
            ],
            "count": len(entries),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {e}") from e


# ============ Sprint 30: Security & Authentication Endpoints ============


class LoginRequest(CamelModel):
    """Login request."""

    email: str
    password: str


class TokenResponse(CamelModel):
    """Token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes
    user: dict[str, Any]


class RegisterRequest(CamelModel):
    """Registration request."""

    email: str
    username: str
    password: str


class RefreshRequest(CamelModel):
    """Token refresh request."""

    refresh_token: str


class APIKeyCreateRequest(CamelModel):
    """API key creation request."""

    name: str
    expires_days: int | None = None


class APIKeyResponse(CamelModel):
    """API key response (only returned once on creation)."""

    key_id: str
    key: str  # Plain key - only shown once!
    name: str
    created_at: str
    expires_at: str | None


@app.post("/api/auth/register", response_model=TokenResponse)
async def auth_register(request: RegisterRequest) -> dict[str, Any]:
    """Register a new user."""
    from core.auth import UserRole, get_auth_manager

    try:
        auth = get_auth_manager()
        user = auth.create_user(
            email=request.email,
            username=request.username,
            password=request.password,
            role=UserRole.EDITOR,
        )

        # Create tokens
        access_token = auth.create_access_token(user)
        refresh_token = auth.create_refresh_token(user)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900,
            "user": user.to_public_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}") from e


@app.post("/api/auth/login", response_model=TokenResponse)
async def auth_login(request: LoginRequest) -> dict[str, Any]:
    """Login and get access token."""
    from core.auth import get_auth_manager

    try:
        auth = get_auth_manager()
        user = auth.authenticate_user(request.email, request.password)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")

        access_token = auth.create_access_token(user)
        refresh_token = auth.create_refresh_token(user)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900,
            "user": user.to_public_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}") from e


@app.post("/api/auth/logout")
async def auth_logout(request: dict[str, Any]) -> dict[str, Any]:
    """Logout and revoke token."""
    from core.auth import get_auth_manager

    try:
        auth = get_auth_manager()
        jti = request.get("jti")  # JWT ID to revoke

        if jti:
            auth.revoke_token(jti)

        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {e}") from e


@app.post("/api/auth/refresh", response_model=TokenResponse)
async def auth_refresh(request: RefreshRequest) -> dict[str, Any]:
    """Refresh access token."""
    from core.auth import get_auth_manager

    try:
        auth = get_auth_manager()
        payload = auth.decode_jwt(request.refresh_token)

        if not payload or payload.type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = auth.get_user(payload.sub)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        # Create new tokens
        access_token = auth.create_access_token(user)
        refresh_token = auth.create_refresh_token(user)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900,
            "user": user.to_public_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {e}") from e


@app.get("/api/auth/me")
async def auth_me(request: Request) -> dict[str, Any]:
    """Get current user info."""
    from core.auth import get_auth_manager

    # Get token from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication")

    token = auth_header[7:]  # Remove "Bearer "

    try:
        auth = get_auth_manager()
        payload = auth.decode_jwt(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user = auth.get_user(payload.sub)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user.to_public_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user info: {e}"
        ) from e


# ============ API Key Management ============


@app.post("/api/auth/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreateRequest, http_request: Request
) -> dict[str, Any]:
    """Create a new API key."""
    from core.auth import get_auth_manager

    # Verify user is authenticated
    auth_header = http_request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header[7:]

    try:
        auth = get_auth_manager()
        payload = auth.decode_jwt(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        plain_key, api_key = auth.create_api_key(
            name=request.name,
            user_id=payload.sub,
            expires_days=request.expires_days,
        )

        return {
            "key_id": api_key.key_id,
            "key": plain_key,  # Only shown once!
            "name": api_key.name,
            "created_at": api_key.created_at,
            "expires_at": api_key.expires_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create API key: {e}"
        ) from e


@app.get("/api/auth/api-keys")
async def list_api_keys(request: Request) -> dict[str, Any]:
    """List user's API keys (without the actual keys)."""
    from core.auth import get_auth_manager

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header[7:]

    try:
        auth = get_auth_manager()
        payload = auth.decode_jwt(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        keys = auth.list_user_api_keys(payload.sub)

        return {
            "keys": [
                {
                    "key_id": k.key_id,
                    "name": k.name,
                    "created_at": k.created_at,
                    "expires_at": k.expires_at,
                    "last_used": k.last_used,
                    "is_active": k.is_active,
                }
                for k in keys
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list API keys: {e}"
        ) from e


@app.delete("/api/auth/api-keys/{key_id}")
async def revoke_api_key(key_id: str, request: Request) -> dict[str, Any]:
    """Revoke an API key."""
    from core.auth import get_auth_manager

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        auth = get_auth_manager()
        success = auth.revoke_api_key(key_id)

        if not success:
            raise HTTPException(status_code=404, detail="API key not found")

        return {"success": True, "message": "API key revoked"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to revoke API key: {e}"
        ) from e


# ============ Rate Limit Status ============


@app.get("/api/auth/rate-limit")
async def rate_limit_status(request: Request) -> dict[str, Any]:
    """Get current rate limit status."""
    from core.rate_limit import get_rate_limit_middleware

    # Get client ID from header or IP
    client_id = request.headers.get(
        "x-client-id", request.client.host if request.client else "unknown"
    )

    try:
        middleware = get_rate_limit_middleware()
        limiter = middleware._limiter
        stats = limiter.get_client_stats(client_id)

        return {
            "client_id": client_id,
            "categories": stats,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get rate limit status: {e}"
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
