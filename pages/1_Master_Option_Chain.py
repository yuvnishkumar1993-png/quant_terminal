import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as si
import plotly.graph_objects as go

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from dhan_api_engine import InstitutionalDataEngine

st.set_page_config(page_title="Institutional Option Chain Desk", page_icon="⚡", layout="wide")
st.markdown("## ⚡ Institutional Option Chain & Gamma Flip Terminal")
st.markdown("---")

selected_symbol = st.session_state.get("global_symbol", "NIFTY")
client_id = st.session_state.get("client_id", "")
access_token = st.session_state.get("access_token", "")

st.sidebar.markdown(f"### 📌 Active Asset: `{selected_symbol}`")

# Guaranteed Direct Mapping (Prevents wrong default fallback to NIFTY)
@st.cache_data(ttl=3600)
def get_asset_master_config(symbol):
    master_dict = {
        "NIFTY": {"sec_id": 13, "seg": "IDX_I", "lot": 25},
        "BANKNIFTY": {"sec_id": 25, "seg": "IDX_I", "lot": 15},
        "FINNIFTY": {"sec_id": 27, "seg": "IDX_I", "lot": 25},
        "SENSEX": {"sec_id": 51, "seg": "BSE_IDX", "lot": 10},
        "RELIANCE": {"sec_id": 2885, "seg": "NSE_EQ", "lot": 250},
        "TCS": {"sec_id": 11536, "seg": "NSE_EQ", "lot": 175},
        "SBIN": {"sec_id": 3045, "seg": "NSE_EQ", "lot": 750}
    }
    
    # Primary check from dictionary
    if symbol.upper() in master_dict:
        cfg = master_dict[symbol.upper()]
        return cfg["sec_id"], cfg["seg"], cfg["lot"]
        
    # Secondary check from Scrip Master CSV
    df_scrip = InstitutionalDataEngine.load_scrip_master()
    if not df_scrip.empty:
        match = df_scrip[df_scrip['SEM_TRADING_SYMBOL'].str.upper() == symbol.upper()]
        if not match.empty:
            row = match.iloc[0]
            return int(row['SEM_SMST_SECURITY_ID']), str(row['SEM_SEGMENT']), int(row.get('SEM_LOT_SIZE', 25))
            
    return 13, "IDX_I", 25

sec_id, seg, auto_lot_size = get_asset_master_config(selected_symbol)

# Expiry fetch based on active asset
expiries = InstitutionalDataEngine.fetch_expiries(client_id, access_token, sec_id, seg)
selected_expiry = st.sidebar.selectbox("Expiry Date", expiries, key=f"exp_{selected_symbol}")

strike_range_mode = st.sidebar.radio(
    "Option Chain Strike Range", 
    ["±10 Strikes", "±20 Strikes", "±30 Strikes", "Full Chain (All)"],
    index=1,
    key=f"range_{selected_symbol}"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Lot Size Control")
lot_size = st.sidebar.number_input(
    "Verify / Override Lot Size", 
    min_value=1, 
    max_value=10000, 
    value=int(auto_lot_size), 
    step=1,
    key=f"lot_{selected_symbol}",
    help="ऑटो-डिटेक्टेड लॉट साइज़।"
)

tab1, tab2, tab3 = st.tabs([
    "📊 Live Option Chain & OI Walls", 
    "🎯 Max Pain, Settlement & GEX Profile", 
    "🚀 IV Smile, Sigma Bands & Strategy Desk"
])

# Fetch data unique to selected asset, sec_id, and expiry
chain_df, live_spot = InstitutionalDataEngine.fetch_live_option_chain(
    client_id, access_token, sec_id, seg, selected_expiry, selected_symbol
)

if "Raw_CE_OI" not in chain_df.columns and "CE_OI" in chain_df.columns:
    chain_df["Raw_CE_OI"] = chain_df["CE_OI"]
    chain_df["Raw_PE_OI"] = chain_df["PE_OI"]

def calculate_institutional_greeks_and_gex(df, spot, lot):
    r = 0.06 
    T = 4 / 365.0 
    ce_deltas, pe_deltas = [], []
    gammas, ce_thetas, pe_thetas, vegas = [], [], [], []
    net_gexs = []
    
    for _, row in df.iterrows():
        K = row['Strike']
        call_oi = row.get('Raw_CE_OI', row.get('CE_OI', 100000))
        put_oi = row.get('Raw_PE_OI', row.get('PE_OI', 100000))
        c_iv = row.get('CE_IV', row.get('CE IV', 14.0)) / 100.0
        sigma = max(c_iv, 0.01)
        
        try:
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
        except Exception:
            c_delta, p_delta, gamma, c_theta, p_theta, vega = 0.5, -0.5, 0.001, -5.0, -5.0, 10.0

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

chain_df['Dist'] = abs(chain_df['Strike'] - live_spot)
center_idx = chain_df['Dist'].idxmin()

if "±10" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-10):min(len(chain_df), center_idx+11)].copy()
elif "±20" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-20):min(len(chain_df), center_idx+21)].copy()
elif "±30" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-30):min(len(chain_df), center_idx+31)].copy()
else:
    disp_df = chain_df.copy()

