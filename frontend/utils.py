# frontend/utils.py
import streamlit as st

def display_header():
    """
    Displays a modern header with the title on the left and user actions on the right.
    """
    # Create two main columns: one for the title, one for the buttons.
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### 🎨 Craft Connect")

    with col2:
        # Check the session state to see if the user is logged in.
        if st.session_state.get("authenticated", False):
            # If logged in, show a welcome message and a sign-out button.
            # Use internal columns to place them side-by-side.
            sub_col1, sub_col2 = st.columns([2, 1])
            with sub_col1:
                st.write("Welcome!") # You can add user details here
            with sub_col2:
                if st.button("Sign Out"):
                    for key in st.session_state.keys():
                        del st.session_state[key]
                    st.switch_page("Home.py")
        else:
            # If logged out, show the sign-in button.
            if st.button("Sign In"):
                st.switch_page("pages/1_Share_Craft.py")

    st.divider()