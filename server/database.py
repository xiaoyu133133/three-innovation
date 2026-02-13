# server/database.py
import sqlite3

# 定义数据库文件名，方便统一修改
DB_FILE = 'shop.db'

def get_db_connection():
    """获取数据库连接的工厂函数"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # 让结果像字典一样访问
    return conn