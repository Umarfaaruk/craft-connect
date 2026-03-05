"""
Craft Connect — Shared UI Utilities
=====================================

Common UI components shared across all Streamlit pages.
Import with: ``from utils import display_header``
"""

import streamlit as st


def display_header() -> None:
    """
    Render the top navigation bar on every page.

    Layout:
        ┌──────────────────────────────────────────────────┐
        │  Craft Connect                   Welcome! [Sign Out] │
        │ ──────────────────────────────────────────────────│
        └──────────────────────────────────────────────────┘

    When the user is **not authenticated**, only the app name is shown.
    When authenticated, a welcome message and sign-out button appear.
    Clicking "Sign Out" clears all session state and redirects to Home.
    """
    col_brand, col_user = st.columns([3, 1])

    with col_brand:
        st.markdown("### Craft Connect")

    with col_user:
        if st.session_state.get("authenticated", False):
            sub_col1, sub_col2 = st.columns([2, 1])
            with sub_col1:
                st.write("Welcome!")
            with sub_col2:
                if st.button("Sign Out"):
                    # Clear all session state and redirect to home
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.switch_page("Home.py")

    st.markdown("---")