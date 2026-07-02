# 使用官方 Python 轻量级镜像
FROM python:3.10-slim
# 设置工作目录
WORKDIR /app
# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 复制项目所有代码到工作目录 COPY [源路径] [目标路径]
COPY .. .
# 暴露端口（假设你的 Python 框架运行在 8000 端口）
EXPOSE 8000
# 启动命令  FastAPI 是 uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]