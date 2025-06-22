#!/bin/bash

# 本地开发和调试启动脚本
# 该脚本假定镜像已经通过 build.sh 或其他方式构建完成

# 定义镜像和容器名称
IMAGE_NAME="melonticket"
CONTAINER_NAME="melonticket-app-local"

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ 未找到.env文件，请根据.env.example创建您的.env配置文件。"
    exit 1
fi

# 确保data和logs目录存在
mkdir -p data logs

# 1. 停止并删除任何同名的旧容器
echo "🧹 正在清理旧的本地容器: $CONTAINER_NAME..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# 2. 运行新容器进行测试
echo "🚀 正在使用镜像 '$IMAGE_NAME' 启动新容器进行本地测试..."
docker run --rm \
    --name $CONTAINER_NAME \
    --env-file .env \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    $IMAGE_NAME

# docker run 命令解释:
# --rm              : 容器退出后自动删除，非常适合测试
# --name            : 为容器指定一个固定的名字
# --env-file        : 从.env文件加载环境变量 (如用户名、密码)
# -v "$(pwd)/data...": 将本地的data目录挂载到容器的/app/data
# -v "$(pwd)/logs...": 将本地的logs目录挂载到容器的/app/logs
# $IMAGE_NAME       : 指定要使用的镜像

if [ $? -ne 0 ]; then
    echo "❌ 容器启动失败。"
    exit 1
fi

echo "✅ 容器执行完成并已自动清理。"
