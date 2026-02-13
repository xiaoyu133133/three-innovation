import sqlite3

def init_db():
    # 1. 连接数据库（会自动生成 shop.db 文件）
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # 2. 创建商品表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        image TEXT,
        tag TEXT
    )
    ''')

    # 3. 准备一些初始数据
    initial_products = [
        ('2026新款 iPad Pro', 6999.00, 'https://img.yzcdn.cn/vant/ipad.jpeg', '自营'),
        ('透气舒适运动跑鞋', 299.00, 'https://img.yzcdn.cn/vant/shoes.jpg', '热销'),
        ('三创比赛专用能量水', 15.50, 'https://img.yzcdn.cn/vant/apple-1.jpg', '推荐'),
        ('Python全栈开发指南', 88.00, 'https://img.yzcdn.cn/vant/apple-2.jpg', '知识'),
        ('可爱的猫咪 (非卖品)', 9999.00, 'https://img.yzcdn.cn/vant/cat.jpeg', '限量')
    ]

    # 4. 清空旧数据并插入新数据（防止重复）
    cursor.execute('DELETE FROM products')
    cursor.executemany('INSERT INTO products (name, price, image, tag) VALUES (?, ?, ?, ?)', initial_products)

    conn.commit()
    conn.close()
    print("✅ 数据库 shop.db 初始化完成！")

if __name__ == '__main__':
    init_db()