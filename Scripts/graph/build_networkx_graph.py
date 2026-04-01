import csv
from operator import itemgetter
import networkx as nx
import matplotlib.pyplot as plt
from utils.project_paths import get_paths
from Scripts.analytics.community_detection import find_communities
from Scripts.analytics.hub_detection import detect_hubs

P = get_paths()
EDGES_CSV = P.EDGES_CSV
SEED = 777

GRAPH_IMG_PATH = P.IMAGES_DIR
ORIGINAL_GRAPH_IMG_NAME = "original_graph.png"
SUBGRAPH_IMG_NAME = "subgraph.png"
COMMUNITY_SUBGRAPH_IMG_NAME = "community_subgraph.png"
HUBS_SUBGRAPH_IMG_NAME = "hubs_subgraph.png"
INTERACTIVE_GRAPH_NAME = "interactive_graph.html"

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

def find_biggest_component(graph: nx.Graph):
    components = nx.connected_components(graph)

    if graph.number_of_nodes() == 0:
        return None

    biggest_component = max(components, key=len)
    return biggest_component

def get_subgraph_from_component_nodes(graph: nx.Graph, components: set[str]):
    return graph.subgraph(components).copy()

def get_top_n_degrees(graph: nx.Graph, n: int):
    pairs = graph.degree()
    sorted_pairs = sorted(pairs, key=itemgetter(1), reverse=True)[:n] # this is hardcoded
                                                                      # idk yet how to do it in another way
    return sorted_pairs

# chatgpt made this, I don't really know what is going on here yet
def get_top_n_strenghts(graph: nx.Graph, n: int):
    # "strength" = weighted degree (sum of edge weights)
    # NetworkX can compute it directly:
    return sorted(graph.degree(weight="weight"), key=itemgetter(1), reverse=True)[:n]

def save_graph_image(graph: nx.Graph, out_path, seed: int = SEED, node_size: int = 40, node_colors: list = None):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(graph, seed=seed)  # deterministic layout

    color_map = None
    draw_kwargs = {}
    if node_colors is not None:
        color_map = plt.cm.tab20
        # Treat numeric values as explicit tab20 indexes (0..19) instead of
        # normalizing only by current min/max values (e.g. [0, 6] -> [0, 1]).
        if all(isinstance(c, (int, float)) for c in node_colors):
            draw_kwargs["vmin"] = 0
            draw_kwargs["vmax"] = 19

    nx.draw(
        graph,
        pos=pos,
        node_size=node_size,
        node_color=node_colors,
        cmap=color_map,
        width=0.5,
        with_labels=False,
        **draw_kwargs,
    )
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()  # prevents figures from stacking up

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

def build_network_graph():
    G = load_graph_from_edges_csv(EDGES_CSV)

    component_nodes = find_biggest_component(G)
    Gc = get_subgraph_from_component_nodes(G, component_nodes)
    Gc_community_colors = split_graph_by_color(Gc, find_communities(Gc, "Newman")[2])

    Gc_hubs = detect_hubs(Gc, "degree", 95)

    hubs_list = []
    for key, value in Gc_hubs.items():
        hubs_list.append(key)

    nodes_list = list(Gc.nodes())
    nodes_list = remove_nodes_from_list(hubs_list, nodes_list)

    final_dict = {
        "nodes_partition": {
            "nodes": nodes_list
        },
        "hubs_partition": {
            "nodes": hubs_list
        }
    }

    Gc_hubs_colors = split_graph_by_color(Gc, final_dict, [0, 6])

    save_graph_image(G, GRAPH_IMG_PATH / ORIGINAL_GRAPH_IMG_NAME, seed=SEED, node_size=20)
    save_graph_image(Gc, GRAPH_IMG_PATH / SUBGRAPH_IMG_NAME, seed=SEED, node_size=40)
    save_graph_image(Gc, GRAPH_IMG_PATH / COMMUNITY_SUBGRAPH_IMG_NAME, seed=SEED,
                     node_size=40, node_colors=Gc_community_colors)
    save_graph_image(Gc, GRAPH_IMG_PATH / HUBS_SUBGRAPH_IMG_NAME, seed=SEED,
                     node_size=40, node_colors=Gc_hubs_colors)

    print("Building network graph is done.")

    # generate_interactive_graph(Gc, INTERACTIVE_GRAPH_NAME) # converting to interactive

#if __name__ == "__main__":
