from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path
from pprint import pprint
from typing import Dict, Hashable, List, Tuple

import networkx as nx

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def get_metrics_from_graph(graph: nx.Graph) -> Tuple[Dict[NodeId, int], Dict[NodeId, float]]:
    # Build degree/strength manually from graph edges.
    adjacency: Dict[NodeId, set[NodeId]] = {node: set() for node in graph.nodes()}
    strengths: Dict[NodeId, float] = {node: 0.0 for node in graph.nodes()}

    for u, v, attrs in graph.edges(data=True):
        if u == v:
            continue

        raw_weight = attrs.get("weight", 1.0)
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            weight = 1.0

        adjacency.setdefault(u, set()).add(v)
        adjacency.setdefault(v, set()).add(u)
        strengths[u] = strengths.get(u, 0.0) + weight
        strengths[v] = strengths.get(v, 0.0) + weight

    degrees = {author_id: len(neighbors) for author_id, neighbors in adjacency.items()}
    return degrees, strengths



def compute_threshold(values: List[float], threshold: float) -> float:
    if not values:
        return math.inf
    if not values:
            return math.inf
    if threshold <= 0:
            return min(values)
    if threshold >= 100:
            return max(values)

    sorted_values = sorted(values)
    # Nearest-rank percentile (simple and stable for reporting).
    rank = math.ceil((threshold / 100) * len(sorted_values)) - 1
    rank = max(0, min(rank, len(sorted_values) - 1))
    return float(sorted_values[rank])


def _filter_hubs_by_metric(
    metric_by_node: Dict[NodeId, float],
    threshold: float,
) -> Dict[NodeId, float]:
    metric_values = list(metric_by_node.values())
    metric_threshold = compute_threshold(metric_values, threshold)

    hub_items = [
        (author_id, value)
        for author_id, value in metric_by_node.items()
        if value >= metric_threshold
    ]
    hub_items.sort(key=lambda x: x[1], reverse=True)

    # dict preserves insertion order, so this keeps the ranked order.
    hubs = {author_id: value for author_id, value in hub_items}
    return hubs


def get_metric_by_node(graph: nx.Graph, metric: str) -> Dict[NodeId, float]:
    degrees, strengths = get_metrics_from_graph(graph)

    if metric == "degree":
        return {author_id: float(degree) for author_id, degree in degrees.items()}

    if metric == "strength":
        return strengths

    raise ValueError(f"Unknown metric: {metric}")


def detect_hubs(
    graph: nx.Graph,
    metric: str,
    threshold: float,
) -> Dict[NodeId, float]:
    metric_by_node = get_metric_by_node(graph, metric)
    return _filter_hubs_by_metric(metric_by_node, threshold=threshold)


def compute_average_hub_metric(hubs: Dict[NodeId, float]):
    if not hubs:
        return 0.0
    return sum(hubs.values()) / len(hubs)

if __name__ == "__main__":
    from Scripts.graph.build_networkx_graph import load_graph_from_edges_csv

    graph = load_graph_from_edges_csv()
    hubs = detect_hubs(
        graph,
        metric="degree",
        threshold=95.0,
    )
    print(hubs)
    print(f"Average hub degree: {compute_average_hub_metric(hubs)}")