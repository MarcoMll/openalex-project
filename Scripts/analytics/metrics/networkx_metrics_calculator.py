from operator import itemgetter

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
    return 2 * number_of_edges / (number_of_nodes * (number_of_nodes - 1)) # D = 2E / [n(n-1)]

def compute_graph_weighted_density(graph: nx.Graph):
    edges = list(graph.edges(data=True)) # [('A', 'B', {'weight': 5}), ('A', 'C', {'weight': 2})]

    sum_of_weights = 0
    max_weight = 0
    for u, v, data in edges:
        weight = data["weight"]
        sum_of_weights += weight
        max_weight = max(max_weight, weight)

    n = graph.number_of_nodes()

    if max_weight == 0:
        raise ValueError("Can't divide by 0: max_weight = 0")

    weighted_density = 2 * sum_of_weights / (n*(n-1)*max_weight) # Dw = (2 * Σw_ij) / [n(n-1) * w_max]
    return weighted_density

def compute_average_normalized_strength_of_edges(graph: nx.Graph):
    density = compute_graph_density(graph)
    weighted_density = compute_graph_weighted_density(graph)

    return weighted_density / density

def get_top_n_degrees(graph: nx.Graph, n: int):
    pairs = graph.degree()
    sorted_pairs = sorted(pairs, key=itemgetter(1), reverse=True)[:n]

    return sorted_pairs

def get_top_n_strenghts(graph: nx.Graph, n: int):
    return sorted(graph.degree(weight="weight"), key=itemgetter(1), reverse=True)[:n]