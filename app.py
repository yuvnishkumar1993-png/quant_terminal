# app.py
# Master 5-Page Dark Split Quant Core Engine UI (Ultra-Clean & Crash-Proof)

import streamlit as st

# Page Setup
st.set_page_config(page_title="Dark Split Quant Terminal", layout="wide", initial_sidebar_state="expanded")

# Safe Import of Dhan API Engine
try:
    from dhan_api_engine import DhanAPIEngine
    api_engine = DhanAPIEngine()
except Exception as e:
    api_engine = None

st.title("🌑 MASTER QUANT CORE ENGINE (PRO TERMINAL)")
st.markdown("---")

st.markdown("""
### 🚀 Welcome to the Institutional Multi-Page Quant Terminal
Your high-performance 5-page quantitative trading desk is now active. 

**Operational Desks Available in Sidebar:**
1. **Master Option Chain Desk:** Live LTP, Spread, Greeks & Dynamic Lot Size.
2. **Graphical Terminal:** 10 Visual modules & Smart Money waves.
3. **Gamma Flip Gatekeeper:** Confluence checklist and लक्ष्मण रेखा.
4. **Quant Screener & Bot:** Auto-scanning F&O stocks with Telegram alerts.
5. **Historical Time-Travel Desk:** Backtesting past dates, IV spikes, and snapshots.
""")

# Session State Global Asset Selector
if "selected_asset" not in st.session_state:
    st.session_state.selected_asset = "SENSEX"

if api_engine:
    try:
        all_symbols = api_engine.get_all_fo_symbols()
        st.session_state.selected_asset = st.sidebar.selectbox("Select Global Asset / Stock:", all_symbols, index=0)
    except:
        st.session_state.selected_asset = st.sidebar.selectbox("Select Global Asset / Stock:", ["SENSEX", "NIFTY", "BANKNIFTY"], index=0)
else:
    st.session_state.selected_asset = st.sidebar.selectbox("Select Global Asset / Stock:", ["SENSEX", "NIFTY", "BANKNIFTY"], index=0)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Use the navigation menu above to switch between the 5 distinct quant desks.")
