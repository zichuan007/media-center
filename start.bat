@echo off
chcp 65001 >nul

echo.
echo =========================================
echo   Media Center - 一键启动
echo =========================================
echo.

:: 创建数据目录
echo [1/3] 创建数据目录...
if not exist "G:\docker-data\alist" mkdir "G:\docker-data\alist"
if not exist "G:\docker-data\jellyfin\config" mkdir "G:\docker-data\jellyfin\config"
if not exist "G:\docker-data\jellyfin\cache" mkdir "G:\docker-data\jellyfin\cache"
if not exist "G:\docker-data\moviepilot\config" mkdir "G:\docker-data\moviepilot\config"
if not exist "G:\docker-data\moviepilot\media" mkdir "G:\docker-data\moviepilot\media"
if not exist "G:\docker-data\moviepilot\core" mkdir "G:\docker-data\moviepilot\core"
echo   OK

:: 启动服务
echo [2/3] 启动 Docker 容器...
docker-compose up -d

:: 输出信息
echo [3/3] 获取初始密码...
timeout /t 5 /nobreak >nul

echo.
echo =========================================
echo   所有服务已启动
echo =========================================
echo   AList:      http://localhost:5244
echo   Jellyfin:   http://localhost:8096
echo   MoviePilot: http://localhost:3000
echo =========================================
echo.
echo AList 初始管理员密码:
docker logs media-alist 2>&1 | findstr /i "password"
echo.
echo MoviePilot 账号: admin（首次登录设置密码）
echo.

pause
