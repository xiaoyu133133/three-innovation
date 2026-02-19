import sqlite3
import datetime
from model import fetch_weather_and_predict

def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pv_prediction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time_point TEXT NOT NULL,
        power_kw REAL NOT NULL,
        prediction_date TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        buy_count REAL,
        total_price REAL,
        trade_time TEXT
    )
    ''')
    
    conn.commit()

    cursor.execute('SELECT count(*) FROM pv_prediction')
    if cursor.fetchone()[0] == 0:
        print("数据库为空，正在执行首次数据初始化...")
        
        real_data = fetch_weather_and_predict()
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        if real_data:
            data_to_insert = []
            for item in real_data:
                data_to_insert.append((item[0], item[1], today_str))
            
            cursor.executemany('INSERT INTO pv_prediction (time_point, power_kw, prediction_date) VALUES (?, ?, ?)', data_to_insert)
            print(f"已初始化 {len(data_to_insert)} 条数据 (日期: {today_str})")
        else:
            print("初始化失败：未获取到气象数据")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()