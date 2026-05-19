import os
import sqlite3
import time
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from nanobot.agent.tools.base import Tool
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from charts.arima_chart import plot_arima_forecast

WORKSPACE = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE / "stock_data.db"
IMAGE_DIR = WORKSPACE / "image_show"


class ArimaStockTool(Tool):

    @property
    def name(self) -> str:
        return "arima_stock"

    @property
    def description(self) -> str:
        return (
            "Use ARIMA model to forecast the closing price of a specified stock for the next N trading days. "
            "Returns forecast table and chart."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ts_code": {
                    "type": "string",
                    "description": "股票代码，如600519.SH"
                },
                "n": {
                    "type": "integer",
                    "description": "预测未来天数，默认5"
                }
            },
            "required": ["ts_code"]
        }

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        ts_code = kwargs.get("ts_code", "").strip()
        n = int(kwargs.get("n", 5))

        if not ts_code:
            return "Error: ts_code is required"

        conn = sqlite3.connect(str(DB_PATH))
        today = datetime.now().date()
        one_year_ago = today - timedelta(days=365)
        query = """
            SELECT trade_date, close, stock_name
            FROM stock_history
            WHERE ts_code = ? AND trade_date >= ?
            ORDER BY trade_date ASC
        """
        df = pd.read_sql_query(query, conn, params=(ts_code, one_year_ago.isoformat()))
        conn.close()

        if df.empty:
            return f"未找到股票 {ts_code} 的历史数据，请检查股票代码是否正确。"

        stock_name = df['stock_name'].iloc[0] if 'stock_name' in df.columns else ts_code
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date').reset_index(drop=True)

        close_prices = df['close'].values.astype(float)

        if len(close_prices) < 30:
            return f"股票 {ts_code} 的历史数据不足（仅{len(close_prices)}条），无法进行ARIMA建模，至少需要30条数据。"

        try:
            model = ARIMA(close_prices, order=(5, 1, 5))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConvergenceWarning)
                model_fit = model.fit()
            forecast_result = model_fit.forecast(steps=n)
            forecast_values = np.array(forecast_result).flatten()
        except Exception as e:
            return f"ARIMA建模失败: {str(e)}"

        last_date = df['trade_date'].iloc[-1]
        forecast_dates = []
        current = last_date
        for _ in range(n):
            current = current + timedelta(days=1)
            while current.weekday() >= 5:
                current = current + timedelta(days=1)
            forecast_dates.append(current)

        forecast_df = pd.DataFrame({
            '日期': forecast_dates,
            '预测收盘价': [round(v, 2) for v in forecast_values]
        })

        md = f"**{stock_name}({ts_code}) ARIMA(5,1,5) 预测结果**\n\n"
        md += f"- 历史数据范围: {df['trade_date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['trade_date'].iloc[-1].strftime('%Y-%m-%d')} ({len(df)}个交易日)\n"
        md += f"- 预测未来 {n} 个交易日收盘价:\n\n"
        md += forecast_df.to_markdown(index=False)
        md += '\n\n> 注意: ARIMA模型基于历史价格趋势进行统计预测，仅供参考，不构成投资建议。'

        os.makedirs(str(IMAGE_DIR), exist_ok=True)
        filename = f"arima_{int(time.time() * 1000)}.png"
        save_path = IMAGE_DIR / filename
        plot_arima_forecast(df, forecast_dates, forecast_values, stock_name, ts_code, str(save_path))
        img_path = f"image_show/{filename}"
        img_md = f"![预测图表]({img_path})"

        return f"{md}\n\n{img_md}"
