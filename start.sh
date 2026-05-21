#!/bin/bash

# 创建数据目录
mkdir -p G:/docker-data/alist
mkdir -p G:/docker-data/jellyfin/config
mkdir -p G:/docker-data/jellyfin/cache

# 启动服务
docker-compose up -d

echo ""
echo "========================================="
echo "  Media Center 启动完成"
echo "========================================="
echo "  AList:    http://localhost:5244"
echo "  Jellyfin: http://localhost:8096"
echo "========================================="
echo ""

# 等待 AList 启动，输出初始密码
sleep 3
echo "AList 初始管理员密码:"
docker logs media-alist 2>&1 | grep -i "password"
