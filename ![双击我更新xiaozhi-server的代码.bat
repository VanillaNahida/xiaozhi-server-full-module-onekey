@echo off
chcp 65001 >nul

set "PYTHON_PATH=%BATCH_DIR%runtime\conda_env\python.exe"
title 小智AI服务端更新脚本
"%PYTHON_PATH%" ".\scripts\updater.py"

echo 开始更新小智AI服务端依赖...
pip install -r "./src/main/xiaozhi-server/requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/
@REM cls
echo 小智AI服务端依赖更新成功！
echo 依赖更新完毕！请按回车键退出...
pause