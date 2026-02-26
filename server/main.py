import random
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

# --- 数据模型 ---
class SimulationRequest(BaseModel):
    buy_count: float
    target_time: str  # ✨ 新增：用户选择的模拟时间，例如 "12:00"

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

# --- 接口 3: 电价模拟 (升级版) ---
@app.post("/api/simulate")
def simulate_price(req: SimulationRequest):
    conn = get_db_connection()
    cursor = conn.execute('SELECT MAX(prediction_date) as latest_date FROM pv_prediction')
    latest_date = cursor.fetchone()['latest_date']
    
    row = conn.execute(
        'SELECT power_kw FROM pv_prediction WHERE prediction_date = ? AND time_point = ?', 
        (latest_date, req.target_time)
    ).fetchone()
    conn.close()
    
    current_power = row['power_kw'] if row else 0
    
    base_price = 0.8  # 基础电价 0.8元/度
    
    # ✨ 核心修改：适配 500kWp 的规模，按比例放大打折的门槛
    if current_power >= 200:
        # 阳光非常充足 (大于 200kW 时)，电价打 4 折
        real_price = base_price * 0.4
        msg = "光伏充足，电价享 4 折特惠"
    elif current_power >= 50:
        # 阳光一般 (大于 50kW 时)，电价打 8 折
        real_price = base_price * 0.8
        msg = "光伏平稳，电价享 8 折优惠"
    else:
        # 晚上或阴天，执行原价
        real_price = base_price
        msg = "当前光伏出力较低，执行标准电价"
        
    total_cost = req.buy_count * real_price
    
    return {
        "status": "success",
        "current_power": current_power,
        "unit_price": round(real_price, 3),
        "total_cost": round(total_cost, 2),
        "message": msg
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

@app.delete("/api/orders/{order_id}")
def delete_order(order_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

# ✨ 新增接口：清空所有记录 (一键清空用)
@app.delete("/api/orders")
def clear_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions')
    conn.commit()
    conn.close()
    return {"status": "success"}

# ✨ 新增接口：获取发电效率评分 (支持传入 mode 进行演示切换)
@app.get("/api/efficiency")
def get_efficiency(mode: str = "良好"):
    # 1. 理论发电量计算
    capacity = 500.0  # 甲方预设：500 kWp
    sun_hours = 4.0   # 兰州地区日均有效日照大致为 4 小时
    sys_efficiency = 0.8 # 系统通用效率系数
    
    theoretical_kwh = capacity * sun_hours * sys_efficiency # 理论值：1600 kWh
    
    # 2. 根据模式生成模拟的实际发电量
    if mode == "优秀":
        # 90-100分
        actual_kwh = theoretical_kwh * random.uniform(0.91, 0.98)
    elif mode == "一般":
        # 70-79分
        actual_kwh = theoretical_kwh * random.uniform(0.71, 0.78)
    elif mode == "异常":
        # <70分
        actual_kwh = theoretical_kwh * random.uniform(0.50, 0.65)
    else:
        # 默认：良好 (80-89分)
        actual_kwh = theoretical_kwh * random.uniform(0.81, 0.88)
        mode = "良好" # 兜底
        
    # 3. 计算评分
    score = int((actual_kwh / theoretical_kwh) * 100)
    
    # 4. 匹配评级与话术、颜色
    if score >= 90:
        grade = "优秀"
        reason = "发电正常，系统运行处于最佳状态"
        color = "#07c160" # 绿色
    elif score >= 80:
        grade = "良好"
        reason = "运行平稳，可能受轻微云层遮挡影响"
        color = "#1989fa" # 蓝色
    elif score >= 70:
        grade = "一般"
        reason = "可能原因：光伏板轻微遮挡 / 表面灰尘影响严重"
        color = "#ff976a" # 橙色
    else:
        grade = "异常"
        reason = "可能原因：逆变器故障 / 严重遮挡，建议立即派单检查"
        color = "#ee0a24" # 红色
        
    return {
        "score": score,
        "grade": grade,
        "theoretical": round(theoretical_kwh, 1),
        "actual": round(actual_kwh, 1),
        "reason": reason,
        "color": color
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)