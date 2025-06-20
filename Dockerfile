# 使用官方Python 3.11镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 配置apt源为清华镜像源，加速软件包下载
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 设置时区为北京时间
ENV TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xvfb \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd -r melonuser && useradd -r -g melonuser -G audio,video melonuser \
    && mkdir -p /home/melonuser/Downloads \
    && chown -R melonuser:melonuser /home/melonuser \
    && chown -R melonuser:melonuser /app

# 配置pip使用清华源，加速Python包下载
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 复制requirements文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV HEADLESS_MODE=true
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium

# 更改所有权到melonuser
RUN chown -R melonuser:melonuser /app

# 切换到非root用户
USER melonuser

# 设置启动命令
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & sleep 2 && python melon_service.py"] 