import streamlit as st
from backend import get_market_data

st.set_page_config(layout="wide")
asset = st.session_state.get("selected_asset", "SENSEX")
spot, _, oi_pcr, _, net_gex = get_market_data(asset)

st.header(f"🖥️ PAGE 3: GEX & GAMMA FLIP GATEKEEPER — {asset}")

flip_level = spot - 120.0
gate1 = spot > flip_level
gate2 = oi_pcr > 1.2
gate3 = net_gex < 50.0

st.markdown(f"""
### 🛡️ Institutional Multi-Gate Confluence System
* **Gate 1 - Gamma Flip Level (लक्ष्मण रेखा):** ₹{flip_level:,.2f} | **Spot:** ₹{spot:,.2f} -> **Status:** {"🟢 PASSED" if gate1 else "🔴 FAILED"}
* **Gate 2 - OI PCR Threshold (1.20):** Current {oi_pcr} -> **Status:** {"🟢 PASSED" if gate2 else "🔴 FAILED"}
* **Gate 3 - Net GEX Regime Check:** Current {net_gex} Cr -> **Status:** {"🟢 PASSED" if gate3 else "🔴 FAILED"}
""")

if gate1 and gate2 and gate3:
    st.success("⚡ FINAL SYSTEM VERDICT: ALL GATES CLEARED — OPTION BUYING EXECUTION AUTHORIZED")
else:
    st.warning("⚠️ FINAL SYSTEM VERDICT: MARKET CONGESTED. EXECUTION RESTRICTED.")
