# frontend/utils.py
import streamlit as st

def display_header():
    """Displays a clean header."""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Craft Connect")

    with col2:
        if st.session_state.get("authenticated", False):
            sub_col1, sub_col2 = st.columns([2, 1])
            with sub_col1:
                st.write("Welcome!")
            with sub_col2:
                if st.button("Sign Out"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.switch_page("Home.py")
        else:
            if st.button("Sign In"):
                st.switch_page("pages/1_Share_Craft.py")

    st.markdown("---")