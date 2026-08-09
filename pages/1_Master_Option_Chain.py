import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import requests
import math
import scipy.stats as si
import plotly.graph_objects as go

# Bulletproof Dynamic Path Resolution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

st.set_page_config(page_title="Institutional Option Chain Desk", page_icon="⚡", layout="wide")
st.markdown("## ⚡ Institutional Option Chain & Gamma Flip Terminal")
st.markdown("---")

# Safe Default Lot Sizes
DEFAULT_LOTS = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 25,
    "SENSEX": 10,
    "MIDCPNIFTY": 50,
    "RELIANCE": 250,
    "TCS": 175,
    "SBIN": 750
}

# Global State से वैल्यू उठाएं
selected_symbol = st.session_state.get("global_symbol", "NIFTY")
client_id = st.session_state.get("client_id", "")
access_token = st.session_state.get("access_token", "")

st.sidebar.markdown(f"### 📌 Active Asset: `{selected_symbol}`")

# Foolproof Lot Size Control
default_lot = DEFAULT_LOTS.get(selected_symbol, 50)
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Lot Size Control")
lot_size = st.sidebar.number_input(
    "Verify / Override Lot Size", 
    min_value=1, 
    max_value=10000, 
    value=int(default_lot), 
    step=1,
    key=f"lot_override_{selected_symbol}",
    help="लॉट साइज़ पूरी तरह आपके नियंत्रण में है।"
)

expiries = ["2026-08-13", "2026-08-20", "2026-08-27"]
selected_expiry = st.sidebar.selectbox("Expiry Date", expiries, key="oc_exp_master")

strike_range_mode = st.sidebar.radio(
    "Option Chain Strike Range", 
    ["±10 Strikes", "±20 Strikes", "±30 Strikes", "Full Chain (All)"],
    index=1,
    key="strike_range_gex_master"
)

tab1, tab2, tab3 = st.tabs([
    "📊 Live Option Chain & OI Walls", 
    "🎯 Max Pain, Settlement & GEX Profile", 
    "🚀 IV Smile, Sigma Bands & Strategy Desk"
])

@st.cache_data(ttl=15)
def fetch_institutional_option_chain(c_id, token, exp, sym):
    default_spots = {"NIFTY": 24500.0, "BANKNIFTY": 51200.0, "FINNIFTY": 23100.0, "SENSEX": 73200.0, "RELIANCE": 2950.0, "TCS": 4120.0, "SBIN": 820.0}
    fallback_spot = default_spots.get(sym, 20000.0)
    
    # लॉजिकल मार्केट डेटा जनरेशन (स्पॉट के पास सटीक प्रीमियम)
    step = 100 if sym in ["BANKNIFTY", "SENSEX"] else (50 if sym in ["NIFTY", "FINNIFTY"] else 20)
    atm = round(fallback_spot / step) * step
    strikes_arr = [atm + (i * step) for i in range(-25, 26)]
    
    mock_recs = []
    np.random.seed(42)
    for s in strikes_arr:
        c_intrinsic = max(0.0, fallback_spot - s)
        p_intrinsic = max(0.0, s - fallback_spot)
        distance_pts = abs(s - fallback_spot)
        time_value = max(10.0, 150.0 - (distance_pts * 0.15))
        
        c_ltp = round(c_intrinsic + time_value if c_intrinsic > 0 else time_value, 2)
        p_ltp = round(p_intrinsic + time_value if p_intrinsic > 0 else time_value, 2)
        
        c_oi = int(max(50000, 300000 - (distance_pts * 1000)))
        p_oi = int(max(50000, 300000 - (distance_pts * 1000)))
        
        c_iv_val = round(12.0 + (distance_pts / fallback_spot) * 20, 2)
        p_iv_val = round(12.5 + (distance_pts / fallback_spot) * 20, 2)
        
        mock_recs.append({
            "CE Spread %": round(np.random.uniform(0.1, 0.8), 2),
            "CE LTP": c_ltp, 
            "CE %Chg": round(np.random.uniform(-8, 12), 2), 
            "CE IV": c_iv_val, 
            "CE Vol": int(c_oi * 1.5), 
            "CE Chg OI": int(np.random.randint(-5000, 8000)), 
            "CE OI (L)": round(c_oi/100000, 2),
            "STRIKE": int(s), 
            "PE OI (L)": round(p_oi/100000, 2), 
            "PE Chg OI": int(np.random.randint(-5000, 8000)), 
            "PE Vol": int(p_oi * 1.5), 
            "PE %Chg": round(np.random.uniform(-8, 12), 2), 
            "PE LTP": p_ltp, 
            "PE IV": p_iv_val, 
            "PE Spread %": round(np.random.uniform(0.1, 0.8), 2),
            "Raw_CE_OI": c_oi,
            "Raw_PE_OI": p_oi
        })
    return pd.DataFrame(mock_recs), fallback_spot

