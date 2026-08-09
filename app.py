import streamlit as st
from dhan_api_engine import DhanAPIEngine

st.set_page_config(page_title="Institutional Quant Terminal", layout="wide", initial_sidebar_state="expanded")
st.markdown("<style>.stApp { background-color: #0E1117; color: #FFFFFF; }</style>", unsafe_allow_headers=True)

api_engine = DhanAPIEngine()

st.title("🌑 MASTER QUANT CORE ENGINE (PRO TERMINAL)")
st.markdown("---")
st.write("Welcome to the Institutional Multi-Page Quant Terminal.")
st.write("Use the sidebar navigation links to access all 5 dedicated operational desks.")

if "selected_asset" not in st.session_state:
    st.session_state.selected_asset = "SENSEX"

symbols = api_engine.get_all_fo_symbols()
st.session_state.selected_asset = st.sidebar.selectbox("Global Asset / Stock:", symbols, index=0)
