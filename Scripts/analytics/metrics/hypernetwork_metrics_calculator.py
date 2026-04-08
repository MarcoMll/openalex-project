from collections import Counter
from collections.abc import Iterable
from typing import Any


def extract_hyperedges(hypergraph: Any) -> list[tuple[Any, ...]]:
    if hypergraph is None:
        return []

    candidates: Any

    get_edges = getattr(hypergraph, "get_edges", None)
    if callable(get_edges):
        candidates = get_edges()
    elif isinstance(hypergraph, dict):
        candidates = hypergraph.keys()
    elif isinstance(hypergraph, Iterable) and not isinstance(hypergraph, (str, bytes)):
        candidates = hypergraph
    else:
        edge_list = getattr(hypergraph, "edge_list", None)
        if edge_list is not None:
            candidates = edge_list
        else:
            raise TypeError(
                "Unsupported hypergraph input. Expected an object with get_edges(), "
                "an iterable of hyperedges, or a dict keyed by hyperedges."
            )

    hyperedges: list[tuple[Any, ...]] = []
    for edge in candidates:
        if isinstance(edge, dict):
            nodes = tuple(edge.keys())
        elif isinstance(edge, Iterable) and not isinstance(edge, (str, bytes)):
            nodes = tuple(edge)
        else:
            continue

        if len(nodes) >= 2:
            hyperedges.append(nodes)

    return hyperedges
    # [('A', 'B', 'C'), ('D', 'E'), ('X', 'Y', 'Z')]

def compute_group_size_proportions(
    hypergraph: Any,
    as_percentage: bool = True,
    precision: int = 2,
) -> dict[int, float]:
    """Return the distribution of group sizes in a hypergraph.

    Example output with ``as_percentage=True``:
    {2: 30.0, 3: 20.0, 4: 50.0}
    """
    hyperedges = extract_hyperedges(hypergraph)
    if len(hyperedges) == 0:
        return {}

    size_counts = Counter(len(edge) for edge in hyperedges)
    total_groups = sum(size_counts.values())
    if total_groups == 0:
        return {}

    scale = 100.0 if as_percentage else 1.0

    return {
        size: round((count / total_groups) * scale, precision)
        for size, count in sorted(size_counts.items())
    }


def compute_average_hyper_degree_per_author(
    hypergraph: Any,
    precision: int = 2,
) -> float:
    """Return the average number of groups each author belongs to."""
    hyperedges = extract_hyperedges(hypergraph)
    if len(hyperedges) == 0:
        return 0.0

    author_group_counts: Counter[Any] = Counter()
    for hyperedge in hyperedges:
        # Count an author once per group even if duplicates appear in an edge.
        for author in set(hyperedge):
            author_group_counts[author] += 1

    if len(author_group_counts) == 0:
        return 0.0

    average_hyper_degree = sum(author_group_counts.values()) / len(author_group_counts)
    return round(average_hyper_degree, precision)