disp_df['View_Dist'] = abs(disp_df['Strike'] - live_spot)
atm_row_view = disp_df.loc[disp_df['View_Dist'].idxmin()]
c_iv_v = atm_row_view.get('CE_IV', atm_row_view.get('CE IV', 14.0))
p_iv_v = atm_row_view.get('PE_IV', atm_row_view.get('PE IV', 14.5))
dynamic_atm_iv = round((c_iv_v + p_iv_v) / 2.0, 2)
disp_df = disp_df.drop(columns=['View_Dist'])

filtered_ce_oi_sum = disp_df['Raw_CE_OI'].sum() if 'Raw_CE_OI' in disp_df.columns else disp_df['CE_OI'].sum()
filtered_pe_oi_sum = disp_df['Raw_PE_OI'].sum() if 'Raw_PE_OI' in disp_df.columns else disp_df['PE_OI'].sum()
dynamic_pcr = round(filtered_pe_oi_sum / filtered_ce_oi_sum, 2) if filtered_ce_oi_sum > 0 else 1.0

flip_strike = live_spot
if not chain_df.empty:
    chain_df['Cum_GEX'] = chain_df['Net_GEX'].cumsum()
    sign_changes = np.where(np.diff(np.sign(chain_df['Cum_GEX'].values)))[0]
    if len(sign_changes) > 0:
        closest_change = min(sign_changes, key=lambda idx: abs(chain_df.loc[idx, 'Strike'] - live_spot))
        flip_strike = chain_df.loc[closest_change, 'Strike']

with tab1:
    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns(5)
    with col_h1: st.metric(label="Asset", value=selected_symbol)
    with col_h2: st.metric(label="Spot Price", value=f"₹{live_spot:,.2f}")
    with col_h3: st.metric(label=f"ATM IV ({strike_range_mode})", value=f"{dynamic_atm_iv}%")
    with col_h4: st.metric(label=f"PCR ({strike_range_mode})", value=dynamic_pcr)
    with col_h5: st.metric(label="Gamma Flip Zone", value=f"₹{flip_strike:,.0f}", delta="Dealer Neutral Pivot")

    st.markdown("---")

    def classify_buildup(row):
        ce_chg = row.get('CE_Chg_OI', row.get('CE Chg OI', 0))
        ce_pct = row.get('CE_%Chg', row.get('CE %Chg', 0))
        if ce_pct > 0 and ce_chg > 0: return "Short Buildup"
        elif ce_pct < 0 and ce_chg < 0: return "Long Unwinding"
        elif ce_pct > 0 and ce_chg < 0: return "Short Covering"
        return "Long Buildup"

    disp_df['OI Action'] = disp_df.apply(classify_buildup, axis=1)

    disp_df['CE OI (L)'] = round(disp_df.get('Raw_CE_OI', disp_df.get('CE_OI', 0)) / 100000, 2)
    disp_df['PE OI (L)'] = round(disp_df.get('Raw_PE_OI', disp_df.get('PE_OI', 0)) / 100000, 2)
    disp_df['STRIKE'] = disp_df['Strike']

    cols_order = [
        "CE_LTP", "CE_IV", "CE Delta", "CE Theta", "CE_Volume", "CE_Chg_OI", "CE OI (L)",
        "STRIKE", "OI Action",
        "Gamma", "Vega", "PE Theta", "PE Delta", "PE_IV", "PE_LTP", "PE_Volume", "PE_Chg_OI", "PE OI (L)"
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
    
    strikes_list = chain_df['Strike'].values
    pain_dict = {}
    for expiry_price in strikes_list:
        total_pain = 0
        for _, row in chain_df.iterrows():
            k = row['Strike']
            c_oi = row.get('Raw_CE_OI', row.get('CE_OI', 0))
            p_oi = row.get('Raw_PE_OI', row.get('PE_OI', 0))
            if expiry_price > k: total_pain += (expiry_price - k) * c_oi
            if expiry_price < k: total_pain += (k - expiry_price) * p_oi
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
    ce_iv_col = 'CE_IV' if 'CE_IV' in iv_plot_df.columns else 'CE IV'
    pe_iv_col = 'PE_IV' if 'PE_IV' in iv_plot_df.columns else 'PE IV'

    fig_iv.add_trace(go.Scatter(x=iv_plot_df['Strike'].astype(str), y=iv_plot_df[ce_iv_col], mode='lines+markers', name="Call IV (Skew)", line=dict(color='#d73a49', width=2.5)))
    fig_iv.add_trace(go.Scatter(x=iv_plot_df['Strike'].astype(str), y=iv_plot_df[pe_iv_col], mode='lines+markers', name="Put IV (Smile)", line=dict(color='#28a745', width=2.5)))
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
