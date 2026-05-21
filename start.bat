@echo off
chcp 65001 >nul

:: 创建数据目录
if not exist "G:\docker-data\alist" mkdir "G:\docker-data\alist"
if not exist "G:\docker-data\jellyfin\config" mkdir "G:\docker-data\jellyfin\config"
if not exist "G:\docker-data\jellyfin\cache" mkdir "G:\docker-data\jellyfin\cache"

:: 启动服务
docker-compose up -d

echo.
echo =========================================
echo   Media Center 启动完成
echo =========================================
echo   AList:    http://localhost:5244
echo   Jellyfin: http://localhost:8096
echo =========================================
echo.

:: 等待 AList 启动，输出初始密码
timeout /t 5 /nobreak >nul
echo AList 初始管理员密码:
docker logs media-alist 2>&1 | findstr /i "password"

pause
