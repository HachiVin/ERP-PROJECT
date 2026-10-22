"""Streamlit helpers shared by every page: theme, header, and the login guard."""

from __future__ import annotations

import html

import streamlit as st

from erp_dashboard import config

_CSS = """<style>
body, .stApp {background-color:#121212;color:#f5f5f5;
font-family:'Segoe UI', Tahoma, Verdana, sans-serif;}
[data-testid="stSidebar"] {display:none;}
#MainMenu, footer {visibility:hidden;}
.header {text-align:center;color:#fff;background:linear-gradient(90deg,#ff7a18,#af002d 85%);
padding:16px;border-radius:10px;font-size:__HEADER_PX__px;font-weight:bold;margin-bottom:20px;
box-shadow:0px 3px 12px rgba(0,0,0,0.4);}
.stButton > button {background:linear-gradient(135deg,#8d35d6,#5a0f9c);color:#fff;border:none;
border-radius:8px;__BUTTON_SIZE__font-weight:600;font-size:15px;
box-shadow:0px 3px 8px rgba(0,0,0,0.4);cursor:pointer;}
.stButton > button:hover {background:linear-gradient(135deg,#a64ce6,#6c12b8);
transform:scale(1.03);transition:all 0.2s ease-in-out;}
</style>"""

# Per-page differences: header font size (px) and button sizing.
HOME_THEME = (26, "height:60px;min-width:260px;width:100%;")
DASHBOARD_THEME = (22, "padding:12px 20px;")


def apply_theme(theme: tuple[int, str]) -> None:
    header_px, button_size = theme
    css = _CSS.replace("__HEADER_PX__", str(header_px)).replace("__BUTTON_SIZE__", button_size)
    st.markdown(css, unsafe_allow_html=True)


def render_header(text: str) -> None:
    st.markdown(f'<div class="header">{html.escape(text)}</div>', unsafe_allow_html=True)


def require_login() -> str:
    """Stop the page unless a user is logged in; return the username otherwise."""
    if not st.session_state.get(config.STATE_LOGGED_IN):
        st.error("⚠️ Kamu harus login dulu.")
        st.stop()
    username = st.session_state.get(config.STATE_USERNAME, "")
    if not username:
        st.error("⚠️ Username tidak ditemukan.")
        st.stop()
    return username
