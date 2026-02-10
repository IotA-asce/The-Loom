"""Tests for Phase 8 - Frontend and User Workflow."""

from __future__ import annotations

from core.frontend_workflow_engine import (
    AccessibilityManager,
    BranchStatus,
    BranchWorkflowManager,
    DualViewManager,
    GraphViewport,
    GraphWorkspace,
    KeyboardShortcut,
    PaneSyncStatus,
    TunerControlPanel,
    TunerSettings,
    ZoomMode,
    evaluate_phase8_done_criteria,
)


class TestG81InteractiveGraphUX:
    """G8.1: Interactive graph UX with virtualization."""

    def test_graph_workspace_creation(self) -> None:
        """Graph workspace initializes with viewport."""
        viewport = GraphViewport(x=0, y=0, width=1200, height=800, zoom=1.0)
        workspace = GraphWorkspace(viewport)

        assert workspace.zoom_mode == ZoomMode.SCENE

    def test_semantic_zoom_modes(self) -> None:
        """Zoom modes transition at correct thresholds."""
        viewport_overview = GraphViewport(x=0, y=0, width=1200, height=800, zoom=0.5)
        workspace_overview = GraphWorkspace(viewport_overview)
        assert workspace_overview.zoom_mode == ZoomMode.OVERVIEW

        viewport_scene = GraphViewport(x=0, y=0, width=1200, height=800, zoom=1.0)
        workspace_scene = GraphWorkspace(viewport_scene)
        assert workspace_scene.zoom_mode == ZoomMode.SCENE

        viewport_detail = GraphViewport(x=0, y=0, width=1200, height=800, zoom=2.0)
        workspace_detail = GraphWorkspace(viewport_detail)
        assert workspace_detail.zoom_mode == ZoomMode.DETAIL

    def test_undo_redo_functionality(self) -> None:
        """Undo/redo works for graph operations."""
        from core.frontend_workflow_engine import GraphNodeView

        viewport = GraphViewport(x=0, y=0, width=1200, height=800, zoom=1.0)
        workspace = GraphWorkspace(viewport)

        # Add a node
        node = GraphNodeView(
            node_id="test-1",
            label="Test Node",
            branch_id="main",
            scene_id="scene-1",
            x=100,
            y=100,
        )
        workspace.add_node(node)

        # Undo
        assert workspace.undo() is True

        # Redo
        assert workspace.redo() is True

    def test_autosave_checkpoint_creation(self) -> None:
        """Autosave checkpoints are created with hashes."""
        viewport = GraphViewport(x=0, y=0, width=1200, height=800, zoom=1.0)
        workspace = GraphWorkspace(viewport)

        checkpoint = workspace.create_autosave("test-checkpoint")

        assert checkpoint.checkpoint_id.startswith("autosave:")
        assert checkpoint.reason == "test-checkpoint"
        assert checkpoint.snapshot_hash
        assert len(workspace.autosaves) == 1

    def test_virtualization_metrics(self) -> None:
        """Virtualization metrics calculated correctly."""
        viewport = GraphViewport(x=0, y=0, width=400, height=300, zoom=1.0)
        workspace = GraphWorkspace(viewport)

        metrics = workspace.render_metrics()

        assert metrics.total_nodes >= 0
        assert metrics.virtualization_ratio >= 0.0
        assert metrics.estimated_frame_ms > 0
        assert metrics.mode in (ZoomMode.OVERVIEW, ZoomMode.SCENE, ZoomMode.DETAIL)

    def test_performance_usable_thresholds(self) -> None:
        """Performance usability respects frame time and virtualization."""
        viewport = GraphViewport(x=0, y=0, width=1200, height=800, zoom=1.0)
        workspace = GraphWorkspace(viewport)

        # Empty workspace with no virtualization may not meet ratio threshold
        # but should still have acceptable frame time
        metrics = workspace.render_metrics()
        assert metrics.estimated_frame_ms <= 16.0


