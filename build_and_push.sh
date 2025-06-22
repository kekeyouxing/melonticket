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

# --- 推送到阿里云镜像仓库 ---
# 请根据您的实际情况修改以下变量
ALIYUN_REGISTRY="registry.cn-shanghai.aliyuncs.com"
# 您提供的参考代码中使用了 'echoclass' 作为命名空间，此处沿用。
# 如果您的命名空间不同，请在此处修改。
ALIYUN_NAMESPACE="echoclass"
ALIYUN_REPOSITORY="melonticket"
IMAGE_TAG="latest"

LOCAL_IMAGE_NAME="melonticket"
REMOTE_IMAGE_NAME="$ALIYUN_REGISTRY/$ALIYUN_NAMESPACE/$ALIYUN_REPOSITORY:$IMAGE_TAG"

# 登录阿里云镜像仓库
# 警告：将密码直接写入脚本存在安全风险。建议使用更安全的方式（如环境变量）进行身份验证。
echo "🔐 正在登录到阿里云镜像仓库..."
# 注意：脚本将使用您提供的密码 '941005kyx'。如果执行失败，请检查凭据是否正确。
echo "941005kyx" | docker login --username=844765548@qq.com --password-stdin $ALIYUN_REGISTRY

if [ $? -ne 0 ]; then
    echo "❌ 登录失败，请检查您的用户名和密码。"
    exit 1
fi

# 给本地镜像打标签
echo "🏷️  为本地镜像打上远程标签: $REMOTE_IMAGE_NAME"
docker tag $LOCAL_IMAGE_NAME:$IMAGE_TAG $REMOTE_IMAGE_NAME

# 推送到阿里云镜像仓库
echo "☁️  正在推送镜像到阿里云..."
docker push $REMOTE_IMAGE_NAME

if [ $? -ne 0 ]; then
    echo "❌ 镜像推送失败。"
    exit 1
fi

echo "✅ 镜像成功推送到: $REMOTE_IMAGE_NAME"
