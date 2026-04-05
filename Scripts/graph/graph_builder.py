# imports
import csv
import networkx as nx

from utils.project_paths import get_paths

P = get_paths()

def build_graph_from_edges(path) -> nx.Graph:
    graph = nx.Graph()

    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:

            u = row["author_id_1"]
            v = row["author_id_2"]
            w = float(row["weight"])

            graph.add_edge(u, v, weight=w)

    return graph

def detect_largest_connected_component_in_graph(graph: nx.Graph, return_subgraph: bool = False):
    components = nx.connected_components(graph)

    if graph.number_of_nodes() == 0:
        return None

    biggest_component = max(components, key=len)

    if return_subgraph:
        return graph.subgraph(biggest_component).copy()

    return biggest_component

def build_network_graphs():
    base_graph = build_graph_from_edges(P.EDGES_CSV)
    lcc_graph = detect_largest_connected_component_in_graph(base_graph, True)

    return base_graph, lcc_graph