    # लॉजिकल और वास्तविक् मूल्य निर्धारण (Logical Pricing based on Spot & Strike distance)
    step = 100 if sym in ["BANKNIFTY", "SENSEX"] else (50 if sym in ["NIFTY", "FINNIFTY"] else 20)
    atm = round(live_spot / step) * step
    strikes_arr = [atm + (i * step) for i in range(-20, 21)]  # ±20 स्ट्राइक्स की सटीक रेंज
    
    mock_recs = []
    np.random.seed(42)
    for s in strikes_arr:
        # स्पॉट से दूरी के हिसाब से प्रीमियम का लॉजिक
        c_intrinsic = max(0.0, live_spot - s)
        p_intrinsic = max(0.0, s - live_spot)
        
        # दूरी के साथ टाइम वैल्यू का घटना (Time decay away from ATM)
        distance_pts = abs(s - live_spot)
        time_value = max(10.0, 150.0 - (distance_pts * 0.15))
        
        c_ltp = round(c_intrinsic + time_value if c_intrinsic > 0 else time_value, 2)
        p_ltp = round(p_intrinsic + time_value if p_intrinsic > 0 else time_value, 2)
        
        c_oi = int(max(50000, 300000 - (distance_pts * 1000)))
        p_oi = int(max(50000, 300000 - (distance_pts * 1000)))
        
        c_iv_val = round(12.0 + (distance_pts / live_spot) * 20, 2)
        p_iv_val = round(12.5 + (distance_pts / live_spot) * 20, 2)
        
        mock_recs.append({
            "CE Spread %": round(np.random.uniform(0.1, 0.8), 2),
            "CE LTP": c_ltp, 
            "CE %Chg": round(np.random.uniform(-8, 12), 2), 
            "CE IV": c_iv_val, 
            "CE Vol": int(c_oi * 1.5), 
            "CE Chg OI": int(np.random.randint(-5000, 8000)), 
            "CE OI (L)": round(c_oi/100000, 2),
            "STRIKE": int(s), 
            "PE OI (L)": round(p_oi/100000, 2), 
            "PE Chg OI": int(np.random.randint(-5000, 8000)), 
            "PE Vol": int(p_oi * 1.5), 
            "PE %Chg": round(np.random.uniform(-8, 12), 2), 
            "PE LTP": p_ltp, 
            "PE IV": p_iv_val, 
            "PE Spread %": round(np.random.uniform(0.1, 0.8), 2),
            "Raw_CE_OI": c_oi,
            "Raw_PE_OI": p_oi
        })
    chain_df = pd.DataFrame(mock_recs)
