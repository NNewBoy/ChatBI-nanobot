import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import pandas as pd
from nanobot.agent.tools.base import Tool

from charts.stock_chart import generate_stock_chart

WORKSPACE = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE / "stock_data.db"
IMAGE_DIR = WORKSPACE / "image_show"


class StockQueryDBTool(Tool):

    @property
    def name(self) -> str:
        return "query_db"

    @property
    def description(self) -> str:
        return (
            "Execute a read-only SQL query against the stock_history database. "
            "Returns query results as markdown table with chart. Only SELECT statements are allowed."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to execute (SELECT only)"
                }
            },
            "required": ["sql"]
        }

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        sql = kwargs.get("sql", "").strip()
        if not sql:
            return "Error: empty SQL query"

        upper = sql.upper().lstrip()
        if not (upper.startswith("SELECT") or upper.startswith("PRAGMA")):
            return "Error: only SELECT and PRAGMA statements are allowed"

        try:
            conn = sqlite3.connect(str(DB_PATH))
            df = pd.read_sql_query(sql, conn)
            conn.close()
        except Exception as e:
            return f"SQL Error: {e}"

        if df.empty:
            return "Query returned 0 rows."

        n = len(df)
        if n <= 10:
            md = df.to_markdown(index=False)
        else:
            md = df.head(5).to_markdown(index=False)
            md += "\n\n... (省略中间数据) ...\n\n"
            md += df.tail(5).to_markdown(index=False)

        if n > 1:
            md += "\n\n**描述统计:**\n\n"
            md += df.describe().to_markdown()

        if len(df) <= 1:
            return md

        os.makedirs(str(IMAGE_DIR), exist_ok=True)
        filename = f"chart_{int(time.time() * 1000)}.png"
        save_path = IMAGE_DIR / filename
        generate_stock_chart(df, str(save_path))
        img_path = f"image_show/{filename}"
        img_md = f"![图表]({img_path})"

        return f"{md}\n\n{img_md}"
