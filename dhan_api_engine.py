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
# 1. PROFESSIONAL LOGGING & SETUP
# =====================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - REAL QUANT ENGINE - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# 2. ANTI-SPAM TELEGRAM BOT
# =====================================================================
class TelegramAlertBot:
    BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE" 
    CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE"
    
    _last_alert_time = {}
    _alert_lock = threading.Lock()
    COOLDOWN_MINUTES = 5 

    @staticmethod
    def send_alert(symbol, signal_type, message):
        if not TelegramAlertBot.BOT_TOKEN or TelegramAlertBot.BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            return

        with TelegramAlertBot._alert_lock:
            key = f"{symbol}_{signal_type}"
            now = datetime.now()
            if key in TelegramAlertBot._last_alert_time:
                time_diff = (now - TelegramAlertBot._last_alert_time[key]).total_seconds() / 60.0
                if time_diff < TelegramAlertBot.COOLDOWN_MINUTES:
                    return 
            TelegramAlertBot._last_alert_time[key] = now

        def _send():
            try:
                url = f"https://api.telegram.org/bot{TelegramAlertBot.BOT_TOKEN}/sendMessage"
                payload = {"chat_id": TelegramAlertBot.CHAT_ID, "text": message, "parse_mode": "HTML"}
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                logger.error(f"Telegram Alert Failed: {str(e)}")

        threading.Thread(target=_send, daemon=True).start()

