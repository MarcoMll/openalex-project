import csv
import json
import networkx as nx

from utils.interactive_graph_converter import generate_interactive_graph
from utils.graph_visualizer import GraphConfig, build_graph_figure, save_graph_figure
from utils.project_paths import get_paths
from Scripts.analytics.community_detection import find_communities, compute_average_community_density
from Scripts.analytics.hub_detection import detect_hubs, compute_average_hub_metric
from Scripts.analytics.metrics.networkx_metrics_calculator import *

P = get_paths()
EDGES_CSV = P.EDGES_CSV
SEED = 777

GRAPH_IMG_PATH = P.IMAGES_DIR
BASE_GRAPH_IMG_NAME = "base_graph.png"
BASE_COMMUNITY_IMG_NAME = "base_graph_community.png"

LCC_IMG_NAME = "largest_connected_component_graph.png"
LCC_COMMUNITY_IMG_NAME = "lcc_community_graph.png"
LCC_HUBS_IMG_NAME = "lcc_hubs_graph.png"

INTERACTIVE_GRAPH_NAME = "interactive_graph.html"
SCHOLARNET_REPORT_JSON_NAME = "scholarnet_report.json"
HARDCODED_METRIC_VALUE = -1

def load_graph_from_edges_csv(path = EDGES_CSV, max_edges: int = -1):
    graph = nx.Graph()
    edges_amount = 0

    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:

            if max_edges != -1 and edges_amount >= max_edges:
                break

            u = row["author_id_1"]
            v = row["author_id_2"]
            w = float(row["weight"])

            graph.add_edge(u, v, weight=w)
            edges_amount += 1

    return graph

def find_largest_connected_component(graph: nx.Graph):
    components = nx.connected_components(graph)

    if graph.number_of_nodes() == 0:
        return None

    biggest_component = max(components, key=len)
    return biggest_component

def get_subgraph_from_component_nodes(graph: nx.Graph, components: set[str]):
    return graph.subgraph(components).copy()

def split_graph_by_color(graph: nx.Graph, partition: dict, custom_colors: list = None):
    node_to_color = {}

    for i, community_name in enumerate(partition):
        for node in partition[community_name]["nodes"]:
            if custom_colors is None:
                node_to_color[node] = i
            else:
                if custom_colors is not None and len(custom_colors) < len(partition):
                    raise ValueError("Not enough colors for all communities.")
                node_to_color[node] = custom_colors[i]

    node_colors = [node_to_color.get(node, -1) for node in graph.nodes()] # safe fallback for color if for some reason node in node_to_color is not in graph.nodes()
    return node_colors

def remove_nodes_from_list(node_ids_to_remove: list, target_list: list):
    temp_list = target_list.copy()

    for node_ref in node_ids_to_remove:
        for node in target_list:
            if node_ref == node:
                temp_list.remove(node)

    return temp_list

def build_graph_stats(
    graph: nx.Graph,
    number_of_communities: int = HARDCODED_METRIC_VALUE,
    number_of_hubs: int = HARDCODED_METRIC_VALUE,
    average_community_density: float = HARDCODED_METRIC_VALUE,
    average_hub_degree: float = HARDCODED_METRIC_VALUE,
):
    average_degree, _ = compute_average_per_node(graph, "degree")
    average_strength, _ = compute_average_per_node(graph, "strength")

    return {
        "total_nodes": graph.number_of_nodes(),
        "average_degree": average_degree,
        "average_strength": average_strength,
        "density": compute_graph_density(graph),
        "weighted_density": compute_graph_weighted_density(graph),
        "average_normalized_strength_of_edges": compute_average_normalized_strength_of_edges(graph),
        "number_of_communities": number_of_communities,
        "number_of_hubs": number_of_hubs,
        "average_community_density": average_community_density,
        "average_hub_degree": average_hub_degree,
    }

def serialize_graph_for_reconstruction(
    graph: nx.Graph,
    seed: int,
    node_sizes: dict,
    communities_colors: list | None = None,
    hubs_colors: list | None = None,
):
    edges = [
        {"u": u, "v": v, "weight": data.get("weight", 1.0)}
        for u, v, data in graph.edges(data=True)
    ]

    return {
        "nodes": list(graph.nodes()),
        "edges": edges,
        "seed": seed,
        "node_sizes": node_sizes,
        "color_partitions": {
            "communities": communities_colors if communities_colors is not None else [],
            "hubs": hubs_colors if hubs_colors is not None else [],
        },
    }

