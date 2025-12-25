@echo off
chcp 65001
cls
set "BATCH_DIR=%~dp0"
set "PYTHON_PATH=%BATCH_DIR%runtime\conda_env\python.exe"
title 重新配置服务器密钥向导
"%PYTHON_PATH%" "%BATCH_DIR%scripts\init_config_pyside6.py"
echo 将在10秒后自动关闭窗口...
timeout /t 10
