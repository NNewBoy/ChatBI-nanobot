import os
import sqlite3
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

WORKSPACE = Path(__file__).resolve().parent
SQLITE_DB_PATH = WORKSPACE / "stock_data.db"

DB_USER = os.getenv("STOCK_DB_USER", "root")
DB_PASSWORD = os.getenv("STOCK_DB_PASSWORD", "")
DB_HOST = os.getenv("STOCK_DB_HOST", "localhost:3306")
DB_NAME = os.getenv("STOCK_DB_NAME", "ai")
DB_CONN_STR = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"


def init_sqlite_from_mysql():
    if SQLITE_DB_PATH.exists():
        print(f"SQLite数据库已存在: {SQLITE_DB_PATH}")
        return

    if not DB_PASSWORD:
        print("未配置 MySQL 连接信息，请设置环境变量:")
        print("  STOCK_DB_USER, STOCK_DB_PASSWORD, STOCK_DB_HOST, STOCK_DB_NAME")
        print("或手动将 stock_data.db 放到 stock-bot/ 目录下")
        return

    print("SQLite数据库不存在，正在从MySQL导入数据...")
    try:
        mysql_engine = create_engine(DB_CONN_STR, connect_args={'connect_timeout': 10})
        df = pd.read_sql('SELECT * FROM stock_history', mysql_engine)

        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        df.to_sql('stock_history', conn, if_exists='replace', index=False)
        conn.execute('CREATE INDEX IF NOT EXISTS idx_ts_code ON stock_history(ts_code)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_date ON stock_history(trade_date)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_ts_code_date ON stock_history(ts_code, trade_date)')
        conn.commit()
        conn.close()
        print(f"已导入 {len(df)} 条记录到 {SQLITE_DB_PATH}")
    except Exception as e:
        print(f"MySQL导入失败: {e}")
        print("请手动将 stock_data.db 放到 stock-bot/ 目录下")


if __name__ == "__main__":
    init_sqlite_from_mysql()
