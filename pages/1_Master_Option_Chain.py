import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as si
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from dhan_api_engine import InstitutionalDataEngine

st.set_page_config(page_title="Institutional Option Chain Desk", page_icon="⚡", layout="wide")
st.markdown("## ⚡ Institutional Mirror-Image Option Chain & Quant Desk")
st.markdown("---")

# --- TOP EMBEDDED CONTROLS ---
col_c1, col_c2, col_c3 = st.columns([2, 2, 4])

with col_c1:
    all_symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "RELIANCE", "TCS", "SBIN"]
    current_idx = all_symbols.index(st.session_state.get("global_symbol", "NIFTY")) if st.session_state.get("global_symbol", "NIFTY") in all_symbols else 0
    selected_symbol = st.selectbox("📌 Underlying Asset", all_symbols, index=current_idx, key="page_asset_sel")
    st.session_state.global_symbol = selected_symbol

client_id = st.session_state.get("client_id", "")
access_token = st.session_state.get("access_token", "")

@st.cache_data(ttl=3600)
def get_server_config(symbol):
    df_scrip = InstitutionalDataEngine.load_scrip_master()
    if not df_scrip.empty:
        match = df_scrip[df_scrip['SEM_TRADING_SYMBOL'].str.upper() == symbol.upper()]
        if not match.empty:
            row = match.iloc[0]
            return int(row['SEM_SMST_SECURITY_ID']), str(row['SEM_SEGMENT']), int(row.get('SEM_LOT_SIZE', 25))
            
    master_dict = {
        "NIFTY": {"sec_id": 13, "seg": "IDX_I", "lot": 25},
        "BANKNIFTY": {"sec_id": 25, "seg": "IDX_I", "lot": 15},
        "FINNIFTY": {"sec_id": 27, "seg": "IDX_I", "lot": 25},
        "SENSEX": {"sec_id": 51, "seg": "BSE_IDX", "lot": 10},
        "RELIANCE": {"sec_id": 2885, "seg": "NSE_EQ", "lot": 250},
        "TCS": {"sec_id": 11536, "seg": "NSE_EQ", "lot": 175},
        "SBIN": {"sec_id": 3045, "seg": "NSE_EQ", "lot": 750}
    }
    cfg = master_dict.get(symbol.upper(), {"sec_id": 13, "seg": "IDX_I", "lot": 25})
    return cfg["sec_id"], cfg["seg"], cfg["lot"]

sec_id, seg, server_lot = get_server_config(selected_symbol)
expiries = InstitutionalDataEngine.fetch_expiries(client_id, access_token, sec_id, seg)

with col_c2:
    selected_expiry = st.selectbox("📅 Expiry Date", expiries, key=f"exp_{selected_symbol}")

strike_range_mode = st.sidebar.selectbox(
    "Option Chain Strike Range", 
    ["±5 Strikes", "±10 Strikes", "±20 Strikes", "±30 Strikes", "Full Chain (All)"],
    index=1,
    key=f"range_{selected_symbol}"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ View Preferences")
show_greeks = st.sidebar.checkbox("Show Quantitative Greeks & GEX", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Lot Size")
lot_size = st.sidebar.number_input(
    "Override Lot Size", 
    min_value=1, 
    max_value=10000, 
    value=int(server_lot), 
    step=1,
    key=f"lot_{selected_symbol}"
)

# --- FETCH DATA ---
chain_df, live_spot = InstitutionalDataEngine.fetch_live_option_chain(
    client_id, access_token, sec_id, seg, selected_expiry, selected_symbol
)

if "Raw_CE_OI" not in chain_df.columns and "CE_OI" in chain_df.columns:
    chain_df["Raw_CE_OI"] = chain_df["CE_OI"]
    chain_df["Raw_PE_OI"] = chain_df["PE_OI"]

# Comprehensive Calculation Engine (Greeks & GEX)
def calculate_comprehensive_metrics(df, spot, lot):
    r = 0.06 
    try:
        T = max(1.0, (datetime.strptime(selected_expiry, "%Y-%m-%d") - datetime.now()).days) / 365.0
    except Exception:
        T = 4 / 365.0
    
    ce_deltas, pe_deltas = [], []
    gammas, ce_thetas, pe_thetas, vegas = [], [], [], []
    ce_gexs, pe_gexs = [], []
    
    for _, row in df.iterrows():
        K = row['Strike']
        call_oi = row.get('Raw_CE_OI', row.get('CE_OI', 100000))
        put_oi = row.get('Raw_PE_OI', row.get('PE_OI', 100000))
        
        c_iv = max(5.0, row.get('CE_IV', 14.0)) / 100.0
        p_iv = max(5.0, row.get('PE_IV', 14.5)) / 100.0
        sigma = (c_iv + p_iv) / 2.0
        
        try:
            d1 = (np.log(spot / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            cdf_d1 = si.norm.cdf(d1)
            pdf_d1 = si.norm.pdf(d1)
            
            c_delta = round(cdf_d1, 2)
            p_delta = round(cdf_d1 - 1.0, 2)
            gamma = round(pdf_d1 / (spot * sigma * np.sqrt(T)), 5)
            c_theta = round((- (spot * pdf_d1 * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * si.norm.cdf(d1 - sigma * np.sqrt(T))) / 365.0, 2)
            p_theta = round((- (spot * pdf_d1 * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * si.norm.cdf(-d1 + sigma * np.sqrt(T))) / 365.0, 2)
            vega = round((spot * np.sqrt(T) * pdf_d1) / 100.0, 2)
        except Exception:
            c_delta, p_delta, gamma, c_theta, p_theta, vega = 0.5, -0.5, 0.001, -5.0, -5.0, 10.0

        # GEX calculation in Crores per strike side
        ce_gex = round(call_oi * lot * (spot ** 2) * gamma / 100000000.0, 2)
        pe_gex = round(put_oi * lot * (spot ** 2) * gamma / 100000000.0, 2)

        ce_deltas.append(c_delta)
        pe_deltas.append(p_delta)
        gammas.append(gamma)
        ce_thetas.append(c_theta)
        pe_thetas.append(p_theta)
        vegas.append(vega)
        ce_gexs.append(ce_gex)
        pe_gexs.append(pe_gex)
        
    df['CE Delta'] = ce_deltas
    df['PE Delta'] = pe_deltas
    df['Gamma'] = gammas
    df['CE Theta'] = ce_thetas
    df['PE Theta'] = pe_thetas
    df['CE Vega'] = vegas
    df['PE Vega'] = vegas
    df['CE GEX (Cr)'] = ce_gexs
    df['PE GEX (Cr)'] = pe_gexs
    return df

chain_df = calculate_comprehensive_metrics(chain_df, live_spot, lot_size)

# Strike Range Filtering Logic
chain_df['Dist'] = abs(chain_df['Strike'] - live_spot)
center_idx = chain_df['Dist'].idxmin()

if "±5" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-5):min(len(chain_df), center_idx+6)].copy()
elif "±10" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-10):min(len(chain_df), center_idx+11)].copy()
elif "±20" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-20):min(len(chain_df), center_idx+21)].copy()
elif "±30" in strike_range_mode:
    disp_df = chain_df.iloc[max(0, center_idx-30):min(len(chain_df), center_idx+31)].copy()
