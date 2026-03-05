"""
Craft Connect — Home Page
==========================

Landing page for the Craft Connect application.
Shows information about Swecha, traditional crafts, and a call-to-action
button that navigates users to the craft upload page.

This is the entry point for ``streamlit run Home.py``.
"""

import streamlit as st
from utils import display_header

# ──────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Craft Connect | Home",
    page_icon="✨",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────────────
# Session State Initialisation
# ──────────────────────────────────────────────────────────────────────────────
# ``authenticated`` controls whether the user sees login forms or upload forms
# throughout the app. Defaults to False on first visit.
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ──────────────────────────────────────────────────────────────────────────────
# Page Layout
# ──────────────────────────────────────────────────────────────────────────────
display_header()

# Hero section
st.markdown(
    "<h1 style='text-align: center; margin-top: 2rem;'>Craft Connect</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; font-size: 1.2rem; margin-bottom: 3rem;'>"
    "Preserving Traditional Crafts &amp; Cultural Heritage</p>",
    unsafe_allow_html=True,
)

st.markdown("---")

# ── About Swecha ──
st.markdown("""
<div style='text-align: center; max-width: 900px; margin: 0 auto 3rem;'>
    <h2 style='margin-bottom: 1.5rem;'>About Swecha</h2>
    <p style='font-size: 1.05rem; line-height: 1.9; margin-bottom: 1.5rem;'>
        Swecha is a free and open source software organization dedicated to preserving and promoting
        our rich cultural heritage through technology. We believe in making traditional knowledge
        accessible to everyone while maintaining its authenticity and value.
    </p>
    <p style='font-size: 1.05rem; line-height: 1.9;'>
        Our mission is to bridge the gap between traditional knowledge and modern technology,
        ensuring that the wisdom of our ancestors is preserved and passed down to future generations
        in accessible digital formats.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Our Tradition ──
st.markdown("""
<div style='text-align: center; max-width: 900px; margin: 0 auto 3rem;'>
    <h2 style='margin-bottom: 1.5rem;'>Our Tradition</h2>
    <p style='font-size: 1.05rem; line-height: 1.9; margin-bottom: 1.5rem;'>
        Traditional crafts represent the wisdom and creativity of our ancestors. From handwoven textiles
        to pottery, from folk art to traditional architecture, each craft tells a story of our heritage.
    </p>
    <p style='font-size: 1.05rem; line-height: 1.9;'>
        Craft Connect is our initiative to document, preserve, and celebrate these traditional crafts
        for future generations.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Call to Action ──
st.markdown("""
<div style='text-align: center; max-width: 900px; margin: 0 auto 2rem;'>
    <h3>Join Us in Preserving Our Heritage</h3>
    <p style='font-size: 1.05rem; line-height: 1.9;'>
        Contribute by sharing your traditional crafts, stories, music, and knowledge.
        Every contribution helps preserve our cultural heritage for future generations.
    </p>
</div>
""", unsafe_allow_html=True)

# Centred "Share Your Craft" button → navigates to the upload page
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("Share Your Craft", type="primary", use_container_width=True):
        st.switch_page("pages/1_Share_Craft.py")