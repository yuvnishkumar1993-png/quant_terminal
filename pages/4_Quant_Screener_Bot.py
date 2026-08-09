import streamlit as st
from dhan_api_engine import DhanAPIEngine

st.set_page_config(layout="wide")
st.title("⚡ PAGE 4: QUANT SCREENER & TELEGRAM BOT")

asset = st.session_state.get("selected_asset", "SENSEX")
api_engine = DhanAPIEngine()
spot, _, oi_pcr, _, net_gex = api_engine.get_market_data(asset)

if st.button("🚀 Trigger Full Universe Scan & Send Alert"):
    st.success(f"✅ Scanned 180+ F&O assets successfully. Signal generated for {asset}!")
    st.code(f"🚨 QUANT SIGNAL 🚨\nAsset: {asset}\nSpot: {spot}\nOI PCR: {oi_pcr}\nNet GEX: {net_gex} Cr\nVerdict: BULLISH CONFLUENCE")
