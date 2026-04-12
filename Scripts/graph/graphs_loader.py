import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import networkx as nx

from Scripts.graph.hypernetwork_builder import build_hypergraphx_graph
from utils.hypergraph_config import HypergraphConfig
from utils.graph_visualizer import GraphConfig, visualize_and_save_graph
from utils.project_paths import get_paths, verify_paths

P = get_paths()

REPORT_FILE_NAME = "scholarnet_report.json"
INTERACTIVE_GRAPH_FILE_NAME = "interactive_graph.html"

BASE_GRAPH_IMAGE_STEM = "base_graph"
LCC_GRAPH_IMAGE_STEM = "largest_connected_component_graph"
LCC_COMMUNITY_IMAGE_STEM = "lcc_community_graph"
LCC_HUBS_IMAGE_STEM = "lcc_hubs_graph"

DEFAULT_SEED = 777
DEFAULT_BASE_NODE_SIZE = 20
DEFAULT_LCC_NODE_SIZE = 40


def _load_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"ScholarNet report file not found at: {path}")

    with path.open("r", encoding="utf-8") as source:
        payload = json.load(source)

    if not isinstance(payload, dict):
        raise ValueError(f"ScholarNet report must be a JSON object: {path}")

    return payload


def _require_graph_section(report: dict[str, Any], graph_key: str, report_path: Path) -> dict[str, Any]:
    section = report.get(graph_key)
    if not isinstance(section, dict):
        raise KeyError(f"Missing graph section '{graph_key}' in {report_path}")
    return section


def _require_reconstruction_data(
    section: dict[str, Any],
    graph_key: str,
    report_path: Path,
) -> dict[str, Any]:
    reconstruction_data = section.get("reconstruction_data")
    if not isinstance(reconstruction_data, dict):
        raise KeyError(
            f"Missing reconstruction_data for '{graph_key}' in {report_path}"
        )
    return reconstruction_data


def _reconstruct_graph(reconstruction_data: dict[str, Any]) -> nx.Graph:
    graph = nx.Graph()

    graph.add_nodes_from(reconstruction_data.get("nodes", []))
    for edge in reconstruction_data.get("edges", []):
        if not isinstance(edge, dict):
            continue
        u = edge.get("u")
        v = edge.get("v")
        if u is None or v is None:
            continue
        graph.add_edge(u, v, weight=edge.get("weight", 1.0))

    return graph


def _reconstruct_lcc_graph(
    base_graph: nx.Graph,
    reconstruction_data: dict[str, Any],
) -> nx.Graph:
    raw_nodes = reconstruction_data.get("nodes", [])
    if isinstance(raw_nodes, list) and raw_nodes:
        lcc_nodes = [node for node in raw_nodes if node in base_graph]
        if len(lcc_nodes) == len(raw_nodes):
            return base_graph.subgraph(lcc_nodes).copy()

    return _reconstruct_graph(reconstruction_data)

def _normalize_hyperedge_nodes(raw_nodes: Any) -> tuple[Any, ...] | None:
    if not isinstance(raw_nodes, Iterable) or isinstance(raw_nodes, (str, bytes)):
        return None

    normalized_nodes: list[Any] = []
    for node in raw_nodes:
        if node is None:
            continue
        if node in normalized_nodes:
            continue
        normalized_nodes.append(node)

    if len(normalized_nodes) < 2:
        return None

    return tuple(normalized_nodes)

def _extract_hyperedges(reconstruction_data: dict[str, Any],):
    raw_hyperedges = reconstruction_data.get("hyperedges")

    hyperedges: list[tuple[Any, ...]] = []

    for raw_hyperedge in raw_hyperedges:
        raw_nodes = raw_hyperedge

        normalized_hyperedge = _normalize_hyperedge_nodes(raw_nodes)
        if normalized_hyperedge is None:
            continue

        hyperedges.append(normalized_hyperedge)

    return hyperedges

def _resolve_hyperedges(hypergraph_section: dict[str, Any], report_path: Path,):
    reconstruction_data = _require_reconstruction_data(
        hypergraph_section, "hypergraph", report_path
    )
    return _extract_hyperedges(reconstruction_data)


def _resolve_hypergraph_config(
    hypergraph_section: dict[str, Any],
    report_path: Path,
    fallback_seed: int,
) -> HypergraphConfig:
    reconstruction_data = _require_reconstruction_data(
        hypergraph_section, "hypergraph", report_path
    )

    raw_hypergraph_config = reconstruction_data.get("hypergraph_config")
    if isinstance(raw_hypergraph_config, dict):
        candidate_payload = dict(raw_hypergraph_config)
        if "seed" not in candidate_payload:
            candidate_payload["seed"] = fallback_seed
        try:
            return HypergraphConfig.from_dict(candidate_payload)
        except ValueError:
            pass

    return HypergraphConfig(seed=fallback_seed)

def _coerce_seed(reconstruction_data: dict[str, Any], fallback_seed: int) -> int:
    graph_config = reconstruction_data.get("graph_config")
    if isinstance(graph_config, dict):
        raw_seed = graph_config.get("seed")
        if isinstance(raw_seed, int):
            return raw_seed

    raw_seed = reconstruction_data.get("seed")
    if isinstance(raw_seed, int):
        return raw_seed

    return fallback_seed

