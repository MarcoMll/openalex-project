from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from app.frontend.templates.graph_templates import (
    _characteristics_for_graph,
    _format_or_minus_one,
    _inject_graph_template_styles,
)


def _get_hypergraph_stats() -> dict[str, str]:
    characteristics = _characteristics_for_graph("hypergraph")

    return {
        "Hyperdensity": "0.42",
        "Average Hyperdegree": _format_or_minus_one(
            characteristics.get("average_hyper_degree_per_author"),
            precision=2,
        ),
    }


def _get_hypergraph_group_size_proportions() -> dict[int, float]:
    characteristics = _characteristics_for_graph("hypergraph")
    raw_proportions = characteristics.get("group_size_proportions", {})

    if not isinstance(raw_proportions, dict):
        return {}

    proportions: dict[int, float] = {}
    for raw_size, raw_value in raw_proportions.items():
        try:
            size = int(raw_size)
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if size < 2 or value < 0:
            continue
        proportions[size] = value

    return proportions


def _get_hypergraph_color_to_group() -> dict[str, str]:
    characteristics = _characteristics_for_graph("hypergraph")
    raw_color_to_group = characteristics.get("color_to_group", {})
    if not isinstance(raw_color_to_group, dict):
        return {}

    color_to_group: dict[str, str] = {}
    for raw_color, raw_group in raw_color_to_group.items():
        if not isinstance(raw_color, str) or not isinstance(raw_group, str):
            continue
        color = raw_color.strip()
        group = raw_group.strip()
        if color and group:
            color_to_group[color] = group

    return color_to_group


def _size_to_color_map(color_to_group: dict[str, str]) -> tuple[dict[int, str], str | None]:
    size_to_color: dict[int, str] = {}
    size_6_plus_color: str | None = None

    for color, group_label in color_to_group.items():
        normalized = group_label.lower()

        if ">=6" in normalized or "6+" in normalized:
            size_6_plus_color = color
            continue

        match = re.search(r"size\s*(\d+)", normalized)
        if not match:
            continue

        size = int(match.group(1))
        if size >= 2:
            size_to_color[size] = color

    return size_to_color, size_6_plus_color


def _size_to_label_map(color_to_group: dict[str, str]) -> tuple[dict[int, str], str | None]:
    size_to_label: dict[int, str] = {}
    size_6_plus_label: str | None = None

    for group_label in color_to_group.values():
        normalized = group_label.lower()

        if ">=6" in normalized or "6+" in normalized:
            size_6_plus_label = group_label
            continue

        match = re.search(r"size\s*(\d+)", normalized)
        if not match:
            continue

        size = int(match.group(1))
        if size >= 2:
            size_to_label[size] = group_label

    return size_to_label, size_6_plus_label


def _colors_for_group_sizes(group_sizes: list[int]) -> list[str]:
    gray_for_two = "#cfd6e0"
    fallback_color = "#63c791"

    color_to_group = _get_hypergraph_color_to_group()
    size_to_color, size_6_plus_color = _size_to_color_map(color_to_group)

    colors: list[str] = []
    for size in group_sizes:
        if size == 2:
            colors.append(gray_for_two)
            continue
        if size in size_to_color:
            colors.append(size_to_color[size])
            continue
        if size >= 6 and size_6_plus_color:
            colors.append(size_6_plus_color)
            continue
        colors.append(fallback_color)

    return colors


def _legend_label_for_size(
    size: int,
    size_to_label: dict[int, str],
    size_6_plus_label: str | None,
) -> str:
    if size == 2:
        return "groups of size 2"
    if size in size_to_label:
        return size_to_label[size]
    if size >= 6 and size_6_plus_label:
        return size_6_plus_label
    return f"groups of size {size}"


def _inject_hypergraph_template_styles() -> None:
    frontend_dir = Path(__file__).resolve().parents[1]
    styles_path = frontend_dir / "styles" / "hypergraph_template.css"
    css = styles_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_hypergraph_summary(title: str) -> None:
    _inject_graph_template_styles()
    stats = _get_hypergraph_stats()

    st.subheader(title)

    cols = st.columns(2, gap="small")
    for idx, (metric_title, metric_value) in enumerate(stats.items()):
        with cols[idx]:
            st.markdown(
                (
                    '<div class="graph-kpi-card">'
                    f'<p class="graph-kpi-title">{metric_title}</p>'
                    f'<p class="graph-kpi-value">{metric_value}</p>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def render_hypergraph_group_size_piechart() -> None:
    group_size_proportions = _get_hypergraph_group_size_proportions()
    if not group_size_proportions:
        return

    import matplotlib.pyplot as plt

    sorted_sizes = sorted(group_size_proportions.keys())
    values = [group_size_proportions[size] for size in sorted_sizes]
    colors = _colors_for_group_sizes(sorted_sizes)
    color_to_group = _get_hypergraph_color_to_group()
    size_to_label, size_6_plus_label = _size_to_label_map(color_to_group)

    st.subheader("Group size proportions")

    fig, ax = plt.subplots(figsize=(5.4, 5.4))
    ax.pie(values, colors=colors, startangle=90, radius=0.92)
    ax.axis("equal")

    left_spacer, chart_col, right_spacer = st.columns([2.6, 2, 2.6])
    with chart_col:
        try:
            st.pyplot(fig, width="stretch")
        except TypeError:
            st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    _inject_hypergraph_template_styles()
    legend_cards = []
    for size, value, color in zip(sorted_sizes, values, colors):
        label = _legend_label_for_size(size, size_to_label, size_6_plus_label)
        legend_cards.append(
            (
                '<div class="hypergraph-legend-card">'
                '<div class="hypergraph-legend-left">'
                f'<span class="hypergraph-legend-swatch" style="background:{color};"></span>'
                f'<span class="hypergraph-legend-label">{label}</span>'
                "</div>"
                f'<span class="hypergraph-legend-value">{value:.2f}%</span>'
                "</div>"
            )
        )
    st.markdown(
        f'<div class="hypergraph-legend-grid">{"".join(legend_cards)}</div>',
        unsafe_allow_html=True,
    )
