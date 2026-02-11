@echo off
chcp 65001
cls
set "BATCH_DIR=%~dp0"
set "PYTHON_PATH=%BATCH_DIR%runtime\conda_env\python.exe"
title MySQL改密工具
"%PYTHON_PATH%" "%BATCH_DIR%scripts\mysql_config_tool.py"
echo 将在5秒后自动关闭窗口...
timeout /t 5
