# frontend/pages/1_Share_Craft.py
import streamlit as st
import time
import requests
from utils import display_header

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Share Your Craft")
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")

display_header()

# --- Authentication Form ---
def show_auth_form():
    """Displays the login form in a square box."""
    # Center the form using empty columns
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Create a styled container for the login form
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 2.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); max-width: 450px; margin: 2rem auto;'>
            <h2 style='text-align: center; margin-bottom: 2rem; color: #333;'>Sign In</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Form container
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Phone Number", placeholder="Enter your phone number")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Please enter both phone number and password.")
                else:
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/token",
                            data={"username": username, "password": password}
                        )
                        if response.status_code == 200:
                            token_data = response.json()
                            st.session_state['access_token'] = token_data.get('access_token')
                            st.session_state['authenticated'] = True
                            st.success("Login Successful!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Login failed. Please check your credentials.")
                    except requests.exceptions.ConnectionError:
                        st.error("Connection failed. Is the backend server running?")

# --- Uploader Page ---
def show_uploader():
    """Displays the upload form."""
    st.markdown("<h1 style='text-align: center;'>Share Your Craft</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Upload your file",
        type=["png", "jpg", "jpeg", "mp4", "mov", "avi"]
    )
    
    description = st.text_area("Description", height=100)
    
    category_id = st.selectbox(
        "Category:",
        options=["category_1", "category_2", "category_3"],
        format_func=lambda x: x.replace("_", " ").title()
    )
    
    language = st.text_input("Language", "English")
    
    release_rights = st.selectbox(
        "Release Rights:",
        options=["Attribution-ShareAlike (CC BY-SA)", "Public Domain (CC0)"]
    )
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Publish to Gallery", type="primary", use_container_width=True):
            if not all([uploaded_file, description.strip(), category_id, language, release_rights]):
                st.warning("Please fill out all fields.")
            elif 'access_token' not in st.session_state:
                st.error("Please log in again.")
            else:
                with st.spinner("Publishing..."):
                    try:
                        auth_header = {"Authorization": f"Bearer {st.session_state['access_token']}"}
                        
                        payload = {
                            'description': description,
                            'category_id': category_id,
                            'language': language,
                            'release_rights': release_rights,
                        }
                        files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        
                        response = requests.post(
                            f"{BACKEND_URL}/crafts",
                            data=payload,
                            files=files,
                            headers=auth_header
                        )

                        if response.status_code == 200:
                            st.success("Published successfully!")
                            time.sleep(1)
                            st.switch_page("pages/_Community_Gallery.py")
                        else:
                            error_msg = response.json().get('detail', 'An unknown error occurred.')
                            st.error(f"Upload failed: {error_msg}")

                    except requests.exceptions.ConnectionError as e:
                        st.error(f"Connection failed: {e}")

# --- Page Router ---
if not st.session_state.get("authenticated", False):
    show_auth_form()
else:
    show_uploader()