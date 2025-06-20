#!/bin/bash

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ 未找到.env文件，请先创建配置文件"
    exit 1
fi

# 创建目录
mkdir -p data logs

# 清理旧容器
docker stop melonticket-app 2>/dev/null || true
docker rm melonticket-app 2>/dev/null || true

# 构建并运行
echo "🔨 构建镜像..."
docker build -t melonticket .

echo "🚀 启动容器..."
docker run -d \
    --name melonticket-app \
    --env-file .env \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    melonticket

echo "✅ 容器已启动"
echo "📝 查看日志: docker logs -f melonticket-app" 