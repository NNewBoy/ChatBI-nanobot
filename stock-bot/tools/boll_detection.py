import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from nanobot.agent.tools.base import Tool

from charts.bollinger_chart import plot_bollinger

WORKSPACE = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE / "stock_data.db"
IMAGE_DIR = WORKSPACE / "image_show"


class BollDetectionTool(Tool):

    @property
    def name(self) -> str:
        return "boll_detection"

    @property
    def description(self) -> str:
        return (
            "Use Bollinger Bands (20-day period + 2σ) to detect overbought and oversold dates for a stock. "
            "Returns detection report and chart."
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
                "start_date": {
                    "type": "string",
                    "description": "检测起始日期，格式YYYY-MM-DD，默认为今天前1年"
                },
                "end_date": {
                    "type": "string",
                    "description": "检测结束日期，格式YYYY-MM-DD，默认为今天"
                }
            },
            "required": ["ts_code"]
        }

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        ts_code = kwargs.get("ts_code", "").strip()
        today = datetime.now().date()
        start_date = kwargs.get("start_date", (today - timedelta(days=365)).isoformat())
        end_date = kwargs.get("end_date", today.isoformat())

        if not ts_code:
            return "Error: ts_code is required"

        conn = sqlite3.connect(str(DB_PATH))
        boll_start = (pd.to_datetime(start_date) - timedelta(days=60)).strftime('%Y-%m-%d')
        query = """
            SELECT trade_date, open, high, low, close, vol, stock_name
            FROM stock_history
            WHERE ts_code = ? AND trade_date >= ? AND trade_date <= ?
            ORDER BY trade_date ASC
        """
        df = pd.read_sql_query(query, conn, params=(ts_code, boll_start, end_date))
        conn.close()

        if df.empty:
            return f"未找到股票 {ts_code} 在指定时间范围内的历史数据，请检查股票代码和日期范围。"

        stock_name = df['stock_name'].iloc[0] if 'stock_name' in df.columns else ts_code
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date').reset_index(drop=True)
        df['close'] = df['close'].astype(float)

        window = 20
        num_std = 2
        df['ma'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        df['upper'] = df['ma'] + num_std * df['std']
        df['lower'] = df['ma'] - num_std * df['std']

        df_detect = df[df['trade_date'] >= pd.to_datetime(start_date)].copy()
        df_detect = df_detect.dropna(subset=['ma', 'upper', 'lower']).reset_index(drop=True)

        if df_detect.empty:
            return f"股票 {ts_code} 在 {start_date} ~ {end_date} 范围内数据不足以计算布林带（需要至少{window}个交易日）。"

        overbought = df_detect[df_detect['close'] > df_detect['upper']].copy()
        oversold = df_detect[df_detect['close'] < df_detect['lower']].copy()

        md = f"**{stock_name}({ts_code}) 布林带异常检测报告**\n\n"
        md += f"- 检测周期: {start_date} ~ {end_date}\n"
        md += f"- 布林带参数: {window}日均线 ± {num_std}σ\n"
        md += f"- 分析数据量: {len(df_detect)}个交易日\n\n"

        md += f"### 超买日期（收盘价突破上轨，共{len(overbought)}天）\n\n"
        if overbought.empty:
            md += "无超买信号\n\n"
        else:
            ob_df = overbought[['trade_date', 'close', 'upper']].copy()
            ob_df.columns = ['日期', '收盘价', '上轨']
            ob_df['日期'] = ob_df['日期'].dt.strftime('%Y-%m-%d')
            ob_df['收盘价'] = ob_df['收盘价'].round(2)
            ob_df['上轨'] = ob_df['上轨'].round(2)
            md += ob_df.to_markdown(index=False)
            md += '\n\n'

        md += f"### 超卖日期（收盘价跌破下轨，共{len(oversold)}天）\n\n"
        if oversold.empty:
            md += "无超卖信号\n\n"
        else:
            os_df = oversold[['trade_date', 'close', 'lower']].copy()
            os_df.columns = ['日期', '收盘价', '下轨']
            os_df['日期'] = os_df['日期'].dt.strftime('%Y-%m-%d')
            os_df['收盘价'] = os_df['收盘价'].round(2)
            os_df['下轨'] = os_df['下轨'].round(2)
            md += os_df.to_markdown(index=False)
            md += '\n\n'

        latest = df_detect.iloc[-1]
        md += f"### 最新状态（{latest['trade_date'].strftime('%Y-%m-%d')}）\n\n"
        md += f"- 收盘价: {latest['close']:.2f}\n"
        md += f"- 中轨(MA{window}): {latest['ma']:.2f}\n"
        md += f"- 上轨: {latest['upper']:.2f}\n"
        md += f"- 下轨: {latest['lower']:.2f}\n"
        pct_in_band = (latest['close'] - latest['lower']) / (latest['upper'] - latest['lower']) * 100
        md += f"- 布林带位置: {pct_in_band:.1f}%\n\n"
        md += '> 注意: 布林带超买/超卖仅表示价格偏离均值程度，不构成买卖建议。'

        os.makedirs(str(IMAGE_DIR), exist_ok=True)
        filename = f"boll_{int(time.time() * 1000)}.png"
        save_path = IMAGE_DIR / filename
        plot_bollinger(df_detect, overbought, oversold, stock_name, ts_code, window, num_std, str(save_path))
        img_path = f"image_show/{filename}"
        img_md = f"![布林带图表]({img_path})"

        return f"{md}\n\n{img_md}"
