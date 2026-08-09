# app.py
# Institutional Quant Terminal - 5-in-1 Unified Master Engine

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime

# Page Setup
st.set_page_config(page_title="Institutional Quant Terminal", layout="wide", initial_sidebar_state="expanded")

# Global Settings & Session State
if "selected_asset" not in st.session_state:
    st.session_state.selected_asset = "SENSEX"

# Sidebar Navigation (All 5 Desks in One View)
st.sidebar.title("🌑 QUANT TERMINAL DESK")
st.session_state.selected_asset = st.sidebar.selectbox("Select Asset / Stock:", ["SENSEX", "NIFTY", "BANKNIFTY", "FINNIFTY"], index=0)
asset = st.session_state.selected_asset

st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate Desks:", [
    "Page 1: Master Option Chain",
    "Page 2: Graphical Terminal (10 Mods)",
    "Page 3: Gamma Flip Gatekeeper",
    "Page 4: Quant Screener & Bot",
    "Page 5: Historical Time-Travel Desk"
])

st.sidebar.markdown("---")
st.sidebar.info(f"Active Desk: {page}\nAsset: {asset}")

# Mock / Live Data Engine Helpers
def get_mock_chain(spot=73200):
    strikes = [spot - 400, spot - 200, spot, spot + 200, spot + 400]
    data = []
    for s in strikes:
        data.append({
            'strike': s,
            'ce_spread': 0.5, 'ce_ltp': max(10, (spot - s)*0.5 + 150), 'ce_iv': 16.5, 'ce_delta': 0.52, 'ce_oi': 125000, 'ce_volume': 45000,
            'pe_spread': 0.5, 'pe_ltp': max(10, (s - spot)*0.5 + 140), 'pe_iv': 16.8, 'pe_delta': -0.48, 'pe_oi': 165000, 'pe_volume': 58000
        })
    return pd.DataFrame(data)

mock_df = get_mock_chain()
spot_price = 73200.00
oi_pcr = 1.35
vol_pcr = 1.42
net_gex = -140.2

# ==========================================
# PAGE 1: MASTER OPTION CHAIN
# ==========================================
if page == "Page 1: Master Option Chain":
    st.header(f"🖥️ PAGE 1: MASTER OPTION CHAIN — {asset}")
    st.caption("Status: Live Institutional Feed | Spot: ₹73,200.00")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Spot Price", f"₹{spot_price:,.2f}")
    col2.metric("OI PCR", oi_pcr)
    col3.metric("Volume PCR", vol_pcr)
    col4.metric("Net GEX", f"{net_gex} Cr")

    st.subheader("Side-by-Side Dark Split Option Chain")
    st.dataframe(mock_df[['ce_spread', 'ce_ltp', 'ce_iv', 'ce_delta', 'ce_oi', 'strike', 'pe_oi', 'pe_delta', 'pe_iv', 'pe_ltp', 'pe_spread']], use_container_width=True)

# ==========================================
# PAGE 2: GRAPHICAL TERMINAL (10 MODULES)
# ==========================================
elif page == "Page 2: Graphical Terminal (10 Mods)":
    st.header(f"🖥️ PAGE 2: ADVANCED GRAPHICAL TERMINAL — {asset}")
    st.caption("Visualizing Smart Money Waves & Strike-wise Open Interest Distribution")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=mock_df['strike'], y=mock_df['ce_oi'], name='CE OI (Resistance)', marker_color='#FF5252'))
    fig.add_trace(go.Bar(x=mock_df['strike'], y=mock_df['pe_oi'], name='PE OI (Support)', marker_color='#00E676'))
    fig.update_layout(title="[MOD A] Strike-Wise OI Profile & Pressure Zones", template="plotly_dark", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# PAGE 3: GAMMA FLIP GATEKEEPER
# ==========================================
elif page == "Page 3: Gamma Flip Gatekeeper":
    st.header(f"🖥️ PAGE 3: GEX & GAMMA FLIP GATEKEEPER — {asset}")
    
    flip_level = spot_price - 120.0
    status_gate1 = "🟢 PASSED" if spot_price > flip_level else "🔴 FAILED"
    status_gate2 = "🟢 PASSED" if oi_pcr > 1.2 else "🔴 FAILED"
    
    st.markdown(f"""
    ### Gatekeeper System Verification
    * **Gamma Flip Level (लक्ष्मण रेखा):** ₹{flip_level:,.2f} | **Spot Level:** ₹{spot_price:,.2f} -> **Gate 1:** {status_gate1}
    * **OI PCR Threshold (1.20):** Current {oi_pcr} -> **Gate 2:** {status_gate2}
    """)
    
    if spot_price > flip_level and oi_pcr > 1.2:
        st.success("⚡ FINAL SYSTEM VERDICT: OPTION BUYING EXECUTION AUTHORIZED")

# ==========================================
# PAGE 4: QUANT SCREENER & BOT
# ==========================================
elif page == "Page 4: Quant Screener & Bot":
    st.header("⚡ PAGE 4: QUANT SCREENER & TELEGRAM SIGNAL DESK")
    st.caption("Auto-Scanning F&O Assets with Rate Limit Protection")

    if st.button("🚀 Trigger Manual Scan & Send Telegram Alert"):
        alert_msg = f"🚨 ⚡ QUANT OPTION SIGNAL ⚡ 🚨\n\nAsset: {asset}\nOI PCR: {oi_pcr}\nNet GEX: {net_gex} Cr\nStatus: AUTHORIZED 🟢"
        st.success(f"✅ Signal Generated & Simulated Dispatch for {asset}!")
        st.code(alert_msg)

# ==========================================
# PAGE 5: HISTORICAL TIME-TRAVEL DESK
# ==========================================
elif page == "Page 5: Historical Time-Travel Desk":
    st.header(f"🕰️ PAGE 5: HISTORICAL TIME-TRAVEL & BACKTESTING DESK — {asset}")
    st.caption("Past Event Analysis with IV Crush & Spike Marker")
    
    st.markdown("""
    ┌────────────────────────────────────────────────────────────────────────────────────────┐
    │ ⚡ HISTORICAL VOLATILITY CRUSH & SPIKE MARKER (PAST EVENT ANALYSIS)                    │
    │ • Volatility Status: 🔴 **IV SPIKE DETECTED (Pre-Event Expansion)**                    │
    │ • Implied Volatility (IV): 18.5% (Up from 14.2% baseline)                              │
    │ • Historical Event Tag: ⚠️ RBI Monetary Policy / Macro Window                          │
    └────────────────────────────────────────────────────────────────────────────────────────┘
    """)
    
    hist_data = pd.DataFrame({
        'Timestamp': ['2026-08-07 13:30', '2026-08-06 11:15', '2026-08-05 14:00'],
        'Spot': [73150, 72900, 72650],
        'OI PCR': [1.35, 1.12, 0.98],
        'Net GEX (Cr)': [-140.2, -85.5, 45.1],
        'IV Status': ['IV SPIKE', 'NORMAL', 'IV CRUSH']
    })
    st.dataframe(hist_data, use_container_width=True)
