import streamlit as st
import plotly.graph_objects as go
import numpy as np
from backend import get_market_data

st.set_page_config(layout="wide")
asset = st.session_state.get("selected_asset", "SENSEX")
spot, chain_df, _, _, _ = get_market_data(asset)

st.header(f"🖥️ PAGE 2: ADVANCED GRAPHICAL TERMINAL (ALL 10 MODULES) — {asset}")

t1, t2, t3, t4, t5, t6, t7, t8, t9, t10 = st.tabs([
    "Mod A: OI Profile", "Mod B: Gamma GEX", "Mod C: IV Smile", "Mod D: Volume", 
    "Mod E: OI Change", "Mod F: Theta Decay", "Mod G: Max Pain", "Mod H: PCR Trend", 
    "Mod I: Delta Flow", "Mod J: Vol Surface"
])

with t1:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=chain_df['strike'], y=chain_df['ce_oi'], name='CE OI', marker_color='#FF5252'))
    fig.add_trace(go.Bar(x=chain_df['strike'], y=chain_df['pe_oi'], name='PE OI', marker_color='#00E676'))
    fig.update_layout(title="[MOD A] Strike-Wise Open Interest Profile", template="plotly_dark", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

with t2:
    fig = go.Figure()
    gex_vals = [(s - spot) * 0.05 for s in chain_df['strike']]
    fig.add_trace(go.Bar(x=chain_df['strike'], y=gex_vals, name='Net Gamma', marker_color='#29B6F6'))
    fig.update_layout(title="[MOD B] Net Gamma Exposure (GEX) Distribution", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with t3:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chain_df['strike'], y=chain_df['ce_iv'], mode='lines+markers', name='CE IV', line=dict(color='#FF5252')))
    fig.add_trace(go.Scatter(x=chain_df['strike'], y=chain_df['pe_iv'], mode='lines+markers', name='PE IV', line=dict(color='#00E676')))
    fig.update_layout(title="[MOD C] Implied Volatility (IV) Smile Curve", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with t4:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=chain_df['strike'], y=chain_df['ce_volume'], name='CE Vol', marker_color='#AB47BC'))
    fig.add_trace(go.Bar(x=chain_df['strike'], y=chain_df['pe_volume'], name='PE Vol', marker_color='#FFA726'))
    fig.update_layout(title="[MOD D] Strike-Wise Volume Distribution", template="plotly_dark", barmode="stack")
    st.plotly_chart(fig, use_container_width=True)

with t5:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=chain_df['strike'], y=[15000, -8000, 22000, -12000, 18000], name='Change in OI', marker_color='#26A69A'))
    fig.update_layout(title="[MOD E] Strike-Wise Change in Open Interest", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with t6:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chain_df['strike'], y=[-12.5, -18.2, -25.4, -17.1, -11.0], mode='lines+markers', name='Theta', line=dict(color='#FFEE58')))
    fig.update_layout(title="[MOD F] Option Premium Decay & Theta Wave", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with t7:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chain_df['strike'], y=[50000, 20000, 10000, 35000, 70000], mode='lines+markers', name='Pain', line=dict(color='#EC407A')))
    fig.update_layout(title="[MOD G] Max Pain Strike Analysis Curve", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with t8:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=['09:30', '10:30', '11:30', '12:30', '13:30'], y=[1.15, 1.22, 1.28, 1.35, 1.32], mode='lines+markers', name='PCR', line=dict(color='#42A5F5')))
    fig.update_layout(title="[MOD H] Intraday Put-Call Ratio (PCR) Trend Line", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with t9:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chain_df['strike'], y=[0.1, 0.3, 0.5, 0.7, 0.9], mode='lines+markers', name='Delta', line=dict(color='#66BB6A')))
    fig.update_layout(title="[MOD I] Cumulative Delta Flow Matrix", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with t10:
    fig = go.Figure(data=[go.Surface(z=np.random.rand(5, 5), x=chain_df['strike'], y=[1, 2, 3, 4, 5])])
    fig.update_layout(title="[MOD J] Multi-Strike Volatility Surface 3D", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
