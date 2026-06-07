# -*- coding: utf-8 -*-
"""
环境变量配置

dev  : 使用本地默认环境，无需额外配置
prod : 加载生产环境变量
"""

import os

PROJECT_ENVIRONMENT = os.environ.get("PROJECT_ENVIRONMENT", "dev")

# ---- dev 环境（本地开发） ----
DEV_ENV = {
    "GRADIO_SERVER_PORT": "7860",
    "GRADIO_SERVER_NAME": "127.0.0.1",
    "PROJECT_ENVIRONMENT": "dev",
    # 以下按需填写，留空则跳过
    "STOCK_DB_USER": "",
    "STOCK_DB_PASSWORD": "",
    "STOCK_DB_HOST": "",
    "STOCK_DB_NAME": "",
    "DASHSCOPE_API_KEY": "",
    "DASHSCOPE_MODEL": "qwen-plus",
}

# ---- prod 环境（服务器部署） ----
PROD_ENV = {
    "GRADIO_SERVER_PORT": "3000",
    "GRADIO_SERVER_NAME": "127.0.0.1",
    "PROJECT_ENVIRONMENT": "prod",
    "STOCK_DB_USER": "root",
    "STOCK_DB_PASSWORD": "",
    "STOCK_DB_HOST": "localhost:3306",
    "STOCK_DB_NAME": "ai",
    "DASHSCOPE_API_KEY": "",
    "DASHSCOPE_MODEL": "qwen-plus",
}


def load_env():
    """根据 PROJECT_ENVIRONMENT 加载对应环境变量，不覆盖已存在的环境变量"""
    env = PROD_ENV if PROJECT_ENVIRONMENT == "prod" else DEV_ENV
    for key, value in env.items():
        if value and key not in os.environ:
            os.environ[key] = value
