# 使用官方 Python 3.10 slim 镜像作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_LOGGER_LEVEL=info

# 安装系统依赖
# reportlab 需要一些系统库来处理字体
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        fonts-liberation \
        fonts-noto-cjk \
        fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建输出目录
RUN mkdir -p /app/output

# 暴露 Streamlit 端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8501/_stcore/health || exit 1

# 运行应用
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
