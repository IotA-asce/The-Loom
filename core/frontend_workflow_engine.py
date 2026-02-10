"""Frontend workflow engine for Phase 8 UX goals."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _clamp(value: float, *, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ZoomMode(Enum):
    """Semantic zoom modes for graph visualization."""

    OVERVIEW = "overview"
    SCENE = "scene"
    DETAIL = "detail"


class BranchStatus(Enum):
    """Branch lifecycle statuses for frontend workflows."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    MERGED = "merged"


class PaneSyncStatus(Enum):
    """Dual-view pane synchronization statuses."""

    SYNCED = "synced"
    TEXT_STALE = "text_stale"
    IMAGE_STALE = "image_stale"
    BOTH_STALE = "both_stale"
    RECONCILING = "reconciling"


@dataclass(frozen=True)
class GraphNodeView:
    """Node view model for virtualized graph rendering."""

    node_id: str
    label: str
    branch_id: str
    scene_id: str
    x: float
    y: float
    width: float = 220.0
    height: float = 90.0
    importance: float = 0.5


@dataclass(frozen=True)
class GraphEdgeView:
    """Directed edge view model for graph rendering."""

    source_id: str
    target_id: str
    relation_type: str = "branch"


@dataclass(frozen=True)
class GraphViewport:
    """Viewport state used for virtualization and semantic zoom."""

    x: float
    y: float
    width: float
    height: float
    zoom: float = 1.0


@dataclass(frozen=True)
class GraphSnapshot:
    """Undo/redo snapshot for graph workspace state."""

    nodes: tuple[GraphNodeView, ...]
    edges: tuple[GraphEdgeView, ...]
    viewport: GraphViewport
    zoom_mode: ZoomMode
    selected_node_id: str | None


@dataclass(frozen=True)
class AutosaveCheckpoint:
    """Autosave checkpoint metadata for editor recovery."""

    checkpoint_id: str
    reason: str
    created_at: str
    snapshot_hash: str


@dataclass(frozen=True)
class GraphRenderMetrics:
    """Virtualized render metrics used for performance checks."""

    total_nodes: int
    visible_nodes: int
    visible_edges: int
    virtualization_ratio: float
    estimated_frame_ms: float
    mode: ZoomMode


