import streamlit as st
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from dhan_api_engine import DhanAPIEngine

st.title("⚡ PAGE 4: QUANT SCREENER & TELEGRAM BOT")
st.caption("Scanning all F&O assets with 5-Minute Rate Limit Throttling")

api_engine = DhanAPIEngine()
all_assets = api_engine.get_all_fo_symbols()
selected_scan_asset = st.selectbox("Select Asset to Test Scan:", all_assets)

if st.button("🚀 Trigger Manual Telegram Alert"):
    alert_msg = f"🚨 ⚡ QUANT OPTION SIGNAL ⚡ 🚨\n\nAsset: {selected_scan_asset}\nStatus: AUTHORIZED 🟢"
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": alert_msg}
        requests.post(url, json=payload, timeout=5)
        st.success("✅ Telegram Alert Triggered Successfully!")
    except Exception as e:
        st.error(f"Failed to send alert: {e}")
