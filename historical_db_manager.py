import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_NAME

class HistoricalDBManager:
    def __init__(self):
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                asset TEXT,
                spot_price REAL,
                oi_pcr REAL,
                vol_pcr REAL,
                net_gex REAL,
                avg_iv REAL,
                iv_status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def save_snapshot(self, asset, spot, oi_pcr, vol_pcr, net_gex, avg_iv):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        iv_status = "NORMAL"
        if avg_iv > 22.0:
            iv_status = "🔴 IV SPIKE DETECTED"
        elif avg_iv < 11.0:
            iv_status = "🟢 IV CRUSH ZONE"
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO historical_snapshots (timestamp, asset, spot_price, oi_pcr, vol_pcr, net_gex, avg_iv, iv_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (now_str, asset, spot, oi_pcr, vol_pcr, net_gex, avg_iv, iv_status))
        conn.commit()
        conn.close()

    def get_historical_snapshots(self, asset):
        conn = sqlite3.connect(DB_NAME)
        query = "SELECT timestamp, spot_price, oi_pcr, vol_pcr, net_gex, avg_iv, iv_status FROM historical_snapshots WHERE asset = ? ORDER BY id DESC"
        df = pd.read_sql_query(query, conn, params=(asset,))
        conn.close()
        return df
