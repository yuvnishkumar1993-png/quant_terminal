# app.py
import streamlit as st

st.set_page_config(
    page_title="Institutional Quant Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌑 INSTITUTIONAL QUANT TERMINAL")
st.markdown("---")
st.write("### Welcome to the Quant Core Engine")
st.write("👉 बाएं हाथ के **Sidebar** में दिए गए पेजेस पर क्लिक करके अलग-अलग डेस्क (Option Chain, Graphics, Gatekeeper, Screener, Historical) पर जाएं।")

if "selected_asset" not in st.session_state:
    st.session_state.selected_asset = "SENSEX"

st.session_state.selected_asset = st.sidebar.selectbox(
    "Select Global Asset / Stock:", 
    ["SENSEX", "NIFTY", "BANKNIFTY", "FINNIFTY", "RELIANCE", "TCS"], 
    index=0
)
