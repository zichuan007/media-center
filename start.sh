#!/bin/bash

echo ""
echo "========================================="
echo "  Media Center - 一键启动"
echo "========================================="
echo ""

# 创建数据目录
echo "[1/3] 创建数据目录..."
mkdir -p G:/docker-data/alist
mkdir -p G:/docker-data/jellyfin/config
mkdir -p G:/docker-data/jellyfin/cache
mkdir -p G:/docker-data/moviepilot/config
mkdir -p G:/docker-data/moviepilot/media
mkdir -p G:/docker-data/moviepilot/core
echo "  OK"

# 启动服务
echo "[2/3] 启动 Docker 容器..."
docker-compose up -d

# 输出信息
echo "[3/3] 获取初始密码..."
sleep 5

echo ""
echo "========================================="
echo "  所有服务已启动"
echo "========================================="
echo "  AList:      http://localhost:5244"
echo "  Jellyfin:   http://localhost:8096"
echo "  MoviePilot: http://localhost:3000"
echo "========================================="
echo ""
echo "AList 初始管理员密码:"
docker logs media-alist 2>&1 | grep -i "password"
echo ""
echo "MoviePilot 账号: admin（首次登录设置密码）"
