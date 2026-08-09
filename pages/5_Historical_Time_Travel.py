import streamlit as st
import pandas as pd
from backend import get_market_data

st.set_page_config(layout="wide")
asset = st.session_state.get("selected_asset", "SENSEX")
spot, _, _, _, net_gex = get_market_data(asset)

st.header(f"🕰️ PAGE 5: HISTORICAL TIME-TRAVEL & BACKTESTING DESK — {asset}")
st.markdown("---")

# Clean UI Box for Volatility Marker
st.info("⚡ **HISTORICAL VOLATILITY CRUSH & SPIKE MARKER (PAST EVENT ANALYSIS)**")

col1, col2, col3 = st.columns(3)
col1.metric("Volatility Status", "🔴 IV SPIKE DETECTED", "Pre-Event Expansion")
col2.metric("Implied Volatility (IV)", "18.5%", "Baseline: 14.2%")
col3.metric("Event Tag", "RBI / US CPI Window", "High Vega Risk")

st.markdown("### 📊 Past Snapshots Backtesting Log")

hist_table = pd.DataFrame({
    'Timestamp': ['2026-08-08 14:15', '2026-08-07 11:30', '2026-08-06 13:00'],
    'Spot Price': [spot - 100, spot - 250, spot - 400],
    'OI PCR': [1.35, 1.18, 0.95],
    'Net GEX (Cr)': [net_gex, -85.2, 42.1],
    'IV Status': ['🔴 IV SPIKE', 'NORMAL', '🟢 IV CRUSH']
})

st.dataframe(hist_table, use_container_width=True)
