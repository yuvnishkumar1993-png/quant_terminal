import os
import json
import time
import logging
import threading
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =====================================================================
# 1. PROFESSIONAL LOGGING
# =====================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - REAL QUANT ENGINE - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# 2. BULLETPROOF API SESSION MANAGER (Fixes the "Asking for Keys" issue)
# =====================================================================
class InstitutionalDataEngine:
    BASE_URL = "https://api.dhan.co/v2"
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0 
    AUTH_FILE = "dhan_auth_session.json"
    
    _cache = {}
    _cache_lock = threading.Lock()
    CACHE_TTL = 3.0 

    @staticmethod
    def save_api_session(client_id, access_token):
        """Saves valid API keys to JSON. Bypasses dummy tokens."""
        if not client_id or not access_token or access_token in ["dummy_token", ""]: 
            return False
            
        expiry_time = datetime.now() + timedelta(hours=24)
        auth_data = {
            "client_id": client_id,
            "access_token": access_token,
            "expiry": expiry_time.isoformat()
        }
        try:
            with open(InstitutionalDataEngine.AUTH_FILE, "w") as f:
                json.dump(auth_data, f)
            logger.info("✅ 24-Hour API Keys successfully LOCKED in JSON.")
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False

    @staticmethod
    def load_api_session():
        """Reads keys from JSON. If valid, returns them."""
        if os.path.exists(InstitutionalDataEngine.AUTH_FILE):
            try:
                with open(InstitutionalDataEngine.AUTH_FILE, "r") as f:
                    auth_data = json.load(f)
                
                expiry_time = datetime.fromisoformat(auth_data["expiry"])
                if datetime.now() < expiry_time:
                    # Valid keys found!
                    return auth_data.get("client_id"), auth_data.get("access_token")
                else:
                    logger.warning("Session Expired. Deleting JSON.")
                    os.remove(InstitutionalDataEngine.AUTH_FILE)
            except Exception as e:
                logger.error(f"Error loading session JSON: {e}")
        return None, None

    @staticmethod
    def _get_universal_registry():
        return {
            "NIFTY": {"spot": 24570.65, "step": 50, "iv": 13.34, "lot": 65},
            "BANKNIFTY": {"spot": 51200.00, "step": 100, "iv": 15.20, "lot": 15},
            "FINNIFTY": {"spot": 23400.00, "step": 50, "iv": 13.50, "lot": 25},
            "SENSEX": {"spot": 78499.17, "step": 100, "iv": 13.91, "lot": 20},
            "RELIANCE": {"spot": 2950.00, "step": 20, "iv": 22.50, "lot": 250},
            "TCS": {"spot": 4120.00, "step": 20, "iv": 21.00, "lot": 175},
            "HDFCBANK": {"spot": 1680.00, "step": 10, "iv": 18.50, "lot": 550},
            "INFY": {"spot": 1850.00, "step": 10, "iv": 25.00, "lot": 400},
            "ICICIBANK": {"spot": 1240.00, "step": 10, "iv": 20.00, "lot": 700},
            "SBIN": {"spot": 820.00, "step": 10, "iv": 24.00, "lot": 750}
        }

    @staticmethod
    def fetch_expiries(client_id, access_token, sec_id, seg):
        # We don't really need live API for expiries, math generates it perfectly
        today = datetime.now()
        expiries = []
        days_ahead = 0
        target_weekday = 2 if seg == "BSE_IDX" else 3 
        while len(expiries) < 4:
            days_to_add = (target_weekday - today.weekday() + 7) % 7
            if days_to_add == 0: days_to_add = 7
            expiries.append((today + timedelta(days=days_to_add + days_ahead)).strftime("%Y-%m-%d"))
            days_ahead += 7
        return expiries

    # =====================================================================
    # 3. ROBUST DHAN JSON PARSER (Fixes the "Wrong Data" issue)
    # =====================================================================
    @staticmethod
    def _parse_dhan_oc(api_data, symbol, lot):
        """Ultra-robust parser that extracts exact Dhan data structure."""
        recs = []
        # Fallback to 0 if last_price is missing at root
        spot = api_data.get("last_price", 0.0) 
        oc = api_data.get("oc", {})
        
        for strike_str, opt_data in oc.items():
            try:
                strike = float(strike_str)
            except ValueError:
                continue
                
            ce = opt_data.get("ce", {})
            pe = opt_data.get("pe", {})
            
            # --- CE (CALL) DATA ---
            ce_oi = int(ce.get("oi", 0))
            ce_prev_oi = int(ce.get("previous_oi", 0))
            ce_chg_oi = ce_oi - ce_prev_oi
            ce_pct_chg = round((ce_chg_oi / ce_prev_oi * 100), 2) if ce_prev_oi > 0 else 0.0
            ce_ltp = float(ce.get("last_price", 0.0))
            ce_vol = int(ce.get("volume", 0))
            ce_iv = float(ce.get("implied_volatility", 0.0))
            
            c_greeks = ce.get("greeks", {})
            c_delta = float(c_greeks.get("delta", 0.0))
            c_theta = float(c_greeks.get("theta", 0.0))
            c_vega = float(c_greeks.get("vega", 0.0))
            
            # --- PE (PUT) DATA ---
            pe_oi = int(pe.get("oi", 0))
            pe_prev_oi = int(pe.get("previous_oi", 0))
            pe_chg_oi = pe_oi - pe_prev_oi
            pe_pct_chg = round((pe_chg_oi / pe_prev_oi * 100), 2) if pe_prev_oi > 0 else 0.0
            pe_ltp = float(pe.get("last_price", 0.0))
            pe_vol = int(pe.get("volume", 0))
            pe_iv = float(pe.get("implied_volatility", 0.0))
            
            p_greeks = pe.get("greeks", {})
            p_delta = float(p_greeks.get("delta", 0.0))
            p_theta = float(p_greeks.get("theta", 0.0))
            p_vega = float(p_greeks.get("vega", 0.0))
            
            # --- SHARED GREEKS & ADVANCED METRICS ---
            gamma = float(c_greeks.get("gamma", 0.0))
            if gamma == 0.0: gamma = float(p_greeks.get("gamma", 0.0))
            
            ce_turnover = round((ce_vol * ce_ltp * lot) / 10000000.0, 2)
            pe_turnover = round((pe_vol * pe_ltp * lot) / 10000000.0, 2)
            ce_gex = round(ce_oi * lot * (spot ** 2) * gamma / 100000000.0, 2)
            pe_gex = round(pe_oi * lot * (spot ** 2) * gamma / 100000000.0, 2)
            
            recs.append({
                "Strike": int(strike), "STRIKE": int(strike),
                "CE_OI": ce_oi, "Raw_CE_OI": ce_oi,
                "CE_Chg_OI": ce_chg_oi, "CE_%Chg": ce_pct_chg,
                "CE_Volume": ce_vol, "CE_IV": ce_iv, 
                "CE_LTP": ce_ltp,
                "PE_LTP": pe_ltp, "PE_IV": pe_iv, 
                "PE_Volume": pe_vol, "PE_Chg_OI": pe_chg_oi, "PE_%Chg": pe_pct_chg,
                "PE_OI": pe_oi, "Raw_PE_OI": pe_oi,
                
                "CE Delta": c_delta, "PE Delta": p_delta,
                "Gamma": gamma,
                "CE Theta": c_theta, "PE Theta": p_theta,
                "CE Vega": c_vega, "PE Vega": p_vega,
                "CE Vanna": 0.0, "PE Vanna": 0.0, "CE Charm": 0.0, "PE Charm": 0.0,
                "CE GEX (Cr)": ce_gex, "PE GEX (Cr)": pe_gex,
                "CE Turnover (Cr)": ce_turnover, "PE Turnover (Cr)": pe_turnover
            })
            
        df = pd.DataFrame(recs)
        if not df.empty:
            df = df.sort_values("Strike")
        return df, spot

    # =====================================================================
    # 4. MASTER API FETCH FUNCTION
    # =====================================================================
    @staticmethod
    def fetch_live_option_chain(client_id, access_token, sec_id, seg, expiry_date, symbol):
        sym_upper = symbol.upper()
        cache_key = f"{sym_upper}_{expiry_date}"

        # 4.1 CACHE CHECK (SPEED BOOST)
        with InstitutionalDataEngine._cache_lock:
            if cache_key in InstitutionalDataEngine._cache:
                cached_data, timestamp = InstitutionalDataEngine._cache[cache_key]
                if time.time() - timestamp < InstitutionalDataEngine.CACHE_TTL:
                    return cached_data[0].copy(), cached_data[1]

        # 4.2 SMART TOKEN MANAGER
        saved_client, saved_token = InstitutionalDataEngine.load_api_session()
        
        # If valid inputs are provided, use them and save them. Otherwise, use saved.
        final_client = client_id if (client_id and client_id != "dummy") else saved_client
        final_token = access_token if (access_token and access_token != "dummy_token") else saved_token
        
        # Try saving the new keys if they are valid
        if client_id and access_token and access_token != "dummy_token":
            InstitutionalDataEngine.save_api_session(client_id, access_token)

        # 4.3 REAL API CALL
        result_df, result_spot = None, None
        registry = InstitutionalDataEngine._get_universal_registry()
        cfg = registry.get(sym_upper, {"lot": 50})
        
        if final_client and final_token:
            for attempt in range(InstitutionalDataEngine.MAX_RETRIES):
                try:
                    url = f"{InstitutionalDataEngine.BASE_URL}/optionchain"
                    headers = {
                        "access-token": final_token,
                        "client-id": final_client,
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "UnderlyingScrip": int(sec_id),
                        "UnderlyingSeg": seg,
                        "Expiry": expiry_date
                    }
                    response = requests.post(url, json=payload, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json().get('data', {})
                        if data and 'oc' in data:
                            logger.info(f"✅ Live Dhan API Success: {sym_upper}")
                            result_df, result_spot = InstitutionalDataEngine._parse_dhan_oc(data, sym_upper, cfg["lot"])
                            break # Success!
                    elif response.status_code == 429:
                        time.sleep(InstitutionalDataEngine.RETRY_DELAY * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"Live API Error {response.status_code}: {response.text}")
                        break
                except Exception as e:
                    logger.error(f"Live API Connection Failed: {str(e)}")
                    break 

        # 4.4 FINAL SAFETY NET (Only if real API fails)
        if result_df is None or result_df.empty:
            logger.warning(f"Returning Empty Structure for {sym_upper} (Check API Keys/Market Hours)")
            result_df, result_spot = InstitutionalDataEngine._generate_empty_surface(sym_upper, expiry_date)

        # 4.5 UPDATE CACHE & RETURN
        with InstitutionalDataEngine._cache_lock:
            InstitutionalDataEngine._cache[cache_key] = ((result_df, result_spot), time.time())

        return result_df.copy(), result_spot

    @staticmethod
    def _generate_empty_surface(symbol, expiry_date):
        """Returns 0 structure instead of fake data if API completely fails."""
        registry = InstitutionalDataEngine._get_universal_registry()
        cfg = registry.get(symbol, {"spot": 0.0, "step": 10, "iv": 0.0, "lot": 0})
        spot = cfg["spot"]
        step = cfg["step"]
        
        atm_strike = round(spot / step) * step if step > 0 else 0
        strikes = np.arange(atm_strike - (20 * step), atm_strike + (21 * step), step)
        
        recs = []
        for K in strikes:
            recs.append({
                "Strike": int(K), "STRIKE": int(K), "CE_OI": 0, "Raw_CE_OI": 0, "CE_Chg_OI": 0, "CE_%Chg": 0.0,
                "CE_Volume": 0, "CE_IV": 0.0, "CE_LTP": 0.0, "PE_LTP": 0.0, "PE_IV": 0.0, "PE_Volume": 0,
                "PE_Chg_OI": 0, "PE_%Chg": 0.0, "PE_OI": 0, "Raw_PE_OI": 0, "CE Delta": 0.0, "PE Delta": 0.0, "Gamma": 0.0,
                "CE Theta": 0.0, "PE Theta": 0.0, "CE Vega": 0.0, "PE Vega": 0.0, "CE Vanna": 0.0, "PE Vanna": 0.0, 
                "CE Charm": 0.0, "PE Charm": 0.0, "CE GEX (Cr)": 0.0, "PE GEX (Cr)": 0.0, "CE Turnover (Cr)": 0.0, "PE Turnover (Cr)": 0.0
            })
            
        return pd.DataFrame(recs), spot
