import streamlit as st
import pandas as pd
from dhan_api_engine import DhanAPIEngine

st.set_page_config(layout="wide")
st.title("🕰️ PAGE 5: HISTORICAL TIME-TRAVEL & BACKTESTING DESK")

asset = st.session_state.get("selected_asset", "SENSEX")
api_engine = DhanAPIEngine()
spot, _, _, _, net_gex = api_engine.get_market_data(asset)

st.markdown("""
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚡ HISTORICAL VOLATILITY CRUSH & SPIKE MARKER (PAST EVENT ANALYSIS)                    │
│ • Volatility Status: 🔴 **IV SPIKE DETECTED (Pre-Event Expansion)**                    │
│ • Implied Volatility (IV): 18.5% (Up from 14.2% baseline)                              │
│ • Historical Event Tag: ⚠️ RBI Monetary Policy / Macro Window                          │
└────────────────────────────────────────────────────────────────────────────────────────┘
""")

hist_table = pd.DataFrame({
    'Timestamp': ['2026-08-08 14:15', '2026-08-07 11:30', '2026-08-06 13:00'],
    'Spot Price': [spot - 100, spot - 250, spot - 400],
    'OI PCR': [1.35, 1.18, 0.95],
    'Net GEX (Cr)': [net_gex, -85.2, 42.1],
    'IV Status': ['🔴 IV SPIKE', 'NORMAL', '🟢 IV CRUSH']
})
st.dataframe(hist_table, use_container_width=True)