else:
    disp_df = chain_df.copy()

# Summary Metrics Bar
disp_df['View_Dist'] = abs(disp_df['Strike'] - live_spot)
atm_row = disp_df.loc[disp_df['View_Dist'].idxmin()]
atm_iv = round((atm_row.get('CE_IV', 14.0) + atm_row.get('PE_IV', 14.5)) / 2.0, 2)
disp_df = disp_df.drop(columns=['View_Dist'])

f_ce_oi = disp_df['Raw_CE_OI'].sum() if 'Raw_CE_OI' in disp_df.columns else disp_df['CE_OI'].sum()
f_pe_oi = disp_df['Raw_PE_OI'].sum() if 'Raw_PE_OI' in disp_df.columns else disp_df['PE_OI'].sum()
pcr_val = round(f_pe_oi / f_ce_oi, 2) if f_ce_oi > 0 else 1.0

st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Underlying Asset", selected_symbol)
with m2: st.metric("Live Spot Price", f"₹{live_spot:,.2f}")
with m3: st.metric("ATM Implied Volatility", f"{atm_iv}%")
with m4: st.metric("Put-Call Ratio (PCR)", pcr_val)
st.markdown("---")

# Format columns for mirror display
disp_df['STRIKE'] = disp_df['Strike']
disp_df['CE OI (L)'] = round(disp_df.get('Raw_CE_OI', disp_df.get('CE_OI', 0)) / 100000, 2)
disp_df['PE OI (L)'] = round(disp_df.get('Raw_PE_OI', disp_df.get('PE_OI', 0)) / 100000, 2)
disp_df['CE Vol (M)'] = round(disp_df.get('CE_Volume', 0) / 1000000, 2)
disp_df['PE Vol (M)'] = round(disp_df.get('PE_Volume', 0) / 1000000, 2)

# Simulated Bid/Ask based on LTP for completeness
disp_df['CE Bid'] = round(disp_df['CE_LTP'] * 0.99, 2)
disp_df['CE Ask'] = round(disp_df['CE_LTP'] * 1.01, 2)
disp_df['PE Bid'] = round(disp_df['PE_LTP'] * 0.99, 2)
disp_df['PE Ask'] = round(disp_df['PE_LTP'] * 1.01, 2)

# --- STRICT INSTITUTIONAL MIRROR MATRIX LAYOUT ---
# Order from Left (Call Side Far) -> Center (Strike) -> Right (Put Side Far)
matrix_cols = [
    "CE Vol (M)", "CE OI (L)", "CE_Chg_OI", "CE Ask", "CE Bid", "CE_IV", "CE_%Chg", "CE_LTP"
]
if show_greeks:
    matrix_cols += ["CE Delta", "Gamma", "CE Theta", "CE Vega", "CE GEX (Cr)"]

# CENTER STRIKE PRICE
matrix_cols += ["STRIKE"]

if show_greeks:
    matrix_cols += ["PE GEX (Cr)", "PE Vega", "PE Theta", "Gamma", "PE Delta"]

matrix_cols += [
    "PE_LTP", "PE_%Chg", "PE_IV", "PE Bid", "PE Ask", "PE_Chg_OI", "PE OI (L)", "PE Vol (M)"
]

final_cols = [c for c in matrix_cols if c in disp_df.columns]
matrix_df = disp_df[final_cols].copy()
matrix_df = matrix_df.loc[:, ~matrix_df.columns.duplicated()]

st.markdown(f"### 📊 Institutional Mirror Option Chain Matrix ({strike_range_mode})")
st.dataframe(matrix_df, use_container_width=True, height=600, hide_index=True)
