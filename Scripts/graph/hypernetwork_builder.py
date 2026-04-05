import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

try:
    from utils.project_paths import get_paths
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from utils.project_paths import get_paths

P = get_paths()
HYPEREDGES_PATH = P.HYPEREDGES
IMAGES_DIR = P.IMAGES_DIR

HYPERGRAPH_IMAGE_NAME = "hypergraph_hgx.png"
HYPERGRAPH_NODE_SIZE = 15
HYPERGRAPH_NODE_COLOR = "#63c791"
HYPERGRAPH_EDGE_COLOR = "black"
HYPERGRAPH_EDGE_WIDTH = 0.1
HYPERGRAPH_CLOUD_ALPHA = 0.5
HYPERGRAPH_FIGURE_SIZE = (18, 10)
HYPERGRAPH_X_STRETCH = 1.35
DEFAULT_LAYOUT_SEED = 777
PAIRWISE_EDGE_COLOR = "black"
PAIRWISE_EDGE_WIDTH = 0.2
PAIRWISE_EDGE_ALPHA = 0.1

HYPEREDGE_COLOR_SIZE_3 = "#4DA3FF"
HYPEREDGE_COLOR_SIZE_4 = "#8E44AD"
HYPEREDGE_COLOR_SIZE_5 = "#E6194B" #800000
HYPEREDGE_COLOR_SIZE_6_PLUS = "#E6194B" #F58231

def load_hyperedges(path: Path):
    hyperedges = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            row = json.loads(line)
            author_ids = row.get("institution_author_ids", [])

            if not isinstance(author_ids, list):
                continue

            # Remove duplicates while keeping original order.
            seen = set()
            clean_authors = []
            for author_id in author_ids:
                if isinstance(author_id, str) and author_id and author_id not in seen:
                    seen.add(author_id)
                    clean_authors.append(author_id)

            # A hyperedge with fewer than 2 nodes is not useful here.
            if len(clean_authors) < 2:
                continue

            hyperedges.append(tuple(clean_authors))

    return hyperedges

def filter_hyperedges_by_nodes(hyperedges: list[tuple], allowed_nodes: set[str]):
    filtered_hyperedges = []

    for hyperedge in hyperedges:
        filtered_nodes = tuple(node for node in hyperedge if node in allowed_nodes)
        if len(filtered_nodes) >= 2:
            filtered_hyperedges.append(filtered_nodes)

    return filtered_hyperedges

def stretch_positions_horizontally(
    node_positions: dict[str, tuple[float, float]] | None,
    x_factor: float,
):
    if node_positions is None:
        return None

    return {
        node: (coords[0] * x_factor, coords[1])
        for node, coords in node_positions.items()
    }


def _get_hyperedge_category(size: int):
    if size <= 2:
        return None
    if size == 3:
        return "size_3"
    if size == 4:
        return "size_4"
    if size == 5:
        return "size_5"
    return "size_6_plus"


def build_hyperedge_color_maps(hyperedges: list[tuple]):
    border_colors = {}
    fill_colors = {}
    color_to_group = {}

    color_for_category = {
        "size_3": HYPEREDGE_COLOR_SIZE_3,
        "size_4": HYPEREDGE_COLOR_SIZE_4,
        "size_5": HYPEREDGE_COLOR_SIZE_5,
        "size_6_plus": HYPEREDGE_COLOR_SIZE_6_PLUS,
    }
    group_label_for_category = {
        "size_3": "groups of size 3",
        "size_4": "groups of size 4",
        "size_5": "groups of size 5",
        "size_6_plus": "groups of size 6+",
    }

    unique_sizes = sorted({len(hyperedge) for hyperedge in hyperedges})
    for size in unique_sizes:
        category = _get_hyperedge_category(size)
        if category is None:
            continue
        order = size - 1  # HGX keys color maps by hyperedge order (= size - 1)
        border_colors[order] = color_for_category[category]
        fill_colors[order] = color_for_category[category]
        color_to_group[color_for_category[category]] = group_label_for_category[category]

    return border_colors, fill_colors, color_to_group


