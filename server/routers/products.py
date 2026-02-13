# server/routers/products.py
from fastapi import APIRouter
from database import get_db_connection # 引用刚才拆出来的配置

# 创建一个路由器
router = APIRouter()

@router.get("/")  # 注意这里是 /，因为在 main.py 里已经挂载到 /api/products 了
def get_products():
    """获取所有商品列表"""
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return {"data": products}

@router.get("/{product_id}")
def get_product_detail(product_id: int):
    """获取单个商品详情 (为下一步做准备)"""
    conn = get_db_connection()
    # 使用参数化查询防止 SQL 注入
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    
    if product is None:
        return {"error": "商品不存在"}
    
    return {"data": product}