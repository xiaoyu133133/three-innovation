import sqlite3
import random
import datetime

def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # --- 1. 光伏功率预测表 (PV_Prediction) ---
    # time_point: 时间点 (例如 "12:00")
    # power_kw: 预测功率 (千瓦)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pv_prediction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time_point TEXT NOT NULL,
        power_kw REAL NOT NULL
    )
    ''')

    # --- 2. 交易记录表 (Transactions) ---
    # user_name: 用户名 (模拟)
    # buy_count: 购电量 (kWh)
    # total_price: 总费用
    # trade_time: 交易时间
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        buy_count REAL,
        total_price REAL,
        trade_time TEXT
    )
    ''')

    # --- 3. 生成模拟数据 (核心算法部分) ---
    # 这里我们用 Python 模拟生成哈班岔村未来24小时的数据
    # 假设：早8点到晚8点有光，中午12-14点是高峰
    
    cursor.execute('DELETE FROM pv_prediction') # 先清空旧数据
    
    data_list = []
    # 模拟从 00:00 到 23:00 的数据
    for hour in range(24):
        time_str = f"{hour:02d}:00"
        
        # 简易物理模型：
        # 夜晚 (0-6点, 19-23点): 功率为 0
        if hour < 7 or hour > 19:
            power = 0
        else:
            # 白天：用一个抛物线/正弦波模拟光照强度
            # 峰值假设为 500kW (哈班岔村光伏电站假设规模)
            # random.uniform(0.8, 1.0) 模拟云层遮挡的随机波动
            mid_day = 13  # 下午1点光照最强
            hour_diff = abs(hour - mid_day)
            # 简单的衰减公式
            base_power = 500 * (1 - (hour_diff / 7)**2) 
            if base_power < 0: base_power = 0
            
            power = base_power * random.uniform(0.9, 1.1)
        
        data_list.append((time_str, round(power, 2)))

    cursor.executemany('INSERT INTO pv_prediction (time_point, power_kw) VALUES (?, ?)', data_list)
    
    conn.commit()
    conn.close()
    print("✅ 能源数据库初始化完成！生成了哈班岔村24小时预测数据。")

if __name__ == '__main__':
    init_db()