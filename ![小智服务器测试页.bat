@echo off
chcp 65001 >nul

title 小智AI服务端测试页Server Test Page
set "BATCH_DIR=%~dp0"
set "PYTHON_PATH=%BATCH_DIR%runtime\conda_env\python.exe"
start "" "http://127.0.0.1:8006/index.html"
"%PYTHON_PATH%" ".\src\main\digital-human\start.py"
