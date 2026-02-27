"""Global CSS injected into Streamlit."""

import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #141824;
        }
        [data-testid="stSidebar"] .stRadio label {
            font-size: 0.95rem;
            padding: 4px 0;
        }

        /* Metric cards */
        [data-testid="metric-container"] {
            background: #1A1F2E;
            border: 1px solid #2a3045;
            border-radius: 8px;
            padding: 12px 16px;
        }

        /* Section headings */
        h2 { border-bottom: 2px solid #4A90D9; padding-bottom: 6px; }

        /* Confidence badge */
        .confidence-high  { color: #4CAF50; font-weight: 700; }
        .confidence-med   { color: #FF9800; font-weight: 700; }
        .confidence-low   { color: #F44336; font-weight: 700; }

        /* Data table */
        [data-testid="stDataFrame"] { border-radius: 8px; }

        /* Hide Streamlit branding */
        #MainMenu, footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )