import csv
from operator import itemgetter

import networkx as nx

from utils.project_paths import get_paths
import matplotlib.pyplot as plt

P = get_paths()
EDGES_CSV = P.EDGES_CSV
SEED = 777

GRAPH_IMG_PATH = P.IMAGES_DIR / "subgraph.png"

def load_graph_from_edges_csv(path, max_edges: int = -1):
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

def get_top_n_degrees(graph, n):
    pairs = G.degree()
    sorted_pairs = sorted(pairs, key=itemgetter(1), reverse=True)[:n] # this is hardcoded
                                                                      # idk yet how to do it in another way
    return sorted_pairs

# chatgpt made this, I don't really know what is going on here yet
def get_top_n_strenghts(G, n):
    # "strength" = weighted degree (sum of edge weights)
    # NetworkX can compute it directly:
    return sorted(G.degree(weight="weight"), key=itemgetter(1), reverse=True)[:n]

if __name__ == "__main__":
    G = load_graph_from_edges_csv(EDGES_CSV)

    component_nodes = find_biggest_component(G)
    Gc = get_subgraph_from_component_nodes(G, component_nodes)

    print("===== Nodes/edges comparison =====")
    print(f"G:  nodes={G.number_of_nodes()} edges={G.number_of_edges()}")
    print(f"Gc: nodes={Gc.number_of_nodes()} edges={Gc.number_of_edges()}")

    print("===== Components =====")
    print("G components number:", nx.number_connected_components(G))
    print("Biggest component size:", Gc.number_of_nodes())

    print("===== Top-10 degree (Gc) =====")
    for node, deg in get_top_n_degrees(Gc, 10):
        print(node, deg)

    print("===== Top-10 strength (Gc) =====")
    for node, s in get_top_n_strenghts(Gc, 10):
        print(node, s)

    pos = nx.spring_layout(Gc, seed=SEED)
    #nx.draw(Gc, pos=pos, with_labels=False, node_size=40)
    nx.draw_spring(Gc, node_size= 40)

    # saving image
    plt.savefig(GRAPH_IMG_PATH, dpi=300, bbox_inches="tight")

    plt.show()