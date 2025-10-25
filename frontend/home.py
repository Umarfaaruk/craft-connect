# frontend/Home.py
import streamlit as st
from utils import display_header

# --- Page Configuration ---
st.set_page_config(
    page_title="Craft Connect | Home",
    page_icon="✨",
    layout="wide"
)

# --- Initialize Session State ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- Display Header ---
display_header()

# --- Main Content ---
st.markdown("<h1 style='text-align: center; margin-top: 2rem;'>Craft Connect</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; margin-bottom: 3rem;'>Preserving Traditional Crafts</p>", unsafe_allow_html=True)

st.markdown("---")

# --- Simple Description ---
st.markdown("""
<div style='text-align: center; max-width: 800px; margin: 0 auto;'>
    <p style='font-size: 1.1rem; line-height: 1.8;'>
        Share your traditional crafts and discover the rich heritage of handmade artistry.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Call to Action ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if st.button("Share Your Craft", type="primary", use_container_width=True):
        st.switch_page("pages/1_Share_Craft.py")
    st.markdown("</div>", unsafe_allow_html=True)