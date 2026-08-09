import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from quant_math_core import QuantMathCore

st.title("🖥️ PAGE 2: ADVANCED GRAPHICAL TERMINAL (10 MODULES)")

asset = st.session_state.get("selected_asset", "SENSEX")
st.subheader(f"Visualizing OI & Volatility Flow for {asset}")

strikes = [72800, 73000, 73200, 73400, 73600]
ce_oi = [50000, 80000, 150000, 90000, 40000]
pe_oi = [40000, 110000, 180000, 100000, 30000]

fig = go.Figure()
fig.add_trace(go.Bar(x=strikes, y=ce_oi, name='CE OI', marker_color='#FF5252'))
fig.add_trace(go.Bar(x=strikes, y=pe_oi, name='PE OI', marker_color='#00E676'))
fig.update_layout(title="[MOD A] Strike-Wise OI Profile", template="plotly_dark", barmode="group")
st.plotly_chart(fig, use_container_width=True)
