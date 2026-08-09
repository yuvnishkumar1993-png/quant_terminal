import streamlit as st
from config import THEME_BG
from dhan_api_engine import DhanAPIEngine

st.set_page_config(page_title="Dark Split Quant Terminal", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>.stApp {{ background-color: {THEME_BG}; color: #FFFFFF; }}</style>", unsafe_allow_headers=True)

api_engine = DhanAPIEngine()

st.title("🌑 MASTER QUANT CORE ENGINE (PRO TERMINAL)")
st.markdown("---")
st.write("Welcome to the Institutional Multi-Page Quant Terminal.")
st.write("Use the sidebar navigation to switch between the 5 distinct operational desks (Option Chain, Graphics, Gatekeeper, Screener, and Historical Backtesting).")

if "selected_asset" not in st.session_state:
    st.session_state.selected_asset = "SENSEX"

all_symbols = api_engine.get_all_fo_symbols()
st.session_state.selected_asset = st.sidebar.selectbox("Global Asset / Stock:", all_symbols, index=0)
