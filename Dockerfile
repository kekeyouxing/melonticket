# 使用官方Python 3.11 slim镜像作为基础
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，确保韩文正确显示和处理
ENV LANG=ko_KR.UTF-8 \
    LANGUAGE=ko_KR:ko \
    LC_ALL=ko_KR.UTF-8 \
    TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# 安装系统依赖
# - ca-certificates: 用于HTTPS连接
# - wget, unzip: 用于下载和解压chromedriver
# - locales, fonts-noto-cjk, fonts-nanum: 韩文语言和字体支持
# - gnupg: 用于处理Google Chrome的签名
# - chromium-driver: ChromeDriver驱动程序
# - 其他: Selenium和Chrome headless模式所需的共享库
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    unzip \
    locales \
    gnupg \
    chromium-driver \
    fonts-noto-cjk \
    fonts-nanum \
    libglib2.0-0 \
    libnss3 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxss1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    # 生成韩文locale并设置时区
    && echo "ko_KR.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen ko_KR.UTF-8 \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 安装Google Chrome (直接下载.deb包，避免访问被墙的Google服务器)
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并配置镜像源进行安装
COPY requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目代码到容器中
COPY . .

# 运行应用程序
CMD ["python", "melon_service.py"]
