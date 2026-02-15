import sqlite3
import datetime
# 👇 引入我们刚才写的真实预测模块
from model import fetch_weather_and_predict

def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # 1. 预测表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pv_prediction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time_point TEXT NOT NULL,
        power_kw REAL NOT NULL
    )
    ''')

    # 2. 交易表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        buy_count REAL,
        total_price REAL,
        trade_time TEXT
    )
    ''')

    # --- 数据更新逻辑 ---
    print("🔄 正在初始化/更新数据库...")
    
    # 1. 先尝试获取真实气象数据
    real_data = fetch_weather_and_predict()
    
    if real_data:
        # 如果拿到了真数据，就清空旧的，存入新的
        cursor.execute('DELETE FROM pv_prediction')
        cursor.executemany('INSERT INTO pv_prediction (time_point, power_kw) VALUES (?, ?)', real_data)
        print(f"✅ 已存入 {len(real_data)} 条来自哈班岔村的真实预测数据！")
    else:
        # 如果断网了，或者没拿到数据，就不用管了（或者你可以保留之前的随机逻辑作为备用）
        print("⚠️ 警告：使用旧数据或空数据（网络请求失败）")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()