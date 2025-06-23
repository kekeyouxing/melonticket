#!/bin/bash

# --- 阿里云镜像仓库信息 ---
# 请确保这些变量与您推送镜像时使用的变量一致
ALIYUN_REGISTRY="registry.cn-shanghai.aliyuncs.com"
ALIYUN_NAMESPACE="echoclass"
ALIYUN_REPOSITORY="melonticket"
IMAGE_TAG="latest"

REMOTE_IMAGE_NAME="$ALIYUN_REGISTRY/$ALIYUN_NAMESPACE/$ALIYUN_REPOSITORY:$IMAGE_TAG"
CONTAINER_NAME="melonticket-app"

# 4. 运行新容器
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