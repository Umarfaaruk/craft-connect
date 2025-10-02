# frontend/pages/2_Community_Gallery.py
import streamlit as st
import requests
import datetime
from utils import display_header

# --- 1. Configuration ---
st.set_page_config(layout="wide", page_title="Community Gallery")
BACKEND_URL = "http://127.0.0.1:8000"  # URL of your running FastAPI backend

# --- 2. Header and Title ---
display_header()
st.title("🖼️ The Community Gallery")
st.write("A live showcase of creations from our talented community.")
st.divider()

# --- 3. Gallery Display Logic ---
try:
    # Make a live API call to your backend to fetch all crafts.
    # Your backend then calls the Corpus API.
    response = requests.get(f"{BACKEND_URL}/crafts")
    response.raise_for_status()  # Raise an exception for HTTP error codes
    gallery_items = response.json()

    if not gallery_items:
        st.info("The gallery is currently empty. Be the first to share your craft!")
    else:
        # Display items in a grid, newest first.
        # Note: The Corpus API might not return items in a specific order.
        num_columns = 3
        
        for i, item in enumerate(gallery_items):
            # Create a new row of columns for every 3 items.
            if i % num_columns == 0:
                cols = st.columns(num_columns)
            
            with cols[i % num_columns]:
                with st.container(border=True):
                    # --- Data Mapping ---
                    # You may need to adjust these '.get()' keys to match the exact
                    # field names returned by the Swecha Corpus API for a "record".
                    title = item.get("title", "Untitled Craft")
                    description = item.get("description", "No description provided.")
                    author_info = item.get("user", {}) # Corpus API often nests user info
                    author_name = author_info.get("name", "Unknown Artist")
                    media_url = item.get("file_url") # Find the correct key for the public URL

                    st.subheader(title)

                    # Display the media if a URL is found
                    if media_url:
                        # Simple check for video based on file extension
                        if any(ext in media_url for ext in ['.mp4', '.mov', '.avi']):
                            st.video(media_url)
                        else:
                            st.image(media_url)
                    
                    st.write(description)
                    st.caption(f"By: {author_name}")
                    st.divider()


except requests.exceptions.RequestException:
    st.error("Could not connect to the backend server. Please ensure it's running.")