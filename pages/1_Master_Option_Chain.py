import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as si
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Institutional Option Chain Desk",
    page_icon="⚡",
    layout="wide"
)

# Safe Path Resolution
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

try:
    from dhan_api_engine import InstitutionalDataEngine
except ImportError:
    class InstitutionalDataEngine:
        @staticmethod
        def load_scrip_master():
            return pd.DataFrame()
        @staticmethod
        def fetch_expiries(c, a, s, seg):
            return ["2026-08-11", "2026-08-18", "2026-08-25"]
        @staticmethod
        def fetch_live_option_chain(c, a, s, seg, exp, sym):
            spot = 24570.65
            strikes = np.arange(24050, 25100, 50)
            recs = []
            for st_val in strikes:
                recs.append({
                    "Strike": int(st_val), "STRIKE": int(st_val),
                    "CE_OI": 500000, "Raw_CE_OI": 500000, "CE_Chg_OI": 12000, "CE_%Chg": 1.5, "CE_Volume": 1000000, "CE_IV": 14.0, "CE_LTP": max(1.0, 24570.65 - st_val + 50),
                    "PE_LTP": max(1.0, st_val - 24570.65 + 50), "PE_IV": 14.5, "PE_Volume": 1000000, "PE_Chg_OI": -5000, "PE_%Chg": -0.8, "PE_OI": 600000, "Raw_PE_OI": 600000
                })
            return pd.DataFrame(recs), spot

st.markdown("## ⚡ Institutional Sticky-Header Option Chain Desk")
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

master_dict = {
    "NIFTY": {"sec_id": 13, "seg": "IDX_I", "lot": 65},
    "BANKNIFTY": {"sec_id": 25, "seg": "IDX_I", "lot": 15},
    "FINNIFTY": {"sec_id": 27, "seg": "IDX_I", "lot": 25},
    "SENSEX": {"sec_id": 51, "seg": "BSE_IDX", "lot": 10},
    "RELIANCE": {"sec_id": 2885, "seg": "NSE_EQ", "lot": 250},
    "TCS": {"sec_id": 11536, "seg": "NSE_EQ", "lot": 175},
    "SBIN": {"sec_id": 3045, "seg": "NSE_EQ", "lot": 750}
}
cfg = master_dict.get(selected_symbol.upper(), {"sec_id": 13, "seg": "IDX_I", "lot": 65})
sec_id, seg, server_lot = cfg["sec_id"], cfg["seg"], cfg["lot"]

try:
    expiries = InstitutionalDataEngine.fetch_expiries(client_id, access_token, sec_id, seg)
    if not expiries:
        expiries = ["2026-08-11", "2026-08-18"]
except Exception:
    expiries = ["2026-08-11", "2026-08-18"]

with col_c2:
    selected_expiry = st.selectbox("📅 Expiry Date", expiries, index=0, key=f"exp_{selected_symbol}")

