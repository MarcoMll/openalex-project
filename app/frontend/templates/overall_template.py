from __future__ import annotations

from typing import Any

import streamlit as st
from Scripts.analytics.report_analyzer import (
    explain_average_hyperdegree,
    explain_most_common_group_size,
    explain_overall_connectivity_and_collaboration_intensity,
)
from app.frontend.templates.graph_templates import _characteristics_for_graph


def _to_non_negative_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _resolve_average_strength(lcc_characteristics: dict[str, Any]) -> float | None:
    average_strength = _to_non_negative_float(lcc_characteristics.get("average_strength"))
    if average_strength is not None:
        return average_strength
    return _to_non_negative_float(
        lcc_characteristics.get("average_normalized_strength_of_edges")
    )


def _most_common_group_size(group_size_proportions: Any) -> int | None:
    if not isinstance(group_size_proportions, dict):
        return None

    parsed: list[tuple[int, float]] = []
    for raw_size, raw_share in group_size_proportions.items():
        try:
            size = int(raw_size)
            share = float(raw_share)
        except (TypeError, ValueError):
            continue
        if size < 1 or share < 0:
            continue
        parsed.append((size, share))

    if not parsed:
        return None

    parsed.sort(key=lambda item: (item[1], item[0]), reverse=True)
    return parsed[0][0]


def render_overall_conclusion(title: str) -> None:
    st.subheader(title)
    st.caption("Conclusion generated from `Data/Analytics/scholarnet_report.json` metrics.")

    lcc_characteristics = _characteristics_for_graph("lcc")
    if not isinstance(lcc_characteristics, dict) or not lcc_characteristics:
        st.warning(
            "No LCC analytics found in report. Run the pipeline and serialization first."
        )
        return

    density = _to_non_negative_float(lcc_characteristics.get("density"))
    average_degree = _to_non_negative_float(lcc_characteristics.get("average_degree"))
    average_strength = _resolve_average_strength(lcc_characteristics)
    weighted_density = _to_non_negative_float(lcc_characteristics.get("weighted_density"))

    if None in {density, average_degree, average_strength, weighted_density}:
        st.warning(
            "Not enough metrics to build overall conclusion. "
            "Expected: density, average_degree, average_strength (or average_normalized_strength_of_edges), weighted_density."
        )
        return

    network_conclusion = explain_overall_connectivity_and_collaboration_intensity(
        density=density,
        average_degree=average_degree,
        average_strength_of_edges=average_strength,
        weighted_density=weighted_density,
        include_section_context=False,
    )

    st.markdown("### Conclusion")
    st.write(network_conclusion)

    hypergraph_characteristics = _characteristics_for_graph("hypergraph")
    if not isinstance(hypergraph_characteristics, dict) or not hypergraph_characteristics:
        return

    st.markdown("### Hypergraph Context")

    average_hyperdegree = _to_non_negative_float(
        hypergraph_characteristics.get("average_hyperdegree")
    )
    if average_hyperdegree is None:
        average_hyperdegree = _to_non_negative_float(
            hypergraph_characteristics.get("average_hyper_degree_per_author")
        )
    if average_hyperdegree is not None:
        st.write(explain_average_hyperdegree(average_hyperdegree))

    mode_group_size = _most_common_group_size(
        hypergraph_characteristics.get("group_size_proportions")
    )
    if mode_group_size is not None:
        st.write(explain_most_common_group_size(mode_group_size))
