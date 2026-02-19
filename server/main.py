from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from model import fetch_weather_and_predict

# 数据库连接 
def get_db_connection():
    conn = sqlite3.connect('shop.db')
    conn.row_factory = sqlite3.Row
    return conn

def scheduled_prediction_task():
    print(f" [{datetime.datetime.now()}] 开始执行定时预测任务...")
    
    #爬取最新数据
    new_data = fetch_weather_and_predict()
    
    if not new_data:
        print("失败：未获取到气象数据")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    try:
        # 清理过期数据
        three_days_ago = (datetime.date.today() - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        cursor.execute("DELETE FROM pv_prediction WHERE prediction_date < ?", (three_days_ago,))
        expired_count = cursor.rowcount # 记录过期删除数
        
        # 覆盖策略旧记录
        cursor.execute("DELETE FROM pv_prediction WHERE prediction_date = ?", (today_str,))
        overwritten_count = cursor.rowcount # 记录覆盖删除数
        
        # 插入今日最新预测
        data_to_insert = [(item[0], item[1], today_str) for item in new_data]
        cursor.executemany('INSERT INTO pv_prediction (time_point, power_kw, prediction_date) VALUES (?, ?, ?)', data_to_insert)
        
        conn.commit()
        
        total_deleted = expired_count + overwritten_count
        print(f"清理旧数据 {total_deleted} 条 (过期:{expired_count}, 覆盖:{overwritten_count})，存入新数据 {len(data_to_insert)} 条 (日期: {today_str})")
        
    except Exception as e:
        print(f"数据库操作出错: {e}")
    finally:
        conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：开启调度器
    scheduler = AsyncIOScheduler()
    
    # 设定任务：每天凌晨 00:30 执行一次
    scheduler.add_job(scheduled_prediction_task, 'cron', hour=0, minute=30)
    
    scheduler.start()
    print("🚀 定时任务调度器已启动 (每天 00:30 自动爬取)")
    
    yield # 服务器开始运行
    
    # 关闭时
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# 数据模型
class SimulationRequest(BaseModel):
    buy_count: float

class TradeRequest(BaseModel):
    user_name: str
    buy_count: float
    total_price: float

@app.get("/api/dashboard")
def get_dashboard_data():
    conn = get_db_connection()
    
    cursor = conn.execute('SELECT MAX(prediction_date) as latest_date FROM pv_prediction')
    latest_date = cursor.fetchone()['latest_date']
    
    if not latest_date:
        return {"categories": [], "series": [], "max_power": 0, "current_power": 0}
        
    rows = conn.execute(
        'SELECT * FROM pv_prediction WHERE prediction_date = ? ORDER BY id ASC', 
        (latest_date,)
    ).fetchall()
    conn.close()
    
    # 格式化数据
    times = [row['time_point'] for row in rows]
    powers = [row['power_kw'] for row in rows]
    
    # 获取当前小时的功率 
    current_hour_index = datetime.datetime.now().hour
    # 防止索引越界
    current_power = powers[current_hour_index] if 0 <= current_hour_index < len(powers) else 0

    return {
        "categories": times,
        "series": powers,
        "max_power": max(powers) if powers else 0,
        "current_power": current_power,
        "data_date": latest_date 
    }

#手动刷新
@app.post("/api/refresh_prediction")
def refresh_prediction():
    # 手动触发一次任务函数
    scheduled_prediction_task()
    return {"status": "success", "message": "已手动触发后台同步任务"}

#  电价模拟 

@app.post("/api/simulate")
def simulate_price(req: SimulationRequest):
    conn = get_db_connection()
    
    cursor = conn.execute('SELECT MAX(prediction_date) as latest_date FROM pv_prediction')
    latest_date = cursor.fetchone()['latest_date']
    
    current_time_str = datetime.datetime.now().strftime("%H:00")
    
    row = conn.execute(
        'SELECT power_kw FROM pv_prediction WHERE prediction_date = ? AND time_point LIKE ?', 
        (latest_date, f"{current_time_str}%")
    ).fetchone()
    conn.close()
    
    current_power = row['power_kw'] if row else 0
    
    base_price = 0.8
    if current_power > 200:
        real_price = base_price * 0.4
    elif current_power > 50:
        real_price = base_price * 0.8
    else:
        real_price = base_price
        
    total_cost = req.buy_count * real_price
    
    return {
        "status": "success",
        "current_power": current_power,
        "unit_price": round(real_price, 3),
        "total_cost": round(total_cost, 2),
        "message": "光伏充足，电价已优惠" if current_power > 200 else "当前光伏出力较低"
    }

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
    order_id = cursor.lastrowid
    conn.close()
    return {"status": "success", "order_id": order_id}

@app.get("/api/orders")
def get_orders():
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM transactions ORDER BY id DESC').fetchall()
    conn.close()
    return {"data": orders}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)