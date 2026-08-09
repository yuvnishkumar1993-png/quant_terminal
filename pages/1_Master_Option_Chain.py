import streamlit as st
import pandas as pd
from dhan_api_engine import DhanAPIEngine
from quant_math_core import QuantMathCore

st.title("🖥️ PAGE 1: MASTER OPTION CHAIN (DARK SPLIT DESK)")

asset = st.session_state.get("selected_asset", "SENSEX")
api_engine = DhanAPIEngine()
expiries = api_engine.get_auto_expiries(asset)
selected_expiry = st.selectbox("Select Expiry Date:", expiries)
lot_size = api_engine.get_lot_size(asset)

st.sidebar.info(f"Active Asset: {asset} | Lot Size: {lot_size}")

def get_mock_chain(spot=73200):
    strikes = [spot - 400, spot - 200, spot, spot + 200, spot + 400]
    data = []
    for s in strikes:
        data.append({
            'strike': s,
            'ce_spread': 0.5, 'ce_ltp': 210.0, 'ce_iv': 16.8, 'ce_delta': 0.49, 'ce_oi': 125000, 'ce_volume': 45000,
            'pe_spread': 0.5, 'pe_ltp': 110.0, 'pe_iv': 16.5, 'pe_delta': -0.51, 'pe_oi': 165000, 'pe_volume': 58000
        })
    return QuantMathCore.sanitize_dataframe(pd.DataFrame(data))

df = get_mock_chain()
st.dataframe(df[['ce_spread', 'ce_ltp', 'ce_iv', 'ce_delta', 'ce_oi', 'strike', 'pe_oi', 'pe_delta', 'pe_iv', 'pe_ltp', 'pe_spread']], use_container_width=True)
