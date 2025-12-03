@echo off
chcp 65001
cls
set "BATCH_DIR=%~dp0"
set "PYTHON_PATH=%BATCH_DIR%runtime\conda_env\python.exe"
title 小智AI全模块服务端一键包启动向导
"%PYTHON_PATH%" "%BATCH_DIR%scripts\check_update.py"
echo 将在10秒后自动关闭窗口...
timeout /t 10
