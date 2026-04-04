import json
import sys
from pathlib import Path
from typing import Any

import networkx as nx

try:
    from Scripts.graph.build_networkx_graph import (
        BASE_GRAPH_IMG_NAME,
        GRAPH_IMG_PATH,
        LCC_COMMUNITY_IMG_NAME,
        LCC_HUBS_IMG_NAME,
        LCC_IMG_NAME,
        INTERACTIVE_GRAPH_NAME,
        SCHOLARNET_REPORT_JSON_NAME,
        SEED,
    )
    from utils.graph_image_utils import build_graph_figure, save_graph_figure
    from utils.project_paths import get_paths
    from utils.interactive_graph_converter import generate_interactive_graph

except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from Scripts.graph.build_networkx_graph import (
        BASE_GRAPH_IMG_NAME,
        GRAPH_IMG_PATH,
        LCC_COMMUNITY_IMG_NAME,
        LCC_HUBS_IMG_NAME,
        LCC_IMG_NAME,
        INTERACTIVE_GRAPH_NAME,
        SCHOLARNET_REPORT_JSON_NAME,
        SEED,
    )
    from utils.graph_image_utils import build_graph_figure, save_graph_figure
    from utils.project_paths import get_paths
    from utils.interactive_graph_converter import generate_interactive_graph

P = get_paths()
SCHOLARNET_REPORT_PATH = P.DATA / "Analytics" / SCHOLARNET_REPORT_JSON_NAME


def _load_scholarnet_report(path: Path | None = None) -> dict[str, Any]:
    resolved_path = path if path is not None else SCHOLARNET_REPORT_PATH
    if not resolved_path.exists():
        raise FileNotFoundError(f"ScholarNet report file not found at: {resolved_path}")

    with resolved_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _reconstruct_graph(reconstruction_data: dict[str, Any]) -> nx.Graph:
    graph = nx.Graph()

    graph.add_nodes_from(reconstruction_data.get("nodes", []))
    for edge in reconstruction_data.get("edges", []):
        graph.add_edge(edge["u"], edge["v"], weight=edge.get("weight", 1.0))

    return graph


def _reconstruct_hypergraph(
    reconstruction_data: dict[str, Any],
):
    raw_hyperedges = reconstruction_data.get("hyperedges", [])
    if not isinstance(raw_hyperedges, list):
        return None

    hyperedges = []
    for raw_hyperedge in raw_hyperedges:
        if not isinstance(raw_hyperedge, list):
            continue
        nodes = tuple(node for node in raw_hyperedge if isinstance(node, str))
        if len(nodes) >= 2:
            hyperedges.append(nodes)

    if len(hyperedges) == 0:
        return None

    try:
        from Scripts.graph.build_hypergraphx_graph import build_hypergraph

        return build_hypergraph(hyperedges)
    except ModuleNotFoundError:
        # Keep report loading resilient when hypergraphx is unavailable.
        return {"hyperedges": hyperedges}


def _require_reconstruction_data(
    scholarnet_report: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    section = scholarnet_report.get(key)
    if not isinstance(section, dict):
        raise KeyError(f"Missing graph section '{key}' in {SCHOLARNET_REPORT_PATH}")

    reconstruction_data = section.get("reconstruction_data")
    if not isinstance(reconstruction_data, dict):
        raise KeyError(
            f"Missing reconstruction_data for '{key}' in {SCHOLARNET_REPORT_PATH}"
        )

    return reconstruction_data


def _normalize_colors(colors: Any) -> list | None:
    if isinstance(colors, list) and len(colors) > 0:
        return colors
    return None

def _normalize_node_positions(node_positions: Any) -> dict | None:
    if not isinstance(node_positions, dict) or len(node_positions) == 0:
        return None

    normalized = {}
    for node, coords in node_positions.items():
        if isinstance(coords, list) and len(coords) == 2:
            normalized[node] = (float(coords[0]), float(coords[1]))

    if len(normalized) == 0:
        return None

    return normalized


def load_graphs():
    scholarnet_report = _load_scholarnet_report()

    base_reconstruction_data = _require_reconstruction_data(scholarnet_report, "base_graph")
    lcc_reconstruction_data = _require_reconstruction_data(scholarnet_report, "lcc")
    hypergraph_section = scholarnet_report.get("hypergraph", {})
    hypergraph_reconstruction_data = {}
    if isinstance(hypergraph_section, dict):
        raw_hypergraph_reconstruction = hypergraph_section.get("reconstruction_data", {})
        if isinstance(raw_hypergraph_reconstruction, dict):
            hypergraph_reconstruction_data = raw_hypergraph_reconstruction

    base_graph = _reconstruct_graph(base_reconstruction_data)
    lcc_graph = _reconstruct_graph(lcc_reconstruction_data)
    hypergraph = (
        _reconstruct_hypergraph(hypergraph_reconstruction_data)
        if hypergraph_reconstruction_data
        else None
    )

    base_node_sizes = base_reconstruction_data.get("node_sizes", {})
    lcc_node_sizes = lcc_reconstruction_data.get("node_sizes", {})
    lcc_color_partitions = lcc_reconstruction_data.get("color_partitions", {})
    base_node_positions = _normalize_node_positions(base_reconstruction_data.get("node_positions"))
    lcc_node_positions = _normalize_node_positions(lcc_reconstruction_data.get("node_positions"))

    graph_render_plan = {
        "base_graph": {
            "graph": base_graph,
            "image_name": BASE_GRAPH_IMG_NAME,
            "seed": base_reconstruction_data.get("seed", SEED),
            "node_size": base_node_sizes.get("default", 20),
            "node_colors": None,
            "node_positions": base_node_positions,
        },
        "lcc_graph": {
            "graph": lcc_graph,
            "image_name": LCC_IMG_NAME,
            "seed": lcc_reconstruction_data.get("seed", SEED),
            "node_size": lcc_node_sizes.get("default", 40),
            "node_colors": None,
            "node_positions": lcc_node_positions,
        },
        "lcc_community_graph": {
            "graph": lcc_graph,
            "image_name": LCC_COMMUNITY_IMG_NAME,
            "seed": lcc_reconstruction_data.get("seed", SEED),
            "node_size": lcc_node_sizes.get("communities", lcc_node_sizes.get("default", 40)),
            "node_colors": _normalize_colors(lcc_color_partitions.get("communities")),
            "node_positions": lcc_node_positions,
        },
        "lcc_hubs_graph": {
            "graph": lcc_graph,
            "image_name": LCC_HUBS_IMG_NAME,
            "seed": lcc_reconstruction_data.get("seed", SEED),
            "node_size": lcc_node_sizes.get("hubs", lcc_node_sizes.get("default", 40)),
            "node_colors": _normalize_colors(lcc_color_partitions.get("hubs")),
            "node_positions": lcc_node_positions,
        },
    }

    for graph_payload in graph_render_plan.values():
        figure = build_graph_figure(
            graph_payload["graph"],
            seed=graph_payload["seed"],
            node_size=graph_payload["node_size"],
            node_colors=graph_payload["node_colors"],
            node_positions=graph_payload["node_positions"],
        )
        save_graph_figure(figure, GRAPH_IMG_PATH / graph_payload["image_name"])

    generate_interactive_graph(lcc_graph, INTERACTIVE_GRAPH_NAME)

    print("Loading graphs completed.")
    return {
        "base_graph": base_graph,
        "lcc_graph": lcc_graph,
        "hypergraph": hypergraph,
    }


if __name__ == "__main__":
    load_graphs()
