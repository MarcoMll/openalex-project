import csv
import networkx as nx
from utils.project_paths import get_paths
import matplotlib.pyplot as plt

P = get_paths()
EDGES_CSV = P.EDGES_CSV

def load_graph_from_edges_csv(path, max_edges: int = -1):
    graph = nx.Graph()
    nodes_amount = 0

    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:

            if max_edges != -1 and nodes_amount >= max_edges:
                break

            u = row["author_id_1"]
            v = row["author_id_2"]
            w = float(row["weight"])

            graph.add_edge(u, v, weight=w)
            nodes_amount += 1

    return graph

edges = [(1, 2, 30), (2, 3, 4), (1, 3, 100), (1, 4, 2), (1, 5, 400), (2, 5, 1), (5, 3, 300), (4, 6, 10),
         (4, 7, 50), (8, 9, 100), (8, 4, 4)]
def create_graph():
    graph = nx.Graph()
    for edge in edges:
        u = edge[0]
        v = edge[1]
        weight = edge[2]
        graph.add_edge(u, v, weight=weight)
    return graph

if __name__ == "__main__":
    G = load_graph_from_edges_csv(EDGES_CSV)
    #G = create_graph()
    print("nodes:", G.number_of_nodes())
    print("edges:", G.number_of_edges())
    print(f"self loops: {nx.number_of_selfloops(G)}")

    nx.draw_spring(G, with_labels=False)
    #print(edges)
    plt.show()