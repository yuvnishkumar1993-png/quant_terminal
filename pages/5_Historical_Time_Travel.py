import streamlit as st
from historical_db_manager import HistoricalDBManager

st.title("🕰️ PAGE 5: HISTORICAL TIME-TRAVEL & BACKTESTING")

asset = st.session_state.get("selected_asset", "SENSEX")
db_manager = HistoricalDBManager()

hist_df = db_manager.get_historical_snapshots(asset)

if not hist_df.empty:
    st.subheader(f"📊 Historical Snapshots Log for {asset}")
    st.dataframe(hist_df, use_container_width=True)
else:
    st.info("No historical snapshots logged yet for this asset. Keep the engine running to record snapshots.")
