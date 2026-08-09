import pandas as pd
import streamlit as st
from datetime import datetime
from config import SCRIP_MASTER_URL

@st.cache_data(ttl=86400)
def load_scrip_master():
    try:
        df = pd.read_csv(SCRIP_MASTER_URL, low_memory=False)
        df.columns = [str(col).lower().strip() for col in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

class DhanAPIEngine:
    def __init__(self):
        self.scrip_df = load_scrip_master()

    def get_all_fo_symbols(self):
        if self.scrip_df.empty:
            return ["SENSEX", "NIFTY", "BANKNIFTY", "FINNIFTY"]
        seg_col = 'exch_seg' if 'exch_seg' in self.scrip_df.columns else 'segment'
        sym_col = 'trading_symbol' if 'trading_symbol' in self.scrip_df.columns else 'symbol'
        if seg_col in self.scrip_df.columns and sym_col in self.scrip_df.columns:
            fno_mask = self.scrip_df[seg_col].astype(str).str.lower().isin(['nse_fno', 'bse_fno'])
            symbols = self.scrip_df[fno_mask][sym_col].dropna().unique()
            indices = ["SENSEX", "NIFTY", "BANKNIFTY", "FINNIFTY"]
            stocks = sorted([str(s) for s in symbols if not any(idx in str(s) for idx in indices)])
            return indices + stocks
        return ["SENSEX", "NIFTY", "BANKNIFTY"]

    def get_auto_expiries(self, asset_name):
        if self.scrip_df.empty:
            return ["2026-08-13"]
        exp_col = 'expiry_date' if 'expiry_date' in self.scrip_df.columns else 'expiry'
        sym_col = 'trading_symbol' if 'trading_symbol' in self.scrip_df.columns else 'symbol'
        if exp_col in self.scrip_df.columns and sym_col in self.scrip_df.columns:
            matched = self.scrip_df[self.scrip_df[sym_col].astype(str).str.contains(str(asset_name), case=False, na=False)]
            expiries = matched[exp_col].dropna().unique()
            today = datetime.now().date()
            parsed = []
            for exp in expiries:
                try:
                    dt = pd.to_datetime(exp).date()
                    if dt >= today:
                        parsed.append(dt)
                except:
                    continue
            sorted_dates = sorted(list(set(parsed)))
            return [d.strftime('%Y-%m-%d') for d in sorted_dates] if sorted_dates else ["2026-08-13"]
        return ["2026-08-13"]

    def get_lot_size(self, asset_name):
        if self.scrip_df.empty:
            return 10
        sym_col = 'trading_symbol' if 'trading_symbol' in self.scrip_df.columns else 'symbol'
        lot_col = 'lot_size' if 'lot_size' in self.scrip_df.columns else ('multiplier' if 'multiplier' in self.scrip_df.columns else None)
        if lot_col and sym_col in self.scrip_df.columns:
            matched = self.scrip_df[self.scrip_df[sym_col].astype(str).str.contains(str(asset_name), case=False, na=False)]
            if not matched.empty:
                for val in matched[lot_col].dropna():
                    try:
                        int_val = int(val)
                        if int_val > 0:
                            return int_val
                    except:
                        continue
        return 10
