@echo off
echo ========================================
echo   夸克网盘资源搜索工具
echo ========================================
echo.

echo [1/2] 启动 Python 后端 (端口 8000)...
start "夸克搜索-后端" cmd /c "cd /d D:\code\workbuddy\search\backend && venv\Scripts\python.exe main.py"

echo [2/2] 启动 Vue 前端 (端口 5173)...
start "夸克搜索-前端" cmd /c "cd /d D:\code\workbuddy\search\frontend && npx vite --host 0.0.0.0"

echo.
echo 启动完成！浏览器访问: http://localhost:5173
echo.
pause
