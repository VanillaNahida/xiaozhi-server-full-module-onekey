@echo off
chcp 65001

:: 获取批处理文件所在目录的完整路径
set "SCRIPT_DIR=%~dp0"

:: 简化路径定义
set "VENV_PATH=%SCRIPT_DIR%runtime\conda_env"
set "FFMPEG_PATH=%SCRIPT_DIR%runtime\ffmpeg"
set "JDK_PATH=%SCRIPT_DIR%runtime\jdk-21.0.9\bin"
set "MAVEN_PATH=%SCRIPT_DIR%runtime\maven-3.9.11\bin"
set "MYSQL_PATH=%SCRIPT_DIR%runtime\mysql-9.4.0\bin"
set "NODE_PATH=%SCRIPT_DIR%runtime\nodejs-v24.11.0"
set "REDIS_PATH=%SCRIPT_DIR%runtime\Redis"
set "WORKSPACE=%SCRIPT_DIR%src\main\xiaozhi-server"

:: 检查虚拟环境是否存在（必需）
if not exist "%VENV_PATH%" (
    echo 错误：虚拟环境不存在于 %VENV_PATH%
    pause
    exit /b 1
)

:: 简单的路径存在性检查，显示警告但不中断脚本
set "MISSING_PATHS="

:: 检查FFmpeg路径
if not exist "%FFMPEG_PATH%" (
    set "MISSING_PATHS=!MISSING_PATHS! FFmpeg"
)

:: 检查JDK路径
if not exist "%JDK_PATH%" (
    set "MISSING_PATHS=!MISSING_PATHS! JDK"
)

:: 检查Redis路径
if not exist "%REDIS_PATH%" (
    set "MISSING_PATHS=!MISSING_PATHS! Redis"
)

:: 检查工作区路径
if not exist "%WORKSPACE%" (
    set "MISSING_PATHS=!MISSING_PATHS! Workspace"
)

:: 如果有缺失的路径，显示警告
if not "%MISSING_PATHS%" == "" (
    echo 警告：以下组件的路径可能不存在或不可访问：
    echo %MISSING_PATHS%
    echo 这可能会影响相关功能的使用。
    echo 但脚本将继续执行...
    pause
)

:: 使用最简单可靠的方式执行命令
cmd /k "cd /d "%VENV_PATH%" && set PATH=%FFMPEG_PATH%;%JDK_PATH%;%MAVEN_PATH%;%MYSQL_PATH%;%NODE_PATH%;%REDIS_PATH%;%WORKSPACE%;%PATH% && call "%VENV_PATH%\Scripts\activate.bat" && echo 虚拟环境已成功激活！ && echo 环境变量已设置：FFmpeg, JDK, Maven, MySQL, Node.js, Redis, 工作区 && cd ..\..\"
