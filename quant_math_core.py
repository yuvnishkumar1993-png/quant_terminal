import numpy as np
import pandas as pd

class QuantMathCore:
    @staticmethod
    def sanitize_dataframe(df):
        cols = ['ce_oi', 'pe_oi', 'ce_volume', 'pe_volume', 'ce_iv', 'pe_iv', 'ce_ltp', 'pe_ltp', 'ce_spread', 'pe_spread']
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            else:
                df[col] = 0.0
        return df

    @staticmethod
    def calculate_pcr(df):
        df = QuantMathCore.sanitize_dataframe(df)
        total_ce_oi = df['ce_oi'].sum()
        total_pe_oi = df['pe_oi'].sum()
        total_ce_vol = df['ce_volume'].sum()
        total_pe_vol = df['pe_volume'].sum()
        oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.00
        vol_pcr = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol > 0 else 1.00
        return oi_pcr, vol_pcr

    @staticmethod
    def calculate_gex(df, spot_price):
        df = QuantMathCore.sanitize_dataframe(df)
        ce_gex = (0.0005 * (spot_price ** 2) * 0.01 * df['ce_oi']) / 10000000
        pe_gex = (0.0005 * (spot_price ** 2) * 0.01 * df['pe_oi']) / 10000000
        net_gex = ce_gex - pe_gex
        return round(net_gex.sum(), 2)