def _coerce_node_size(
    reconstruction_data: dict[str, Any],
    *,
    variant: str,
    fallback_node_size: int,
) -> int:
    # New format: reconstruction_data.graph_config.node_size
    graph_config = reconstruction_data.get("graph_config")
    if isinstance(graph_config, dict):
        raw_node_size = graph_config.get("node_size")
        if isinstance(raw_node_size, int):
            return raw_node_size

    # Legacy format: reconstruction_data.node_sizes[variant/default]
    node_sizes = reconstruction_data.get("node_sizes")
    if isinstance(node_sizes, dict):
        preferred = node_sizes.get(variant)
        if isinstance(preferred, int):
            return preferred
        default = node_sizes.get("default")
        if isinstance(default, int):
            return default

    return fallback_node_size


def _extract_color_partitions(reconstruction_data: dict[str, Any]) -> dict[str, list[Any]]:
    color_partitions = reconstruction_data.get("color_partitions")
    if not isinstance(color_partitions, dict):
        return {}
    return color_partitions


def _normalize_node_colors(colors: Any) -> list[Any] | None:
    if isinstance(colors, list) and len(colors) > 0:
        return colors
    return None


def _render_graph(
    *,
    image_stem: str,
    graph: nx.Graph,
    seed: int,
    node_size: int,
    node_colors: list[Any] | None,
) -> None:
    visualize_and_save_graph(
        graph_name=image_stem,
        graph=graph,
        graph_config=GraphConfig(seed=seed, node_size=node_size),
        node_colors=node_colors,
    )


def _generate_interactive_graph(lcc_graph: nx.Graph) -> None:
    # Lazy import: keep loader importable even when pyvis is unavailable.
    try:
        from utils.interactive_graph_converter import generate_interactive_graph
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "Interactive graph generation requires optional dependency 'pyvis'."
        ) from error

    generate_interactive_graph(lcc_graph, INTERACTIVE_GRAPH_FILE_NAME)


def load_graphs(report_path: Path | None = None):
    verify_paths()

    resolved_report_path = report_path or (P.ANALYTICS_DIR / REPORT_FILE_NAME)
    report = _load_report(resolved_report_path)

    base_section = _require_graph_section(report, "base_graph", resolved_report_path)
    lcc_section = _require_graph_section(report, "lcc", resolved_report_path)

    base_reconstruction_data = _require_reconstruction_data(
        base_section, "base_graph", resolved_report_path
    )
    lcc_reconstruction_data = _require_reconstruction_data(
        lcc_section, "lcc", resolved_report_path
    )

    base_graph = _reconstruct_graph(base_reconstruction_data)
    lcc_graph = _reconstruct_lcc_graph(base_graph, lcc_reconstruction_data)

    base_seed = _coerce_seed(base_reconstruction_data, DEFAULT_SEED)
    lcc_seed = _coerce_seed(lcc_reconstruction_data, DEFAULT_SEED)

    base_default_node_size = _coerce_node_size(
        base_reconstruction_data,
        variant="default",
        fallback_node_size=DEFAULT_BASE_NODE_SIZE,
    )
    lcc_default_node_size = _coerce_node_size(
        lcc_reconstruction_data,
        variant="default",
        fallback_node_size=DEFAULT_LCC_NODE_SIZE,
    )
    lcc_community_node_size = _coerce_node_size(
        lcc_reconstruction_data,
        variant="communities",
        fallback_node_size=lcc_default_node_size,
    )
    lcc_hubs_node_size = _coerce_node_size(
        lcc_reconstruction_data,
        variant="hubs",
        fallback_node_size=lcc_default_node_size,
    )

    lcc_color_partitions = _extract_color_partitions(lcc_reconstruction_data)
    lcc_community_colors = _normalize_node_colors(lcc_color_partitions.get("communities"))
    lcc_hubs_colors = _normalize_node_colors(lcc_color_partitions.get("hubs"))

    _render_graph(
        image_stem=BASE_GRAPH_IMAGE_STEM,
        graph=base_graph,
        seed=base_seed,
        node_size=base_default_node_size,
        node_colors=None,
    )
    _render_graph(
        image_stem=LCC_GRAPH_IMAGE_STEM,
        graph=lcc_graph,
        seed=lcc_seed,
        node_size=lcc_default_node_size,
        node_colors=None,
    )
    _render_graph(
        image_stem=LCC_COMMUNITY_IMAGE_STEM,
        graph=lcc_graph,
        seed=lcc_seed,
        node_size=lcc_community_node_size,
        node_colors=lcc_community_colors,
    )
    _render_graph(
        image_stem=LCC_HUBS_IMAGE_STEM,
        graph=lcc_graph,
        seed=lcc_seed,
        node_size=lcc_hubs_node_size,
        node_colors=lcc_hubs_colors,
    )

    hypergraph_section = _require_graph_section(
        report, "hypergraph", resolved_report_path
    )
    hyperedges = _resolve_hyperedges(hypergraph_section, resolved_report_path)
    hypergraph_config = _resolve_hypergraph_config(
        hypergraph_section,
        resolved_report_path,
        lcc_seed,
    )
    hypergraph = build_hypergraphx_graph(
        lcc_graph,
        hypergraph_config=hypergraph_config,
        hyperedges_list=hyperedges,
    )
    _generate_interactive_graph(lcc_graph)

    print("Loading graphs completed.")
    return {
        "base_graph": base_graph,
        "lcc_graph": lcc_graph,
        "hypergraph": hypergraph,
    }


if __name__ == "__main__":
    load_graphs()
