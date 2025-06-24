#!/bin/bash

# --- 阿里云镜像仓库信息 ---
# 请确保这些变量与您推送镜像时使用的变量一致
ALIYUN_REGISTRY="registry.cn-shanghai.aliyuncs.com"
ALIYUN_NAMESPACE="echoclass"
ALIYUN_REPOSITORY="melonticket"
IMAGE_TAG="latest"

REMOTE_IMAGE_NAME="$ALIYUN_REGISTRY/$ALIYUN_NAMESPACE/$ALIYUN_REPOSITORY:$IMAGE_TAG"
CONTAINER_NAME="melonticket-app"

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ 未找到.env文件，请先创建配置文件"
    exit 1
fi

# 创建本地挂载目录，以防不存在
mkdir -p data logs

# 1. 停止并删除旧容器
echo "🧹 正在停止并删除旧容器: $CONTAINER_NAME..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# 2. 删除旧的本地镜像
echo "🗑️  正在强制删除旧的本地镜像..."
docker rmi -f $REMOTE_IMAGE_NAME 2>/dev/null || true

# 3. 登录阿里云镜像仓库
# 警告：将密码直接写入脚本存在安全风险。
echo "🔐 正在登录到阿里云镜像仓库..."
echo "941005kyx" | docker login --username=844765548@qq.com --password-stdin $ALIYUN_REGISTRY
if [ $? -ne 0 ]; then
    echo "❌ 登录失败，请检查您的用户名和密码。"
    exit 1
fi

# 4. 拉取最新镜像
echo "☁️  正在从阿里云拉取最新镜像: $REMOTE_IMAGE_NAME"
docker pull $REMOTE_IMAGE_NAME
if [ $? -ne 0 ]; then
    echo "❌ 镜像拉取失败。"
    exit 1
fi

# 5. 运行新容器
echo "🚀 正在从新镜像启动容器..."
docker run -d \
    --name $CONTAINER_NAME \
    --env-file .env \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    $REMOTE_IMAGE_NAME

if [ $? -ne 0 ]; then
    echo "❌ 容器启动失败。"
    exit 1
fi

echo "✅ 容器已成功启动！"
echo "   容器名称: $CONTAINER_NAME"
echo "   使用的镜像: $REMOTE_IMAGE_NAME"
echo "📝 使用以下命令查看实时日志: docker logs -f $CONTAINER_NAME" 