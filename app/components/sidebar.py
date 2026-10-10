"""Navigation and user settings sidebar."""

import streamlit as st


def render_sidebar(data_source: str) -> str:
    """Render navigation and return the selected page."""
    with st.sidebar:
        st.header("Onis")
        st.caption(f"Nguồn dữ liệu: {data_source}")
        return st.radio("Điều hướng", ["Tổng quan", "Trò chuyện"], label_visibility="collapsed")