class GraphWorkspace:
    """Interactive graph workspace with virtualization, zoom, and history."""

    def __init__(self, viewport: GraphViewport) -> None:
        self._nodes: dict[str, GraphNodeView] = {}
        self._edges: list[GraphEdgeView] = []
        self._viewport = viewport
        self._zoom_mode = self._resolve_zoom_mode(viewport.zoom)
        self._selected_node_id: str | None = None
        self._undo_stack: list[GraphSnapshot] = []
        self._redo_stack: list[GraphSnapshot] = []
        self._autosaves: list[AutosaveCheckpoint] = []

    def _resolve_zoom_mode(self, zoom: float) -> ZoomMode:
        if zoom < 0.75:
            return ZoomMode.OVERVIEW
        if zoom < 1.6:
            return ZoomMode.SCENE
        return ZoomMode.DETAIL

    def _snapshot(self) -> GraphSnapshot:
        return GraphSnapshot(
            nodes=tuple(sorted(self._nodes.values(), key=lambda node: node.node_id)),
            edges=tuple(self._edges),
            viewport=self._viewport,
            zoom_mode=self._zoom_mode,
            selected_node_id=self._selected_node_id,
        )

    def _apply_snapshot(self, snapshot: GraphSnapshot) -> None:
        self._nodes = {node.node_id: node for node in snapshot.nodes}
        self._edges = list(snapshot.edges)
        self._viewport = snapshot.viewport
        self._zoom_mode = snapshot.zoom_mode
        self._selected_node_id = snapshot.selected_node_id

    def _push_undo(self) -> None:
        self._undo_stack.append(self._snapshot())
        if len(self._undo_stack) > 200:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def add_node(self, node: GraphNodeView) -> None:
        self._push_undo()
        self._nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdgeView) -> None:
        self._push_undo()
        self._edges.append(edge)

    def select_node(self, node_id: str | None) -> None:
        self._push_undo()
        self._selected_node_id = node_id

    def set_viewport(self, viewport: GraphViewport) -> None:
        self._push_undo()
        self._viewport = viewport
        self._zoom_mode = self._resolve_zoom_mode(viewport.zoom)

    def set_zoom(self, zoom: float) -> None:
        self._push_undo()
        self._viewport = replace(self._viewport, zoom=zoom)
        self._zoom_mode = self._resolve_zoom_mode(zoom)

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(self._snapshot())
        snapshot = self._undo_stack.pop()
        self._apply_snapshot(snapshot)
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(self._snapshot())
        snapshot = self._redo_stack.pop()
        self._apply_snapshot(snapshot)
        return True

    def create_autosave(self, reason: str) -> AutosaveCheckpoint:
        snapshot = self._snapshot()
        payload = "|".join(
            [
                snapshot.viewport.__repr__(),
                snapshot.zoom_mode.value,
                str(snapshot.selected_node_id),
                ",".join(node.node_id for node in snapshot.nodes),
                ",".join(
                    f"{edge.source_id}->{edge.target_id}" for edge in snapshot.edges
                ),
            ]
        )
        checkpoint = AutosaveCheckpoint(
            checkpoint_id=f"autosave:{len(self._autosaves) + 1:04d}",
            reason=reason,
            created_at=_timestamp(),
            snapshot_hash=_hash_text(payload),
        )
        self._autosaves.append(checkpoint)
        return checkpoint

    def visible_nodes(self, *, padding: float = 180.0) -> tuple[GraphNodeView, ...]:
        viewport = self._viewport
        visible: list[GraphNodeView] = []
        left = viewport.x - padding
        top = viewport.y - padding
        right = viewport.x + viewport.width + padding
        bottom = viewport.y + viewport.height + padding

        for node in self._nodes.values():
            node_left = node.x
            node_top = node.y
            node_right = node.x + node.width
            node_bottom = node.y + node.height

            if node_right < left or node_left > right:
                continue
            if node_bottom < top or node_top > bottom:
                continue
            visible.append(node)

        visible.sort(key=lambda node: node.node_id)
        return tuple(visible)

    def visible_edges(self, visible_node_ids: set[str]) -> tuple[GraphEdgeView, ...]:
        visible = [
            edge
            for edge in self._edges
            if edge.source_id in visible_node_ids and edge.target_id in visible_node_ids
        ]
        return tuple(visible)

    def descendants(self, node_id: str) -> tuple[str, ...]:
        adjacency: dict[str, list[str]] = {}
        for edge in self._edges:
            adjacency.setdefault(edge.source_id, []).append(edge.target_id)

        visited: set[str] = set()
        queue: list[str] = [node_id]
        while queue:
            current = queue.pop(0)
            for neighbor in adjacency.get(current, []):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)
        return tuple(sorted(visited))

    def render_metrics(self) -> GraphRenderMetrics:
        visible_nodes = self.visible_nodes()
        visible_ids = {node.node_id for node in visible_nodes}
        visible_edges = self.visible_edges(visible_ids)

        total_nodes = len(self._nodes)
        visible_count = len(visible_nodes)
        virtualization_ratio = (
            1.0 - (visible_count / total_nodes) if total_nodes > 0 else 0.0
        )

        estimated_frame_ms = (
            2.8 + (visible_count * 0.018) + (len(visible_edges) * 0.007)
        )

        return GraphRenderMetrics(
            total_nodes=total_nodes,
            visible_nodes=visible_count,
            visible_edges=len(visible_edges),
            virtualization_ratio=_clamp(virtualization_ratio),
            estimated_frame_ms=estimated_frame_ms,
            mode=self._zoom_mode,
        )

    def is_performance_usable(
        self,
        *,
        max_frame_ms: float = 16.0,
        min_virtualization_ratio: float = 0.65,
    ) -> bool:
        metrics = self.render_metrics()
        return (
            metrics.estimated_frame_ms <= max_frame_ms
            and metrics.virtualization_ratio >= min_virtualization_ratio
        )

    @property
    def zoom_mode(self) -> ZoomMode:
        return self._zoom_mode

    @property
    def autosaves(self) -> tuple[AutosaveCheckpoint, ...]:
        return tuple(self._autosaves)

    @property
    def selected_node_id(self) -> str | None:
        return self._selected_node_id


