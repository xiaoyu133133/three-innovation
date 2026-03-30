import random
import requests
from fastapi import FastAPI, Header, HTTPException
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

# --- 核心任务：定时爬取、存储、清理 ---
def scheduled_prediction_task():
    print(f"⏰ [{datetime.datetime.now()}] 开始执行定时预测任务...")
    
    new_data = fetch_weather_and_predict()
    if not new_data:
        print("❌ 任务失败：未获取到气象数据")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    try:
        # 2. 清理过期策略：删除 5 天前的数据
        five_days_ago = (datetime.date.today() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
        cursor.execute("DELETE FROM pv_prediction WHERE prediction_date < ?", (five_days_ago,))
        
        # ✨ 新增：同步清理 5 天前的效率数据
        cursor.execute("DELETE FROM daily_efficiency WHERE prediction_date < ?", (five_days_ago,))
        expired_count = cursor.rowcount
        
        cursor.execute("DELETE FROM pv_prediction WHERE prediction_date = ?", (today_str,))
        overwritten_count = cursor.rowcount 
        
        data_to_insert = [(item[0], item[1], today_str) for item in new_data]
        cursor.executemany('INSERT INTO pv_prediction (time_point, power_kw, prediction_date) VALUES (?, ?, ?)', data_to_insert)
        
        conn.commit()
        total_deleted = expired_count + overwritten_count
        print(f"✅ 任务完成！清理旧数据 {total_deleted} 条，存入新数据 {len(data_to_insert)} 条 (日期: {today_str})")
        
    except Exception as e:
        print(f"❌ 数据库操作出错: {e}")
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

# 在前面的 class SimulationRequest(BaseModel): 附近加上：
class WithdrawRequest(BaseModel):
    amount: float

class LoginRequest(BaseModel):
    code: str

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

@app.post("/api/login")
def wechat_login(req: LoginRequest):
    # 🚨 注意：这里必须替换为你自己的小程序 AppID 和 AppSecret！
    # 登录 微信公众平台 -> 开发管理 -> 开发设置 中获取
    APP_ID = "wxa358095e0335a6b6" 
    APP_SECRET = "f6567723f596e0dc0b362b8318b8161b"
    wx_url = f"https://api.weixin.qq.com/sns/jscode2session?appid={APP_ID}&secret={APP_SECRET}&js_code={req.code}&grant_type=authorization_code"
    try:
        res = requests.get(wx_url, timeout=10)
        response = res.json()
        openid = response.get("openid")
        
        if openid:
            # ✨ 核心：用户存在则忽略，不存在则自动注册入库
            conn = get_db_connection()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT OR IGNORE INTO users (openid, join_time) VALUES (?, ?)", (openid, now))
            conn.commit()
            conn.close()
            
            return {
                "status": "success", 
                "message": "登录成功",
                "data": {"openid": openid, "token": f"token_{openid[:10]}"}
            }
        else:
            return {"status": "error", "message": f"鉴权失败: {response.get('errmsg')}"}
    except Exception as e:
        return {"status": "error", "message": f"后端运行异常: {str(e)}"}
    
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
# --- ✨ 接口：获取发电效率评分 (支持固化数据与强制演示切换) ---
@app.get("/api/efficiency")
def get_efficiency(mode: str = "良好", force: str = "false"):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    conn = get_db_connection()
    is_force = (force.lower() == "true")
    
    capacity = 500.0
    sun_hours = 4.0
    sys_efficiency = 0.8
    theoretical_kwh = capacity * sun_hours * sys_efficiency
    
    # 查询今天是否已经有评分了
    row = conn.execute("SELECT score FROM daily_efficiency WHERE prediction_date = ?", (today_str,)).fetchone()
    
    if row and not is_force:
        # 如果已经存在，且不是强制切换，则直接使用现有分数，逆向推导实际发电量
        score = row['score']
        actual_kwh = theoretical_kwh * (score / 100.0)
    else:
        # 如果是今天第一次，或者是点击了“切换按钮(force=true)”，则重新生成随机数
        if mode == "优秀": actual_kwh = theoretical_kwh * random.uniform(0.91, 0.98)
        elif mode == "一般": actual_kwh = theoretical_kwh * random.uniform(0.71, 0.78)
        elif mode == "异常": actual_kwh = theoretical_kwh * random.uniform(0.50, 0.65)
        else:
            actual_kwh = theoretical_kwh * random.uniform(0.81, 0.88)
            mode = "良好"
        score = int((actual_kwh / theoretical_kwh) * 100)

    # 根据分数匹配文案和颜色 (保持全局统一)
    if score >= 90:
        grade, reason, color = "优秀", "发电正常，系统运行处于最佳状态", "#07c160"
    elif score >= 80:
        grade, reason, color = "良好", "运行平稳，可能受轻微云层遮挡影响", "#1989fa"
    elif score >= 70:
        grade, reason, color = "一般", "可能原因：光伏板轻微遮挡 / 表面灰尘影响严重", "#ff976a"
    else:
        grade, reason, color = "异常", "可能原因：逆变器故障 / 严重遮挡，建议立即派单检查", "#ee0a24"
        
    # 保存或更新今天的固定效率
    conn.execute("INSERT OR REPLACE INTO daily_efficiency (prediction_date, score) VALUES (?, ?)", (today_str, score))
    conn.commit()
    conn.close()
        
    return {
        "score": score,
        "grade": grade,
        "theoretical": round(theoretical_kwh, 1),
        "actual": round(actual_kwh, 1),
        "reason": reason,
        "color": color
    }

# ✨ 新增接口：获取最近 5 天真实的计算收益
# ================= ✨ 2. 收益模拟接口升级：分离个人与村集体 =================
# 这里我们用一个非常精妙的数学魔法：用总发电量除以 130（村里总户数），算作个人的独立发电量和收益！
@app.get("/api/surplus")
def get_surplus_data(x_wx_openid: str = Header(None)): # 👈 接收前端的 openid 身份头
    if not x_wx_openid:
        return {"error": "未登录或未传递身份信息"}

    conn = get_db_connection()
    
    try:
        today = datetime.date.today()
        days = [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4, -1, -1)]
        
        chart_data = []
        today_data = {}
        
        # 获取用户的个人碳积分 (展示独立账户)
        user_row = conn.execute("SELECT carbon_points FROM users WHERE openid = ?", (x_wx_openid,)).fetchone()
        my_points = user_row['carbon_points'] if user_row else 0
        
        for d in days:
            row = conn.execute("SELECT SUM(power_kw) as total_power FROM pv_prediction WHERE prediction_date = ?", (d,)).fetchone()
            global_theoretical = row['total_power'] if row and row['total_power'] else (2000.0 + random.uniform(-200, 200))
            score_row = conn.execute("SELECT score FROM daily_efficiency WHERE prediction_date = ?", (d,)).fetchone()
            score = score_row['score'] if score_row else 85
            
            global_actual_gen = global_theoretical * (score / 100.0)
            
            # ✨ 核心隔离逻辑：计算该用户的个人份额 (全村 130 户平分)
            my_actual_gen = global_actual_gen / 130.0
            
            my_surplus = my_actual_gen * 0.70 
            my_self_use = my_actual_gen * 0.30 
            
            my_income = my_surplus * 0.41 
            my_saved = my_self_use * 0.56 
            my_total_rev = my_income + my_saved
            
            chart_data.append({"date": d, "income": round(my_income, 2), "saved": round(my_saved, 2)})
            
            if d == today.strftime("%Y-%m-%d"):
                today_data = {
                    "totalGen": round(my_actual_gen, 1),
                    "selfUse": round(my_self_use, 1),
                    "surplus": round(my_surplus, 1),
                    "income": round(my_income, 2),
                    "saved": round(my_saved, 2),
                    "totalRev": round(my_total_rev, 2),
                    "myPoints": my_points # 将该用户独立的积分下发
                }
        return {"chart_data": chart_data, "today_data": today_data}
    except Exception as e:
        return {"error": str(e)}
    finally:        
            
        conn.close()

