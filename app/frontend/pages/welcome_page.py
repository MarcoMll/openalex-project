import base64
import json
from pathlib import Path

import streamlit as st


KICKER_FONT_SIZE_PX = 16
KICKER_FONT_WEIGHT = 300
TITLE_FONT_SIZE_PX = 24
TITLE_FONT_WEIGHT = 550


def _image_to_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    suffix = path.suffix.lower()
    if suffix == ".png":
        return f"data:image/png;base64,{encoded}"
    return f"data:image/jpeg;base64,{encoded}"


def _load_welcome_css(styles_path: Path, gradient_uri: str) -> str:
    css = styles_path.read_text(encoding="utf-8")
    return (
        css.replace("__GRADIENT_URI__", gradient_uri)
        .replace("__KICKER_FONT_SIZE_PX__", str(KICKER_FONT_SIZE_PX))
        .replace("__KICKER_FONT_WEIGHT__", str(KICKER_FONT_WEIGHT))
        .replace("__TITLE_FONT_SIZE_PX__", str(TITLE_FONT_SIZE_PX))
        .replace("__TITLE_FONT_WEIGHT__", str(TITLE_FONT_WEIGHT))
    )


def render_welcome_page() -> None:
    app_dir = Path(__file__).resolve().parents[2]
    frontend_dir = Path(__file__).resolve().parents[1]
    project_root = app_dir.parent

    assets_gui_dir = project_root / "Assets" / "gui"
    gradient_path = assets_gui_dir / "gradient-2.jpg"
    logo_path = assets_gui_dir / "sn_logo.png"
    styles_path = frontend_dir / "styles" / "welcome.css"

    gradient_uri = _image_to_data_uri(gradient_path)
    logo_uri = _image_to_data_uri(logo_path)
    css = _load_welcome_css(styles_path=styles_path, gradient_uri=gradient_uri)

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown(
            f"""
            <div class="gradient-card">
                <img class="gradient-logo" src="{logo_uri}" alt="Logo" />
                <div class="gradient-text-container">
                    <div class="gradient-text-kicker">You can easily</div>
                    <div class="gradient-text-title">Explore your research network in one place.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown("## Insert your institution.")
        st.caption("Connect, analyze, and visualize co-authorship patterns across institutions")
        institution_id = st.text_input("Institution ID", placeholder="i56...917")
        email = st.text_input("OpenAlex Email", placeholder="name@example.com")
        api_key = st.text_input("API key", type="password", placeholder="************")

        get_started_clicked = st.button("Get started", use_container_width=True)
        if get_started_clicked:
            if not institution_id.strip() or not email.strip() or not api_key.strip():
                st.error("Please fill institution ID, email, and API key.")
            else:
                st.session_state["pipeline_config"] = {
                    "institution_id": institution_id.strip(),
                    "api_email": email.strip(),
                    "api_key": api_key.strip(),
                }
                st.session_state["pipeline_status"] = "Preparing pipeline"
                st.session_state["pipeline_error"] = ""
                st.session_state["pipeline_complete"] = False
                st.session_state["pipeline_started"] = False
                st.session_state["current_page"] = "loading"
                st.rerun()

        st.markdown(
            """
            <div class="or-divider">
                <span>or</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_report = st.file_uploader("Upload report (.json)", type=["json"], key="report_json_file")
        load_report_clicked = st.button("Load Report", use_container_width=True)

        if load_report_clicked:
            if uploaded_report is None:
                st.error("Please upload a report JSON file first.")
            else:
                report_bytes = uploaded_report.getvalue()
                try:
                    json.loads(report_bytes.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    st.error("Uploaded file is not a valid UTF-8 JSON report.")
                else:
                    st.session_state["report_json_bytes"] = report_bytes
                    st.session_state["report_loading_started"] = False
                    st.session_state["report_loading_complete"] = False
                    st.session_state["report_loading_error"] = ""
                    st.session_state["current_page"] = "report_loading"
                    st.rerun()