@dataclass(frozen=True)
class BranchImpactPreview:
    """Impact preview data shown before branch creation."""

    node_id: str
    descendant_count: int
    divergence_score: float
    summary: str


@dataclass(frozen=True)
class UiBranchRecord:
    """Frontend branch record with lineage and status."""

    branch_id: str
    parent_branch_id: str | None
    source_node_id: str
    label: str
    status: BranchStatus
    lineage: tuple[str, ...]
    created_at: str
    merged_into: str | None = None
    archive_reason: str | None = None


class BranchWorkflowManager:
    """Frontend branch workflow manager for creation/archive/merge actions."""

    def __init__(self) -> None:
        self._counter = 0
        self._branches: dict[str, UiBranchRecord] = {
            "main": UiBranchRecord(
                branch_id="main",
                parent_branch_id=None,
                source_node_id="root",
                label="Main Timeline",
                status=BranchStatus.ACTIVE,
                lineage=("main",),
                created_at=_timestamp(),
            )
        }

    def preview_impact(
        self, node_id: str, graph: GraphWorkspace
    ) -> BranchImpactPreview:
        descendants = graph.descendants(node_id)
        descendant_count = len(descendants)

        node = graph._nodes.get(node_id)
        importance = node.importance if node is not None else 0.5
        divergence_score = _clamp((descendant_count * 0.08) + (importance * 0.42))

        summary = (
            f"Branching at {node_id} affects {descendant_count} downstream node(s) "
            f"with impact score {divergence_score:.2f}."
        )
        return BranchImpactPreview(
            node_id=node_id,
            descendant_count=descendant_count,
            divergence_score=divergence_score,
            summary=summary,
        )

    def create_branch(
        self,
        *,
        source_node_id: str,
        label: str,
        parent_branch_id: str = "main",
    ) -> UiBranchRecord:
        parent = self._branches.get(parent_branch_id)
        if parent is None:
            msg = f"Parent branch '{parent_branch_id}' does not exist."
            raise KeyError(msg)
        if parent.status != BranchStatus.ACTIVE:
            msg = f"Parent branch '{parent_branch_id}' is not active."
            raise ValueError(msg)

        self._counter += 1
        branch_id = f"{parent_branch_id}.u{self._counter:03d}"
        branch = UiBranchRecord(
            branch_id=branch_id,
            parent_branch_id=parent_branch_id,
            source_node_id=source_node_id,
            label=label,
            status=BranchStatus.ACTIVE,
            lineage=(*parent.lineage, branch_id),
            created_at=_timestamp(),
        )
        self._branches[branch_id] = branch
        return branch

    def archive_branch(self, branch_id: str, *, reason: str) -> UiBranchRecord:
        branch = self._branches.get(branch_id)
        if branch is None:
            msg = f"Branch '{branch_id}' not found."
            raise KeyError(msg)
        archived = replace(branch, status=BranchStatus.ARCHIVED, archive_reason=reason)
        self._branches[branch_id] = archived
        return archived

    def merge_branch(
        self,
        *,
        source_branch_id: str,
        target_branch_id: str,
    ) -> UiBranchRecord:
        source = self._branches.get(source_branch_id)
        target = self._branches.get(target_branch_id)
        if source is None or target is None:
            msg = "Source or target branch not found."
            raise KeyError(msg)
        merged = replace(
            source, status=BranchStatus.MERGED, merged_into=target_branch_id
        )
        self._branches[source_branch_id] = merged
        return merged

    def get_branch(self, branch_id: str) -> UiBranchRecord | None:
        return self._branches.get(branch_id)

    def list_branches(self) -> tuple[UiBranchRecord, ...]:
        return tuple(self._branches[key] for key in sorted(self._branches))


@dataclass(frozen=True)
class TunerSettings:
    """Phase 8 frontend tuner settings."""

    violence: float
    humor: float
    romance: float


@dataclass(frozen=True)
class TunerResolution:
    """Resolved tuner settings after precedence rules."""

    violence: float
    humor: float
    romance: float
    warnings: tuple[str, ...]
    precedence_order: tuple[str, ...]


@dataclass(frozen=True)
class TunerPreview:
    """Generated preview text for control panel impact."""

    tone_summary: str
    intensity_summary: str


