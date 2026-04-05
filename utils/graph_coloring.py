from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from Scripts.analytics.graph_analyzer import AnalysisArtifacts


@dataclass
class GraphColoringArtifacts:
    node_order: list[str] = field(default_factory=list)
    communities: list[Any] = field(default_factory=list)
    hubs: list[Any] = field(default_factory=list)

@dataclass
class GraphColoringConfig:
    community_palette: list[str] | None = None
    hub_palette: list[str] | None = None


def _is_hex_color(value: str) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) not in (7, 9) or not value.startswith("#"):
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value[1:])


def _build_colors_from_partition(
    node_order: list[str],
    partition: dict,
) -> list[int]:
    node_to_color: dict[str, int] = {}

    for color_id, community_name in enumerate(partition):
        community_nodes = partition[community_name].get("nodes", [])
        for node in community_nodes:
            node_to_color[node] = color_id

    return [node_to_color.get(node, -1) for node in node_order]


def _build_hub_category_colors(
    node_order: list[str],
    hubs: list[str],
) -> list[int]:
    hubs_set = set(hubs)

    # 0 -> ordinary node, 1 -> hub node.
    return [1 if node in hubs_set else 0 for node in node_order]


def _apply_hex_palette(
    color_ids: list[int],
    palette: list[str] | None,
    palette_name: str,
) -> list[Any]:
    if palette is None:
        return color_ids

    if len(palette) == 0:
        raise ValueError(f"{palette_name} must not be empty.")

    if not all(_is_hex_color(color) for color in palette):
        raise ValueError(f"{palette_name} must contain only hex colors.")

    max_color_id = max(color_ids, default=-1)
    if max_color_id >= len(palette):
        raise ValueError(
            f"{palette_name} has {len(palette)} colors, but requires at least {max_color_id + 1}."
        )

    if any(color_id < 0 for color_id in color_ids):
        raise ValueError(
            f"{palette_name} cannot be applied because some nodes have unassigned color ids."
        )

    return [palette[color_id] for color_id in color_ids]


def build_graph_coloring_artifacts(
    graph: nx.Graph,
    analysis_artifacts: AnalysisArtifacts,
    config: GraphColoringConfig | None = None,
) -> GraphColoringArtifacts:
    if config is None:
        config = GraphColoringConfig()

    node_order = list(graph.nodes())

    communities_ids = (
        _build_colors_from_partition(node_order, analysis_artifacts.best_partition)
        if analysis_artifacts.best_partition
        else []
    )
    hubs_ids = (
        _build_hub_category_colors(node_order, analysis_artifacts.hubs)
        if analysis_artifacts.hubs
        else []
    )

    communities = _apply_hex_palette(
        communities_ids,
        config.community_palette,
        "community_palette",
    )
    hubs = _apply_hex_palette(
        hubs_ids,
        config.hub_palette,
        "hub_palette",
    )

    return GraphColoringArtifacts(
        node_order=node_order,
        communities=communities,
        hubs=hubs,
    )
