import os
import re
import sys
import subprocess
import json
import requests
from typing import Tuple, List
import pop_window_pyside as pwp

# 获取脚本所在目录的上级目录
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 内嵌Git客户端路径
git_path = os.path.join(script_dir, "runtime", "git-2.48.1", "cmd", "git.exe")
# 内嵌Python路径
python_path = os.path.join(script_dir, "runtime", "conda_env", "python.exe")
# GitHub仓库信息
GITHUB_REPO_OWNER = "VanillaNahida"
GITHUB_REPO_NAME = "xiaozhi-server-full-module-onekey"

def check_updates():
    # 读取本地版本信息
    local_version_path = os.path.join(script_dir, "version.json")
    try:
        with open(local_version_path, "r", encoding="utf-8") as f:
            local_version_data = json.load(f)
        local_tag = local_version_data.get("tag_name", "")
        print(f"本地版本: {local_tag}")
    except Exception as e:
        print(f"读取本地版本信息失败: {e}")
        return
    
    # 使用GitHub API检查最新版本
    try:
        # 使用加速地址检查更新
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
        print("检查新版本……")
        
        # 设置超时
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        release_data = response.json()
        remote_tag = release_data.get("tag_name", "")
        print(f"远程最新版本: {remote_tag}")
        
        # 对比版本
        if not remote_tag:
            print("无法获取远程版本信息")
            return
        
        if local_tag != remote_tag:
            print(f'❗发现新版本！{local_tag} → {remote_tag}')
            print(f'\n{"="*50}')
            print(f'更新说明:')
            print(f'{release_data.get("body", "无更新说明")}')
            print(f'\n{"="*50}')
            print(f'建议按照弹窗提示，运行更新脚本获取一键包最新版！')
            
            # 显示弹窗并获取用户选择结果
            update_result = pwp.show_github_release()
            # 如果用户选择了立即更新，退出程序
            if update_result:
                sys.exit(1)
            # 如果用户选择了暂不更新，继续执行而不退出
        else:
            print('\n🎉 恭喜！你的本地一键包已是最新版本！')
            print(f'当前版本: {local_tag}')
    except Exception as e:
        print(f"检查更新时发生错误: {e}")
    
    print("\n检查完毕！正在启动小智AI服务端……")

def start_onekey():
    """
    启动小智AI全模块带智控台一键包。
    """
    base_dir = os.path.join(script_dir)
    wrapped = rf'start "小智AI全模块服务端" "{python_path}" scripts\main.py'
    subprocess.Popen(wrapped, cwd=base_dir, shell=True)

def check_path_for_chinese():
    """
    检查路径是否有中文
    """
    # 获取当前工作目录
    current_path = os.getcwd()
    # 检查路径是否包含中文字符（Unicode范围）
    has_chinese = bool(re.search(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]', current_path))
    # 输出结果
    if has_chinese:
        print(f"警告，当前路径包含中文等特殊字符: {current_path}\n已自动退出，请将一键包移动到非中文目录再启动！")
        return False
    else:
        return True
        

def switch_mysql_version():
    """
    切换MySQL版本。
    """
    base_dir = os.path.join(script_dir)
    wrapped = rf'start "切换MySQL版本" "{python_path}" scripts\switch_mysql_version.py'
    subprocess.Popen(wrapped, cwd=base_dir, shell=True)

def check_mysql_config():
    """
    检查MySQL配置文件是否合法，并确保datadir路径使用双反斜杠转义。
    """
    # 构建绝对路径
    config_path = os.path.join(script_dir, "runtime", "mysql-8.4.7", "my.ini")
    
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 使用正则表达式查找datadir行
    pattern = r'(datadir=)(.*)'
    match = re.search(pattern, content)
    
    if match:
        datadir_key = match.group(1)
        datadir_path = match.group(2)
        
        # 使用正则表达式将所有连续的反斜杠序列替换为恰好两个反斜杠
        desired_path = re.sub(r'\\+', r'\\\\', datadir_path)
        
        # 如果当前路径与期望的双反斜杠路径不同，则进行替换
        if datadir_path != desired_path:
            new_content = content.replace(match.group(0), f'{datadir_key}{desired_path}')
            
            # 将修改后的内容写回配置文件
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            print(f"已修复MySQL配置文件中的datadir路径转义: {datadir_path} -> {desired_path}")
        else:
            print("MySQL配置文件中的datadir路径转义已正确")
    else:
        print("未在MySQL配置文件中找到datadir行")


if __name__ == '__main__':
    # 检查路径合法性
    if not check_path_for_chinese():
        sys.exit()
    if not os.path.exists("./data/.is_first_run"):
        print("检测到首次运行一键包，正在打开说明。")
        if not pwp.first_run():
            print("用户已取消，程序退出。")
            sys.exit()

    os.system("cls")

    # 检查MySQL版本是否需要切换
    mysql_dir = os.path.join("./runtime/mysql-9.4.0")
    if os.path.exists(mysql_dir) or not os.path.exists("./runtime/mysql-8.4.7"):
        print("检测到MySQL 版本不符合要求，可能会导致服务端无法运行，正在切换到8.4.7版本...")
        switch_mysql_version()
        print("MySQL版本切换中，程序即将退出...")
        sys.exit()
    # 检查mysql配置文件
    if os.path.exists("./runtime/mysql-8.4.7/my.ini"):
        check_mysql_config()

    if os.path.exists("skip_update.txt"):
        print("检测到 skip_update.txt，跳过更新检查。")
    else:
        check_updates()
    # 启动一键包
    start_onekey()