# ================= ✨ 提现记录相关接口 =================

# 1. 申请提现
@app.post("/api/withdraw")
def apply_withdraw(req: WithdrawRequest, x_wx_openid: str = Header(None)): # 👈 认人
    if not x_wx_openid:
        return {"error": "权限不足"}
    conn = get_db_connection()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 存入带有专属 openid 的提现记录
    conn.execute("INSERT INTO withdrawals (openid, amount, status, apply_time) VALUES (?, ?, ?, ?)", (x_wx_openid, req.amount, 0, now))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/withdraws")
def get_withdraws(x_wx_openid: str = Header(None)): # 👈 认人
    conn = get_db_connection()
    # ✨ 核心隔离逻辑：只查询该 openid 名下的提现流水！
    rows = conn.execute("SELECT * FROM withdrawals WHERE openid = ? ORDER BY id DESC", (x_wx_openid,)).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows]}

# 3. 删除提现记录
@app.delete("/api/withdraws/{w_id}")
def delete_withdraw(w_id: int):
    conn = get_db_connection()
    conn.execute('DELETE FROM withdrawals WHERE id = ?', (w_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

# ✨ 4. 新增：推进结算状态接口 (0->1->2)
@app.put("/api/withdraws/{w_id}/advance")
def advance_withdraw(w_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT status FROM withdrawals WHERE id = ?", (w_id,)).fetchone()
    if row and row['status'] < 2:
        new_status = row['status'] + 1
        conn.execute("UPDATE withdrawals SET status = ? WHERE id = ?", (new_status, w_id))
        conn.commit()
    conn.close()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)