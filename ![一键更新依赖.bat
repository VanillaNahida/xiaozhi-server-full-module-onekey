@echo off
chcp 65001 >nul

set "BATCH_DIR=%~dp0"
cd "%BATCH_DIR%runtime\conda_env\Scripts"

title 一键更新依赖

echo 开始更新一键包依赖...
pip install -r "../../../scripts/requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/
cls
echo 一键包依赖更新成功！

echo 开始更新小智服务器依赖...
pip install -r "../../../src/main/xiaozhi-server/requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/
cls
echo 小智服务器依赖更新成功！

echo 全部依赖更新完毕！
pause