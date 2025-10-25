# frontend/pages/_Community_Gallery.py
import streamlit as st
import requests
from utils import display_header

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Community Gallery")
BACKEND_URL = "https://craft-connect-backend-0qs7.onrender.com"

display_header()

st.markdown("<h1 style='text-align: center;'>Community Gallery</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Gallery Display ---
try:
    with st.spinner("Loading gallery..."):
        response = requests.get(f"{BACKEND_URL}/crafts", timeout=10)
        response.raise_for_status()
        gallery_items = response.json()

    if not gallery_items:
        st.info("The gallery is empty. Be the first to share your craft!")
    else:
        # Display items in a grid
        num_columns = 3
        
        for i, item in enumerate(gallery_items):
            if i % num_columns == 0:
                cols = st.columns(num_columns)
            
            with cols[i % num_columns]:
                title = item.get("title", "Untitled Craft")
                description = item.get("description", "No description provided.")
                author_info = item.get("user", {})
                author_name = author_info.get("name", "Unknown Artist")
                media_url = item.get("file_url")

                st.markdown(f"**{title}**")
                
                if media_url:
                    if any(ext in media_url for ext in ['.mp4', '.mov', '.avi']):
                        st.video(media_url)
                    else:
                        st.image(media_url)
                
                st.write(description)
                st.caption(f"By: {author_name}")

except requests.exceptions.Timeout:
    st.error("Connection timeout. The server is taking too long to respond. Please try again later.")
except requests.exceptions.ConnectionError:
    st.error("Could not connect to the server. Please check your internet connection or try again later.")
    st.info("If the problem persists, the backend server may be temporarily unavailable.")
except requests.exceptions.RequestException as e:
    st.error(f"An error occurred while loading the gallery: {str(e)}")
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")