class TunerControlPanel:
    """Tuner control engine with precedence, preview, and warnings."""

    def __init__(
        self,
        precedence_order: tuple[str, ...] = ("violence", "romance", "humor"),
    ) -> None:
        self._precedence_order = precedence_order

    def resolve(self, settings: TunerSettings) -> TunerResolution:
        warnings: list[str] = []

        violence = _clamp(settings.violence)
        humor = _clamp(settings.humor)
        romance = _clamp(settings.romance)

        if violence >= 0.85 and humor >= 0.7:
            humor = _clamp(humor - 0.22)
            warnings.append("Humor reduced to preserve violence-first precedence.")

        if violence >= 0.8 and romance >= 0.82:
            romance = _clamp(romance - 0.12)
            warnings.append("Romance trimmed to keep high-intensity coherence.")

        if violence >= 0.92:
            warnings.append("Extreme violence setting enabled.")
        if humor >= 0.92:
            warnings.append("Extreme humor setting may distort tone.")
        if romance >= 0.92:
            warnings.append("Extreme romance setting may dominate scene intent.")

        return TunerResolution(
            violence=violence,
            humor=humor,
            romance=romance,
            warnings=tuple(warnings),
            precedence_order=self._precedence_order,
        )

    def preview(self, resolution: TunerResolution) -> TunerPreview:
        def _descriptor(value: float, options: tuple[str, str, str]) -> str:
            if value < 0.34:
                return options[0]
            if value < 0.67:
                return options[1]
            return options[2]

        violence_text = _descriptor(
            resolution.violence,
            ("contained", "tense", "volatile"),
        )
        humor_text = _descriptor(
            resolution.humor,
            ("dry", "wry", "playful"),
        )
        romance_text = _descriptor(
            resolution.romance,
            ("subtle", "warm", "intimate"),
        )

        tone_summary = (
            f"Tone preview: {violence_text} conflict, {humor_text} relief, "
            f"{romance_text} connection."
        )
        intensity = _clamp(
            (resolution.violence * 0.6)
            + (resolution.romance * 0.25)
            + (resolution.humor * 0.15)
        )
        intensity_summary = f"Expected scene intensity: {intensity:.2f}"
        return TunerPreview(
            tone_summary=tone_summary, intensity_summary=intensity_summary
        )


@dataclass(frozen=True)
class SentenceEditAction:
    """Sentence edit action in Director Mode."""

    action_id: str
    sentence_index: int
    previous_text: str
    new_text: str
    actor: str
    created_at: str


@dataclass(frozen=True)
class PanelRedrawAction:
    """Panel redraw request in Director Mode."""

    action_id: str
    panel_index: int
    reason: str
    actor: str
    created_at: str


@dataclass(frozen=True)
class SyncBadge:
    """Non-color sync badge visible in dual-view UI."""

    label: str
    status: PaneSyncStatus
    icon: str


@dataclass(frozen=True)
class DualViewState:
    """Dual-view frontend state for text/image synchronization."""

    scene_id: str
    text_version: str
    image_version: str
    text_status: PaneSyncStatus
    image_status: PaneSyncStatus
    badges: tuple[SyncBadge, ...]
    sentence_edits: tuple[SentenceEditAction, ...]
    panel_redraws: tuple[PanelRedrawAction, ...]
    reconcile_actions: tuple[str, ...]