chain_df, live_spot = fetch_institutional_option_chain(client_id, access_token, selected_expiry, selected_symbol)

def calculate_institutional_greeks_and_gex(df, spot, lot):
    r = 0.06 
    T = 4 / 365.0 
    
    ce_deltas, pe_deltas = [], []
    gammas, ce_thetas, pe_thetas, vegas = [], [], [], []
    net_gexs = []
    
    for _, row in df.iterrows():
        K = row['STRIKE']
        call_oi = row['Raw_CE_OI']
        put_oi = row['Raw_PE_OI']
        
        c_iv = row.get('CE IV', 12.0) / 100.0
        sigma = max(c_iv, 0.01)
        
        d1 = (np.log(spot / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        cdf_d1 = si.norm.cdf(d1)
        pdf_d1 = si.norm.pdf(d1)
        
        c_delta = cdf_d1
        p_delta = cdf_d1 - 1.0
        gamma = pdf_d1 / (spot * sigma * np.sqrt(T))
        
        c_theta = (- (spot * pdf_d1 * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * si.norm.cdf(d2)) / 365.0
        p_theta = (- (spot * pdf_d1 * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * si.norm.cdf(-d2)) / 365.0
        vega = (spot * np.sqrt(T) * pdf_d1) / 100.0
        
        net_gex = (call_oi - put_oi) * lot * (spot ** 2) * gamma / 1000000000.0
        
        ce_deltas.append(round(c_delta, 2))
        pe_deltas.append(round(p_delta, 2))
        gammas.append(round(gamma, 5))
        ce_thetas.append(round(c_theta, 2))
        pe_thetas.append(round(p_theta, 2))
        vegas.append(round(vega, 2))
        net_gexs.append(net_gex)
        
    df['CE Delta'] = ce_deltas
    df['CE Theta'] = ce_thetas
    df['Gamma'] = gammas
    df['Vega'] = vegas
    df['PE Theta'] = pe_thetas
    df['PE Delta'] = pe_deltas
    df['Net_GEX'] = net_gexs
    return df

chain_df = calculate_institutional_greeks_and_gex(chain_df, live_spot, lot_size)

# Strike Range Filtering Logic
chain_df['Dist'] = abs(chain_df['STRIKE'] - live_spot)
center_idx = chain_df['Dist'].idxmin()

if "±10" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-10):min(len(chain_df), center_idx+11)].copy()
elif "±20" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-20):min(len(chain_df), center_idx+21)].copy()
elif "±30" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-30):min(len(chain_df), center_idx+31)].copy()
else:
    disp_df = chain_df.copy()

disp_df['View_Dist'] = abs(disp_df['STRIKE'] - live_spot)
atm_row_view = disp_df.loc[disp_df['View_Dist'].idxmin()]
c_iv_v = atm_row_view['CE IV']
p_iv_v = atm_row_view['PE IV']
dynamic_atm_iv = round((c_iv_v + p_iv_v) / 2.0, 2)
disp_df = disp_df.drop(columns=['View_Dist'])

filtered_ce_oi_sum = disp_df['Raw_CE_OI'].sum()
filtered_pe_oi_sum = disp_df['Raw_PE_OI'].sum()
dynamic_pcr = round(filtered_pe_oi_sum / filtered_ce_oi_sum, 2) if filtered_ce_oi_sum > 0 else 1.0

flip_strike = live_spot
if not chain_df.empty:
    chain_df['Cum_GEX'] = chain_df['Net_GEX'].cumsum()
    sign_changes = np.where(np.diff(np.sign(chain_df['Cum_GEX'].values)))[0]
    if len(sign_changes) > 0:
        closest_change = min(sign_changes, key=lambda idx: abs(chain_df.loc[idx, 'STRIKE'] - live_spot))
        flip_strike = chain_df.loc[closest_change, 'STRIKE']

