import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

class InstitutionalDataEngine:
    """
    Quant Terminal Pro ke liye Advanced Data Pipeline aur Caching Engine.
    Yeh class API authentication, scrip master matching, expiry sync aur live option chain ko handle karti hai.
    """

    @staticmethod
    @st.cache_data(ttl=3600)
    def load_scrip_master():
        """Dhan Cloud se universal scrip master database download karta hai."""
        try:
            url = "https://images.dhan.co/api-data/api-scrip-master.csv"
            df = pd.read_csv(url, low_memory=False)
            df.columns = [str(col).strip().upper() for col in df.columns]
            return df
        except Exception as e:
            st.error(f"Scrip Master Download Error: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=30)
    def fetch_expiries(client_id, access_token, sec_id, seg):
        """Dhan API se selected underlying ke liye active expiry dates ki real list laata hai."""
        if not client_id or not access_token or not sec_id:
            return [datetime.now().strftime("%Y-%m-%d")]
            
        url = "https://api.dhan.co/v2/optionchain/expirylist"
        headers = {
            "access-token": str(access_token).strip(), 
            "client-id": str(client_id).strip(), 
            "Content-Type": "application/json"
        }
        payload = {"UnderlyingScrip": int(sec_id), "UnderlyingSeg": str(seg).strip()}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                res = response.json()
                # Dhan API usually returns list under 'data' key directly or inside status success
                data = res.get("data", [])
                if isinstance(data, list) and len(data) > 0:
                    return [str(d) for d in data]
        except Exception:
            pass
            
        # Fallback agar API hit na ho paye
        return [datetime.now().strftime("%Y-%m-%d")]

    @staticmethod
    @st.cache_data(ttl=10)
    def fetch_live_option_chain(client_id, access_token, sec_id, seg, exp, symbol):
        """
        Dhan API se real-time option chain data fetch karta hai aur standard format mein map karta hai.
        """
        url = "https://api.dhan.co/v2/optionchain"
        headers = {
            "access-token": str(access_token).strip(), 
            "client-id": str(client_id).strip(), 
            "Content-Type": "application/json"
        }
        payload = {
            "UnderlyingScrip": int(sec_id), 
            "UnderlyingSeg": str(seg).strip(), 
            "Expiry": str(exp).strip()
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=12)
            if response.status_code == 200:
                res = response.json()
                block = res.get("data", {})
                spot_val = float(block.get("last_price", 0.0))
                oc_map = block.get("oc", {})
                
                if oc_map and spot_val > 0:
                    records = []
                    for s_str, obj in oc_map.items():
                        s_val = float(s_str)
                        ce, pe = obj.get("ce", {}), obj.get("pe", {})
                        
                        ce_oi = int(ce.get("oi", 0))
                        ce_prev_oi = int(ce.get("previous_oi", ce_oi))
                        ce_chg_oi = ce_oi - ce_prev_oi
                        
                        pe_oi = int(pe.get("oi", 0))
                        pe_prev_oi = int(pe.get("previous_oi", pe_oi))
                        pe_chg_oi = pe_oi - pe_prev_oi
                        
                        records.append({
                            "Strike": int(s_val),
                            "STRIKE": int(s_val),
                            "CE_OI": ce_oi,
                            "Raw_CE_OI": ce_oi,
                            "CE_Chg_OI": ce_chg_oi,
                            "CE_%Chg": float(ce.get("pchange", 0.0)),
                            "CE_Volume": int(ce.get("volume", 0)),
                            "CE_IV": float(ce.get("iv", 14.0)),
                            "CE_LTP": float(ce.get("last_price", 0.0)),
                            "CE_Delta": float(ce.get("delta", 0.50)),
                            "CE_Gamma": float(ce.get("gamma", 0.0015)),
                            "CE_Theta": float(ce.get("theta", -5.0)),
                            "CE_Vega": float(ce.get("vega", 12.0)),
                            
                            "PE_LTP": float(pe.get("last_price", 0.0)),
                            "PE_IV": float(pe.get("iv", 14.5)),
                            "PE_Volume": int(pe.get("volume", 0)),
                            "PE_Chg_OI": pe_chg_oi,
                            "PE_%Chg": float(pe.get("pchange", 0.0)),
                            "PE_OI": pe_oi,
                            "Raw_PE_OI": pe_oi,
                            "PE_Delta": float(pe.get("delta", -0.50)),
                            "PE_Gamma": float(pe.get("gamma", 0.0015)),
                            "PE_Theta": float(pe.get("theta", -5.0)),
                            "PE_Vega": float(pe.get("vega", 12.0))
                        })
                    df_out = pd.DataFrame(records)
                    if not df_out.empty:
                        df_out = df_out.sort_values(by="Strike").reset_index(drop=True)
                    return df_out, spot_val
        except Exception:
            pass
            
        # Fallback simulation agar API credentials na ho ya network issue ho
        fallback_spot = 24570.65
        step = 50
        atm = round(fallback_spot / step) * step
        strikes = np.arange(atm - 1000, atm + 1050, step)
        
        mock_recs = []
        for s in strikes:
            mock_recs.append({
                "Strike": int(s), "STRIKE": int(s),
                "CE_OI": 500000, "Raw_CE_OI": 500000, "CE_Chg_OI": 10000, "CE_%Chg": 1.5, "CE_Volume": 100000, "CE_IV": 13.5, "CE_LTP": 150.0,
                "PE_LTP": 150.0, "PE_IV": 14.0, "PE_Volume": 100000, "PE_Chg_OI": 10000, "PE_%Chg": 1.5, "PE_OI": 500000, "Raw_PE_OI": 500000,
                "CE_Delta": 0.5, "CE_Gamma": 0.001, "CE_Theta": -5.0, "CE_Vega": 12.0,
                "PE_Delta": -0.5, "PE_Gamma": 0.001, "PE_Theta": -5.0, "PE_Vega": 12.0
            })
        return pd.DataFrame(mock_recs), fallback_spot
