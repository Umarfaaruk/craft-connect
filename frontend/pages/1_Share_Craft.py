# frontend/pages/1_Share_Craft.py
import streamlit as st
import time
import requests
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import display_header

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Share Your Craft")
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")

display_header()

# --- Category Mapping ---
CATEGORIES = {
    "category_1": "📚 Fables - Traditional stories with moral lessons and mythical characters",
    "category_2": "🎉 Events - Happenings, celebrations, and special occasions",
    "category_3": "🎵 Music - Musical content, songs, instruments, and audio experiences",
    "category_4": "🏛️ Places - Locations, landmarks, and geographical content",
    "category_5": "🍽️ Food - Culinary content, recipes, and food-related information",
    "category_6": "👥 People - Individuals, personalities, and human-related content",
    "category_7": "📖 Literature - Books, poems, writings, and literary works",
    "category_8": "🏗️ Architecture - Buildings, structures, and architectural designs",
    "category_9": "⚡ Skills - Abilities, talents, and learning resources",
    "category_10": "🖼️ Images - Visual content, pictures, and graphic materials",
    "category_11": "🎭 Culture - Cultural traditions, customs, and heritage",
    "category_12": "🌿 Flora & Fauna - Plants, animals, and natural life forms",
    "category_13": "🎓 Education - Learning materials, courses, and educational content",
    "category_14": "🌱 Vegetation - Plant life, gardening, and botanical content",
    "category_15": "📓 Folk Tales - Stories passed orally across generations",
    "category_16": "🎶 Folk Songs - Traditional music reflecting cultural heritage",
    "category_17": "🛠️ Traditional Skills - Artisanal and craft practices (e.g., weaving, pottery)",
    "category_18": "🏛️ Local Cultural History - Cultural events, rituals, and customs",
    "category_19": "📜 Local History - Historical events and figures significant to region",
    "category_20": "🌾 Food & Agriculture - Traditional recipes, cooking methods, tools, and practices",
    "category_21": "📰 Newspapers Older Than 1980s - Historical newspaper archives",
}

# --- Authentication Form ---
def show_auth_form():
    """Displays the login/signup form in a smaller square box."""
    # Center the form using empty columns
    col1, col2, col3 = st.columns([2, 1.5, 2])
    
    with col2:
        # Tab selection
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            # Simple title without box
            st.markdown("<h3 style='text-align: center; margin-bottom: 1rem;'>Sign In</h3>", unsafe_allow_html=True)
            
            # Login form container
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Phone Number", placeholder="Enter phone number")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                
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
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
        
        with tab2:
            # Simple title without box
            st.markdown("<h3 style='text-align: center; margin-bottom: 1rem;'>Sign Up</h3>", unsafe_allow_html=True)
            
            # Registration form container
            with st.form("register_form", clear_on_submit=False):
                reg_username = st.text_input("Phone Number", placeholder="Enter phone number", key="reg_username")
                reg_password = st.text_input("Password", type="password", placeholder="Enter password", key="reg_password")
                reg_email = st.text_input("Email (Optional)", placeholder="Enter email address", key="reg_email")
                
                submit_reg = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
                
                if submit_reg:
                    if not reg_username or not reg_password:
                        st.error("Please enter both phone number and password.")
                    else:
                        try:
                            reg_data = {
                                "username": reg_username,
                                "password": reg_password
                            }
                            if reg_email.strip():
                                reg_data["email"] = reg_email
                            
                            response = requests.post(
                                f"{BACKEND_URL}/auth/register",
                                data=reg_data
                            )
                            if response.status_code == 200:
                                token_data = response.json()
                                st.session_state['access_token'] = token_data.get('access_token')
                                st.session_state['authenticated'] = True
                                st.success("Registration Successful! You are now logged in.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                error_detail = "Registration failed. Please try again."
                                try:
                                    error_data = response.json()
                                    if "detail" in error_data:
                                        error_detail = error_data["detail"]
                                except:
                                    pass
                                st.error(error_detail)
                        except requests.exceptions.ConnectionError:
                            st.error("Connection failed. Is the backend server running?")
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")

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
        options=list(CATEGORIES.keys()),
        format_func=lambda x: CATEGORIES[x]
    )
    
    # Language options as per Corpus API requirements
    LANGUAGE_OPTIONS = {
        "NA": "Not Applicable",
        "hindi": "Hindi",
        "bengali": "Bengali", 
        "telugu": "Telugu",
        "marathi": "Marathi",
        "tamil": "Tamil",
        "gujarati": "Gujarati",
        "urdu": "Urdu",
        "kannada": "Kannada",
        "odia": "Odia",
        "malayalam": "Malayalam",
        "punjabi": "Punjabi",
        "assamese": "Assamese",
        "bodo": "Bodo",
        "dogri": "Dogri",
        "kashmiri": "Kashmiri",
        "konkani": "Konkani",
        "maithili": "Maithili",
        "meitei": "Meitei",
        "nepali": "Nepali",
        "sanskrit": "Sanskrit",
        "santali": "Santali",
        "sindhi": "Sindhi"
    }
    
    language = st.selectbox(
        "Language:",
        options=list(LANGUAGE_OPTIONS.keys()),
        format_func=lambda x: LANGUAGE_OPTIONS[x],
        index=0  # Default to "NA"
    )
    
    # Hidden release_rights field with default value
    release_rights = "Yes"  # Default value
    
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
                        
                        # Debug: Print payload to see what's being sent (remove this line after testing)
                        # st.write("Debug - Payload being sent:", payload)
                        
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