import sqlite3
import datetime
from model import fetch_weather_and_predict

def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # ✨ 1. 新增：用户主表 (独立账户体系的核心)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        openid TEXT PRIMARY KEY,
        nickname TEXT,
        avatar_url TEXT,
        carbon_points INTEGER DEFAULT 0,
        balance REAL DEFAULT 0.0,
        join_time TEXT
    )
    ''')

    # 2. 预测表 (全局物理数据)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pv_prediction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time_point TEXT NOT NULL,
        power_kw REAL NOT NULL,
        prediction_date TEXT NOT NULL
    )
    ''')
    
    # 3. 每日发电效率评分表 (全局物理数据)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_efficiency (
        prediction_date TEXT PRIMARY KEY,
        score INTEGER NOT NULL
    )
    ''')

    # ✨ 4. 升级：交易表 (加上 openid)
    # 因为改了表结构，开发阶段为了防止报错，先删除旧表
    cursor.execute('DROP TABLE IF EXISTS transactions')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        openid TEXT NOT NULL,
        trade_type TEXT,
        amount REAL,
        trade_time TEXT
    )
    ''')

    # ✨ 5. 升级：提现记录表 (加上 openid，实现每个人只能看自己的提现)
    cursor.execute('DROP TABLE IF EXISTS withdrawals')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        openid TEXT NOT NULL,
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
            
            # 塞入一条演示用的用户和提现记录
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            demo_openid = "demo_user_001"
            cursor.execute('INSERT INTO users (openid, nickname, join_time) VALUES (?, ?, ?)', (demo_openid, "演示用户", now_str))
            cursor.execute('INSERT INTO withdrawals (openid, amount, status, apply_time) VALUES (?, ?, ?, ?)', (demo_openid, 200.5, 2, now_str))
            
            print(f"✅ 已初始化今日数据与效率 (日期: {today_str})")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()