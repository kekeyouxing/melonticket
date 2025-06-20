# 使用官方Python 3.11 slim镜像（兼容性更好）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置时区、环境变量和字符编码
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:99 \
    HEADLESS_MODE=true \
    CHROME_BIN=/usr/bin/chromium \
    CHROME_PATH=/usr/bin/chromium \
    LANG=ko_KR.UTF-8 \
    LANGUAGE=ko_KR:ko \
    LC_ALL=ko_KR.UTF-8 \
    PYTHONIOENCODING=utf-8

# 一次性安装所有系统依赖并清理，减少镜像层数
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 时区支持
    tzdata \
    # 韩文语言包和字符编码支持
    locales \
    # 必需的浏览器依赖
    chromium \
    chromium-driver \
    # 虚拟显示
    xvfb \
    # 完整的韩文字体支持
    fonts-liberation \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-nanum \
    fonts-baekmuk \
    fonts-unfonts-core \
    # 额外的字体支持
    fontconfig \
    # 必需的系统依赖
    ca-certificates \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    # 生成韩文locale
    && echo "ko_KR.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen ko_KR.UTF-8 \
    # 更新字体缓存
    && fc-cache -fv \
    # 创建用户
    && groupadd -r melonuser && useradd -r -g melonuser melonuser \
    && mkdir -p /home/melonuser/Downloads \
    && chown -R melonuser:melonuser /home/melonuser \
    # 清理apt缓存和临时文件
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc/* /usr/share/man/*

# 配置pip使用清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 复制requirements文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt \
    # 清理pip缓存
    && pip cache purge \
    # 删除不必要的文件
    && find /usr/local -name "*.pyc" -delete \
    && find /usr/local -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 复制应用代码（只复制必要文件）
COPY *.py ./
COPY *.md ./

# 更改所有权到melonuser
RUN chown -R melonuser:melonuser /app

# 切换到非root用户
USER melonuser

# 设置启动命令
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & sleep 2 && python melon_service.py"]
