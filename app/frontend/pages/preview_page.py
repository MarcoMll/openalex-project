from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st
from app.frontend.templates.graph_templates import (
    render_community_summary,
    render_graph_summary,
    render_hubs_summary,
)
from app.frontend.templates.hypergraph_template import (
    render_hypergraph_group_size_piechart,
    render_hypergraph_summary,
)
from app.frontend.templates.interactive_environment_template import render_interactive_environment
from app.frontend.templates.overall_template import render_overall_conclusion


ROOT_DIR = Path(__file__).resolve().parents[3]
GUI_DIR = ROOT_DIR / "Assets" / "gui"
IMAGES_DIR = ROOT_DIR / "Assets" / "Images"
GRAPHS_DIR = ROOT_DIR / "Assets" / "Graphs"
SCHOLARNET_REPORT_PATH = ROOT_DIR / "Data" / "Analytics" / "scholarnet_report.json"
INTERACTIVE_GRAPH_HTML_PATH = GRAPHS_DIR / "interactive_graph.html"

NAV_ITEMS = [
    ("original", "original_graph_icon.png", "Original graph"),
    ("lcc", "lcc_icon.png", "Largest Connected Component graph"),
    ("hypergraph", "meshes_icon.png", "Hypergraph"),
    # In repository this icon is named analytics_icon.png.
    ("overall", "analytics_icon.png", "Overall"),
    ("interactive", "interactive_icon.png", "Interactive Environment"),
]

GRAPH_IMAGES = {
    "original": IMAGES_DIR / "base_graph.png",
    "lcc": IMAGES_DIR / "largest_connected_component_graph.png",
}

COMMUNITY_GRAPH_IMAGES = {
    "original": IMAGES_DIR / "original_community_graph.png",
    "lcc": IMAGES_DIR / "lcc_community_graph.png",
}

HUBS_GRAPH_IMAGES = {
    "original": IMAGES_DIR / "original_hubs_graph.png",
    "lcc": IMAGES_DIR / "lcc_hubs_graph.png",
}

HYPERGRAPH_IMAGE_PATH = IMAGES_DIR / "hypergraph_hgx.png"


def _resolve_report_path() -> Path | None:
    if SCHOLARNET_REPORT_PATH.exists():
        return SCHOLARNET_REPORT_PATH
    return None


def _to_data_uri(image_path: Path) -> str:
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    suffix = image_path.suffix.lower().replace(".", "") or "png"
    mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
    return f"data:image/{mime};base64,{encoded}"


def _resolve_icon_path(primary_name: str, fallback_name: str) -> Path:
    primary_path = GUI_DIR / primary_name
    if primary_path.exists():
        return primary_path
    return GUI_DIR / fallback_name


def _load_preview_css(
    styles_path: Path,
    original_icon_uri: str,
    lcc_icon_uri: str,
    hypergraph_icon_uri: str,
    analytics_icon_uri: str,
    interactive_icon_uri: str,
    export_report_icon_uri: str,
) -> str:
    css = styles_path.read_text(encoding="utf-8")
    return (
        css.replace("__ORIGINAL_ICON_URI__", original_icon_uri)
        .replace("__LCC_ICON_URI__", lcc_icon_uri)
        .replace("__HYPERGRAPH_ICON_URI__", hypergraph_icon_uri)
        .replace("__ANALYTICS_ICON_URI__", analytics_icon_uri)
        .replace("__INTERACTIVE_ICON_URI__", interactive_icon_uri)
        .replace("__EXPORT_REPORT_ICON_URI__", export_report_icon_uri)
    )


def render_preview_page() -> None:
    if "preview_nav" not in st.session_state:
        st.session_state["preview_nav"] = "original"

    selected = st.session_state["preview_nav"]
    if selected not in {item[0] for item in NAV_ITEMS}:
        selected = "original"
        st.session_state["preview_nav"] = selected

    frontend_dir = Path(__file__).resolve().parents[1]
    original_icon_uri = _to_data_uri(GUI_DIR / "original_graph_icon.png")
    lcc_icon_uri = _to_data_uri(GUI_DIR / "lcc_icon.png")
    hypergraph_icon_uri = _to_data_uri(GUI_DIR / "meshes_icon.png")
    analytics_icon_uri = _to_data_uri(GUI_DIR / "analytics_icon.png")
    interactive_icon_uri = _to_data_uri(_resolve_icon_path("interactive_icon.png", "analytics_icon.png"))
    export_report_icon_uri = _to_data_uri(GUI_DIR / "export_report_icon.png")
    styles_path = frontend_dir / "styles" / "preview.css"
    css = _load_preview_css(
        styles_path=styles_path,
        original_icon_uri=original_icon_uri,
        lcc_icon_uri=lcc_icon_uri,
        hypergraph_icon_uri=hypergraph_icon_uri,
        analytics_icon_uri=analytics_icon_uri,
        interactive_icon_uri=interactive_icon_uri,
        export_report_icon_uri=export_report_icon_uri,
    )

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <style>
        .st-key-nav_{selected} button {{
            background-color: #63c791 !important;
            color: #ffffff !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.25, 3.2], gap="large")

    with left_col:
        st.markdown('<div class="preview-nav">', unsafe_allow_html=True)
        st.markdown('<p class="preview-nav-title">Navigation</p>', unsafe_allow_html=True)
        for key, _, label in NAV_ITEMS:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state["preview_nav"] = key
                st.rerun()
        report_path = _resolve_report_path()
        report_bytes = report_path.read_bytes() if report_path else None
        st.download_button(
            label="Export Report",
            data=report_bytes if report_bytes is not None else b"",
            file_name="scholarnet_report.json",
            mime="application/json",
            key="nav_export_report",
            use_container_width=True,
            disabled=report_bytes is None,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="preview-content">', unsafe_allow_html=True)
        selected_label = next((label for key, _, label in NAV_ITEMS if key == selected), "Original graph")
        if selected in {"original", "lcc"}:
            render_graph_summary(graph_key=selected, title=selected_label)
            graph_image_path = GRAPH_IMAGES.get(selected)
            if graph_image_path and graph_image_path.exists():
                st.image(str(graph_image_path), use_container_width=True)
            else:
                st.warning(f"Graph image not found: {graph_image_path}")

            community_graph_image_path = COMMUNITY_GRAPH_IMAGES.get(selected)
            if community_graph_image_path and community_graph_image_path.exists():
                render_community_summary(graph_key=selected)
                st.image(str(community_graph_image_path), use_container_width=True)

            hubs_graph_image_path = HUBS_GRAPH_IMAGES.get(selected)
            if hubs_graph_image_path and hubs_graph_image_path.exists():
                render_hubs_summary(graph_key=selected)
                st.image(str(hubs_graph_image_path), use_container_width=True)
        elif selected == "hypergraph":
            render_hypergraph_summary(title=selected_label)
            if HYPERGRAPH_IMAGE_PATH.exists():
                st.image(str(HYPERGRAPH_IMAGE_PATH), use_container_width=True)
            else:
                st.warning(f"Hypergraph image not found: {HYPERGRAPH_IMAGE_PATH}")
            render_hypergraph_group_size_piechart()
        elif selected == "interactive":
            render_interactive_environment(
                title=selected_label,
                graph_html_path=INTERACTIVE_GRAPH_HTML_PATH,
            )
        else:
            render_overall_conclusion(title=selected_label)
        if st.button("Back to welcome"):
            st.session_state["current_page"] = "welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
