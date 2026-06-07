# gunicorn.conf.py
import os
# import multiprocessing

# 基础配置
bind = "127.0.0.1:3000"            # 监听地址，只允许本机访问
workers = 2  # 工作进程数 multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"              # 工作模式，对于 Gradio 通常 sync 就够了
timeout = 120                      # 超时时间，可根据业务调整
keepalive = 5                      # Keep-Alive 连接时间

# 日志配置
accesslog = "/var/ChatBI-nanobot/log/gunicorn/access.log"
errorlog = "/var/ChatBI-nanobot/log/gunicorn/error.log"
loglevel = "info"

# 设置环境变量
# 当代码中需要使用 GRADIO_SERVER_PORT 时，可以在这里设置
os.environ["GRADIO_SERVER_PORT"] = "3000" # Gradio 服务端口
os.environ["GRADIO_SERVER_NAME"] = "127.0.0.1" # Gradio 服务地址
os.environ["PROJECT_ENVIRONMENT"] = "prod" # 项目环境，dev启动本地调试
os.environ["STOCK_DB_USER"] = "root" # 数据库用户名
os.environ["STOCK_DB_PASSWORD"] = "" # 数据库密码
os.environ["STOCK_DB_HOST"] = "localhost:3306" # 数据库主机地址
os.environ["STOCK_DB_NAME"] = "ai" # 数据库名称
os.environ["DASHSCOPE_API_KEY"] = "" # DashScope API 密钥
os.environ["DASHSCOPE_MODEL"] = "qwen-plus" # DashScope 模型