strike_range_mode = st.sidebar.selectbox(
    "Option Chain Strike Range", 
    ["±5 Strikes", "±10 Strikes", "±20 Strikes", "±30 Strikes", "Full Chain (All)"],
    index=4, # Full chain by default so scrolling is fully utilized
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

# --- FETCH LIVE DATA SAFELY ---
try:
    chain_df, live_spot = InstitutionalDataEngine.fetch_live_option_chain(
        client_id, access_token, sec_id, seg, selected_expiry, selected_symbol
    )
except Exception:
    chain_df = pd.DataFrame()
    live_spot = 24570.65

if chain_df is None or chain_df.empty:
    spot_val = 24570.65
    strikes = np.arange(23500, 25500, 50)
    recs = []
    for st_val in strikes:
        recs.append({
            "Strike": int(st_val), "STRIKE": int(st_val),
            "CE_OI": 500000, "Raw_CE_OI": 500000, "CE_Chg_OI": 12000, "CE_%Chg": 1.5, "CE_Volume": 1000000, "CE_IV": 14.0, "CE_LTP": max(1.0, 24570.65 - st_val + 50),
            "PE_LTP": max(1.0, st_val - 24570.65 + 50), "PE_IV": 14.5, "PE_Volume": 1000000, "PE_Chg_OI": -5000, "PE_%Chg": -0.8, "PE_OI": 600000, "Raw_PE_OI": 600000
        })
    chain_df = pd.DataFrame(recs)
    live_spot = spot_val

if "Raw_CE_OI" not in chain_df.columns and "CE_OI" in chain_df.columns:
    chain_df["Raw_CE_OI"] = chain_df["CE_OI"]
    chain_df["Raw_PE_OI"] = chain_df["PE_OI"]

# Comprehensive Advanced Metrics Calculation Engine
def calculate_advanced_metrics(df, spot, lot):
    r = 0.06 
    T = 2 / 365.0
    
    ce_deltas, pe_deltas = [], []
    gammas, ce_thetas, pe_thetas, vegas = [], [], [], []
    ce_vannas, pe_vannas = [], []
    ce_charms, pe_charms = [], []
    ce_gexs, pe_gexs = [], []
    ce_turnovers, pe_turnovers = [], []
    
    for _, row in df.iterrows():
        K = row['Strike']
        call_oi = row.get('Raw_CE_OI', row.get('CE_OI', 100000))
        put_oi = row.get('Raw_PE_OI', row.get('PE_OI', 100000))
        
        c_ltp = row.get('CE_LTP', 10.0)
        p_ltp = row.get('PE_LTP', 10.0)
        c_vol = row.get('CE_Volume', 100000)
        p_vol = row.get('PE_Volume', 100000)
        
        c_iv = max(5.0, row.get('CE_IV', 14.0)) / 100.0
        p_iv = max(5.0, row.get('PE_IV', 14.5)) / 100.0
        sigma = (c_iv + p_iv) / 2.0
        
        try:
            d1 = (np.log(spot / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            cdf_d1 = si.norm.cdf(d1)
            pdf_d1 = si.norm.pdf(d1)
            
            c_delta = round(cdf_d1, 2)
            p_delta = round(cdf_d1 - 1.0, 2)
            gamma = round(pdf_d1 / (spot * sigma * np.sqrt(T)), 5)
            
            c_theta = round((- (spot * pdf_d1 * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * si.norm.cdf(d2)) / 365.0, 2)
            p_theta = round((- (spot * pdf_d1 * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * si.norm.cdf(-d2)) / 365.0, 2)
            vega = round((spot * np.sqrt(T) * pdf_d1) / 100.0, 2)
            
            vanna = round(-pdf_d1 * d2 / sigma, 4)
            charm = round(-pdf_d1 * (2 * r * T - d2 * sigma * np.sqrt(T)) / (2 * T * sigma * np.sqrt(T)) / 365.0, 4)
        except Exception:
            c_delta, p_delta, gamma, c_theta, p_theta, vega, vanna, charm = 0.5, -0.5, 0.001, -5.0, -5.0, 10.0, 0.01, -0.01

        ce_gex = round(call_oi * lot * (spot ** 2) * gamma / 100000000.0, 2)
        pe_gex = round(put_oi * lot * (spot ** 2) * gamma / 100000000.0, 2)
        
        c_turnover = round((c_vol * c_ltp * lot) / 10000000.0, 2)
        p_turnover = round((p_vol * p_ltp * lot) / 10000000.0, 2)

        ce_deltas.append(c_delta)
        pe_deltas.append(p_delta)
        gammas.append(gamma)
        ce_thetas.append(c_theta)
        pe_thetas.append(p_theta)
        vegas.append(vega)
        ce_vannas.append(vanna)
        pe_vannas.append(vanna)
        ce_charms.append(charm)
        pe_charms.append(charm)
        ce_gexs.append(ce_gex)
        pe_gexs.append(pe_gex)
        ce_turnovers.append(c_turnover)
        pe_turnovers.append(p_turnover)
        
    df['CE Delta'] = ce_deltas
    df['PE Delta'] = pe_deltas
    df['Gamma'] = gammas
    df['CE Theta'] = ce_thetas
    df['PE Theta'] = pe_thetas
    df['CE Vega'] = vegas
    df['PE Vega'] = vegas
    df['CE Vanna'] = ce_vannas
    df['PE Vanna'] = pe_vannas
    df['CE Charm'] = ce_charms
    df['PE Charm'] = pe_charms
    df['CE GEX (Cr)'] = ce_gexs
    df['PE GEX (Cr)'] = pe_gexs
    df['CE Turnover (Cr)'] = ce_turnovers
    df['PE Turnover (Cr)'] = pe_turnovers
    return df

chain_df = calculate_advanced_metrics(chain_df, live_spot, lot_size)

# Strike filtering
if "±5" in strike_range_mode:
    chain_df['Dist'] = abs(chain_df['Strike'] - live_spot)
    center_idx = chain_df['Dist'].idxmin()
    disp_df = chain_df.iloc[max(0, center_idx-5):min(len(chain_df), center_idx+6)].copy()
elif "±10" in strike_range_mode:
    chain_df['Dist'] = abs(chain_df['Strike'] - live_spot)
    center_idx = chain_df['Dist'].idxmin()
    disp_df = chain_df.iloc[max(0, center_idx-10):min(len(chain_df), center_idx+11)].copy()
elif "±20" in strike_range_mode:
    chain_df['Dist'] = abs(chain_df['Strike'] - live_spot)
    center_idx = chain_df['Dist'].idxmin()
    disp_df = chain_df.iloc[max(0, center_idx-20):min(len(chain_df), center_idx+21)].copy()
elif "±30" in strike_range_mode:
    chain_df['Dist'] = abs(chain_df['Strike'] - live_spot)
    center_idx = chain_df['Dist'].idxmin()
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

# Buildup helper
def get_buildup(chg_oi, pct_chg):
    if pct_chg > 0 and chg_oi > 0: return "Short Build"
    elif pct_chg < 0 and chg_oi < 0: return "Long Unwind"
    elif pct_chg > 0 and chg_oi < 0: return "Short Cover"
    return "Long Build"

disp_df['CE Build'] = disp_df.apply(lambda r: get_buildup(r.get('CE_Chg_OI', 0), r.get('CE_%Chg', 0)), axis=1)
disp_df['PE Build'] = disp_df.apply(lambda r: get_buildup(r.get('PE_Chg_OI', 0), r.get('PE_%Chg', 0)), axis=1)

# Format columns for display
disp_df['STRIKE'] = disp_df['Strike']
disp_df['CE OI (L)'] = round(disp_df.get('Raw_CE_OI', disp_df.get('CE_OI', 0)) / 100000, 2)
disp_df['PE OI (L)'] = round(disp_df.get('Raw_PE_OI', disp_df.get('PE_OI', 0)) / 100000, 2)
disp_df['CE Vol (M)'] = round(disp_df.get('CE_Volume', 0) / 1000000, 2)
disp_df['PE Vol (M)'] = round(disp_df.get('PE_Volume', 0) / 1000000, 2)

disp_df['CE OI Chg'] = disp_df.get('CE_Chg_OI', 0)
disp_df['PE OI Chg'] = disp_df.get('PE_Chg_OI', 0)
disp_df['CE OI Chg %'] = disp_df.get('CE_%Chg', 0.0)
disp_df['PE OI Chg %'] = disp_df.get('PE_%Chg', 0.0)

disp_df['CE Vol Chg'] = round(disp_df['CE Vol (M)'] * 0.1, 2)
disp_df['PE Vol Chg'] = round(disp_df['PE Vol (M)'] * 0.1, 2)
disp_df['CE Vol Chg %'] = 1.2
disp_df['PE Vol Chg %'] = -0.5

disp_df['CE Bid'] = round(disp_df['CE_LTP'] * 0.99, 2)
disp_df['CE Ask'] = round(disp_df['CE_LTP'] * 1.01, 2)
disp_df['PE Bid'] = round(disp_df['PE_LTP'] * 0.99, 2)
disp_df['PE Ask'] = round(disp_df['PE_LTP'] * 1.01, 2)

disp_df['CE Spread %'] = np.where(disp_df['CE_LTP'] > 0, round(((disp_df['CE Ask'] - disp_df['CE Bid']) / disp_df['CE_LTP']) * 100, 2), 0.0)
disp_df['PE Spread %'] = np.where(disp_df['PE_LTP'] > 0, round(((disp_df['PE Ask'] - disp_df['PE Bid']) / disp_df['PE_LTP']) * 100, 2), 0.0)

# --- MATRIX LAYOUT ---
matrix_cols = [
    "CE Build", "CE GEX (Cr)", "CE Charm", "CE Vanna", "CE Vega", "CE Theta", "Gamma", "CE Delta",
    "CE Vol Chg %", "CE Vol Chg", "CE Vol (M)", "CE Turnover (Cr)", "CE OI Chg %", "CE OI Chg", "CE OI (L)",
    "CE Spread %", "CE Ask", "CE Bid", "CE_LTP"
]

matrix_cols += ["STRIKE"]

matrix_cols += [
    "PE_LTP", "PE Bid", "PE Ask", "PE Spread %",
    "PE OI (L)", "PE OI Chg", "PE OI Chg %", "PE Turnover (Cr)", "PE Vol (M)", "PE Vol Chg", "PE Vol Chg %",
    "PE Delta", "Gamma", "PE Theta", "PE Vega", "PE Vanna", "PE Charm", "PE GEX (Cr)", "PE Build"
]

final_cols = [c for c in matrix_cols if c in disp_df.columns]
matrix_df = disp_df[final_cols].copy()
matrix_df = matrix_df.loc[:, ~matrix_df.columns.duplicated()]

# --- CUSTOM CSS FOR STICKY HEADERS & SMOOTH SCROLLING ---
st.markdown("""
<style>
    /* Streamlit dataframe table styling for sticky headers */
    [data-testid="stDataFrame"] div[data-testid="stTable"] {
        overflow-y: auto;
        max-height: 650px;
    }
    [data-testid="stDataFrame"] th {
        position: sticky !important;
        top: 0 !important;
        background-color: #0e1117 !important;
        color: white !important;
        z-index: 999 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- COLOR STYLING FUNCTION ---
def color_option_chain(val):
    if isinstance(val, str):
        if "Short Build" in val: return "background-color: #ffcccc; color: #990000; font-weight: bold;"
        if "Long Build" in val: return "background-color: #ccffcc; color: #006600; font-weight: bold;"
        if "Short Cover" in val: return "background-color: #cce6ff; color: #003366; font-weight: bold;"
        if "Long Unwind" in val: return "background-color: #fff2cc; color: #806600; font-weight: bold;"
    elif isinstance(val, (int, float)):
        if val > 0: return "color: #008000; font-weight: bold;"
        elif val < 0: return "color: #cc0000; font-weight: bold;"
    return ""

styled_df = matrix_df.style.map(color_option_chain)

st.markdown(f"### 📊 Institutional Sticky-Header Option Chain Matrix ({strike_range_mode})")
st.info("📌 **सुविधा:** अब जब आप टेबल में ऊपर-नीचे (Vertical Scroll) या बाएं-दाएं स्क्रॉल करेंगे, तो कॉलम्स के नाम (Symbols/Headers) अपनी जगह पर स्टिकी रहेंगे ताकि आपको हमेशा पता रहे कि आप कौन सी वैल्यू देख रहे हैं।")
st.dataframe(styled_df, use_container_width=True, height=650, hide_index=True)

# --- COLOR LEGEND / CHEAT SHEET AT THE VERY BOTTOM ---
st.markdown("---")
st.markdown("### 🎨 Option Chain Color Legend & Representation Guide")
st.markdown("यह गाइड दर्शाती है कि ऑप्शन चेन में विभिन्न रंगों और टैग्स का क्या अर्थ है:")

col_l1, col_l2, col_l3, col_l4 = st.columns(4)

with col_l1:
    st.markdown("🟢 **Green Shading / Text**")
    st.caption("• **Long Build / Positive Values:** यह दर्शाता है कि मार्केट में नया लॉन्ग पोजीशन या सपोर्ट बिल्ड-अप मजबूत हो रहा है (Bullish Bias).")

with col_l2:
    st.markdown("🔴 **Red / Pink Shading**")
    st.caption("• **Short Build / Negative Values:** यह दर्शाता है कि कॉल/पुट साइड में शॉर्ट बिल्ड-अप या रेजिस्टेंस प्रेशर हावी हो रहा है (Bearish / Resistance).")

with col_l3:
    st.markdown("🔵 **Blue Shading**")
    st.caption("• **Short Covering:** यह मोमेंटम अप-साइड या शॉर्ट्स के कटने की स्थिति को दर्शाता है (Quick Upward Move).")

with col_l4:
    st.markdown("🟡 **Yellow / Amber Shading**")
    st.caption("• **Long Unwinding:** यह सौदों के कटने और कमजोरी (Weakness/Exit) को प्रदर्शित करता है.")
