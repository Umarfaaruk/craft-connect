"""
Craft Connect — Community Gallery Page
=======================================

Displays all publicly shared crafts in a responsive 3-column grid.

Data flow:
    1. Fetch all crafts via GET /crafts from the backend.
    2. Render each craft as a card with title, media, description, and author.
    3. Images are rendered with ``st.image()``, videos with ``st.video()``.

Error handling:
    • Connection errors, timeouts, and HTTP errors are caught and shown
      as user-friendly messages.
    • Individual gallery items that fail to render don't crash the page —
      only that card shows an error.
"""

# ──────────────────────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────────────────────
import sys
import os

import streamlit as st
import requests

# Ensure the parent directory is on the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import display_header

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Community Gallery")

# Backend URL — can be overridden in .streamlit/secrets.toml for deployment
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")

# Number of columns in the gallery grid
NUM_COLUMNS = 3

# Video file extensions used to decide between st.image() and st.video()
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".webm", ".mkv")

# ──────────────────────────────────────────────────────────────────────────────
# Page Layout
# ──────────────────────────────────────────────────────────────────────────────
display_header()

st.markdown("<h1 style='text-align: center;'>Community Gallery</h1>", unsafe_allow_html=True)
st.markdown("---")


# ──────────────────────────────────────────────────────────────────────────────
# Gallery Display
# ──────────────────────────────────────────────────────────────────────────────

def _render_gallery_item(item: dict) -> None:
    """
    Render a single craft card inside the current Streamlit column.

    Shows the title in bold, the media (image or video), a description,
    and the author's name. If anything goes wrong, an error message is
    shown in place of the card.
    """
    title       = item.get("title", "Untitled Craft")
    description = item.get("description", "No description provided.")
    media_url   = item.get("file_url")

    # Extract author name — the "user" field may be a dict or missing
    author_info = item.get("user", {}) if isinstance(item.get("user"), dict) else {}
    author_name = author_info.get("name", "Unknown Artist") if author_info else "Unknown Artist"

    # Title
    st.markdown(f"**{title}**")

    # Media (image or video)
    if media_url:
        try:
            if media_url.lower().endswith(VIDEO_EXTENSIONS):
                st.video(media_url)
            else:
                st.image(media_url)
        except Exception:
            st.warning(f"Could not load media: {media_url}")

    # Description and author
    st.write(description)
    st.caption(f"By: {author_name}")


# ── Fetch and render gallery ──
try:
    with st.spinner("Loading gallery..."):
        response = requests.get(f"{BACKEND_URL}/crafts", timeout=30)
        response.raise_for_status()
        gallery_items = response.json() or []

    if not gallery_items:
        st.info(
            "🌱 The gallery is empty. Be the first to share your craft! "
            "Click **Share Your Craft** in the sidebar to get started."
        )
    else:
        # Display items in a responsive grid
        for i, item in enumerate(gallery_items):
            if i % NUM_COLUMNS == 0:
                cols = st.columns(NUM_COLUMNS)

            with cols[i % NUM_COLUMNS]:
                try:
                    _render_gallery_item(item)
                except Exception as item_error:
                    st.error(f"Error displaying gallery item: {item_error}")

# ── Error handling ──
except requests.exceptions.Timeout:
    st.error("Connection timeout. The server is taking too long to respond. Please try again later.")

except requests.exceptions.ConnectionError:
    st.error("Could not connect to the server. Please check your internet connection or try again later.")
    st.info("If the problem persists, the backend server may be temporarily unavailable.")

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        st.error("The gallery endpoint was not found. The backend may not be deployed or the URL is incorrect.")
        st.info(f"Attempted to connect to: {BACKEND_URL}/crafts")
    elif e.response.status_code == 403:
        st.info("The gallery is currently empty. Be the first to share your craft!")
    else:
        st.error(f"HTTP error {e.response.status_code}: {e}")

except requests.exceptions.RequestException as e:
    st.error(f"An error occurred while loading the gallery: {e}")

except Exception as e:
    st.error(f"Unexpected error: {e}")