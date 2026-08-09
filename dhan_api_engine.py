import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

class InstitutionalDataEngine:
    """
    Quant Terminal Pro ke liye Advanced Data Pipeline aur Caching Engine.
    """

    @staticmethod
    @st.cache_data(ttl=3600)
    def load_scrip_master():
        try:
            url = "https://images.dhan.co/api-data/api-scrip-master.csv"
            df = pd.read_csv(url, low_memory=False)
            df.columns = [str(col).strip().upper() for col in df.columns]
            return df
        except Exception:
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=30)
    def fetch_expiries(client_id, access_token, sec_id, seg):
        """Dhan API se active expiry dates fetch karta hai, validation ke sath."""
        if not client_id or not access_token or not sec_id:
            # Fallback: Current date se aage ke upcoming Thursdays ki list generate karega
            base_date = datetime.now()
            expiries = []
            for i in range(1, 5):
                next_thu = base_date + timedelta(days=(3 - base_date.weekday() + 7 * i) % 7)
                expiries.append(next_thu.strftime("%Y-%m-%d"))
            return expiries
            
        url = "https://api.dhan.co/v2/optionchain/expirylist"
        headers = {
            "access-token": str(access_token).strip(), 
            "client-id": str(client_id).strip(), 
            "Content-Type": "application/json"
        }
        payload = {"UnderlyingScrip": int(sec_id), "UnderlyingSeg": str(seg).strip()}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=8)
            if response.status_code == 200:
                res = response.json()
                data = res.get("data", [])
                if isinstance(data, list) and len(data) > 0:
                    return [str(d) for d in data]
        except Exception:
            pass
            
        base_date = datetime.now()
        return [(base_date + timedelta(days=7*i)).strftime("%Y-%m-%d") for i in range(1, 4)]

    @staticmethod
    @st.cache_data(ttl=10)
    def fetch_live_option_chain(client_id, access_token, sec_id, seg, exp, symbol):
        """Selected asset ke anuroop real-time option chain data ya dynamic realistic simulation laata hai."""
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
            response = requests.post(url, json=payload, headers=headers, timeout=10)
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
            
        # Asset-specific dynamic fallback spots and steps
        spot_map = {
            "NIFTY": 24570.0, "BANKNIFTY": 51200.0, "FINNIFTY": 23100.0, 
            "SENSEX": 73200.0, "RELIANCE": 2950.0, "TCS": 4120.0, "SBIN": 820.0
        }
        fallback_spot = spot_map.get(symbol, 2000.0)
        step = 100 if symbol in ["BANKNIFTY", "SENSEX"] else (50 if symbol in ["NIFTY", "FINNIFTY"] else 20)
        atm = round(fallback_spot / step) * step
        strikes = np.arange(atm - (step * 15), atm + (step * 16), step)
        
        mock_recs = []
        np.random.seed(hash(symbol) % 2026)
        for s in strikes:
            dist = abs(s - fallback_spot)
            c_oi = int(max(50000, 5000000 - (dist * 1000)))
            p_oi = int(max(50000, 5000000 - (dist * 1000)))
            mock_recs.append({
                "Strike": int(s), "STRIKE": int(s),
                "CE_OI": c_oi, "Raw_CE_OI": c_oi, "CE_Chg_OI": int(np.random.randint(-10000, 15000)), "CE_%Chg": round(np.random.uniform(-5, 5), 2), "CE_Volume": c_oi * 2, "CE_IV": 14.0, "CE_LTP": max(0.5, round(fallback_spot - s + 50, 2) if s < fallback_spot else 50.0),
                "PE_LTP": max(0.5, round(s - fallback_spot + 50, 2) if s > fallback_spot else 50.0), "PE_IV": 14.5, "PE_Volume": p_oi * 2, "PE_Chg_OI": int(np.random.randint(-10000, 15000)), "PE_%Chg": round(np.random.uniform(-5, 5), 2), "PE_OI": p_oi, "Raw_PE_OI": p_oi,
                "CE_Delta": 0.5, "CE_Gamma": 0.001, "CE_Theta": -5.0, "CE_Vega": 12.0,
                "PE_Delta": -0.5, "PE_Gamma": 0.001, "PE_Theta": -5.0, "PE_Vega": 12.0
            })
        return pd.DataFrame(mock_recs), fallback_spot
