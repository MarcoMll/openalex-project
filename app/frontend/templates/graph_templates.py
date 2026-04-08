from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


GRAPH_KEY_TO_CHARACTERISTICS_KEY = {
    "original": "base_graph",
    "lcc": "lcc",
}


def _format_metric_value(value: Any, *, precision: int = 2, as_int: bool = False) -> str:
    if as_int:
        return f"{int(value):,}"
    return f"{float(value):.{precision}f}"


def _is_valid_metric_value(value: Any) -> bool:
    if value is None:
        return False
    if not isinstance(value, (int, float)):
        return False
    return value >= 0


def _format_or_minus_one(value: Any, *, precision: int = 2, as_int: bool = False) -> str:
    if not _is_valid_metric_value(value):
        return "-1"
    return _format_metric_value(value, precision=precision, as_int=as_int)


@st.cache_data(show_spinner=False)
def _load_scholarnet_report() -> dict[str, dict[str, Any]]:
    root_dir = Path(__file__).resolve().parents[3]
    json_paths = [root_dir / "Data" / "Analytics" / "scholarnet_report.json"]
    jsonl_paths = [root_dir / "Data" / "Analytics" / "scholarnet_report.jsonl"]

    for json_path in json_paths:
        if not json_path.exists():
            continue

        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except (json.JSONDecodeError, OSError):
            continue

    for jsonl_path in jsonl_paths:
        if not jsonl_path.exists():
            continue

        try:
            merged: dict[str, dict[str, Any]] = {}
            for raw_line in jsonl_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if not isinstance(item, dict):
                    continue

                if len(item) == 1:
                    key, value = next(iter(item.items()))
                    if isinstance(value, dict):
                        merged[str(key)] = value
                        continue

                graph_name = item.get("graph_key") or item.get("graph_name") or item.get("name") or item.get("id")
                if isinstance(graph_name, str):
                    merged[graph_name] = {
                        k: v for k, v in item.items() if k not in {"graph_key", "graph_name", "name", "id"}
                    }

            return merged
        except (json.JSONDecodeError, OSError):
            continue

    return {}


def _characteristics_for_graph(graph_key: str) -> dict[str, Any]:
    stats = _load_scholarnet_report()
    source_key = GRAPH_KEY_TO_CHARACTERISTICS_KEY.get(graph_key, graph_key)
    payload = stats.get(source_key, {})
    if not isinstance(payload, dict):
        return {}

    # New report format stores metrics inside "<graph_key>.graph_analytics".
    # Keep backward compatibility with the old flat format as fallback.
    analytics = payload.get("graph_analytics")
    if isinstance(analytics, dict):
        return analytics

    return payload


def _reconstruction_data_for_graph(graph_key: str) -> dict[str, Any]:
    stats = _load_scholarnet_report()
    source_key = GRAPH_KEY_TO_CHARACTERISTICS_KEY.get(graph_key, graph_key)
    payload = stats.get(source_key, {})
    if not isinstance(payload, dict):
        return {}

    reconstruction_data = payload.get("reconstruction_data")
    if not isinstance(reconstruction_data, dict):
        return {}

    return reconstruction_data


def _get_main_stats(graph_key: str) -> dict[str, str]:
    characteristics = _characteristics_for_graph(graph_key)

    edge_weight_value = characteristics.get("average_edge_weight")
    if not _is_valid_metric_value(edge_weight_value):
        edge_weight_value = characteristics.get("average_normalized_strength_of_edges")

    return {
        "Total Nodes": _format_or_minus_one(characteristics.get("total_nodes"), as_int=True),
        "Average Degree": _format_or_minus_one(characteristics.get("average_degree"), precision=2),
        "Average edge weight": _format_or_minus_one(edge_weight_value, precision=3),
        "Network Density": _format_or_minus_one(characteristics.get("density"), precision=4),
    }


def _get_community_stats(graph_key: str) -> dict[str, str]:
    characteristics = _characteristics_for_graph(graph_key)

    return {
        "Total communities": _format_or_minus_one(characteristics.get("number_of_communities"), as_int=True),
        "Average Community Density": _format_or_minus_one(characteristics.get("average_community_density"), precision=3),
    }


def _get_hubs_stats(graph_key: str) -> dict[str, str]:
    characteristics = _characteristics_for_graph(graph_key)

    return {
        "Total hubs": _format_or_minus_one(characteristics.get("number_of_hubs"), as_int=True),
        "Average Hub Degree": _format_or_minus_one(characteristics.get("average_hub_degree"), precision=2),
    }


def _inject_graph_template_styles() -> None:
    frontend_dir = Path(__file__).resolve().parents[1]
    styles_path = frontend_dir / "styles" / "graph_templates.css"
    css = styles_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_graph_summary(graph_key: str, title: str) -> None:
    _inject_graph_template_styles()
    stats = _get_main_stats(graph_key)

    st.subheader(title)

    cols = st.columns(4, gap="small")
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


def render_community_summary(graph_key: str) -> None:
    _inject_graph_template_styles()
    stats = _get_community_stats(graph_key)

    st.markdown('<hr class="graph-section-divider" />', unsafe_allow_html=True)
    st.subheader("Communities detection")

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


def render_hubs_summary(graph_key: str) -> None:
    _inject_graph_template_styles()
    stats = _get_hubs_stats(graph_key)

    st.markdown('<hr class="graph-section-divider" />', unsafe_allow_html=True)
    st.subheader("Hubs detection")

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
