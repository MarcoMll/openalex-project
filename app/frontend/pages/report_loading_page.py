import base64
import sys
from pathlib import Path

import streamlit as st

from utils.spritesheet_animation import play_spritesheet_animation


ROOT_DIR = Path(__file__).resolve().parents[3]
SCHOLARNET_REPORT_PATH = ROOT_DIR / "Data" / "Analytics" / "scholarnet_report.json"


def _image_to_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _inject_loader_styles(frontend_dir: Path, project_root: Path) -> None:
    styles_path = frontend_dir / "styles" / "loading.css"
    loading_css = styles_path.read_text(encoding="utf-8")

    spritesheet_path = project_root / "Assets" / "gui" / "bar_chart_animation_spritesheet.png"
    spritesheet_css = play_spritesheet_animation(
        spritesheet=spritesheet_path,
        px=640,
        speed=10,
        class_name=".sprite-bar-chart",
        display_size_px=44,
    )
    st.markdown(f"<style>{loading_css}\n{spritesheet_css}</style>", unsafe_allow_html=True)


def _render_loader(*, build_complete: bool, checkmark_uri: str) -> None:
    complete_class = " is-complete" if build_complete else ""
    st.markdown(
        f"""
        <div class="loading-layout">
            <div class="loading-center">
                <div class="loader-switcher{complete_class}">
                    <div class="loader-breathe-wrap" aria-hidden="true">
                        <div class="insight-loader" aria-label="Loading">
                            <div class="loader-ring-track"></div>
                            <div class="loader-ring-progress"></div>
                            <div class="loader-core">
                                <div class="sprite-bar-chart" aria-hidden="true"></div>
                            </div>
                        </div>
                    </div>
                    <img class="loader-checkmark" src="{checkmark_uri}" alt="Completed" />
                </div>
            </div>
            <div class="loading-title">Preparing your report</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_footer_logo(logo_uri: str) -> None:
    st.markdown(
        f"""
        <div class="loading-footer-logo-wrap">
            <img class="loading-footer-logo" src="{logo_uri}" alt="SN Logo" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def _run_report_reconstruction(report_bytes: bytes) -> None:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))

    from Scripts.graph.load_graphs import load_graphs

    st.session_state["report_loading_started"] = True
    st.session_state["report_loading_error"] = ""
    st.session_state["report_loading_complete"] = False

    try:
        SCHOLARNET_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCHOLARNET_REPORT_PATH.write_bytes(report_bytes)
        st.cache_data.clear()
        load_graphs()
        st.cache_data.clear()
        st.session_state["report_loading_complete"] = True
    except Exception as exc:
        st.session_state["report_loading_error"] = str(exc)


def render_report_loading_page() -> None:
    app_dir = Path(__file__).resolve().parents[2]
    frontend_dir = Path(__file__).resolve().parents[1]
    project_root = app_dir.parent
    assets_gui_dir = project_root / "Assets" / "gui"

    report_bytes = st.session_state.get("report_json_bytes")
    if not report_bytes:
        st.error("Report file was not found in session. Please upload it again.")
        if st.button("Back to welcome"):
            st.session_state["current_page"] = "welcome"
            st.rerun()
        return

    _inject_loader_styles(frontend_dir, project_root)
    build_complete = st.session_state.get("report_loading_complete", False)
    logo_full_uri = _image_to_data_uri(assets_gui_dir / "sn_logo_full_solid_bg.png")
    checkmark_uri = _image_to_data_uri(assets_gui_dir / "checkmark.png")

    _render_loader(build_complete=build_complete, checkmark_uri=checkmark_uri)
    _render_footer_logo(logo_full_uri)

    if not st.session_state.get("report_loading_started", False):
        _run_report_reconstruction(report_bytes)
        st.rerun()

    loading_error = st.session_state.get("report_loading_error", "")
    if loading_error:
        st.error(f"Report loading failed: {loading_error}")
        if st.button("Back to welcome"):
            st.session_state["current_page"] = "welcome"
            st.rerun()
        return

    if st.session_state.get("report_loading_complete", False):
        _, center_col, _ = st.columns([1, 1.4, 1])
        with center_col:
            if st.button("Go to preview", key="go_to_preview", use_container_width=True):
                st.session_state["current_page"] = "preview"
                st.rerun()
