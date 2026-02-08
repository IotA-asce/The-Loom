"""Smoke tests for phase-zero scaffolding."""

from __future__ import annotations

from pathlib import Path

from agents.archivist import SUPPORTED_MANGA_IMAGE_EXTENSIONS, list_manga_image_pages
from core.graph_logic import BranchGraph, StoryNode
from core.profiles import ToneProfile


def test_fixture_directories_exist() -> None:
    fixture_root = Path("tests/fixtures")
    expected_paths = [
        fixture_root / "text",
        fixture_root / "pdf",
        fixture_root / "epub",
        fixture_root / "cbz",
        fixture_root / "images",
        fixture_root / "golden",
    ]

    for expected_path in expected_paths:
        assert expected_path.exists(), f"Missing fixture directory: {expected_path}"


def test_supported_manga_extensions_include_required_formats() -> None:
    assert {".png", ".jpg", ".jpeg", ".webp"}.issubset(SUPPORTED_MANGA_IMAGE_EXTENSIONS)


def test_list_manga_image_pages_filters_and_sorts(tmp_path: Path) -> None:
    (tmp_path / "page-10.webp").write_text("fake")
    (tmp_path / "page-2.jpg").write_text("fake")
    (tmp_path / "page-1.png").write_text("fake")
    (tmp_path / "notes.txt").write_text("ignore")

    pages = list_manga_image_pages(tmp_path)
    page_names = [page.name for page in pages]

    assert page_names == ["page-1.png", "page-2.jpg", "page-10.webp"]


def test_branch_graph_adds_parent_child_relationship() -> None:
    graph = BranchGraph()
    root = StoryNode(node_id="n0", summary="start")
    child = StoryNode(node_id="n1", summary="branch", parent_id="n0")

    graph.add_node(root)
    graph.add_node(child)

    assert graph.get_children("n0") == [child]


def test_tone_profile_bounds() -> None:
    profile = ToneProfile(tone_label="dark", maturity_score=0.8, confidence=0.9)
    assert profile.in_bounds()
