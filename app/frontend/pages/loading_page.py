import base64
import sys
from pathlib import Path

import streamlit as st

from utils.spritesheet_animation import DEFAULT_FRAME_DURATION_MS, play_spritesheet_animation


def _image_to_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _status_markup(message: str) -> str:
    return f'<div class="loading-status">{message}</div>'


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


def _render_loader(*, pipeline_complete: bool, checkmark_uri: str) -> None:
    complete_class = " is-complete" if pipeline_complete else ""
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


def _run_pipeline(pipeline_config_data: dict, status_placeholder) -> None:
    from Scripts.init_pipeline import PipelineConfig, init_pipeline

    def update_status(message: str) -> None:
        st.session_state["pipeline_status"] = message
        status_placeholder.markdown(_status_markup(message), unsafe_allow_html=True)

    st.session_state["pipeline_started"] = True
    st.session_state["pipeline_error"] = ""
    st.session_state["pipeline_complete"] = False

    pipeline_config = PipelineConfig(
        institution_id=pipeline_config_data["institution_id"],
        api_email=pipeline_config_data["api_email"],
        api_key=pipeline_config_data["api_key"],
    )

    try:
        init_pipeline(pipeline_config, on_status=update_status)
        st.session_state["pipeline_complete"] = True
    except Exception as exc:
        st.session_state["pipeline_error"] = str(exc)


def render_loading_page() -> None:
    app_dir = Path(__file__).resolve().parents[2]
    frontend_dir = Path(__file__).resolve().parents[1]
    project_root = app_dir.parent
    assets_gui_dir = project_root / "Assets" / "gui"

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    pipeline_config_data = st.session_state.get("pipeline_config")
    if not pipeline_config_data:
        st.error("Pipeline config was not found. Please go back and submit the form again.")
        if st.button("Back to welcome"):
            st.session_state["current_page"] = "welcome"
            st.rerun()
        return

    _inject_loader_styles(frontend_dir, project_root)
    pipeline_complete = st.session_state.get("pipeline_complete", False)
    logo_full_uri = _image_to_data_uri(assets_gui_dir / "sn_logo_full_solid_bg.png")
    checkmark_uri = _image_to_data_uri(assets_gui_dir / "checkmark.png")

    _render_loader(pipeline_complete=pipeline_complete, checkmark_uri=checkmark_uri)
    status_placeholder = st.empty()
    current_status = st.session_state.get("pipeline_status", "Ready to start")
    status_placeholder.markdown(_status_markup(current_status), unsafe_allow_html=True)
    _render_footer_logo(logo_full_uri)

    if not st.session_state.get("pipeline_started", False):
        _run_pipeline(pipeline_config_data, status_placeholder)
        st.rerun()

    pipeline_error = st.session_state.get("pipeline_error", "")
    if pipeline_error:
        st.error(f"Pipeline failed: {pipeline_error}")
        if st.button("Back to welcome"):
            st.session_state["current_page"] = "welcome"
            st.rerun()
        return

    if st.session_state.get("pipeline_complete", False):
        _, center_col, _ = st.columns([1, 1.4, 1])
        with center_col:
            if st.button("Go to preview", key="go_to_preview", use_container_width=True):
                st.session_state["current_page"] = "preview"
                st.rerun()
