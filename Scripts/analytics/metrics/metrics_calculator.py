import networkx as nx
from typing import Literal

def compute_average_per_node(graph: nx.Graph, metric: Literal["degree", "strength"]):
    count_dict = {node: 0 for node in graph.nodes()}

    for u, v, data in graph.edges(data=True):
        if metric == "degree":
            count_dict[u] += 1
            count_dict[v] += 1
        elif metric == "strength":
            weight = data.get("weight", 1) # get weight or fallback to 1
            count_dict[u] += weight
            count_dict[v] += weight
        else:
            raise ValueError("metric must be 'degree' or 'strength'")

    return sum(count_dict.values()) / graph.number_of_nodes(), count_dict

def compute_graph_density(graph: nx.Graph):
    number_of_nodes = graph.number_of_nodes()
    number_of_edges = graph.number_of_edges()
    return 2 * number_of_edges / number_of_nodes * (number_of_nodes - 1) # d = 2E / n(n-1)

def compute_graph_weighted_density(graph: nx.Graph):
    edges = list(graph.edges())