import pandas as pd
import numpy as np

def get_market_data(asset_name):
    spot_map = {
        "SENSEX": 73200.0, "NIFTY": 24500.0, 
        "BANKNIFTY": 51200.0, "FINNIFTY": 23100.0, 
        "RELIANCE": 2950.0, "TCS": 4120.0
    }
    spot = spot_map.get(asset_name, 25000.0)
    
    strikes = [spot - 400, spot - 200, spot, spot + 200, spot + 400]
    data = []
    for i, s in enumerate(strikes):
        ce_oi = int(100000 + (i * 25000) % 80000)
        pe_oi = int(120000 + ((4-i) * 30000) % 90000)
        data.append({
            'strike': s,
            'ce_spread': 0.5,
            'ce_ltp': round(max(5.0, (spot - s)*0.5 + 150), 2),
            'ce_iv': round(15.2 + i * 0.8, 2),
            'ce_delta': round(0.5 + (spot - s)*0.001, 2),
            'ce_oi': ce_oi,
            'ce_volume': int(ce_oi * 0.4),
            'pe_spread': 0.5,
            'pe_ltp': round(max(5.0, (s - spot)*0.5 + 140), 2),
            'pe_iv': round(15.8 + (4-i) * 0.7, 2),
            'pe_delta': round(-0.5 + (spot - s)*0.001, 2),
            'pe_oi': pe_oi,
            'pe_volume': int(pe_oi * 0.45)
        })
    df = pd.DataFrame(data)
    total_ce_oi = df['ce_oi'].sum()
    total_pe_oi = df['pe_oi'].sum()
    oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0
    vol_pcr = round(df['pe_volume'].sum() / df['ce_volume'].sum(), 2) if df['ce_volume'].sum() > 0 else 1.0
    net_gex = round((0.0005 * (spot**2) * 0.01 * (total_ce_oi - total_pe_oi)) / 10000000, 2)
    return spot, df, oi_pcr, vol_pcr, net_gex
