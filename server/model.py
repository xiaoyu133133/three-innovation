import requests
import datetime

# --- 哈班岔村坐标 ---
LAT = 35.85
LON = 104.12

def fetch_weather_and_predict():
    """
    1. 从气象接口获取未来24小时的辐射数据
    2. 使用物理模型计算光伏功率
    """
    print(f"📡 正在连接气象卫星数据... [坐标: {LAT}, {LON}]")
    
    # 1. 构造请求地址 (获取短波辐射 shortwave_radiation)
    # 这是一个真实的气象 API，不是随机数！
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=shortwave_radiation&timezone=Asia%2FShanghai&forecast_days=1"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # 获取 API 返回的时间和辐射列表
        hourly_data = data.get("hourly", {})
        times = hourly_data.get("time", []) # 格式: "2026-02-06T00:00"
        radiations = hourly_data.get("shortwave_radiation", []) # 单位: W/m²
        
        prediction_results = []
        
        # --- 2. 加载哈班岔村光伏模型参数 ---
        # 假设：村里铺设了 2000 平方米的光伏板
        # 假设：光伏板转换效率 18%
        # 假设：系统综合效率 (PR) 0.8 (线损、灰尘等)
        TOTAL_AREA = 3000  # m²
        EFFICIENCY = 0.18
        PR_FACTOR = 0.85 
        
        print("⚙️ 加载预测模型参数：Area=3000m², Eff=18%, PR=0.85")

        for i in range(len(times)):
            # 拿到时间 (只取小时部分，如 "12:00")
            dt_str = times[i]
            # API返回的是 "2026-02-06T13:00"，我们处理一下
            dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
            time_point = dt_obj.strftime("%H:%M")
            
            # 拿到辐射值 W/m²
            G = radiations[i] 
            
            # --- 核心公式 ---
            # 功率 (kW) = 辐射(W/m²) * 面积 * 效率 * PR / 1000
            power_kw = (G * TOTAL_AREA * EFFICIENCY * PR_FACTOR) / 1000
            
            # 保留两位小数
            prediction_results.append((time_point, round(power_kw, 2)))
            
        print("✅ 预测计算完成！")
        return prediction_results

    except Exception as e:
        print(f"❌ 获取气象数据失败: {e}")
        # 如果断网了，只能返回空列表，或者在这里写备用的随机逻辑
        return []

# 用于测试
if __name__ == "__main__":
    res = fetch_weather_and_predict()
    print(res)