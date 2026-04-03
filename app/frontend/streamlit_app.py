import streamlit as st

from pages.loading_page import render_loading_page
from pages.preview_page import render_preview_page
from pages.report_loading_page import render_report_loading_page
from pages.welcome_page import render_welcome_page


st.set_page_config(page_title="ScholarNet UI", layout="wide")

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "welcome"

PAGE_RENDERERS = {
    "welcome": render_welcome_page,
    "loading": render_loading_page,
    "report_loading": render_report_loading_page,
    "preview": render_preview_page,
}

current_page = st.session_state.get("current_page", "welcome")
render_page = PAGE_RENDERERS.get(current_page, render_welcome_page)
render_page()
