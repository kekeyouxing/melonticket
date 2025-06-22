#!/bin/bash

# 本地镜像构建脚本
# 该脚本仅用于在本地构建镜像，不涉及推送等操作。

# 定义镜像名称和标签
IMAGE_NAME="melonticket"
IMAGE_TAG="latest"

echo "🔨 开始构建本地镜像: $IMAGE_NAME:$IMAGE_TAG..."

# 执行标准的Docker构建命令
docker build -t "$IMAGE_NAME:$IMAGE_TAG" .

# 检查构建是否成功
if [ $? -ne 0 ]; then
    echo "❌ 镜像构建失败。"
    exit 1
fi

echo "✅ 本地镜像 $IMAGE_NAME:$IMAGE_TAG 构建成功！" 