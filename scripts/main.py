import os
import sys
import time
import json
import requests
import subprocess
import ctypes

try:
    import webbrowser
except ImportError:
    print("正在安装webbrowser模块...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "webbrowser"])
    import webbrowser
    print("webbrowser模块安装成功！")
except subprocess.CalledProcessError:
    print("webbrowser模块安装失败！")

except Exception as e:
    print(f"安装出错！{e}")

# 获取当前脚本所在目录的父目录作为基础路径
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
runtime_dir = os.path.join(base_dir, 'runtime')

# 定义终端输出
def print_gradient_text(text, start_color, end_color):
    """
    在终端打印彩色渐变文字
    
    参数:
    text: 要打印的文字
    start_color: 起始颜色 (R, G, B) 元组, 范围0-255
    end_color: 结束颜色 (R, G, B) 元组, 范围0-255
    """
    r1, g1, b1 = start_color
    r2, g2, b2 = end_color
    
    gradient_text = []
    for i, char in enumerate(text):
        # 计算当前字符的颜色插值
        ratio = i / (len(text) - 1) if len(text) > 1 else 0
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        # 使用ANSI转义序列设置颜色
        gradient_text.append(f"\033[38;2;{r};{g};{b}m{char}")
    
    # 组合所有字符并重置颜色
    print(''.join(gradient_text) + '\033[0m')

def get_hitokoto():
    """获取一言"""
    print_gradient_text("正在加载中，请耐心等待...", (200, 250, 50), (0, 128, 0))
    try:
        response = requests.get('https://v1.hitokoto.cn/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            hitokoto = data.get('hitokoto', '')
            from_ = data.get('from', '')
            from_who = data.get('from_who', '未知')
            if not from_who:
                from_who = '未知'
            return True, f"""===================================【一言】========================================
    {hitokoto}  —— ⌈{from_}⌋ {from_who}
===================================================================================
"""
    except Exception as e:
        return False, ""

def get_welcome_text():
    """生成欢迎页面文本"""
    # 读取版本号文件动态显示版本号
    with open(os.path.join(base_dir, 'version.json'), 'r', encoding='utf-8') as f:
        version_data = json.load(f)
        version = version_data.get('tag_name', '')
    # 获取一言
    hitokoto_bool, hitokoto_text = get_hitokoto()
    text = f"""
==========================【欢迎使用小智AI全模块一键包】===========================
    小智AI全模块一键包启动器 {version} By: 哔哩哔哩: @香草味的纳西妲喵
    个人主页: https://space.bilibili.com/1347891621
    GitHub:   https://github.com/VanillaNahida
    我的博客: https://www.xcnahida.cn/
    小智服务端项目开源地址: https://github.com/xinnan-tech/xiaozhi-esp32-server
===================================================================================
    使用过程中有任何疑问欢迎来群里讨论，如有报错请截图反馈。
    QQ群: https://www.bilibili.com/opus/1045130607332425735
    感谢你的使用！"""

    # 输出提示
    print_gradient_text(text, (160, 240, 160), (40, 200, 40))
    if hitokoto_bool:
        # 输出一言
        print_gradient_text(hitokoto_text, (67, 233, 123), (56, 249, 215))
    else:
        line = "=" * 83
        print_gradient_text(line, (160, 240, 160), (40, 200, 40))

# 设置环境变量
def set_environment_variables():
    """设置环境变量.bat"""
    # Java环境变量
    jdk_path = os.path.join(runtime_dir, 'jdk-21.0.9', 'bin')
    java_home = os.path.join(runtime_dir, 'jdk-21.0.9')
    # Maven环境变量
    maven_path = os.path.join(runtime_dir, 'maven-3.9.11', 'bin')
    m2_home = os.path.join(runtime_dir, 'maven-3.9.11')
    # MySQL环境变量
    mysql_path = os.path.join(runtime_dir, 'mysql-8.4.7', 'bin')
    # Redis环境变量
    redis_path = os.path.join(runtime_dir, 'Redis')
    # Node.js环境变量
    node_path = os.path.join(runtime_dir, 'nodejs-v24.11.0')
    # Python环境变量
    python_path = os.path.join(runtime_dir, 'conda_env')
    # FFmpeg环境变量
    ffmpeg_path = os.path.join(runtime_dir, 'ffmpeg')
    # 基础runtime路径
    runtime_path = runtime_dir
    # 获取当前PATH
    current_path = os.environ.get('PATH', '')
    # 构建新的PATH
    new_path = f"{runtime_path};{jdk_path};{maven_path};{mysql_path};{redis_path};{node_path};{python_path};{ffmpeg_path};{current_path}"
    # 设置环境变量
    os.environ['RUNTIME_PATH'] = runtime_path
    os.environ['JDK_PATH'] = jdk_path
    os.environ['JAVA_HOME'] = java_home
    os.environ['MAVEN_PATH'] = maven_path
    os.environ['M2_HOME'] = m2_home
    os.environ['MYSQL_PATH'] = mysql_path
    os.environ['REDIS_PATH'] = redis_path
    os.environ['NODE_PATH'] = node_path
    os.environ['PYTHON_PATH'] = python_path
    os.environ['PATH'] = new_path

    print_gradient_text("🎉运行环境初始化成功！\n", (200, 250, 50), (0, 128, 0))

def start_process(cmd, cwd=None, window_title=None, wait=False):
    """在单独的窗口启动进程，如果wait=True则等待进程完成并返回布尔值表示成功与否"""
    try:
        if wait:
            # 使用cmd /c让命令执行完后自动关闭窗口，并等待完成
            process = subprocess.run(
                f'start "{window_title}" cmd /c "{cmd}"', 
                cwd=cwd, 
                shell=True,
                check=False,
                capture_output=True,
                text=True
            )
            return process.returncode == 0
        else:
            # 不等待进程完成
            if window_title:
                subprocess.Popen(f'start "{window_title}" cmd /k "{cmd}"', cwd=cwd, shell=True)
            else:
                subprocess.Popen(f'start cmd /k "{cmd}"', cwd=cwd, shell=True)
            return True
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return False

def check_config():
    # 定义配置成功文件路径 - 移到函数开头确保所有代码路径都能访问
    config_success_file = os.path.join(base_dir, 'data', '.config_init_success')
    
    # 检测配置是否已初始化
    if not os.path.exists(config_success_file):
        print("检测到配置文件未初始化，需要进行初始化...")
        print("正在打开配置初始化工具...")
        # 启动配置初始化工具并等待其完成
        print("请完成配置初始化...")
        success = start_process(r'python scripts\init_config_pyside6.py', cwd=base_dir, window_title="小智服务端配置初始化", wait=True)
        
        # 检查配置是否已初始化
        if not os.path.exists(config_success_file):
            print("警告：配置文件似乎仍未初始化完成。")
            if not success:
                print("配置初始化过程中可能出现了错误。")
            response = input("是否仍要继续启动服务？(y/n)(默认y): ")
            if response.lower() == 'n':
                print("已取消服务启动操作！")
                return False
    
    # 返回配置是否已初始化
    return os.path.exists(config_success_file)

def check_mysql():
    """检查MySQL是否初始化过"""
    if os.path.exists(os.path.join(base_dir, "data", '.mysql_init_sucess')):
        return True
    else:
        return False

def start_mysql_service():
    """单独启动MySQL服务"""
    if not check_mysql():
        print("MySQL未初始化，未初始化数据库会导致无法运行小智服务端。")
        response = input("需要为你自动初始化MySQL数据库吗？留空回车则执行MySQL初始化(y/n): ")
        if response.lower() == 'y':
            is_init = True
        elif response == "":
            is_init = True
        else:
            is_init = False
        # 检测是否需要初始化
        if is_init:
            # 执行初始化MySQL数据库
            print("正在初始化MySQL数据库，请不要关闭本窗口...")
            start_process(r'python scripts\init_mysql.py', cwd=base_dir, window_title="MySQL初始化", wait=True)
            print("MySQL初始化完成，现在启动MySQL服务...")
        else:
            print("已取消MySQL数据库初始化操作！")
            return
            
    print("正在启动MySQL服务...")
    mysql_cmd = 'mysqld --console'
    start_process(mysql_cmd, window_title="MySQL服务器")
    print("MySQL服务已启动！")


def start_redis_service():
    """单独启动Redis服务"""
    print("正在启动Redis服务...")
    redis_cwd = os.path.join(base_dir, 'data')
    print(f"Redis运行目录: {redis_cwd}")
    redis_cmd = 'redis-server.exe'
    start_process(redis_cmd, cwd=redis_cwd, window_title="Redis服务器")
    print("Redis服务已启动！")


def start_frontend_service():
    """单独启动前端服务"""
    print("启动前端服务...")
    frontend_cwd = os.path.join(base_dir, 'src', 'main', 'manager-web')
    # 先安装依赖（等待完成）
    print("开始安装前端依赖...")
    if start_process('npm install', cwd=frontend_cwd, window_title="前端依赖安装", wait=True):
        print("前端依赖安装成功！")
        # 启动服务（不等待）
        print("启动前端服务...")
        start_process('title 前端服务器 & npm run serve', cwd=frontend_cwd, window_title="前端服务器")
        print("请在浏览器中访问 http://localhost:8001 查看。")
        print("即将在5秒后自动打开浏览器...")
        time.sleep(5)
        webbrowser.open("http://localhost:8001")
    else:
        print("前端依赖安装失败！")

def kill_mysql(use_admin=False):
    """单独结束MySQL服务"""
    if use_admin:
        try:
            print("正在以管理员权限结束MySQL进程...")
            print("期间可能会弹出两次UAC弹窗，请点击“是”。")
            # 结束MySQL相关进程
            # 以管理员权限执行taskkill命令结束mysqld.exe进程
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskkill.exe", "/F /IM mysqld.exe /T", None, 0)
            # 以管理员权限执行taskkill命令结束mysql.exe进程
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskkill.exe", "/F /IM mysql.exe /T", None, 0)
        except Exception as e:
            print(f"以管理员身份结束进程时出错: {e}")
    else:
        try:
            print("正在结束MySQL...")
            subprocess.run("taskkill /F /IM mysqld.exe /T", shell=True)
            subprocess.run("taskkill /F /IM mysql.exe /T", shell=True)
        except Exception as e:
            print(f"结束进程时出错: {e}")

    print("已成功执行操作！将在3秒后继续...")
    time.sleep(3)

def kill_redis(use_admin=False):
    """单独结束MySQL服务"""
    if use_admin:
        try:
            print("正在以管理员权限结束MySQL和Redis相关进程...")
            print("期间可能会弹出四次UAC弹窗，请点击“是”。")
            # 以管理员权限执行taskkill命令结束redis-server.exe进程
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskkill.exe", "/F /IM redis-server.exe /T", None, 0)
            # 以管理员权限执行taskkill命令结束redis-cli.exe进程
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskkill.exe", "/F /IM redis-cli.exe /T", None, 0)
        except Exception as e:
            print(f"以管理员身份结束进程时出错: {e}")
    else:
        try:
            print("正在结束Redis...")
            print("结束Redis相关进程...")
            subprocess.run("taskkill /F /IM redis-server.exe /T", shell=True)
            subprocess.run("taskkill /F /IM redis-cli.exe /T", shell=True)
        except Exception as e:
            print(f"结束进程时出错: {e}")

    print("已成功执行操作！将在3秒后继续...")
    time.sleep(3)

def end_database_processes(use_admin=False):
    """使用管理员权限结束MySQL和Redis相关进程"""
    if use_admin:
        try:
            print("正在以管理员权限结束MySQL和Redis相关进程...")
            print("期间可能会弹出四次UAC弹窗，请点击“是”。")
            # 结束MySQL相关进程
            print("结束MySQL相关进程...")
            # 以管理员权限执行taskkill命令结束mysqld.exe进程
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskkill.exe", "/F /IM mysqld.exe /T", None, 0)
            # 以管理员权限执行taskkill命令结束mysql.exe进程
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskkill.exe", "/F /IM mysql.exe /T", None, 0)
            # 结束Redis相关进程
            print("结束Redis相关进程...")
            # 以管理员权限执行taskkill命令结束redis-server.exe进程
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskkill.exe", "/F /IM redis-server.exe /T", None, 0)
            # 以管理员权限执行taskkill命令结束redis-cli.exe进程
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskkill.exe", "/F /IM redis-cli.exe /T", None, 0)
        except Exception as e:
            print(f"以管理员身份结束进程时出错: {e}")
    else:
        try:
            print("正在结束MySQL和Redis相关进程...")
            print("结束MySQL相关进程...")
            subprocess.run("taskkill /F /IM mysqld.exe /T", shell=True)
            subprocess.run("taskkill /F /IM mysql.exe /T", shell=True)
            print("结束Redis相关进程...")
            subprocess.run("taskkill /F /IM redis-server.exe /T", shell=True)
            subprocess.run("taskkill /F /IM redis-cli.exe /T", shell=True)
        except Exception as e:
            print(f"结束进程时出错: {e}")

    print("已成功执行操作！将在3秒后继续...")
    time.sleep(3)

def start_backend_service():
    """单独启动后端API服务器"""
    print("启动后端API服务器...")
    backend_cwd = os.path.join(base_dir, 'src', 'main', 'manager-api')
    backend_cmd = 'chcp 65001 & mvn spring-boot:run'
    start_process(backend_cmd, cwd=backend_cwd, window_title="后端API服务器")
    print("后端API服务器已启动！请等待一段时间让服务完全启动。")


def start_python_service():
    """单独启动Python服务端（小智AI服务器）"""
    print("启动小智AI服务器...")
    python_cwd = os.path.join(base_dir, 'src', 'main', 'xiaozhi-server')
    python_cmd = 'python app.py'
    
    # 检查配置
    if check_config():
        # 启动服务（不等待）
        start_process(python_cmd, cwd=python_cwd, window_title="小智AI服务器")
        print("小智AI服务器已启动！")
    else:
        print("无法启动服务，配置未初始化或用户取消了操作。")

def start_init_config():
    """启动小智服务端配置文件初始化工具"""
    print("正在重新配置服务器密钥...")
    python_cwd = os.path.join(base_dir, 'scripts')
    python_cmd = 'python init_config_pyside6.py'
    # 启动服务（不等待）
    start_process(python_cmd, cwd=python_cwd, window_title="小智AI服务器")

def start_all_services():
    """一键启动所有服务，参考一键启动带智控台的服务端.bat"""
    if not check_mysql():
        print("MySQL未初始化，未初始化数据库会导致无法运行小智服务端。")
        response = input("需要为你自动初始化MySQL数据库吗？留空回车则执行MySQL初始化(y/n): ")
        if response.lower() == 'y':
            is_init = True
        elif response == "":
            is_init = True
        else:
            is_init = False
        # 检测是否需要初始化
        if is_init:
            # 执行初始化MySQL数据库
            start_process(r'python scripts\init_mysql.py', cwd=base_dir, window_title="MySQL初始化", wait=True)
            print("MySQL初始化完成，继续启动其他服务...")
        else:
            print("已取消MySQL数据库初始化操作！")
            sys.exit(1)

    print("正在启动所有服务...")
    
    # 1. 启动MySQL服务
    print("启动MySQL服务...")
    mysql_cmd = 'mysqld --console'
    start_process(mysql_cmd, window_title="MySQL服务器")

    # 2. 启动Redis服务
    print("启动Redis服务...")
    redis_cwd = os.path.join(base_dir, 'data')
    print(f"Redis运行目录: {redis_cwd}")
    redis_cmd = 'redis-server.exe'
    start_process(redis_cmd, cwd=redis_cwd, window_title="Redis服务器")

    # 3. 启动前端服务
    print("启动前端服务...")
    frontend_cwd = os.path.join(base_dir, 'src', 'main', 'manager-web')
    # 先安装依赖（等待完成）
    print("开始安装前端依赖...")
    if start_process('npm install', cwd=frontend_cwd, window_title="前端依赖安装", wait=True):
        print("前端依赖安装成功！")
        # 启动服务（不等待）
        print("启动前端服务...")
        start_process('title 前端服务器 & npm run serve', cwd=frontend_cwd, window_title="前端服务器")
    else:
        print("前端依赖安装失败！")
    
    # 4. 启动后端API服务器
    print("启动后端API服务器...")
    backend_cwd = os.path.join(base_dir, 'src', 'main', 'manager-api')
    backend_cmd = 'chcp 65001 & mvn spring-boot:run'
    start_process(backend_cmd, cwd=backend_cwd, window_title="后端API服务器")
    
    # 等待后端API服务器启动完成
    backend_url = "http://localhost:8002/xiaozhi/doc.html"
    max_attempts = 120  # 最多等待120秒
    attempt = 0
    
    print(f"等待后端API服务器启动中，正在尝试连接后端服务...")
    
    while attempt < max_attempts:
        attempt += 1
        try:
            # 发送GET请求到后端API
            response = requests.get(backend_url, timeout=2)
            # 检查响应状态码是否为200（成功）
            if response.status_code == 200:
                print(f"成功连接到后端API服务器！")
                break
            else:
                # 服务器已启动但返回非200状态码
                print(f"第 {attempt} 秒：后端API服务器已响应，但状态码为 {response.status_code}，继续等待...")
        except requests.ConnectionError:
            # 连接失败
            if attempt % 5 == 0:  # 每5秒打印一次提示，避免输出过多
                print(f"第 {attempt} 秒：后端API服务器尚未启动或无法连接，继续等待...")
        except requests.Timeout:
            # 请求超时
            print(f"第 {attempt} 秒：连接后端API服务器超时，继续等待...")
        except requests.RequestException as e:
            # 捕获其他所有请求相关异常
            print(f"第 {attempt} 秒：请求发生异常: {str(e)}")
        except Exception as e:
            # 捕获所有其他意外异常
            print(f"第 {attempt} 秒：发生意外错误: {str(e)}")
        
        time.sleep(1)  # 每秒尝试一次
    
    if attempt >= max_attempts:
        print(f"警告：在 {max_attempts} 秒内未能成功连接到后端API服务器")
        print(f"将继续执行后续步骤，但可能会影响功能")
    else:
        print(f"后端API服务器检查完成，耗时 {attempt} 秒，准备启动小智AI服务端...")
    
    # 5. 启动Python服务端
    if check_config():
        print("启动小智AI服务器...")
        python_cwd = os.path.join(base_dir, 'src', 'main', 'xiaozhi-server')
        python_cmd = 'python app.py'
        start_process(python_cmd, cwd=python_cwd, window_title="小智AI服务器")
    else:
        print("检测到配置文件尚未初始化，正在启动初始化...")
        print("已自动打开智控台。请前往智控台注册登录账号后在初始化窗口填写服务器密钥。")
        webbrowser.open("http://localhost:8001")
        start_process(r'python scripts\init_config_pyside6.py', cwd=base_dir, window_title="小智服务端配置初始化")
    print("所有服务启动完成！")
    time.sleep(5)

def main():
    """主函数"""
    # 欢迎界面
    get_welcome_text()
    # 1. 设置环境变量
    set_environment_variables()
    
    while True:
        print("=" * 55)
        print("首次运行建议直接按回车执行 1. 一键启动所有服务并自动初始化")
        print("请选择操作: ")
        print("=" * 55)
        print("1. 一键启动所有服务并自动初始化")
        print("2. 单独启动MySQL服务")
        print("3. 单独启动Redis服务")
        print("4. 单独启动前端服务")
        print("5. 单独启动后端API服务器")
        print("6. 单独启动小智AI服务器(Python)")
        print("=" * 55)
        print("7. 重新配置服务器密钥")
        print("8. 结束MySQL和Redis相关进程")
        print("9. 结束MySQL和Redis相关进程（管理员身份）")
        print("10. 重新初始化MySQL数据库")
        print("11. 退出")
        print("=" * 55)
        choice = input("请输入选项 (1-11)(留空则默认执行1): ") or '1'
        
        if choice == '1':
            start_all_services()
        elif choice == '2':
            start_mysql_service()
        elif choice == '3':
            start_redis_service()
        elif choice == '4':
            start_frontend_service()
        elif choice == '5':
            start_backend_service()
        elif choice == '6':
            start_python_service()
        elif choice == '7':
            start_init_config()
        elif choice == '8':
            end_database_processes(False)
        elif choice == '9':
            end_database_processes(True)
        elif choice == '10':
            start_process(r'python scripts\init_mysql.py', cwd=base_dir, window_title="小智服务端MySQL数据库初始化")
        elif choice == '11':
            print("退出程序...")
            sys.exit(0)
        elif choice == '':
            start_all_services()
        else:
            print("无效选项，请重新输入有效选项(1-11)")
            time.sleep(3)

        os.system('cls')
        get_welcome_text()

if __name__ == "__main__":
    main()
