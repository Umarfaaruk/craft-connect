"""
Craft Connect — Share Your Craft Page
=======================================

This page handles two flows:

1. **Authentication** — If the user is not logged in, show a tabbed
   Sign In / Sign Up form. On successful auth the page reloads and
   switches to the upload form.

2. **Upload** — If authenticated, show a form to upload an image/video
   with a description. On publish, the craft is sent to the backend
   which proxies it to the Swecha Corpus API.

Supported file types: PNG, JPG, JPEG, MP4, MOV, AVI
Maximum file size: 1 GB
"""

# ──────────────────────────────────────────────────────────────────────────────
# Imports
# ──────────────────────────────────────────────────────────────────────────────
import time
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
st.set_page_config(layout="wide", page_title="Share Your Craft")

# Backend URL — can be overridden in .streamlit/secrets.toml for deployment
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")

# File size limit (1 GB in bytes)
MAX_FILE_SIZE_BYTES = 1_073_741_824

display_header()


# ══════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION FORM
# ══════════════════════════════════════════════════════════════════════════════

def show_auth_form():
    """
    Display a centred login / registration form with tabs.

    On successful authentication the user's ``access_token`` is stored
    in ``st.session_state`` and the page is reloaded so ``show_uploader``
    takes over.
    """
    # Centre the form using column spacing
    _, col_form, _ = st.columns([2, 1.5, 2])

    with col_form:
        tab_login, tab_register = st.tabs(["Sign In", "Sign Up"])

        # ── Sign In Tab ──
        with tab_login:
            st.markdown(
                "<h3 style='text-align: center; margin-bottom: 1rem;'>Sign In</h3>",
                unsafe_allow_html=True,
            )
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Phone Number", placeholder="Enter phone number")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

                if submitted:
                    if not username or not password:
                        st.error("Please enter both phone number and password.")
                    else:
                        _attempt_login(username, password)

        # ── Sign Up Tab ──
        with tab_register:
            st.markdown(
                "<h3 style='text-align: center; margin-bottom: 1rem;'>Sign Up</h3>",
                unsafe_allow_html=True,
            )
            with st.form("register_form", clear_on_submit=False):
                reg_username = st.text_input("Phone Number", placeholder="Enter phone number", key="reg_username")
                reg_password = st.text_input("Password", type="password", placeholder="Enter password", key="reg_password")
                reg_email    = st.text_input("Email (Optional)", placeholder="Enter email address", key="reg_email")
                submitted    = st.form_submit_button("Sign Up", type="primary", use_container_width=True)

                if submitted:
                    if not reg_username or not reg_password:
                        st.error("Please enter both phone number and password.")
                    else:
                        _attempt_register(reg_username, reg_password, reg_email)


