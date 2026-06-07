## 快速上手/部署教程

### 新建代码目录（如 '/var/ChatBI-nanobot），Git克隆项目

```bash
cd /var/ChatBI-nanobot
git clone <你的项目Git仓库地址>
```
### 创建并激活虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 安装项目依赖

```bash
pip install -r requirements.txt
```

### 配置项目环境变量
修改 gunicorn.conf.py 中的环境变量为你的数据库配置和 DashScope API 密钥。

## 让项目持久化运行

### 创建 systemd 服务文件

```bash
cp /var/ChatBI-nanobot/ChatBI-nanobot.service /etc/systemd/system/ChatBI-nanobot.service
```

### 编辑服务配置
将文件中ChatBI-nanobot替换为你的项目名称

### 启动并管理服务

```bash
# 1. 重新加载 systemd 配置，让它识别到新创建的服务文件
sudo systemctl daemon-reload
# 2. 设置服务开机自启
sudo systemctl enable myapp
# 3. 立即启动服务
sudo systemctl start myapp
# 4. 查看服务状态（用于调试，确认是否正常运行）
sudo systemctl status myapp
```

