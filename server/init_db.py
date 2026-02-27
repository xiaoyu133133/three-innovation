import sqlite3
import datetime
from model import fetch_weather_and_predict

def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # 1. 预测表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pv_prediction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time_point TEXT NOT NULL,
        power_kw REAL NOT NULL,
        prediction_date TEXT NOT NULL
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
    
    # 3. 每日发电效率评分表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_efficiency (
        prediction_date TEXT PRIMARY KEY,
        score INTEGER NOT NULL
    )
    ''')

    # ✨ 4. 新增：提现记录表
    # status: 0-待审核, 1-结算中, 2-已到账
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        status INTEGER NOT NULL,
        apply_time TEXT NOT NULL
    )
    ''')
    
    conn.commit()

    # 初始数据填充
    cursor.execute('SELECT count(*) FROM pv_prediction')
    if cursor.fetchone()[0] == 0:
        print("🚀 数据库为空，正在执行首次数据初始化...")
        real_data = fetch_weather_and_predict()
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        if real_data:
            data_to_insert = [(item[0], item[1], today_str) for item in real_data]
            cursor.executemany('INSERT INTO pv_prediction (time_point, power_kw, prediction_date) VALUES (?, ?, ?)', data_to_insert)
            cursor.execute('INSERT OR REPLACE INTO daily_efficiency (prediction_date, score) VALUES (?, ?)', (today_str, 85))
            
            # 塞入一条演示用的提现记录
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('INSERT INTO withdrawals (amount, status, apply_time) VALUES (?, ?, ?)', (200.5, 2, now_str))
            
            print(f"✅ 已初始化今日数据与效率 (日期: {today_str})")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()