# =====================================================================
# 3. LIVE DHAN API DATA ENGINE (NO MORE SIMULATION)
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
        if not client_id or not access_token or access_token == "dummy_token": return
        expiry_time = datetime.now() + timedelta(hours=24)
        auth_data = {"client_id": client_id, "access_token": access_token, "expiry": expiry_time.isoformat()}
        try:
            with open(InstitutionalDataEngine.AUTH_FILE, "w") as f:
                json.dump(auth_data, f)
        except Exception: pass

    @staticmethod
    def load_api_session():
        if os.path.exists(InstitutionalDataEngine.AUTH_FILE):
            try:
                with open(InstitutionalDataEngine.AUTH_FILE, "r") as f:
                    auth_data = json.load(f)
                if datetime.now() < datetime.fromisoformat(auth_data["expiry"]):
                    return auth_data.get("client_id"), auth_data.get("access_token")
                else: os.remove(InstitutionalDataEngine.AUTH_FILE)
            except Exception: pass
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
            "SBIN": {"spot": 820.00, "step": 10, "iv": 24.00, "lot": 750},
            "TATAMOTORS": {"spot": 740.00, "step": 10, "iv": 28.00, "lot": 1400}
        }

    @staticmethod
    def fetch_expiries(client_id, access_token, sec_id, seg):
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

    @staticmethod
    def _parse_dhan_oc(api_data, symbol, lot):
        """Parses real live data exactly as received from Dhan V2 Option Chain API."""
        recs = []
        spot = api_data.get("last_price", 0.0)
        oc = api_data.get("oc", {})
        
        for strike_str, opt_data in oc.items():
            try:
                strike = float(strike_str)
            except ValueError:
                continue
                
            ce = opt_data.get("ce", {})
            pe = opt_data.get("pe", {})
            
            # CE Processing
            ce_oi = ce.get("oi", 0)
            ce_prev_oi = ce.get("previous_oi", 0)
            ce_chg_oi = ce_oi - ce_prev_oi
            ce_pct_chg = round((ce_chg_oi / ce_prev_oi * 100), 2) if ce_prev_oi > 0 else 0.0
            c_greeks = ce.get("greeks", {})
            ce_ltp = ce.get("last_price", 0.0)
            ce_vol = ce.get("volume", 0)
            
            # PE Processing
            pe_oi = pe.get("oi", 0)
            pe_prev_oi = pe.get("previous_oi", 0)
            pe_chg_oi = pe_oi - pe_prev_oi
            pe_pct_chg = round((pe_chg_oi / pe_prev_oi * 100), 2) if pe_prev_oi > 0 else 0.0
            p_greeks = pe.get("greeks", {})
            pe_ltp = pe.get("last_price", 0.0)
            pe_vol = pe.get("volume", 0)
            
            gamma = c_greeks.get("gamma", 0.0)
            if gamma == 0.0: gamma = p_greeks.get("gamma", 0.0)
            
            # Turnover and Gamma Exposure (Crores)
            ce_turnover = round((ce_vol * ce_ltp * lot) / 10000000.0, 2)
            pe_turnover = round((pe_vol * pe_ltp * lot) / 10000000.0, 2)
            ce_gex = round(ce_oi * lot * (spot ** 2) * gamma / 100000000.0, 2)
            pe_gex = round(pe_oi * lot * (spot ** 2) * gamma / 100000000.0, 2)
            
            recs.append({
                "Strike": int(strike), "STRIKE": int(strike),
                "CE_OI": ce_oi, "Raw_CE_OI": ce_oi,
                "CE_Chg_OI": ce_chg_oi, "CE_%Chg": ce_pct_chg,
                "CE_Volume": ce_vol, "CE_IV": ce.get("implied_volatility", 0.0), 
                "CE_LTP": ce_ltp,
                "PE_LTP": pe_ltp, "PE_IV": pe.get("implied_volatility", 0.0), 
                "PE_Volume": pe_vol, "PE_Chg_OI": pe_chg_oi, "PE_%Chg": pe_pct_chg,
                "PE_OI": pe_oi, "Raw_PE_OI": pe_oi,
                
                # Pre-calculated Live Greeks from Dhan API
                "CE Delta": c_greeks.get("delta", 0.0), "PE Delta": p_greeks.get("delta", 0.0),
                "Gamma": gamma,
                "CE Theta": c_greeks.get("theta", 0.0), "PE Theta": p_greeks.get("theta", 0.0),
                "CE Vega": c_greeks.get("vega", 0.0), "PE Vega": p_greeks.get("vega", 0.0),
                "CE Vanna": 0.0, "PE Vanna": 0.0, "CE Charm": 0.0, "PE Charm": 0.0,
                "CE GEX (Cr)": ce_gex, "PE GEX (Cr)": pe_gex,
                "CE Turnover (Cr)": ce_turnover, "PE Turnover (Cr)": pe_turnover
            })
            
        df = pd.DataFrame(recs)
        if not df.empty:
            df = df.sort_values("Strike")
        return df, spot

    @staticmethod
    def fetch_live_option_chain(client_id, access_token, sec_id, seg, expiry_date, symbol):
        sym_upper = symbol.upper()
        cache_key = f"{sym_upper}_{expiry_date}"

        # 1. Smart Memory Cache
        with InstitutionalDataEngine._cache_lock:
            if cache_key in InstitutionalDataEngine._cache:
                cached_data, timestamp = InstitutionalDataEngine._cache[cache_key]
                if time.time() - timestamp < InstitutionalDataEngine.CACHE_TTL:
                    return cached_data[0].copy(), cached_data[1]

        # 2. Token Injection
        saved_client, saved_token = InstitutionalDataEngine.load_api_session()
        final_client = client_id if (client_id and client_id != "dummy") else saved_client
        final_token = access_token if (access_token and access_token != "dummy_token") else saved_token
        
        if client_id and access_token and access_token != "dummy_token":
            InstitutionalDataEngine.save_api_session(client_id, access_token)

        # 3. REAL LIVE DHAN API GATEWAY
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
                    response = requests.post(url, json=payload, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json().get('data', {})
                        if data and 'oc' in data:
                            # 100% REAL LIVE DATA EXTRACTION
                            result_df, result_spot = InstitutionalDataEngine._parse_dhan_oc(data, sym_upper, cfg["lot"])
                            break 
                            
                    elif response.status_code == 429:
                        time.sleep(InstitutionalDataEngine.RETRY_DELAY * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"Live API Error {response.status_code}: {response.text}")
                        break
                except Exception as e:
                    logger.error(f"Live API Connection Failed: {str(e)}")
                    break 

        # Update Cache
        if result_df is not None and not result_df.empty:
            with InstitutionalDataEngine._cache_lock:
                InstitutionalDataEngine._cache[cache_key] = ((result_df, result_spot), time.time())
            return result_df.copy(), result_spot
        else:
            # Fallback ONLY if the user has NO tokens or API totally fails
            return InstitutionalDataEngine._generate_mathematical_surface(sym_upper, expiry_date)

    @staticmethod
    def _generate_mathematical_surface(symbol, expiry_date):
        """Fallback Generator (Empty/Null structure) to prevent crashes if no API token is present."""
        registry = InstitutionalDataEngine._get_universal_registry()
        cfg = registry.get(symbol, {"spot": 1200.0, "step": 10, "iv": 24.0, "lot": 500})
        spot = cfg["spot"]
        step = cfg["step"]
        
        atm_strike = round(spot / step) * step
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
