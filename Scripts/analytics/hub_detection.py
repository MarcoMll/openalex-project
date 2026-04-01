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

# Allow running this script from project root or from the Scripts directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.project_paths import get_paths

P = get_paths()
DEFAULT_EDGES_PATH = P.EDGES_CSV
DEFAULT_OUT_DIR = P.DERIVED_DIR
NodeId = Hashable


def load_graph_from_edges_csv(path: Path) -> nx.Graph:
    graph = nx.Graph()

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            u = row["author_id_1"]
            v = row["author_id_2"]
            raw_weight = row.get("weight", 1.0)

            try:
                weight = float(raw_weight)
            except (TypeError, ValueError):
                weight = 1.0

            graph.add_edge(u, v, weight=weight)

    return graph


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


def percentile_threshold(values: List[float], percentile: float) -> float:
    if not values:
        return math.inf
    if percentile <= 0:
        return min(values)
    if percentile >= 100:
        return max(values)

    sorted_values = sorted(values)
    # Nearest-rank percentile (simple and stable for reporting).
    rank = math.ceil((percentile / 100) * len(sorted_values)) - 1
    rank = max(0, min(rank, len(sorted_values) - 1))
    return float(sorted_values[rank])


def compute_threshold(values: List[float], method: str, threshold: float) -> float:
    if not values:
        return math.inf

    if method == "percentile":
        return percentile_threshold(values, threshold)

    if method == "zscore":
        mu = statistics.fmean(values)
        sigma = statistics.pstdev(values)
        return mu + (threshold * sigma)

    if method == "iqr":
        q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
        iqr = q3 - q1
        # Tukey-style upper fence with configurable multiplier.
        return q3 + (threshold * iqr)

    raise ValueError(f"Unknown method: {method}")


def _filter_hubs_by_metric(
    metric_by_node: Dict[NodeId, float],
    method: str,
    threshold: float,
) -> Dict[NodeId, float]:
    metric_values = list(metric_by_node.values())
    metric_threshold = compute_threshold(metric_values, method, threshold)

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
    method: str,
    threshold: float,
) -> Dict[NodeId, float]:
    metric_by_node = get_metric_by_node(graph, metric)
    return _filter_hubs_by_metric(metric_by_node, method=method, threshold=threshold)


# function for writing hubs to CSV not sure if we need it now
# def write_hubs_csv(
#     out_path: Path,
#     hubs: Dict[NodeId, float],
#     degrees: Dict[NodeId, int],
#     strengths: Dict[NodeId, float],
#     metric_name: str,
# ) -> None:
#     out_path.parent.mkdir(parents=True, exist_ok=True)
#     with out_path.open("w", encoding="utf-8", newline="") as file:
#         writer = csv.writer(file)
#         writer.writerow(["author_id", "metric", "metric_value", "degree", "strength"])
#         for author_id, metric_value in hubs.items():
#             writer.writerow(
#                 [
#                     author_id,
#                     metric_name,
#                     metric_value,
#                     degrees.get(author_id, 0),
#                     strengths.get(author_id, 0.0),
#                 ]
#             )


def print_preview(title: str, hubs: Dict[NodeId, float], preview_size: int) -> None:
    print(f"\n=== {title} ===")
    print(f"Hub count: {len(hubs)}")
    print(f"Top {min(preview_size, len(hubs))}:")
    for author_id, value in list(hubs.items())[:preview_size]:
        print(f"{author_id} -> {value:.4f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual hub detection from a NetworkX graph.")
    parser.add_argument("--edges-csv", type=Path, default=DEFAULT_EDGES_PATH, help="Path to Data/Derived/edges.csv")
    parser.add_argument("--metric", choices=["degree", "strength"], default="degree")
    parser.add_argument("--method", choices=["percentile", "zscore", "iqr"], default="percentile")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Meaning depends on --method: percentile (0-100), zscore (z value), iqr (IQR multiplier, e.g. 1.5).",
    )
    parser.add_argument("--preview", type=int, default=15, help="How many hubs to print")
    parser.add_argument("--print-dict", action="store_true", help="Print the full final hubs dictionary.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for output CSV files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.threshold is None:
        if args.method == "percentile":
            method_threshold = 95.0
        elif args.method == "zscore":
            method_threshold = 2.0
        else:
            method_threshold = 1.5
    else:
        method_threshold = args.threshold

    graph = load_graph_from_edges_csv(args.edges_csv)
    hubs = detect_hubs(
        graph,
        metric=args.metric,
        method=args.method,
        threshold=method_threshold,
    )

    print(f"Loaded graph from {args.edges_csv}")
    print(f"Nodes: {graph.number_of_nodes()} | Edges: {graph.number_of_edges()}")
    print(f"Metric: {args.metric} | Method: {args.method} | Threshold: {method_threshold}")
    print_preview(f"{args.metric.title()} Hubs", hubs, args.preview)
    if args.print_dict:
        print("\nFinal hubs dictionary:")
        pprint(hubs)

    # CSV output is intentionally disabled for testing.
    # Uncomment this block when you want to persist results.
    # degrees, strengths = get_metrics_from_graph(graph)
    # out_path = args.out_dir / f"hubs_{args.metric}.csv"
    # write_hubs_csv(out_path, hubs, degrees, strengths, args.metric)
    # print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