class DualViewManager:
    """Dual-view state manager with stale indicators and reconcile workflows."""

    def __init__(self) -> None:
        self._states: dict[str, DualViewState] = {}
        self._counter = 0

    def initialize(
        self, scene_id: str, *, text_version: str, image_version: str
    ) -> DualViewState:
        state = DualViewState(
            scene_id=scene_id,
            text_version=text_version,
            image_version=image_version,
            text_status=PaneSyncStatus.SYNCED,
            image_status=PaneSyncStatus.SYNCED,
            badges=(SyncBadge("Synchronized", PaneSyncStatus.SYNCED, "[OK]"),),
            sentence_edits=(),
            panel_redraws=(),
            reconcile_actions=(),
        )
        self._states[scene_id] = state
        return state

    def _set_state(self, scene_id: str, state: DualViewState) -> DualViewState:
        self._states[scene_id] = state
        return state

    def _next_action_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}:{self._counter:06d}"

    def _sync_badges(self, state: DualViewState) -> tuple[SyncBadge, ...]:
        badges: list[SyncBadge] = []
        if (
            state.text_status == PaneSyncStatus.SYNCED
            and state.image_status == PaneSyncStatus.SYNCED
        ):
            badges.append(SyncBadge("Synchronized", PaneSyncStatus.SYNCED, "[OK]"))
        else:
            if state.text_status in (
                PaneSyncStatus.TEXT_STALE,
                PaneSyncStatus.BOTH_STALE,
            ):
                badges.append(
                    SyncBadge("Text Stale", PaneSyncStatus.TEXT_STALE, "[TXT]")
                )
            if state.image_status in (
                PaneSyncStatus.IMAGE_STALE,
                PaneSyncStatus.BOTH_STALE,
            ):
                badges.append(
                    SyncBadge("Image Stale", PaneSyncStatus.IMAGE_STALE, "[IMG]")
                )
            if (
                state.text_status == PaneSyncStatus.RECONCILING
                or state.image_status == PaneSyncStatus.RECONCILING
            ):
                badges.append(
                    SyncBadge("Reconciling", PaneSyncStatus.RECONCILING, "[~]")
                )
        return tuple(badges)

    def _mark_text_stale(self, state: DualViewState) -> DualViewState:
        image_stale = state.image_status in (
            PaneSyncStatus.IMAGE_STALE,
            PaneSyncStatus.BOTH_STALE,
        )
        text_status = (
            PaneSyncStatus.BOTH_STALE if image_stale else PaneSyncStatus.TEXT_STALE
        )
        image_status = PaneSyncStatus.BOTH_STALE if image_stale else state.image_status
        updated = replace(state, text_status=text_status, image_status=image_status)
        return replace(updated, badges=self._sync_badges(updated))

    def _mark_image_stale(self, state: DualViewState) -> DualViewState:
        text_stale = state.text_status in (
            PaneSyncStatus.TEXT_STALE,
            PaneSyncStatus.BOTH_STALE,
        )
        text_status = PaneSyncStatus.BOTH_STALE if text_stale else state.text_status
        image_status = (
            PaneSyncStatus.BOTH_STALE if text_stale else PaneSyncStatus.IMAGE_STALE
        )
        updated = replace(state, text_status=text_status, image_status=image_status)
        return replace(updated, badges=self._sync_badges(updated))

    def record_sentence_edit(
        self,
        *,
        scene_id: str,
        sentence_index: int,
        previous_text: str,
        new_text: str,
        actor: str = "user",
    ) -> DualViewState:
        state = self._states[scene_id]
        edit = SentenceEditAction(
            action_id=self._next_action_id("edit"),
            sentence_index=sentence_index,
            previous_text=previous_text,
            new_text=new_text,
            actor=actor,
            created_at=_timestamp(),
        )
        updated = replace(state, sentence_edits=(*state.sentence_edits, edit))
        updated = self._mark_text_stale(updated)
        updated = replace(
            updated,
            reconcile_actions=(
                *updated.reconcile_actions,
                f"sync image for sentence {sentence_index}",
            ),
        )
        return self._set_state(scene_id, updated)

    def request_panel_redraw(
        self,
        *,
        scene_id: str,
        panel_index: int,
        reason: str,
        actor: str = "user",
    ) -> DualViewState:
        state = self._states[scene_id]
        redraw = PanelRedrawAction(
            action_id=self._next_action_id("redraw"),
            panel_index=panel_index,
            reason=reason,
            actor=actor,
            created_at=_timestamp(),
        )
        updated = replace(state, panel_redraws=(*state.panel_redraws, redraw))
        updated = self._mark_image_stale(updated)
        updated = replace(
            updated,
            reconcile_actions=(
                *updated.reconcile_actions,
                f"sync text for panel {panel_index}",
            ),
        )
        return self._set_state(scene_id, updated)

    def reconcile(
        self,
        *,
        scene_id: str,
        text_version: str,
        image_version: str,
    ) -> DualViewState:
        state = self._states[scene_id]
        reconciling = replace(
            state,
            text_status=PaneSyncStatus.RECONCILING,
            image_status=PaneSyncStatus.RECONCILING,
        )
        reconciling = replace(reconciling, badges=self._sync_badges(reconciling))

        synced = replace(
            reconciling,
            text_version=text_version,
            image_version=image_version,
            text_status=PaneSyncStatus.SYNCED,
            image_status=PaneSyncStatus.SYNCED,
            reconcile_actions=(),
        )
        synced = replace(synced, badges=self._sync_badges(synced))
        return self._set_state(scene_id, synced)

    def get_state(self, scene_id: str) -> DualViewState | None:
        return self._states.get(scene_id)

    def is_sync_state_visible(self, scene_id: str) -> bool:
        state = self._states.get(scene_id)
        if state is None:
            return False
        return len(state.badges) > 0

    def is_sync_state_accurate(self, scene_id: str) -> bool:
        state = self._states.get(scene_id)
        if state is None:
            return False

        versions_match = state.text_version == state.image_version
        statuses_synced = (
            state.text_status == PaneSyncStatus.SYNCED
            and state.image_status == PaneSyncStatus.SYNCED
        )

        if versions_match:
            return statuses_synced
        return not statuses_synced


