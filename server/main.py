from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import datetime
import uvicorn

app = FastAPI()

# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('shop.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- 数据模型 ---
class SimulationRequest(BaseModel):
    buy_count: float  # 用户想买多少度电

class TradeRequest(BaseModel):
    user_name: str
    buy_count: float
    total_price: float

# --- 接口 1: 获取光伏预测数据 (用于 ECharts 展示) ---
@app.get("/api/dashboard")
def get_dashboard_data():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM pv_prediction').fetchall()
    conn.close()
    
    # 格式化为前端 ECharts 容易读取的数组
    times = [row['time_point'] for row in rows]
    powers = [row['power_kw'] for row in rows]
    
    return {
        "categories": times, # X轴
        "series": powers,    # Y轴
        "max_power": max(powers) if powers else 0,
        "current_power": powers[datetime.datetime.now().hour] if powers else 0
    }

# --- 接口 2: 电价模拟计算 ---
@app.post("/api/simulate")
def simulate_price(req: SimulationRequest):
    # 1. 获取当前小时的光伏功率
    current_hour = datetime.datetime.now().hour
    time_str = f"{current_hour:02d}:00"
    
    conn = get_db_connection()
    row = conn.execute('SELECT power_kw FROM pv_prediction WHERE time_point = ?', (time_str,)).fetchone()
    conn.close()
    
    current_power = row['power_kw'] if row else 0
    
    # 2. 定价算法 (数学建模的核心部分)
    # 逻辑：光伏功率越高，供过于求，电价越便宜；晚上没光，电价贵。
    base_price = 0.8  # 基础电价 0.8元/度
    
    if current_power > 200:
        # 阳光充足，打折
        real_price = base_price * 0.4 # 0.32元
    elif current_power > 50:
        # 阳光一般，打8折
        real_price = base_price * 0.8
    else:
        # 晚上或阴天，原价
        real_price = base_price
        
    total_cost = req.buy_count * real_price
    
    return {
        "status": "success",
        "current_power": current_power,
        "unit_price": round(real_price, 3), # 单价
        "total_cost": round(total_cost, 2), # 总价
        "message": "光伏充足，电价已优惠" if current_power > 200 else "当前光伏出力较低"
    }

# --- 接口 3: 提交交易 ---
@app.post("/api/trade")
def submit_trade(req: TradeRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        'INSERT INTO transactions (user_name, buy_count, total_price, trade_time) VALUES (?, ?, ?, ?)',
        (req.user_name, req.buy_count, req.total_price, now)
    )
    
    conn.commit()
    conn.close()
    
    return {"status": "success", "order_id": cursor.lastrowid}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)