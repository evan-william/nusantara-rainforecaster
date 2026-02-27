"""
Nusantara RainForecaster — Main Application Entry Point
"""

import streamlit as st
from pages.dashboard import render_dashboard
from pages.forecast import render_forecast
from pages.explorer import render_explorer
from utils.style import inject_css

st.set_page_config(
    page_title="Nusantara RainForecaster",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


def main():
    st.sidebar.title("Nusantara RainForecaster")
    st.sidebar.caption("Prediksi Cuaca Berbasis AI untuk Indonesia")

    pages = {
        "Dashboard": render_dashboard,
        "Data Explorer": render_explorer,
        "AI Forecaster": render_forecast,
    }

    page = st.sidebar.radio("Navigasi", list(pages.keys()), label_visibility="collapsed")
    pages[page]()


if __name__ == "__main__":
    main()