@dataclass(frozen=True)
class KeyboardShortcut:
    """Keyboard shortcut metadata for accessibility audits."""

    key: str
    action: str
    description: str


@dataclass(frozen=True)
class ResponsiveLayout:
    """Responsive layout settings for current viewport width."""

    viewport_width: int
    breakpoint: str
    graph_columns: int
    controls_stacked: bool
    dual_view_stacked: bool
    graph_height: int


@dataclass(frozen=True)
class AccessibilityAudit:
    """Accessibility and mobile readiness audit summary."""

    keyboard_coverage: float
    semantic_label_coverage: float
    non_color_indicator_coverage: float
    mobile_ready: bool
    issues: tuple[str, ...]

    def critical_flows_usable(self) -> bool:
        return (
            self.keyboard_coverage >= 0.95
            and self.semantic_label_coverage >= 0.95
            and self.non_color_indicator_coverage >= 0.95
            and self.mobile_ready
        )


class AccessibilityManager:
    """Accessibility and responsive UX helper for frontend workflows."""

    REQUIRED_ACTIONS = (
        "create_branch",
        "undo",
        "redo",
        "zoom_in",
        "zoom_out",
        "open_tuner",
        "save_checkpoint",
        "toggle_dual_view",
        "reconcile_sync",
    )

    REQUIRED_LABELS = (
        "graph_canvas",
        "branch_button",
        "zoom_slider",
        "tuner_panel",
        "text_editor",
        "image_panel",
        "sync_badges",
    )

    REQUIRED_INDICATORS = (
        "sync_icon",
        "warning_icon",
        "stale_badge",
    )

    def layout_for_width(self, viewport_width: int) -> ResponsiveLayout:
        if viewport_width < 768:
            return ResponsiveLayout(
                viewport_width=viewport_width,
                breakpoint="mobile",
                graph_columns=1,
                controls_stacked=True,
                dual_view_stacked=True,
                graph_height=360,
            )
        if viewport_width < 1100:
            return ResponsiveLayout(
                viewport_width=viewport_width,
                breakpoint="tablet",
                graph_columns=2,
                controls_stacked=True,
                dual_view_stacked=False,
                graph_height=420,
            )
        return ResponsiveLayout(
            viewport_width=viewport_width,
            breakpoint="desktop",
            graph_columns=3,
            controls_stacked=False,
            dual_view_stacked=False,
            graph_height=520,
        )

    def keyboard_next_index(
        self,
        *,
        current_index: int,
        key: str,
        item_count: int,
    ) -> int:
        if item_count <= 0:
            return 0

        normalized_key = key.lower()
        if normalized_key in {"arrowright", "arrowdown"}:
            return (current_index + 1) % item_count
        if normalized_key in {"arrowleft", "arrowup"}:
            return (current_index - 1) % item_count
        if normalized_key == "home":
            return 0
        if normalized_key == "end":
            return item_count - 1
        return current_index

    def audit(
        self,
        *,
        shortcuts: tuple[KeyboardShortcut, ...],
        semantic_labels: tuple[str, ...],
        non_color_indicators: tuple[str, ...],
        viewport_width: int,
    ) -> AccessibilityAudit:
        shortcut_actions = {shortcut.action for shortcut in shortcuts}
        keyboard_coverage = len(shortcut_actions & set(self.REQUIRED_ACTIONS)) / len(
            self.REQUIRED_ACTIONS
        )

        labels = set(semantic_labels)
        semantic_label_coverage = len(labels & set(self.REQUIRED_LABELS)) / len(
            self.REQUIRED_LABELS
        )

        indicators = set(non_color_indicators)
        non_color_coverage = len(indicators & set(self.REQUIRED_INDICATORS)) / len(
            self.REQUIRED_INDICATORS
        )

        layout = self.layout_for_width(viewport_width)
        mobile_ready = (
            layout.breakpoint == "mobile"
            and layout.controls_stacked
            and layout.dual_view_stacked
        )

        issues: list[str] = []
        if keyboard_coverage < 1.0:
            issues.append("missing keyboard shortcut coverage")
        if semantic_label_coverage < 1.0:
            issues.append("missing semantic labels")
        if non_color_coverage < 1.0:
            issues.append("missing non-color indicators")
        if not mobile_ready:
            issues.append("mobile layout not ready")

        return AccessibilityAudit(
            keyboard_coverage=_clamp(keyboard_coverage),
            semantic_label_coverage=_clamp(semantic_label_coverage),
            non_color_indicator_coverage=_clamp(non_color_coverage),
            mobile_ready=mobile_ready,
            issues=tuple(issues),
        )