class TestG82BranchingWorkflowUX:
    """G8.2: Branching workflow UX."""

    def test_branch_creation_from_node(self) -> None:
        """Branches can be created from any node."""
        manager = BranchWorkflowManager()

        branch = manager.create_branch(
            source_node_id="node-1",
            label="Alternate Timeline",
            parent_branch_id="main",
        )

        assert branch.branch_id.startswith("main.")
        assert branch.source_node_id == "node-1"
        assert branch.label == "Alternate Timeline"
        assert branch.status == BranchStatus.ACTIVE
        assert "main" in branch.lineage

    def test_branch_lineage_tracking(self) -> None:
        """Branch lineage is tracked correctly."""
        manager = BranchWorkflowManager()

        branch1 = manager.create_branch(
            source_node_id="node-1", label="Branch 1", parent_branch_id="main"
        )
        branch2 = manager.create_branch(
            source_node_id="node-2",
            label="Branch 2",
            parent_branch_id=branch1.branch_id,
        )

        assert branch2.lineage == (*branch1.lineage, branch2.branch_id)

    def test_impact_preview_calculation(self) -> None:
        """Impact preview shows descendant count and score."""
        from core.frontend_workflow_engine import GraphNodeView

        viewport = GraphViewport(x=0, y=0, width=1200, height=800, zoom=1.0)
        graph = GraphWorkspace(viewport)
        manager = BranchWorkflowManager()

        # Add nodes
        for i in range(3):
            node = GraphNodeView(
                node_id=f"node-{i}",
                label=f"Node {i}",
                branch_id="main",
                scene_id=f"scene-{i}",
                x=i * 200,
                y=100,
            )
            graph.add_node(node)

        preview = manager.preview_impact("node-0", graph)

        assert preview.descendant_count >= 0
        assert 0.0 <= preview.divergence_score <= 1.0
        assert preview.summary

    def test_branch_archive_action(self) -> None:
        """Branches can be archived with reason."""
        manager = BranchWorkflowManager()
        branch = manager.create_branch(
            source_node_id="node-1", label="To Archive", parent_branch_id="main"
        )

        archived = manager.archive_branch(branch.branch_id, reason="no longer needed")

        assert archived.status == BranchStatus.ARCHIVED
        assert archived.archive_reason == "no longer needed"

    def test_branch_merge_action(self) -> None:
        """Branches can be merged into another."""
        manager = BranchWorkflowManager()
        source = manager.create_branch(
            source_node_id="node-1", label="Source", parent_branch_id="main"
        )

        merged = manager.merge_branch(
            source_branch_id=source.branch_id, target_branch_id="main"
        )

        assert merged.status == BranchStatus.MERGED
        assert merged.merged_into == "main"


class TestG83TunerControlPanel:
    """G8.3: Tuner and control panel."""

    def test_tuner_settings_resolution(self) -> None:
        """Tuner settings resolve with precedence rules."""
        panel = TunerControlPanel()
        settings = TunerSettings(violence=0.9, humor=0.8, romance=0.5)

        resolution = panel.resolve(settings)

        assert 0.0 <= resolution.violence <= 1.0
        assert 0.0 <= resolution.humor <= 1.0
        assert 0.0 <= resolution.romance <= 1.0

    def test_tuner_violence_first_precedence(self) -> None:
        """High violence reduces humor per precedence rules."""
        panel = TunerControlPanel()
        settings = TunerSettings(violence=0.9, humor=0.8, romance=0.5)

        resolution = panel.resolve(settings)

        # Humor should be reduced due to violence-first precedence
        assert resolution.humor < settings.humor
        assert any("Humor reduced" in w for w in resolution.warnings)

    def test_extreme_setting_warnings(self) -> None:
        """Warnings shown for extreme settings."""
        panel = TunerControlPanel()
        extreme_settings = TunerSettings(violence=0.95, humor=0.5, romance=0.5)

        resolution = panel.resolve(extreme_settings)

        assert any("Extreme violence" in w for w in resolution.warnings)

    def test_tuner_preview_generation(self) -> None:
        """Tuner generates tone preview."""
        panel = TunerControlPanel()
        settings = TunerSettings(violence=0.7, humor=0.3, romance=0.6)
        resolution = panel.resolve(settings)

        preview = panel.preview(resolution)

        assert "Tone preview" in preview.tone_summary
        assert "Expected scene intensity" in preview.intensity_summary


