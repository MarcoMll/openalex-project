from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# Allow running this script from project root or from the Scripts directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.project_paths import get_paths

P = get_paths()
DEFAULT_EDGES_PATH = P.EDGES_CSV
DEFAULT_OUT_DIR = P.DERIVED_DIR


def load_metrics_from_edges(path: Path) -> Tuple[Dict[str, int], Dict[str, float]]:
    adjacency: Dict[str, set[str]] = {}
    strengths: Dict[str, float] = {}

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            u = row["author_id_1"]
            v = row["author_id_2"]
            weight = float(row["weight"])

            if u == v:
                continue

            adjacency.setdefault(u, set()).add(v)
            adjacency.setdefault(v, set()).add(u)

            strengths[u] = strengths.get(u, 0.0) + weight
            strengths[v] = strengths.get(v, 0.0) + weight

    degrees = {author_id: len(neighbors) for author_id, neighbors in adjacency.items()}

    for author_id in degrees:
        strengths.setdefault(author_id, 0.0)

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


def compute_threshold(values: List[float], method: str, percentile: float, z_score: float) -> float:
    if not values:
        return math.inf

    if method == "percentile":
        return percentile_threshold(values, percentile)

    if method == "zscore":
        mu = statistics.fmean(values)
        sigma = statistics.pstdev(values)
        return mu + (z_score * sigma)

    if method == "iqr":
        q1, q2, q3 = statistics.quantiles(values, n=4, method="inclusive")
        iqr = q3 - q1
        # Tukey outlier fence.
        return q3 + 1.5 * iqr

    raise ValueError(f"Unknown method: {method}")


def detect_hubs(
    metric_by_node: Dict[str, float],
    method: str,
    percentile: float,
    z_score: float,
) -> Tuple[float, List[Tuple[str, float]]]:
    metric_values = list(metric_by_node.values())
    threshold = compute_threshold(metric_values, method, percentile, z_score)

    hubs = [
        (author_id, value)
        for author_id, value in metric_by_node.items()
        if value >= threshold
    ]
    hubs.sort(key=lambda x: x[1], reverse=True)
    return threshold, hubs

#function for writing hubs to CSV not sure if we need it now
# def write_hubs_csv(
#     out_path: Path,
#     hubs: Iterable[Tuple[str, float]],
#     degrees: Dict[str, int],
#     strengths: Dict[str, float],
#     metric_name: str,
# ) -> None:
#     out_path.parent.mkdir(parents=True, exist_ok=True)
#     with out_path.open("w", encoding="utf-8", newline="") as file:
#         writer = csv.writer(file)
#         writer.writerow(["author_id", "metric", "metric_value", "degree", "strength"])
#         for author_id, metric_value in hubs:
#             writer.writerow(
#                 [
#                     author_id,
#                     metric_name,
#                     metric_value,
#                     degrees.get(author_id, 0),
#                     strengths.get(author_id, 0.0),
#                 ]
#             )


def print_preview(title: str, threshold: float, hubs: List[Tuple[str, float]], preview_size: int) -> None:
    print(f"\n=== {title} ===")
    print(f"Threshold: {threshold:.4f}")
    print(f"Hub count: {len(hubs)}")
    print(f"Top {min(preview_size, len(hubs))}:")
    for author_id, value in hubs[:preview_size]:
        print(f"{author_id} -> {value:.4f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual hub detection from edges.csv (no NetworkX centrality helpers).")
    parser.add_argument("--edges-csv", type=Path, default=DEFAULT_EDGES_PATH, help="Path to Data/Derived/edges.csv")
    parser.add_argument("--method", choices=["percentile", "zscore", "iqr"], default="percentile")
    parser.add_argument("--percentile", type=float, default=95.0, help="Used when method=percentile")
    parser.add_argument("--z", type=float, default=2.0, help="Used when method=zscore")
    parser.add_argument("--preview", type=int, default=15, help="How many hubs to print")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for output CSV files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    degrees, strengths = load_metrics_from_edges(args.edges_csv)

    degree_metric = {k: float(v) for k, v in degrees.items()}
    strength_metric = strengths

    degree_threshold, degree_hubs = detect_hubs(
        degree_metric,
        method=args.method,
        percentile=args.percentile,
        z_score=args.z,
    )
    strength_threshold, strength_hubs = detect_hubs(
        strength_metric,
        method=args.method,
        percentile=args.percentile,
        z_score=args.z,
    )

    print(f"Loaded {len(degrees)} authors from {args.edges_csv}")
    print_preview("Degree Hubs", degree_threshold, degree_hubs, args.preview)
    print_preview("Strength Hubs", strength_threshold, strength_hubs, args.preview)

    # CSV output is intentionally disabled for testing.
    # Uncomment this block when you want to persist results.
    # degree_out = args.out_dir / "hubs_degree.csv"
    # strength_out = args.out_dir / "hubs_strength.csv"
    # write_hubs_csv(degree_out, degree_hubs, degrees, strengths, "degree")
    # write_hubs_csv(strength_out, strength_hubs, degrees, strengths, "strength")
    # print(f"\nSaved: {degree_out}")
    # print(f"Saved: {strength_out}")


if __name__ == "__main__":
    main()