def build_hypergraph(hyperedges: list[tuple]):
    from hypergraphx.core.hypergraph import Hypergraph

    return Hypergraph(edge_list=hyperedges)

def save_hypergraph_images(
    hypergraph,
    hyperedges: list[tuple],
    images_dir: Path,
    node_positions: dict | None = None,
    pairwise_edges: list[tuple[str, str]] | None = None,
) -> dict[str, str]:
    from hypergraphx.viz.draw_hypergraph import draw_hypergraph

    images_dir.mkdir(parents=True, exist_ok=True)

    stretched_positions = stretch_positions_horizontally(
        node_positions,
        HYPERGRAPH_X_STRETCH,
    )

    draw_kwargs = {}
    if stretched_positions is not None:
        # Use the same node coordinates as the existing LCC networkx graph.
        hypergraph_nodes = list(hypergraph.get_nodes())
        positions_for_hypergraph = {
            node: stretched_positions[node]
            for node in hypergraph_nodes
            if node in stretched_positions
        }
        if len(positions_for_hypergraph) == len(hypergraph_nodes):
            draw_kwargs["pos"] = positions_for_hypergraph

    hyperedge_color_by_order, hyperedge_facecolor_by_order, color_to_group = (
        build_hyperedge_color_maps(hyperedges)
    )

    plt.figure(figsize=HYPERGRAPH_FIGURE_SIZE)
    draw_hypergraph(
        hypergraph,
        node_size=HYPERGRAPH_NODE_SIZE,
        node_color=HYPERGRAPH_NODE_COLOR,
        node_facecolor=HYPERGRAPH_NODE_COLOR,
        edge_color=HYPERGRAPH_EDGE_COLOR,
        hyperedge_color_by_order=hyperedge_color_by_order,
        hyperedge_facecolor_by_order=hyperedge_facecolor_by_order,
        edge_width=HYPERGRAPH_EDGE_WIDTH,
        hyperedge_alpha=HYPERGRAPH_CLOUD_ALPHA,
        **draw_kwargs,
    )

    if stretched_positions is not None and pairwise_edges:
        # Overlay classic pairwise edges so all LCC edges stay visible.
        overlay_graph = nx.Graph()
        overlay_graph.add_nodes_from(hypergraph.get_nodes())
        overlay_graph.add_edges_from(pairwise_edges)
        nx.draw_networkx_edges(
            overlay_graph,
            pos=stretched_positions,
            edge_color=PAIRWISE_EDGE_COLOR,
            width=PAIRWISE_EDGE_WIDTH,
            alpha=PAIRWISE_EDGE_ALPHA,
        )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(images_dir / HYPERGRAPH_IMAGE_NAME, dpi=300, bbox_inches="tight", pad_inches=0)
    plt.close()
    return color_to_group


def build_hypergraphx_graph(
    graph: nx.Graph,
    return_color_groups: bool = False,
    layout_seed: int = DEFAULT_LAYOUT_SEED,
):
    if not isinstance(graph, nx.Graph):
        raise TypeError("build_hypergraphx_graph expects an input nx.Graph as lcc_graph.")

    if graph.number_of_nodes() == 0:
        print("LCC graph is empty.")
        return None

    hyperedges = load_hyperedges(HYPEREDGES_PATH)
    lcc_nodes = set(graph.nodes())
    lcc_positions = nx.spring_layout(graph, seed=layout_seed)
    lcc_pairwise_edges = list(graph.edges())
    lcc_hyperedges = filter_hyperedges_by_nodes(hyperedges, lcc_nodes)

    if len(lcc_hyperedges) == 0:
        print("No hyperedges found for LCC.")
        return None

    hypergraph = build_hypergraph(lcc_hyperedges)
    color_to_group = save_hypergraph_images(
        hypergraph,
        lcc_hyperedges,
        IMAGES_DIR,
        node_positions=lcc_positions,
        pairwise_edges=lcc_pairwise_edges,
    )
    print("HGX LCC hypergraph image created.")
    if return_color_groups:
        return hypergraph, color_to_group

    return hypergraph