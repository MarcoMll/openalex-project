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
        SCHOLARNET_REPORT_JSON_NAME,
        SEED,
        save_graph_image,
    )
    from utils.project_paths import get_paths
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
        SCHOLARNET_REPORT_JSON_NAME,
        SEED,
        save_graph_image,
    )
    from utils.project_paths import get_paths

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


def load_graphs():
    scholarnet_report = _load_scholarnet_report()

    base_reconstruction_data = _require_reconstruction_data(scholarnet_report, "base_graph")
    lcc_reconstruction_data = _require_reconstruction_data(scholarnet_report, "lcc")

    base_graph = _reconstruct_graph(base_reconstruction_data)
    lcc_graph = _reconstruct_graph(lcc_reconstruction_data)

    base_node_sizes = base_reconstruction_data.get("node_sizes", {})
    lcc_node_sizes = lcc_reconstruction_data.get("node_sizes", {})
    lcc_color_partitions = lcc_reconstruction_data.get("color_partitions", {})

    graph_render_plan = {
        "base_graph": {
            "graph": base_graph,
            "image_name": BASE_GRAPH_IMG_NAME,
            "seed": base_reconstruction_data.get("seed", SEED),
            "node_size": base_node_sizes.get("default", 20),
            "node_colors": None,
        },
        "lcc_graph": {
            "graph": lcc_graph,
            "image_name": LCC_IMG_NAME,
            "seed": lcc_reconstruction_data.get("seed", SEED),
            "node_size": lcc_node_sizes.get("default", 40),
            "node_colors": None,
        },
        "lcc_community_graph": {
            "graph": lcc_graph,
            "image_name": LCC_COMMUNITY_IMG_NAME,
            "seed": lcc_reconstruction_data.get("seed", SEED),
            "node_size": lcc_node_sizes.get("communities", lcc_node_sizes.get("default", 40)),
            "node_colors": _normalize_colors(lcc_color_partitions.get("communities")),
        },
        "lcc_hubs_graph": {
            "graph": lcc_graph,
            "image_name": LCC_HUBS_IMG_NAME,
            "seed": lcc_reconstruction_data.get("seed", SEED),
            "node_size": lcc_node_sizes.get("hubs", lcc_node_sizes.get("default", 40)),
            "node_colors": _normalize_colors(lcc_color_partitions.get("hubs")),
        },
    }

    for graph_payload in graph_render_plan.values():
        save_graph_image(
            graph_payload["graph"],
            GRAPH_IMG_PATH / graph_payload["image_name"],
            seed=graph_payload["seed"],
            node_size=graph_payload["node_size"],
            node_colors=graph_payload["node_colors"],
        )

    print("Loading graphs completed.")
    return {
        "base_graph": base_graph,
        "lcc_graph": lcc_graph,
    }


if __name__ == "__main__":
    load_graphs()