def build_network_graph():
    base_graph = load_graph_from_edges_csv(EDGES_CSV)

    lcc_hubs_metric = "degree"
    lcc_hubs_threshold = 95

    largest_component_nodes = find_largest_connected_component(base_graph)
    lcc_subgraph = get_subgraph_from_component_nodes(base_graph, largest_component_nodes)

    _, lcc_number_of_communities, lcc_partition = find_communities(lcc_subgraph, "Newman")

    lcc_hubs_dict: dict = detect_hubs(lcc_subgraph, lcc_hubs_metric, lcc_hubs_threshold)
    lcc_hubs = list(lcc_hubs_dict.keys())
    nodes_without_hubs = remove_nodes_from_list(lcc_hubs, list(lcc_subgraph.nodes()))

    bg_stats = build_graph_stats(base_graph)
    lcc_stats = build_graph_stats(
        lcc_subgraph,
        number_of_communities=lcc_number_of_communities,
        number_of_hubs=len(lcc_hubs),
        average_community_density=compute_average_community_density(lcc_partition),
        average_hub_degree=compute_average_hub_metric(lcc_hubs_dict)
    )

    scholarnet_report = {
        "base_graph": bg_stats,
        "lcc": lcc_stats,
    }

    final_dict = {
        "ordinary_nodes": {
            "nodes": nodes_without_hubs
        },
        "hubs": {
            "nodes": lcc_hubs
        }
    }

    #base_graph_community_colors = split_graph_by_color(base_graph, find_communities(base_graph, "Newman")[2])

    lcc_community_colors = split_graph_by_color(lcc_subgraph, lcc_partition)
    lcc_hub_colors = split_graph_by_color(lcc_subgraph, final_dict, ["#63C791", "#C76399"])
    scholarnet_report["base_graph"]["reconstruction_data"] = serialize_graph_for_reconstruction(
        base_graph,
        seed=SEED,
        node_sizes={"default": 20},
        communities_colors=[],
        hubs_colors=[],
    )
    scholarnet_report["lcc"]["reconstruction_data"] = serialize_graph_for_reconstruction(
        lcc_subgraph,
        seed=SEED,
        node_sizes={"default": 40, "communities": 40, "hubs": 40},
        communities_colors=lcc_community_colors,
        hubs_colors=lcc_hub_colors,
    )

    analytics_dir = P.DATA / "Analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)
    scholarnet_report_path = analytics_dir / SCHOLARNET_REPORT_JSON_NAME
    with scholarnet_report_path.open("w", encoding="utf-8") as out_file:
        json.dump(scholarnet_report, out_file, ensure_ascii=False, indent=2)

    graph_render_plan = {
        "base_graph": {
            "graph": base_graph,
            "image_name": BASE_GRAPH_IMG_NAME,
            "node_size": 20,
            "node_colors": None,
        },
        "lcc_graph": {
            "graph": lcc_subgraph,
            "image_name": LCC_IMG_NAME,
            "node_size": 40,
            "node_colors": None,
        },
        "lcc_community_graph": {
            "graph": lcc_subgraph,
            "image_name": LCC_COMMUNITY_IMG_NAME,
            "node_size": 40,
            "node_colors": lcc_community_colors,
        },
        "lcc_hubs_graph": {
            "graph": lcc_subgraph,
            "image_name": LCC_HUBS_IMG_NAME,
            "node_size": 40,
            "node_colors": lcc_hub_colors,
        },
    }

    for graph_payload in graph_render_plan.values():
        figure = build_graph_figure(
            graph_payload["graph"],
            graph_config=GraphConfig(seed=SEED, node_size=graph_payload["node_size"]),
            node_colors=graph_payload["node_colors"],
        )
        save_graph_figure(figure, GRAPH_IMG_PATH / graph_payload["image_name"])

    print("Building graphs completed.")

    generate_interactive_graph(lcc_subgraph, INTERACTIVE_GRAPH_NAME) # converting to interactive
    return base_graph, lcc_subgraph

if __name__ == "__main__":
    build_network_graph()
