# server/main.py
from fastapi import FastAPI
import uvicorn
from routers import products  # 导入下面的路由模块

app = FastAPI(title="三创商城后端 API")

# 注册路由：把 products 里的接口挂载到 /api/products 下
app.include_router(products.router, prefix="/api/products", tags=["商品管理"])

@app.get("/")
def read_root():
    return {"message": "商城后端服务已启动 (Structured Version)"}

# ... 之前的代码 ...

# 新增接口：根据 ID 获取单个商品详情
@app.get("/api/products/{product_id}")
def get_product_detail(product_id: int):
    conn = get_db_connection()
    # 使用 ? 作为占位符，防止 SQL 注入安全问题
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    
    if product is None:
        return {"error": "商品不存在"}
    
    # fetchone 返回的是 Row 对象，直接返回会被 FastAPI 转成 JSON
    return {"data": product}

# ... existing code ...

if __name__ == "__main__":
    # 以后运行还是运行这个文件
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)