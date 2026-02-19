import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

# --- 配置 ---
CSV_FILE = 'hour data.csv'
MODEL_FILE = 'pv_model.pkl'

def train_model():
    print(f"📂 正在读取 {CSV_FILE} ...")
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ 错误：找不到文件 {CSV_FILE}，请确保它在 server 目录下！")
        return

    # 1. 读取数据 (PVGIS 导出的 CSV 前面通常有 10 行元数据，需要跳过)
    # 关键列名映射:
    # 'time': 时间
    # 'P': 发电功率 (W) -> 目标值 (Target)
    # 'G(i)': 坡面辐射 (W/m2) -> 特征 (Feature)
    # 'T2m': 2米气温 (deg C) -> 特征 (Feature)
    # 'WS10m': 10米风速 (m/s) -> 特征 (Feature)
    
    try:
        df = pd.read_csv(CSV_FILE, skiprows=10)
    except Exception as e:
        print(f"❌ 读取 CSV 失败: {e}")
        return

    # 2. 数据清洗
    # 2.1 转换 P 列为数字 (处理可能存在的非数字字符)
    df['P'] = pd.to_numeric(df['P'], errors='coerce')
    
    # 2.2 删除包含空值的行
    df = df.dropna(subset=['P', 'G(i)', 'T2m', 'WS10m'])
    
    # 2.3 提取特征 X 和 目标 y
    # 我们用 [辐射, 温度, 风速] 来预测 [功率]
    # 注意：这里我们假设未来天气预报能提供这三个数据
    feature_cols = ['G(i)', 'T2m', 'WS10m']
    X = df[feature_cols]
    y = df['P']
    
    print(f"📊 数据加载成功，共 {len(df)} 条有效记录。")
    print("🚀 开始训练随机森林模型 (RandomForest)...")
    
    # 3. 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. 训练模型
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # 5. 验证模型
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"✅ 训练完成！")
    print(f"   - R² 得分 (越接近1越好): {r2:.4f}")
    print(f"   - 均方误差 (MSE): {mse:.2f}")
    
    # 6. 保存模型
    joblib.dump(model, MODEL_FILE)
    print(f"💾 模型已保存为: {MODEL_FILE}")

if __name__ == "__main__":
    train_model()