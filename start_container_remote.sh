#!/bin/bash

# Define variables
IMAGE_NAME="registry.cn-shanghai.aliyuncs.com/echoclass/melonticket"
CONTAINER_NAME="melonticket-app"

# Stop and remove the existing container if it exists
if [ $(docker ps -q -f name=^/${CONTAINER_NAME}$) ]; then
    echo "Stopping existing container..."
    docker stop ${CONTAINER_NAME}
fi
if [ $(docker ps -a -q -f name=^/${CONTAINER_NAME}$) ]; then
    echo "Removing existing container..."
    docker rm ${CONTAINER_NAME}
fi

# Run the Docker container from the existing image
echo "Running Docker container from image ${IMAGE_NAME}..."
docker run -d --name ${CONTAINER_NAME} ${IMAGE_NAME}

echo "Container started." 