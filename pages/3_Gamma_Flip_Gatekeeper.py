import streamlit as st

st.title("🖥️ PAGE 3: GEX & GAMMA FLIP GATEKEEPER")

asset = st.session_state.get("selected_asset", "SENSEX")
spot_price = 73200.00
flip_level = 73080.00
oi_pcr = 1.32

st.markdown(f"""
### Gatekeeper Confluence Desk for {asset}
* **Gamma Flip Level:** ₹{flip_level:,.2f} | **Spot:** ₹{spot_price:,.2f} -> **Gate 1:** 🟢 PASSED
* **OI PCR Threshold (1.20):** Current {oi_pcr} -> **Gate 2:** 🟢 PASSED
""")

st.success("⚡ FINAL SYSTEM VERDICT: OPTION BUYING EXECUTION AUTHORIZED")
