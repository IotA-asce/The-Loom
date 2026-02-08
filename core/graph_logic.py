"""Minimal branch graph structures used by early tests and scaffolding."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StoryNode:
    """A single point in a narrative branch."""

    node_id: str
    summary: str
    parent_id: str | None = None


@dataclass
class BranchGraph:
    """A simple directed graph keyed by node identifiers."""

    nodes: dict[str, StoryNode] = field(default_factory=dict)
    children: dict[str, list[str]] = field(default_factory=dict)

    def add_node(self, node: StoryNode) -> None:
        if node.node_id in self.nodes:
            msg = f"Node '{node.node_id}' already exists."
            raise ValueError(msg)

        if node.parent_id is not None and node.parent_id not in self.nodes:
            msg = f"Parent node '{node.parent_id}' does not exist."
            raise ValueError(msg)

        self.nodes[node.node_id] = node
        self.children.setdefault(node.node_id, [])

        if node.parent_id is not None:
            self.children.setdefault(node.parent_id, []).append(node.node_id)

    def get_children(self, node_id: str) -> list[StoryNode]:
        child_ids = self.children.get(node_id, [])
        return [self.nodes[child_id] for child_id in child_ids]
