# frontend/Home.py
import streamlit as st
from utils import display_header

# --- Page Configuration ---
st.set_page_config(
    page_title="Craft Connect | Home",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialize Session State ---
# Ensures that app state is maintained across page reloads
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if 'gallery_items' not in st.session_state:
    st.session_state.gallery_items = []


# --- Display the persistent header ---
display_header()


# --- Main Page Content ---
st.title("Welcome to Craft Connect ✨")
st.markdown(
    """
    #### A platform to celebrate and preserve traditional craftsmanship.
    
    In a world buzzing with digital noise, the authentic touch of a human creator is more valuable than ever. 
    Craft Connect is a platform where you can share the traditional crafts from your surroundings, exploring the rich heritage our ancestors used to make their lives simpler and more beautiful. 
    
    We provide you with cutting-edge AI tools to not just share your work, but to understand it, refine its story, and connect with a vibrant community of fellow artisans.
    """
)
st.markdown("---")


# --- Key Features Section ---
st.header("Our Core Features", anchor=False)
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.subheader("🤖 AI Description Writer")
    st.write(
        "Struggling with descriptions? Upload an image or video, and our AI will help generate compelling, editable descriptions and relevant tags for your craft."
    )
with col2:
    st.subheader("🖼️ Instant Showcase")
    st.write(
        "Publish your work directly to a beautiful, dynamic **Community Gallery**. See your creations featured alongside other talented artisans in real-time."
    )
with col3:
    st.subheader("🌐 Community Connection")
    st.write(
        "Discover, appreciate, and draw inspiration from a diverse range of crafts. Our platform is a meeting place for creators to celebrate the art of making."
    )

st.markdown("---")

# --- Call to Action ---
st.header("Ready to Inspire?", anchor=False)
st.write("Join our community and share your creative crafts. Your first piece is just a click away.")

if st.button("Share Your Craft →", type="primary"):
    # Updated to the standardized page name
    st.switch_page("pages/1_Share_Craft.py")