def _attempt_login(username: str, password: str) -> None:
    """Send login credentials to the backend and store the token on success."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/token",
            data={"username": username, "password": password},
            timeout=15,
        )
        if response.status_code == 200:
            token_data = response.json()
            st.session_state["access_token"] = token_data.get("access_token")
            st.session_state["authenticated"] = True
            st.success("Login Successful!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Login failed. Please check your credentials.")

    except requests.exceptions.ConnectionError:
        st.error("Connection failed. Is the backend server running?")
    except Exception as exc:
        st.error(f"An error occurred: {exc}")


def _attempt_register(username: str, password: str, email: str) -> None:
    """Send registration data to the backend and store the token on success."""
    try:
        reg_data = {"username": username, "password": password}
        if email and email.strip():
            reg_data["email"] = email

        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            data=reg_data,
            timeout=15,
        )
        if response.status_code == 200:
            token_data = response.json()
            st.session_state["access_token"] = token_data.get("access_token")
            st.session_state["authenticated"] = True
            st.success("Registration Successful! You are now logged in.")
            time.sleep(1)
            st.rerun()
        else:
            error_detail = "Registration failed. Please try again."
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_detail = error_data["detail"]
            except Exception:
                pass
            st.error(error_detail)

    except requests.exceptions.ConnectionError:
        st.error("Connection failed. Is the backend server running?")
    except Exception as exc:
        st.error(f"An error occurred: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  UPLOAD FORM
# ══════════════════════════════════════════════════════════════════════════════

def show_uploader():
    """
    Display the craft upload form (shown only when authenticated).

    Workflow:
        1. User selects a file (image or video, max 1 GB).
        2. User provides a description.
        3. On "Publish to Gallery" click:
           a. Validate inputs and file size.
           b. Fetch the first available category from backend.
           c. POST the craft to ``/crafts`` with bearer auth.
           d. Redirect to Community Gallery on success.
    """
    st.markdown("<h1 style='text-align: center;'>Share Your Craft</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # ── File Upload ──
    uploaded_file = st.file_uploader(
        "Upload your file",
        type=["png", "jpg", "jpeg", "mp4", "mov", "avi"],
        help="Supported: PNG, JPG, JPEG, MP4, MOV, AVI — Maximum size: 1 GB",
    )

    # ── Description ──
    description = st.text_area(
        "Description",
        height=100,
        help="Describe your craft. This will be shown as the title and description in the gallery.",
    )

    # Default values for optional Corpus API fields
    language = "NA"             # Could be extended to a language selector
    release_rights = "NA"       # Could be "creator", "others", "downloaded"

    st.markdown("---")

    # ── Publish Button ──
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("Publish to Gallery", type="primary", use_container_width=True):
            _handle_publish(uploaded_file, description, language, release_rights)


def _handle_publish(uploaded_file, description: str, language: str, release_rights: str) -> None:
    """Validate inputs, upload the file, and handle the response."""

    # ── Validation ──
    if not uploaded_file or not description.strip():
        st.warning("Please fill out all fields.")
        return

    if "access_token" not in st.session_state:
        st.error("Your session has expired. Please log in again.")
        return

    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        size_mb = uploaded_file.size / (1024 * 1024)
        st.error(f"File size ({size_mb:.1f} MB) exceeds the 1 GB limit. Please upload a smaller file.")
        return

    # ── Upload ──
    with st.spinner("Publishing your craft..."):
        try:
            auth_header = {"Authorization": f"Bearer {st.session_state['access_token']}"}

            # Auto-select the first available category (if any)
            category_id = _fetch_default_category()

            payload = {
                "title": description,
                "description": description,
                "language": language,
                "release_rights": release_rights,
            }
            if category_id:
                payload["category_id"] = category_id

            uploaded_file.seek(0)
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

            response = requests.post(
                f"{BACKEND_URL}/crafts",
                data=payload,
                files=files,
                headers=auth_header,
                timeout=120,
            )

            if response.status_code == 200:
                st.success("Published successfully! 🎉")
                time.sleep(1)
                st.switch_page("pages/_Community_Gallery.py")
            else:
                error_msg = "Upload failed."
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except Exception:
                    error_msg = response.text or f"Server returned status {response.status_code}"
                st.error(f"Upload failed: {error_msg}")

        except requests.exceptions.ConnectionError:
            st.error("Connection failed. Please check if the backend server is running.")
        except requests.exceptions.Timeout:
            st.error("Upload timed out. The file might be too large or the server is slow. Try again.")
        except Exception as exc:
            st.error(f"An error occurred: {exc}")


def _fetch_default_category() -> str | None:
    """
    Fetch the first available category ID from the backend.

    Returns None if categories can't be fetched (the backend will
    return a validation error, but the upload won't crash).
    """
    try:
        resp = requests.get(f"{BACKEND_URL}/categories", timeout=4)
        if resp.status_code == 200:
            cat_list = resp.json()
            if isinstance(cat_list, list) and cat_list:
                first = cat_list[0]
                return first.get("id") or first.get("uuid") or first.get("_id")
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ROUTER
# ══════════════════════════════════════════════════════════════════════════════
# If the user is authenticated → show the upload form.
# Otherwise → show the login/registration form.

if not st.session_state.get("authenticated", False):
    show_auth_form()
else:
    show_uploader()