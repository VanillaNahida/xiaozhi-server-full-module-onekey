import os
import sys
import subprocess
import platform
import time

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

def welcome():
    """
    欢迎界面
    """
    text = """
 __      __            _  _  _            _   _         _      _      _        
 \ \    / /           (_)| || |          | \ | |       | |    (_)    | |       
  \ \  / /__ _  _ __   _ | || |  __ _    |  \| |  __ _ | |__   _   __| |  __ _ 
   \ \/ // _` || '_ \ | || || | / _` |   | . ` | / _` || '_ \ | | / _` | / _` |
    \  /| (_| || | | || || || || (_| |   | |\  || (_| || | | || || (_| || (_| |
     \/  \__,_||_| |_||_||_||_| \__,_|   |_| \_| \__,_||_| |_||_| \__,_| \__,_|   

    纳西妲世界第一可爱！
"""
    print_gradient_text(text, (200, 250, 50), (0, 128, 0))
    text = """
===================================================================================
    小智AI全模块一键包启动器 By: 哔哩哔哩: @香草味的纳西妲喵
    个人主页: https://space.bilibili.com/1347891621
    GitHub:  https://github.com/VanillaNahida
    我的博客: https://www.xcnahida.cn/
    小智服务端项目开源地址: https://github.com/xinnan-tech/xiaozhi-esp32-server
===================================================================================
    使用过程中有任何疑问欢迎来群里讨论，如有报错请截图反馈。
    群: https://www.bilibili.com/opus/1045130607332425735
    感谢你的使用！
===================================================================================
"""
    # print_gradient_text(text, (200, 250, 50), (0, 128, 0))
    print_gradient_text(text, (160, 240, 160), (40, 200, 40))

# 设置环境变量
def set_environment_variables():
    """设置环境变量，参考激活环境变量.bat"""
    # Java环境变量
    jdk_path = os.path.join(runtime_dir, 'jdk-21.0.9', 'bin')
    java_home = os.path.join(runtime_dir, 'jdk-21.0.9')
    # Maven环境变量
    maven_path = os.path.join(runtime_dir, 'maven-3.9.11', 'bin')
    m2_home = os.path.join(runtime_dir, 'maven-3.9.11')
    # MySQL环境变量
    mysql_path = os.path.join(runtime_dir, 'mysql-9.4.0', 'bin')
    # Redis环境变量
    redis_path = os.path.join(runtime_dir, 'Redis')
    # Node.js环境变量
    node_path = os.path.join(runtime_dir, 'nodejs-v24.11.0')
    # Python环境变量
    python_path = os.path.join(runtime_dir, 'conda_env')
    # FFmpeg环境变量
    ffmpeg_path = os.path.join(runtime_dir, 'ffmpeg', 'bin')
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

    text = f"""🎉运行环境初始化成功！
1. JDK 21.0.9:       {java_home}
2. Maven 3.9.11:     {m2_home}
3. MySQL 9.4.0:      {mysql_path}
4. Redis:            {redis_path}
5. Node.js v24.11.0: {node_path}
6. Python环境:       {python_path}"""

    print_gradient_text(text, (200, 250, 50), (0, 128, 0))

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
    # 定义配置成功文件路径
    config_success_file = os.path.join(base_dir, 'data', '.config_init_success')
    # 检测配置是否已初始化
    if not os.path.exists(config_success_file):
        print("检测到配置文件未初始化，需要进行初始化...")
        print("正在打开配置初始化工具...")
        # 启动配置初始化工具并等待其完成
        print("请完成配置初始化...")
        success = start_process('python scripts\init_config.py', cwd=base_dir, window_title="小智服务端配置初始化", wait=True)
        
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
    else:
        # 配置已初始化
        return True

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
            start_process('python scripts\init_mysql.py', cwd=base_dir, window_title="MySQL初始化", wait=True)
            print("MySQL初始化完成，现在启动MySQL服务...")
        else:
            print("已取消MySQL数据库初始化操作！")
            return
    
    print("启动MySQL服务...")
    mysql_cmd = 'mysqld --console'
    start_process(mysql_cmd, window_title="MySQL服务器")
    print("MySQL服务已启动！")


def start_redis_service():
    """单独启动Redis服务"""
    print("启动Redis服务...")
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
    else:
        print("前端依赖安装失败！")


def start_backend_service():
    """单独启动后端API服务器"""
    print("启动后端API服务器...")
    backend_cwd = os.path.join(base_dir, 'src', 'main', 'manager-api')
    backend_cmd = 'mvn spring-boot:run'
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
            start_process('python scripts\init_mysql.py', cwd=base_dir, window_title="MySQL初始化", wait=True)
            sys.exit(0)
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
    backend_cmd = 'mvn spring-boot:run'
    start_process(backend_cmd, cwd=backend_cwd, window_title="后端API服务器")
    
    # 等待后端API服务器启动完成
    print("等待后端API服务器启动完成...（15秒）")
    time.sleep(15)
    
    # 5. 启动Python服务端
    if check_config():
        print("启动小智AI服务器...")
        python_cwd = os.path.join(base_dir, 'src', 'main', 'xiaozhi-server')
        python_cmd = 'python app.py'
        start_process(python_cmd, cwd=python_cwd, window_title="小智AI服务器")
    else:
        print("检测到配置文件尚未初始化，正在启动初始化...")
        start_process('python scripts\init_config.py', cwd=base_dir, window_title="小智服务端配置初始化")
    print("所有服务启动完成！")
    time.sleep(3)

def main():
    """主函数"""
    # 欢迎界面
    welcome()
    # 1. 设置环境变量
    set_environment_variables()
    
    while True:
        print("=" * 50)
        print("请选择操作: ")
        print("1. 一键启动所有服务（留空则为默认）")
        print("2. 单独启动MySQL服务")
        print("3. 单独启动Redis服务")
        print("4. 单独启动前端服务")
        print("5. 单独启动后端API服务器")
        print("6. 单独启动小智AI服务器(Python)")
        print("7. 退出")
        print("=" * 50)
        choice = input("请输入选项 (1-7)(留空则默认1): ") or '1'
        
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
            print("退出程序...")
            sys.exit(0)
        elif choice == '':
            start_all_services()
        else:
            print("无效选项，请重新输入有效选项(1-7)")
            time.sleep(3)

        os.system('cls')

if __name__ == "__main__":
    main()