@dataclass(frozen=True)
class FrontendPhase8Metrics:
    """Aggregated metrics for Phase 8 done-criteria validation."""

    graph_performance_usable: bool
    keyboard_mobile_usable: bool
    dual_sync_visible_and_accurate: bool
    virtualization_ratio: float
    estimated_frame_ms: float
    keyboard_coverage: float
    mismatch_rate: float


def evaluate_phase8_done_criteria(
    *,
    graph_metrics: GraphRenderMetrics,
    accessibility_audit: AccessibilityAudit,
    dual_view_state: DualViewState,
) -> FrontendPhase8Metrics:
    """Evaluate Phase 8 done criteria across graph, accessibility, and sync."""

    sync_visible = len(dual_view_state.badges) > 0
    versions_match = dual_view_state.text_version == dual_view_state.image_version
    statuses_synced = (
        dual_view_state.text_status == PaneSyncStatus.SYNCED
        and dual_view_state.image_status == PaneSyncStatus.SYNCED
    )
    sync_accurate = statuses_synced if versions_match else not statuses_synced

    mismatch_indicators = [
        dual_view_state.text_status
        in (PaneSyncStatus.TEXT_STALE, PaneSyncStatus.BOTH_STALE),
        dual_view_state.image_status
        in (PaneSyncStatus.IMAGE_STALE, PaneSyncStatus.BOTH_STALE),
    ]
    mismatch_rate = sum(1 for flag in mismatch_indicators if flag) / len(
        mismatch_indicators
    )

    return FrontendPhase8Metrics(
        graph_performance_usable=(
            graph_metrics.estimated_frame_ms <= 16.0
            and graph_metrics.virtualization_ratio >= 0.65
        ),
        keyboard_mobile_usable=accessibility_audit.critical_flows_usable(),
        dual_sync_visible_and_accurate=(sync_visible and sync_accurate),
        virtualization_ratio=graph_metrics.virtualization_ratio,
        estimated_frame_ms=graph_metrics.estimated_frame_ms,
        keyboard_coverage=accessibility_audit.keyboard_coverage,
        mismatch_rate=mismatch_rate,
    )


__all__ = [
    "AccessibilityAudit",
    "AccessibilityManager",
    "AutosaveCheckpoint",
    "BranchImpactPreview",
    "BranchStatus",
    "BranchWorkflowManager",
    "DualViewManager",
    "DualViewState",
    "FrontendPhase8Metrics",
    "GraphEdgeView",
    "GraphNodeView",
    "GraphRenderMetrics",
    "GraphSnapshot",
    "GraphViewport",
    "GraphWorkspace",
    "KeyboardShortcut",
    "PaneSyncStatus",
    "PanelRedrawAction",
    "ResponsiveLayout",
    "SentenceEditAction",
    "SyncBadge",
    "TunerControlPanel",
    "TunerPreview",
    "TunerResolution",
    "TunerSettings",
    "UiBranchRecord",
    "ZoomMode",
    "evaluate_phase8_done_criteria",
]