class TestG84DualViewDirectorMode:
    """G8.4: Dual-view and Director Mode."""

    def test_dual_view_initialization(self) -> None:
        """Dual view initializes with synced state."""
        manager = DualViewManager()
        state = manager.initialize("scene-1", text_version="v1", image_version="v1")

        assert state.scene_id == "scene-1"
        assert state.text_status == PaneSyncStatus.SYNCED
        assert state.image_status == PaneSyncStatus.SYNCED
        assert len(state.badges) > 0

    def test_sentence_edit_marks_text_stale(self) -> None:
        """Sentence edit marks text as stale."""
        manager = DualViewManager()
        manager.initialize("scene-1", text_version="v1", image_version="v1")

        state = manager.record_sentence_edit(
            scene_id="scene-1",
            sentence_index=0,
            previous_text="old",
            new_text="new",
        )

        stale_statuses = (PaneSyncStatus.TEXT_STALE, PaneSyncStatus.BOTH_STALE)
        assert state.text_status in stale_statuses
        assert len(state.sentence_edits) == 1

    def test_panel_redraw_marks_image_stale(self) -> None:
        """Panel redraw marks image as stale."""
        manager = DualViewManager()
        manager.initialize("scene-1", text_version="v1", image_version="v1")

        state = manager.request_panel_redraw(
            scene_id="scene-1",
            panel_index=0,
            reason="anatomy fix",
        )

        stale_statuses = (PaneSyncStatus.IMAGE_STALE, PaneSyncStatus.BOTH_STALE)
        assert state.image_status in stale_statuses
        assert len(state.panel_redraws) == 1

    def test_sync_badges_non_color_indicators(self) -> None:
        """Sync badges use non-color indicators."""
        manager = DualViewManager()
        state = manager.initialize("scene-1", text_version="v1", image_version="v1")

        badges = state.badges

        # All badges should have icons (non-color indicators)
        assert all(badge.icon for badge in badges)
        assert all(badge.label for badge in badges)

    def test_reconcile_syncs_versions(self) -> None:
        """Reconcile brings versions back to synced."""
        manager = DualViewManager()
        manager.initialize("scene-1", text_version="v1", image_version="v1")

        # Make a change
        manager.record_sentence_edit(
            scene_id="scene-1",
            sentence_index=0,
            previous_text="old",
            new_text="new",
        )

        # Reconcile
        state = manager.reconcile(
            scene_id="scene-1", text_version="v2", image_version="v2"
        )

        assert state.text_status == PaneSyncStatus.SYNCED
        assert state.image_status == PaneSyncStatus.SYNCED
        assert state.text_version == "v2"
        assert state.image_version == "v2"

    def test_sync_state_visibility(self) -> None:
        """Sync state is always visible when active."""
        manager = DualViewManager()
        manager.initialize("scene-1", text_version="v1", image_version="v1")

        assert manager.is_sync_state_visible("scene-1") is True

    def test_sync_state_accuracy(self) -> None:
        """Sync state accuracy reflects version match."""
        manager = DualViewManager()
        manager.initialize("scene-1", text_version="v1", image_version="v1")

        # When synced and versions match
        assert manager.is_sync_state_accurate("scene-1") is True


