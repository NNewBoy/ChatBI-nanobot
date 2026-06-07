
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Query Agent -- nanobot 版

使用 nanobot 框架的股票查询助手，支持 SQL 查询、ARIMA 预测、布林带检测。

运行:
  python agent.py "查询贵州茅台最新收盘价"
  python agent.py
"""

import asyncio
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).resolve().parent
NANOBOT_ROOT = WORKSPACE.parent / "nanobot-main"
if str(NANOBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(NANOBOT_ROOT))

sys.path.insert(0, str(WORKSPACE))

from nanobot.agent.hook import AgentHook, AgentHookContext
from nanobot.agent.loop import AgentLoop
from nanobot.bus.queue import MessageBus
from nanobot.config.loader import load_config
from nanobot.nanobot import Nanobot, _make_provider

from tools.query_db import StockQueryDBTool
from tools.arima_stock import ArimaStockTool
from tools.boll_detection import BollDetectionTool


class PrintHook(AgentHook):
    async def before_execute_tools(self, ctx: AgentHookContext) -> None:
        for tc in ctx.tool_calls:
            print(f"  >> {tc.name}: {str(tc.arguments)[:120]}")


def build_bot() -> Nanobot:
    dashscope_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not dashscope_key:
        print("[Error] DASHSCOPE_API_KEY not set")
        sys.exit(1)

    # 先设置环境变量，让 config 可能使用（虽然 load_config 在下面，我们手动设置）
    os.environ["DASHSCOPE_API_KEY"] = dashscope_key

    # 加载配置
    config = load_config(WORKSPACE / "config.json")
    config.agents.defaults.workspace = str(WORKSPACE)
    # 手动设置 API key！这是关键！
    config.providers.dashscope.api_key = dashscope_key

    # 创建 provider，完全正确的方法
    provider = _make_provider(config)

    defaults = config.agents.defaults
    bus = MessageBus()

    # 正确创建 AgentLoop，包括所有需要的参数！
    loop = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=WORKSPACE,
        model=os.environ.get("DASHSCOPE_MODEL", defaults.model),
        max_iterations=defaults.max_tool_iterations,
        context_window_tokens=defaults.context_window_tokens,
        context_block_limit=defaults.context_block_limit,
        max_tool_result_chars=defaults.max_tool_result_chars,
        provider_retry_mode=defaults.provider_retry_mode,
        web_config=config.tools.web,
        exec_config=config.tools.exec,
        restrict_to_workspace=config.tools.restrict_to_workspace,
        mcp_servers=config.tools.mcp_servers,
        timezone=defaults.timezone,
    )

    # 注册我们的自定义工具
    loop.tools.register(StockQueryDBTool())
    loop.tools.register(ArimaStockTool())
    loop.tools.register(BollDetectionTool())

    return Nanobot(loop)


async def main():
    from init_db import init_sqlite_from_mysql
    init_sqlite_from_mysql()

    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "查询贵州茅台最新收盘价"

    print(f"\nStock Query Agent (nanobot)")
    print(f"Question: {question}\n")

    bot = build_bot()
    result = await bot.run(question, session_key="stock:run", hooks=[PrintHook()])

    print(f"\n{'=' * 60}")
    print(f"Answer: {result.content}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