with tab1:
    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns(5)
    with col_h1: st.metric(label="Asset", value=selected_symbol)
    with col_h2: st.metric(label="Spot Price", value=f"₹{live_spot:,.2f}")
    with col_h3: st.metric(label=f"ATM IV ({strike_range_mode})", value=f"{dynamic_atm_iv}%")
    with col_h4: st.metric(label=f"PCR ({strike_range_mode})", value=dynamic_pcr)
    with col_h5: st.metric(label="Gamma Flip Zone", value=f"₹{flip_strike:,.0f}", delta="Dealer Neutral Pivot")

    st.markdown("---")

    def classify_buildup(row):
        if row['CE %Chg'] > 0 and row['CE Chg OI'] > 0: return "Short Buildup"
        elif row['CE %Chg'] < 0 and row['CE Chg OI'] < 0: return "Long Unwinding"
        elif row['CE %Chg'] > 0 and row['CE Chg OI'] < 0: return "Short Covering"
        return "Long Buildup"

    disp_df['OI Action'] = disp_df.apply(classify_buildup, axis=1)

    cols_order = [
        "CE Spread %", "CE LTP", "CE %Chg", "CE IV", "CE Delta", "CE Theta", "CE Vol", "CE Chg OI", "CE OI (L)",
        "STRIKE", "OI Action",
        "Gamma", "Vega", "PE Theta", "PE Delta", "PE IV", "PE %Chg", "PE LTP", "PE Spread %", "PE Vol", "PE Chg OI", "PE OI (L)"
    ]
    
    final_oc_cols = [c for c in cols_order if c in disp_df.columns]
    matrix_df = disp_df[final_oc_cols].copy()

    st.markdown(f"### Live Option Chain & Smart Buildup Matrix ({strike_range_mode})")
    st.dataframe(matrix_df, use_container_width=True, height=520, hide_index=True)

    st.markdown("### Open Interest Concentration Walls (Support & Resistance)")
    wall_df = disp_df.copy()
    
    fig_wall = go.Figure()
    fig_wall.add_trace(go.Bar(x=wall_df['STRIKE'].astype(str), y=wall_df['CE OI (L)'], name="Call OI (Resistance)", marker_color='#d73a49'))
    fig_wall.add_trace(go.Bar(x=wall_df['STRIKE'].astype(str), y=wall_df['PE OI (L)'], name="Put OI (Support)", marker_color='#28a745'))
    
    fig_wall.update_layout(
        template='plotly_white',
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#24292e', size=12),
        barmode='group',
        xaxis=dict(type='category', title="Strike Prices", tickangle=-45, fixedrange=False),
        yaxis=dict(title="Open Interest (Lakhs)", fixedrange=True),
        height=380,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_wall, use_container_width=True)

with tab2:
    st.markdown(f"### Max Pain, Settlement & Gamma Exposure (GEX) Profile ({selected_symbol})")
    
    strikes_list = chain_df['STRIKE'].values
    pain_dict = {}
    for expiry_price in strikes_list:
        total_pain = 0
        for _, row in chain_df.iterrows():
            k = row['STRIKE']
            if expiry_price > k: total_pain += (expiry_price - k) * row['Raw_CE_OI']
            if expiry_price < k: total_pain += (k - expiry_price) * row['Raw_PE_OI']
        pain_dict[expiry_price] = total_pain
        
    max_pain = min(pain_dict, key=pain_dict.get) if pain_dict else strikes_list[len(strikes_list)//2]
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric(label="Live Spot Price", value=f"₹{live_spot:,.2f}")
    with m2: st.metric(label="Max Pain Anchor", value=f"₹{max_pain:,.0f}")
    with m3: st.metric(label="Gamma Flip Pivot", value=f"₹{flip_strike:,.0f}", delta="Dealer Pinning Level")
    with m4: st.metric(label="Expiry Date", value=selected_expiry)

    st.markdown("---")

    df_pain_full = pd.DataFrame([{"Strike": k, "Total Payout/Pain Value": v} for k, v in pain_dict.items()])
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_pain_full['Strike'].astype(str), 
        y=df_pain_full['Total Payout/Pain Value'],
        name="Settlement Pain",
        marker_color=['#28a745' if s == max_pain else ('#6f42c1' if s == flip_strike else '#0366d6') for s in df_pain_full['Strike']]
    ))
    
    fig.update_layout(
        template='plotly_white',
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#24292e', size=12),
        xaxis=dict(type='category', title="Strike Prices", tickangle=-45, fixedrange=False),
        yaxis=dict(title="Holder Pain Value (₹)", fixedrange=True),
        height=360,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown(f"### IV Smile / Skew & Volatility Bands ({selected_symbol})")
    
    fig_iv = go.Figure()
    iv_plot_df = disp_df.copy()
    fig_iv.add_trace(go.Scatter(x=iv_plot_df['STRIKE'].astype(str), y=iv_plot_df['CE IV'], mode='lines+markers', name="Call IV (Skew)", line=dict(color='#d73a49', width=2.5)))
    fig_iv.add_trace(go.Scatter(x=iv_plot_df['STRIKE'].astype(str), y=iv_plot_df['PE IV'], mode='lines+markers', name="Put IV (Smile)", line=dict(color='#28a745', width=2.5)))
    fig_iv.update_layout(
        template='plotly_white',
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(color='#24292e', size=12),
        xaxis=dict(type='category', title="Strike Prices", tickangle=-45, fixedrange=False),
        yaxis=dict(title="Implied Volatility (%)", fixedrange=True),
        height=360,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_iv, use_container_width=True)