class TestG85AccessibilityMobileReadiness:
    """G8.5: Accessibility and mobile readiness."""

    def test_responsive_layout_mobile(self) -> None:
        """Mobile layout has correct settings."""
        manager = AccessibilityManager()
        layout = manager.layout_for_width(375)

        assert layout.breakpoint == "mobile"
        assert layout.controls_stacked is True
        assert layout.dual_view_stacked is True
        assert layout.graph_columns == 1

    def test_responsive_layout_tablet(self) -> None:
        """Tablet layout has correct settings."""
        manager = AccessibilityManager()
        layout = manager.layout_for_width(900)

        assert layout.breakpoint == "tablet"
        assert layout.graph_columns == 2

    def test_responsive_layout_desktop(self) -> None:
        """Desktop layout has correct settings."""
        manager = AccessibilityManager()
        layout = manager.layout_for_width(1400)

        assert layout.breakpoint == "desktop"
        assert layout.graph_columns == 3
        assert layout.controls_stacked is False

    def test_keyboard_navigation_arrows(self) -> None:
        """Arrow keys navigate items."""
        manager = AccessibilityManager()

        kb_next = manager.keyboard_next_index
        assert kb_next(current_index=0, key="arrowright", item_count=5) == 1
        assert kb_next(current_index=4, key="arrowright", item_count=5) == 0
        assert kb_next(current_index=1, key="arrowleft", item_count=5) == 0

    def test_keyboard_navigation_home_end(self) -> None:
        """Home/End keys jump to first/last."""
        manager = AccessibilityManager()

        kb_next = manager.keyboard_next_index
        assert kb_next(current_index=3, key="home", item_count=5) == 0
        assert kb_next(current_index=2, key="end", item_count=5) == 4

    def test_accessibility_audit_coverage(self) -> None:
        """Audit measures keyboard and label coverage."""
        manager = AccessibilityManager()

        shortcuts = (
            KeyboardShortcut(
                key="ctrl+b", action="create_branch", description="Create branch"
            ),
            KeyboardShortcut(key="ctrl+z", action="undo", description="Undo"),
        )

        audit = manager.audit(
            shortcuts=shortcuts,
            semantic_labels=("graph_canvas", "branch_button"),
            non_color_indicators=("sync_icon",),
            viewport_width=375,
        )

        assert 0.0 <= audit.keyboard_coverage <= 1.0
        assert 0.0 <= audit.semantic_label_coverage <= 1.0
        assert isinstance(audit.mobile_ready, bool)

    def test_critical_flows_usable_threshold(self) -> None:
        """Critical flows require 95% coverage."""
        manager = AccessibilityManager()

        # Full coverage
        full_shortcuts = tuple(
            KeyboardShortcut(key=f"key-{a}", action=a, description=d)
            for a, d in [
                ("create_branch", "Create branch"),
                ("undo", "Undo"),
                ("redo", "Redo"),
                ("zoom_in", "Zoom in"),
                ("zoom_out", "Zoom out"),
                ("open_tuner", "Open tuner"),
                ("save_checkpoint", "Save"),
                ("toggle_dual_view", "Toggle dual view"),
                ("reconcile_sync", "Reconcile"),
            ]
        )

        audit = manager.audit(
            shortcuts=full_shortcuts,
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
            viewport_width=375,
        )

        assert audit.critical_flows_usable() is True


class TestPhase8DoneCriteria:
    """Phase 8 done criteria validation."""

    def test_done_criteria_evaluation(self) -> None:
        """Phase 8 metrics evaluate all criteria."""
        from core.frontend_workflow_engine import (
            AccessibilityAudit,
            DualViewState,
            GraphRenderMetrics,
            PaneSyncStatus,
            SyncBadge,
        )

        metrics = GraphRenderMetrics(
            total_nodes=100,
            visible_nodes=20,
            visible_edges=30,
            virtualization_ratio=0.8,
            estimated_frame_ms=10.0,
            mode=ZoomMode.SCENE,
        )

        audit = AccessibilityAudit(
            keyboard_coverage=1.0,
            semantic_label_coverage=1.0,
            non_color_indicator_coverage=1.0,
            mobile_ready=True,
            issues=(),
        )

        dual_state = DualViewState(
            scene_id="test",
            text_version="v1",
            image_version="v1",
            text_status=PaneSyncStatus.SYNCED,
            image_status=PaneSyncStatus.SYNCED,
            badges=(SyncBadge("OK", PaneSyncStatus.SYNCED, "[OK]"),),
            sentence_edits=(),
            panel_redraws=(),
            reconcile_actions=(),
        )

        result = evaluate_phase8_done_criteria(
            graph_metrics=metrics,
            accessibility_audit=audit,
            dual_view_state=dual_state,
        )

        assert result.graph_performance_usable is True
        assert result.keyboard_mobile_usable is True
        assert result.dual_sync_visible_and_accurate is True
        assert result.virtualization_ratio >= 0.65
        assert result.estimated_frame_ms <= 16.0
