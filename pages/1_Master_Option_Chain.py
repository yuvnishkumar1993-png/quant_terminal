import streamlit as st
from dhan_api_engine import DhanAPIEngine

st.set_page_config(layout="wide")
st.title("🖥️ PAGE 1: MASTER OPTION CHAIN (DARK SPLIT DESK)")

asset = st.session_state.get("selected_asset", "SENSEX")
api_engine = DhanAPIEngine()
spot, chain_df, oi_pcr, vol_pcr, net_gex = api_engine.get_market_data(asset)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Spot Price", f"₹{spot:,.2f}")
c2.metric("OI PCR", oi_pcr)
c3.metric("Volume PCR", vol_pcr)
c4.metric("Net GEX", f"{net_gex} Cr")

st.subheader(f"Institutional Option Chain — {asset}")
display_cols = ['ce_spread', 'ce_ltp', 'ce_iv', 'ce_delta', 'ce_oi', 'strike', 'pe_oi', 'pe_delta', 'pe_iv', 'pe_ltp', 'pe_spread']
st.dataframe(chain_df[display_cols], use_container_width=True)
