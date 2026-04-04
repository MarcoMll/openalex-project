from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx


def _is_hex_color(value: str):
    if not isinstance(value, str):
        return False

    if len(value) not in (7, 9) or not value.startswith("#"):
        return False

    return all(char in "0123456789abcdefABCDEF" for char in value[1:])


def _resolve_graph_draw_style(graph: nx.Graph, node_colors: list | None):
    color_map = None
    draw_kwargs = {}

    if node_colors is None:
        resolved_node_colors = "#63c791"
    elif isinstance(node_colors, list) and all(_is_hex_color(c) for c in node_colors):
        resolved_node_colors = node_colors

        # Matplotlib expects either one color, or one color per node.
        # If user passes a short hex palette, repeat it to match node count.
        if len(resolved_node_colors) == 0:
            raise ValueError("node_colors cannot be an empty hex color list.")
        if len(resolved_node_colors) == 1:
            resolved_node_colors = resolved_node_colors[0]
        elif len(resolved_node_colors) != graph.number_of_nodes():
            palette = resolved_node_colors
            resolved_node_colors = [
                palette[i % len(palette)] for i, _ in enumerate(graph.nodes())
            ]
    else:
        resolved_node_colors = node_colors
        color_map = plt.cm.tab20

        if all(isinstance(c, (int, float)) for c in resolved_node_colors):
            draw_kwargs["vmin"] = 0
            draw_kwargs["vmax"] = 19

    if (
        isinstance(resolved_node_colors, Sequence)
        and not isinstance(resolved_node_colors, (str, bytes))
        and len(resolved_node_colors) not in (1, graph.number_of_nodes())
    ):
        raise ValueError(
            f"node_colors must have length 1 or match graph nodes count ({graph.number_of_nodes()}); "
            f"got {len(resolved_node_colors)}."
        )

    return resolved_node_colors, color_map, draw_kwargs


def build_graph_figure(
    graph: nx.Graph,
    seed: int,
    node_size: int = 40,
    node_colors: list | None = None,
    node_positions: dict | None = None,
    figure_size: tuple[int, int] = (14, 10),
):
    figure = plt.figure(figsize=figure_size)
    if node_positions is None:
        pos = nx.spring_layout(graph, seed=seed)  # deterministic layout
    else:
        missing_nodes = [node for node in graph.nodes() if node not in node_positions]
        if missing_nodes:
            raise ValueError(
                f"node_positions is missing {len(missing_nodes)} graph nodes."
            )
        pos = node_positions

    resolved_node_colors, color_map, draw_kwargs = _resolve_graph_draw_style(
        graph, node_colors
    )

    nx.draw(
        graph,
        pos=pos,
        node_size=node_size,
        node_color=resolved_node_colors,
        cmap=color_map,
        width=0.5,
        with_labels=False,
        **draw_kwargs,
    )

    return figure


def save_graph_figure(figure, out_path: Path, dpi: int = 300):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(figure)  # prevents figures from stacking up
