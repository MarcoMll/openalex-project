from __future__ import annotations

from pathlib import Path

import streamlit as st
from utils.hypergraph_config import HypergraphConfig

from app.frontend.templates.graph_templates import (
    _characteristics_for_graph,
    _format_or_minus_one,
    _inject_graph_template_styles,
    _reconstruction_data_for_graph,
)


def _get_hypergraph_stats() -> dict[str, str]:
    characteristics = _characteristics_for_graph("hypergraph")
    average_hyperdegree = characteristics.get("average_hyperdegree")
    if average_hyperdegree is None:
        average_hyperdegree = characteristics.get("average_hyper_degree_per_author")

    return {
        "Hyperdensity": "0.42",
        "Average Hyperdegree": _format_or_minus_one(
            average_hyperdegree,
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


def _get_hypergraph_config() -> HypergraphConfig:
    reconstruction_data = _reconstruction_data_for_graph("hypergraph")
    raw_hypergraph_config = reconstruction_data.get("hypergraph_config")
    try:
        return HypergraphConfig.from_dict(raw_hypergraph_config)
    except ValueError:
        return HypergraphConfig()


def _colors_for_group_sizes(group_sizes: list[int], config: HypergraphConfig) -> list[str]:
    return [config.color_for_group_size(size) for size in group_sizes]


def _legend_label_for_size(size: int, config: HypergraphConfig) -> str:
    return config.label_for_group_size(size)


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

    hypergraph_config = _get_hypergraph_config()
    sorted_sizes = sorted(group_size_proportions.keys())
    values = [group_size_proportions[size] for size in sorted_sizes]
    colors = _colors_for_group_sizes(sorted_sizes, hypergraph_config)

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
        label = _legend_label_for_size(size, hypergraph_config)
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
