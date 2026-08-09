import streamlit as st

st.set_page_config(
    page_title="Help Center & Support Desk",
    page_icon="🛠️",
    layout="wide"
)

st.markdown("## 🛠️ Quant Terminal Pro — Help Center & Support Desk")
st.markdown("---")

# Quick Navigation Header
st.markdown("""
Welcome to the official support and documentation hub for **Quant Terminal Pro**. Below you will find a comprehensive guide on how to configure your credentials, navigate modules, and utilize quantitative analytics effectively.
""")

# Expandable Sections for Clean UI
with st.expander("🔐 1. Broker Authentication & API Setup", expanded=True):
    st.markdown("""
    * **Step 1:** Navigate to the main home page (`app.py`).
    * **Step 2:** Look at the left sidebar under the **Broker Authentication** section.
    * **Step 3:** Enter your **Dhan Client ID** and secure **Access Token**.
    * **Step 4:** Click **Connect & Save Credentials** to authorize the application. Once connected, a green status badge will appear confirming active data pipelines.
    """)

with st.expander("📊 2. Master Option Chain & Quantitative Desk", expanded=False):
    st.markdown("""
    * **Embedded Asset Selector:** At the top of the Master Option Chain page, use the asset dropdown to instantly switch between indices and equities (e.g., NIFTY, BANKNIFTY, SENSEX, RELIANCE, TCS, SBIN).
    * **Expiry Sync:** Expiry dates are fetched directly in real-time from the broker server, with the nearest active expiry selected by default.
    * **Mirror-Image Layout:** The option chain follows an institutional standard layout with Strike Price centered, flanked immediately by LTP, Bid/Ask prices, Open Interest, Volumes, and advanced Greeks ($\Delta, \Gamma, \Theta, \nu, \text{GEX}$).
    """)

with st.expander("⚙️ 3. Lot Size & View Preferences", expanded=False):
    st.markdown("""
    * **Server-Synced Lot Sizes:** Lot sizes are automatically retrieved from the universal scrip master database corresponding to the active asset.
    * **Manual Override:** If required, you can override or verify the lot size using the sidebar control input.
    * **Column Manager:** Toggle quantitative Greeks and concentration metrics on or off using the view preference checkboxes in the sidebar.
    """)

with st.expander("🚀 4. Multi-Page Analytical Modules", expanded=False):
    st.markdown("""
    * **Graphical Terminal:** Interactive visual charts for technical and quantitative trend analysis.
    * **Gamma Flip Gatekeeper:** Tracks dealer gamma exposure profiles and zero-gamma inflection pivots.
    * **Quant Screener Bot:** Automated filtering tool for discovering high-probability setup opportunities.
    * **Historical Time Travel:** Replay past market states and historical tick data for backtesting.
    """)

st.markdown("---")
st.markdown("### 💡 Troubleshooting & Support")
st.info("""
If you encounter data fetch delays or connection drops:
1. Verify that your Dhan API token has not expired.
2. Check your internet connection.
3. Refresh the app cache from the Streamlit menu if layout discrepancies occur.
""")
