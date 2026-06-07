
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Bot Web UI -- Gradio 版

参考 qwen-agent WebUI 的设计，用原生 Gradio 组件搭建。
支持流式输出、图片显示、推荐对话。

运行:
  python web_ui.py
"""

import asyncio
import base64
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any
from queue import Queue
from threading import Lock

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

import gradio as gr

from agent import build_bot
from init_db import init_sqlite_from_mysql
from fastapi import FastAPI

BOT_NAME = "股票查询助手"
BOT_DESCRIPTION = "股票行情查询、ARIMA预测、布林带异常检测"
PROMPT_SUGGESTIONS = [
    "查询2025年全年贵州茅台的收盘价走势",
    "统计2025年4月广发证券的日均成交量",
    "对比2025年中芯国际和贵州茅台的涨跌幅",
    "预测贵州茅台未来5天的收盘价",
    "检测贵州茅台最近的超买超卖信号",
]

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

# 全局 bot 单例，避免每次重新创建
_bot_instance = None
_bot_lock = Lock()


def get_bot():
    global _bot_instance
    with _bot_lock:
        if _bot_instance is None:
            _bot_instance = build_bot()
        return _bot_instance


def image_path_to_base64(path_str: str) -> str:
    p = Path(path_str)
    if not p.is_absolute():
        p = WORKSPACE / path_str
    if not p.exists():
        return path_str
    ext = p.suffix.lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    with open(p, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{ext};base64,{data}"


def convert_images_to_base64(text: str) -> str:
    import re
    pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
    def replacer(match):
        alt = match.group(1)
        path_str = match.group(2)
        if any(path_str.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
            b64 = image_path_to_base64(path_str)
            return f"![{alt}]({b64})"
        return match.group(0)
    return re.sub(pattern, replacer, text)


def run_agent_in_thread(message: str, q: Queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _on_stream(delta: str):
        q.put(("delta", delta))

    async def _run_task():
        try:
            bot = get_bot()
            response = await bot._loop.process_direct(
                message,
                session_key="stock:webui",
                on_stream=_on_stream,
            )
            final_text = ""
            if response and response.content:
                final_text = response.content
            final_text = convert_images_to_base64(final_text)
            q.put(("done", final_text))
        except Exception as e:
            q.put(("error", f"处理请求时出错: {str(e)}"))
            traceback.print_exc()

    try:
        loop.run_until_complete(_run_task())
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        try:
            loop.close()
        except Exception:
            pass


def chat_respond(message: str, history: list):
    if not message or not message.strip():
        return history

    history = history + [{"role": "user", "content": message}]

    q = Queue()

    import threading
    thread = threading.Thread(
        target=run_agent_in_thread,
        args=(message, q),
        daemon=True,
    )
    thread.start()

    accumulated = ""
    timeout = 120
    start = time.time()

    while True:
        try:
            remaining = timeout - (time.time() - start)
            if remaining <= 0:
                break

            try:
                item = q.get(timeout=min(remaining, 0.5))
            except:
                if not thread.is_alive():
                    break
                if accumulated:
                    history[-1] = {"role": "assistant", "content": accumulated}
                    yield history
                continue

            kind, data = item

            if kind == "delta":
                accumulated += data
                converted = convert_images_to_base64(accumulated)
                history[-1] = {"role": "assistant", "content": converted}
                yield history
            elif kind == "done":
                if data and data != accumulated:
                    history[-1] = {"role": "assistant", "content": data}
                    yield history
                elif not accumulated:
                    history[-1] = {"role": "assistant", "content": data or "（无回复）"}
                    yield history
                break
            elif kind == "error":
                history[-1] = {"role": "assistant", "content": f"❌ {data}"}
                yield history
                break

        except Exception as e:
            history[-1] = {"role": "assistant", "content": f"❌ 渲染错误: {str(e)}"}
            yield history
            break

    thread.join(timeout=5)

    if not history[-1].get("content"):
        history[-1] = {"role": "assistant", "content": accumulated or "（超时无回复）"}
        yield history


def build_ui():
    with gr.Blocks(
        title="股票查询助手",
        theme=gr.themes.Default(
            primary_hue=gr.themes.utils.colors.blue,
            radius_size=gr.themes.utils.sizes.radius_none,
        ),
        css="""
        .contain { max-width: 1200px; margin: auto; }
        .suggestions button {
            font-size: 0.9em;
            padding: 8px 16px;
            border-radius: 8px;
        }
        """,
    ) as demo:
        gr.Markdown(
            f"# 📈 {BOT_NAME}\n"
            f"{BOT_DESCRIPTION}\n\n"
            "支持: SQL查询、ARIMA股价预测、布林带超买超卖检测"
        )

        chatbot = gr.Chatbot(
            type="messages",
            height=600,
            show_copy_button=True,
            latex_delimiters=[
                {"left": "\\(", "right": "\\)", "display": True},
                {"left": "\\[", "right": "\\]", "display": True},
            ],
            avatar_images=(None, "🤖"),
        )

        with gr.Row():
            user_input = gr.Textbox(
                placeholder="请输入您的问题，如：查询贵州茅台最新收盘价",
                show_label=False,
                scale=8,
                autofocus=True,
                lines=1,
            )
            submit_btn = gr.Button("发送", variant="primary", scale=1)
            clear_btn = gr.Button("清除", scale=1)

        gr.Examples(
            label="推荐对话",
            examples=PROMPT_SUGGESTIONS,
            inputs=[user_input],
        )

        gr.Markdown(
            "---\n"
            "💡 **提示**: 可使用自然语言提问，系统会自动编写SQL查询数据库。\n"
            "支持预测和布林带分析，如「预测茅台未来5天收盘价」「检测超买超卖」。\n\n"
            "> ⚠️ 预测和分析结果仅供参考，不构成投资建议。"
        )

        user_input.submit(
            fn=chat_respond,
            inputs=[user_input, chatbot],
            outputs=[chatbot],
        ).then(
            fn=lambda: "",
            outputs=[user_input],
        )

        submit_btn.click(
            fn=chat_respond,
            inputs=[user_input, chatbot],
            outputs=[chatbot],
        ).then(
            fn=lambda: "",
            outputs=[user_input],
        )

        clear_btn.click(
            fn=lambda: [],
            outputs=[chatbot],
        )

    return demo


def main():
    init_sqlite_from_mysql()

    demo = build_ui()
    print(f"\n📈 {BOT_NAME} Web UI 启动中...")
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("GRADIO_SERVER_PORT", 7860)),
        share=False,
    )
    
if __name__ == "__main__":
    main()
