@echo off
chcp 65001 >nul
echo =============================================
echo   🚀 Headroom Proxy（端口 8787）
echo   压缩 AI 请求上下文，减少 Token 消耗
echo =============================================
echo.
echo 启动后把 API 地址改成：
echo   http://localhost:8787/v1
echo.
echo 按 Ctrl+C 停止
echo =============================================
echo.
headroom proxy --port 8787
pause
