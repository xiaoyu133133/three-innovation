import requests
import datetime
import joblib
import pandas as pd
import os

# --- 哈班岔村坐标 ---
LAT = 35.85
LON = 104.12

# 模型文件路径
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'pv_model.pkl')

SYSTEM_SCALE = 100 

def fetch_weather_and_predict():
    
    # 1. 爬取数据
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=shortwave_radiation,temperature_2m,windspeed_10m&timezone=Asia%2FShanghai&forecast_days=1"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        hourly_data = data.get("hourly", {})
        times = hourly_data.get("time", [])
        radiations = hourly_data.get("shortwave_radiation", [])
        temperatures = hourly_data.get("temperature_2m", [])
        wind_speeds = hourly_data.get("windspeed_10m", [])
        
        # 准备输入给模型的数据列表
        input_data = []
        time_points = []
        
        for i in range(len(times)):
            dt_str = times[i]
            dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
            time_point = dt_obj.strftime("%H:%M")
            
            # 收集特征：[G(i), T2m, WS10m] 
            input_data.append([radiations[i], temperatures[i], wind_speeds[i]])
            time_points.append(time_point)
            
        if not os.path.exists(MODEL_PATH):
            print("错误：找不到模型文件 pv_model.pkl，请先运行 train.py")
            return []
            
        model = joblib.load(MODEL_PATH)
        
        X_predict = pd.DataFrame(input_data, columns=['G(i)', 'T2m', 'WS10m'])
        
        predicted_power_watts = model.predict(X_predict)
        
        results = []
        for i in range(len(time_points)):
            # 1kWp基准
            # 转换公式：(W / 1000) * 100 = kW
            power_kw = (predicted_power_watts[i] / 1000) * SYSTEM_SCALE
            
            # 保留两位小数
            power_kw = round(max(0, power_kw), 2)
            
            results.append((time_points[i], power_kw))
            
        return results

    except Exception as e:
        print(f"预测失败: {e}")
        return []

if __name__ == "__main__":

    res = fetch_weather_and_predict()
    print(res[:5])