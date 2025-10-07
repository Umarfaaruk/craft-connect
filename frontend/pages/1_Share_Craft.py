# frontend/pages/1_Share_Craft.py
import streamlit as st
import time
import requests
from utils import display_header

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Share Your Craft")
BACKEND_URL = "https://craft-connect-backend-0qs7.onrender.com"  # URL of your running FastAPI backend

# --- Header ---
display_header()

# --- AUTHENTICATION FORM ---
def show_auth_form():
    """Displays the login form for authenticating with the Corpus API."""
    st.warning("Please sign in with your Corpus account to share your craft.")
    st.info("Don't have an account? You must register on the main Swecha Corpus platform first.")

    with st.form("login_form"):
        username = st.text_input("Username (Phone Number)")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Sign In", type="primary"):
            try:
                # API call to your backend's /token endpoint, which proxies to the Corpus API
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

# --- UPLOADER PAGE ---
def show_uploader():
    """Displays the main page for uploading a new craft after authentication."""
    st.title("🎨 Share Your Craft")
    st.write("Upload an image or video and provide its details to add it to the gallery.")

    uploaded_file = st.file_uploader(
        "Upload your media file",
        type=["png", "jpg", "jpeg", "mp4", "mov", "avi"]
    )
    description = st.text_area("Describe your creation:", height=150)
    
    # In a real app, you would fetch these categories from the API.
    # For now, we use placeholders that match what the API might expect.
    categories = {
        "category_1": "Painting",
        "category_2": "Sculpture",
        "category_3": "Textile Art"
    }
    category_id = st.selectbox(
        "Select a Category:",
        options=list(categories.keys()),
        format_func=lambda x: categories[x]
    )
    
    language = st.text_input("Language of the Craft/Description", "English")
    
    release_rights = st.selectbox(
        "Release Rights:",
        options=["Attribution-ShareAlike (CC BY-SA)", "Public Domain (CC0)"],
        help="Choose the license under which you are releasing this craft."
    )
    
    if st.button("🌍 Publish to Gallery", type="primary"):
        if not all([uploaded_file, description.strip(), category_id, language, release_rights]):
            st.warning("Please fill out all fields and upload a file.")
        elif 'access_token' not in st.session_state:
            st.error("Authentication token not found. Please log in again.")
        else:
            with st.spinner("Publishing your craft..."):
                try:
                    # Prepare the authorization header with the saved token
                    auth_header = {"Authorization": f"Bearer {st.session_state['access_token']}"}
                    
                    # Prepare the complete payload with all required fields
                    payload = {
                        'description': description,
                        'category_id': category_id,
                        'language': language,
                        'release_rights': release_rights,
                    }
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    
                    # Make the API call to your backend's /crafts endpoint
                    response = requests.post(
                        f"{BACKEND_URL}/crafts",
                        data=payload,
                        files=files,
                        headers=auth_header
                    )

                    if response.status_code == 200:
                        st.balloons()
                        st.success("Published! You will be redirected to the gallery.")
                        time.sleep(2)
                        st.switch_page("pages/2_Community_Gallery.py")
                    else:
                        # Display the specific error message from the API
                        st.error(f"Upload failed: {response.json().get('detail', 'An unknown error occurred.')}")

                except requests.exceptions.ConnectionError as e:
                    st.error(f"Connection failed. Is the backend server running? Details: {e}")

# --- Page Router ---
# This logic decides whether to show the login form or the uploader page.
if not st.session_state.get("authenticated", False):
    show_auth_form()
else:
    show_uploader()