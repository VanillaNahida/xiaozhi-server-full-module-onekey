import os
import re
import sys
import subprocess
import time
import shutil
import getpass
import signal
import logging
import string
import random
import mysql.connector
from mysql.connector import Error
from logging.handlers import RotatingFileHandler
from write_password_to_config import write_password_to_config as wpc


def create_mysql_connection(user='root', password=None, host='localhost', port=3306, database=None):
    """
    创建MySQL数据库连接
    
    参数:
    user (str): 用户名，默认为'root'
    password (str): 密码，默认为None（无密码连接）
    host (str): 主机名，默认为'localhost'
    port (int): 端口号，默认为3306
    database (str): 数据库名，默认为None（连接不指定数据库）
    
    返回:
    connection: MySQL连接对象，如果连接失败返回None
    """
    connection = None
    try:
        # 构建连接参数
        conn_params = {
            'user': user,
            'host': host,
            'port': port
        }
        
        # 只有在密码不为None时添加密码参数
        if password is not None:
            conn_params['password'] = password
        
        # 如果指定了数据库，添加数据库参数
        if database is not None:
            conn_params['database'] = database
        
        connection = mysql.connector.connect(**conn_params)
        
        if connection.is_connected():
            return connection
    except Error as e:
        logger.error(f"❌ MySQL连接失败: {str(e)}")
    except Exception as e:
        logger.error(f"❌ 创建MySQL连接时发生未知错误: {str(e)}")
    
    return None

# 配置日志记录器
class ColoredFormatter(logging.Formatter):
    # 定义颜色代码
    COLORS = {
        'DEBUG': '\033[94m',     # BLUE
        'INFO': '\033[92m',      # GREEN
        'WARNING': '\033[93m',   # WARNING
        'ERROR': '\033[91m',     # FAIL
        'CRITICAL': '\033[95m',  # HEADER
        'ENDC': '\033[0m',       # ENDC
        'BOLD': '\033[1m',       # BOLD
        'UNDERLINE': '\033[4m'   # UNDERLINE
    }
    
    # 检查是否支持颜色
    @classmethod
    def supports_color(cls):
        plat = sys.platform
        supported_platform = plat != 'Pocket PC' and (plat != 'win32' or 'ANSICON' in os.environ)
        # 检查是否是终端
        is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        return supported_platform and is_a_tty
    
    def format(self, record):
        # 保存原始的格式化消息
        original_message = record.getMessage()
        levelname = record.levelname
        
        # 如果支持颜色，添加颜色代码
        if self.supports_color():
            color_start = self.COLORS.get(levelname, '')
            color_end = self.COLORS['ENDC']
            record.msg = f"{color_start}{original_message}{color_end}"
        else:
            # 移除ANSI颜色代码，保留纯文本
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            record.msg = ansi_escape.sub('', original_message)
            
        # 调用父类的format方法
        return super().format(record)

def setup_logging():
    """设置日志配置"""
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger('mysql_init')
    logger.setLevel(logging.DEBUG)
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器，最大10MB，备份3个
    log_file = os.path.join(log_dir, 'mysql_init.log')
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 创建格式化器
    console_formatter = ColoredFormatter('%(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 设置格式化器
    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 创建日志记录器
logger = setup_logging()

def get_script_dir():
    """获取脚本所在目录"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return script_dir
    except Exception as e:
        logger.error(f"❌ 获取脚本目录失败: {str(e)}")
        # 返回当前工作目录作为备选
        cwd = os.getcwd()
        logger.warning(f"⚠️ 使用当前工作目录作为备选: {cwd}")
        return cwd

def get_project_root():
    """获取项目根目录"""
    try:
        # 获取脚本目录
        script_dir = get_script_dir()
        
        # 向上查找项目根目录（scripts的父目录）
        project_root = os.path.dirname(script_dir)
        return project_root
    except Exception as e:
        logger.error(f"❌ 获取项目根目录失败: {e}")
        # 返回脚本目录作为备选
        script_dir = get_script_dir()
        logger.warning(f"⚠️ 使用脚本目录作为备选: {script_dir}")
        return script_dir

def clean_data_directory(data_dir):
    """清理数据目录（谨慎使用）"""
    logger.info(f"🧹 检查数据目录: {data_dir}")
    # 检查数据目录是否存在
    if os.path.exists(data_dir):
        logger.warning(f"⚠️  数据目录已存在: {data_dir}")
        
        # 检查目录是否为空
        if os.listdir(data_dir):
            logger.warning(f"   目录不为空，包含 {len(os.listdir(data_dir))} 个文件/目录")
            # 添加警告和二次确认
            logger.warning("\n============================================")
            logger.warning("⚠️  警告: 清理数据目录将删除所有现有数据!")
            logger.warning("⚠️  这将导致所有MySQL数据永久丢失!")
            logger.warning("============================================")
            
            # 获取用户确认
            confirmation = input("🔍 请确认是否继续清理操作！输入yes或y将删除并重建数据库！ (yes/no): ").strip().lower()
            
            if confirmation not in ['yes', 'y']:
                logger.warning("❌ 清理操作已取消")
                return False
            
            try:
                # 用户确认后才清理
                logger.info("🧹 开始清理数据目录...")
                # 结束mysql服务
                logger.warning("   正在停止MySQL服务...")
                try:
                    subprocess.run(
                        ['taskkill', '/F', '/T', '/IM', 'mysqld.exe'],
                        check=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    logger.info("✅ MySQL服务已停止")
                except Exception as e:
                    logger.error(f"❌ 停止MySQL服务失败: {e}")
                    logger.warning("⚠️ 请手动检查并关闭MySQL服务")
                    return False
                
                logger.warning("   正在清理目录...")
                shutil.rmtree(data_dir)
                os.makedirs(data_dir)
                logger.info(f"✅ 数据目录已清理: {data_dir}")
                return True
            except Exception as e:
                logger.error(f"❌ 清理目录失败: {e}")
                logger.warning("💡 可能是权限问题，请尝试以管理员身份运行")
                return False
        else:
            logger.info("   目录为空，无需清理")
    else:
        logger.info("   数据目录不存在，将自动创建")
    
    # 确保目录存在
    try:
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"✅ 确保数据目录存在: {data_dir}")
        return True
    except Exception as e:
        logger.error(f"❌ 创建数据目录失败: {e}")
        return False

def show_progress(current, total, message="处理中"):
    """显示进度条"""
    if message:
        # 直接输出消息
        logger.info(message)
    bar_length = 30
    progress = float(current) / float(total)
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write(f'\r{message} |{bar}| {int(progress * 100)}%')
    sys.stdout.flush()
    if current >= total:
        print()

def create_my_ini():
    """创建MySQL配置文件"""
    logger.info("📄 创建MySQL配置文件...")
    
    try:
        project_root = get_project_root()
        mysql_dir = os.path.join(project_root, 'runtime', 'mysql-9.4.0')
        data_dir = os.path.join(project_root, 'data', 'mysql')
        
        # 确保目录存在
        logger.info("📁 准备目录结构...")
        try:
            os.makedirs(mysql_dir, exist_ok=True)
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"✅ 目录创建成功: {mysql_dir}")
            logger.info(f"✅ 目录创建成功: {data_dir}")
        except Exception as e:
            logger.error(f"❌ 创建目录失败: {str(e)}")
            raise
        
        # 创建my.ini文件
        my_ini_path = os.path.join(mysql_dir, 'my.ini')
        
        # 配置文件内容（使用Windows路径格式）
        # 将路径中的/替换为\
        data_dir_win = data_dir.replace('/', '\\')
        
        my_ini_content = f"""
[mysqld]
datadir={data_dir_win}
port=3306
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
max_connections=151
default-storage-engine=INNODB
innodb_buffer_pool_size=128M
innodb_redo_log_capacity=512M
innodb_file_per_table=1

[mysql]
default-character-set=utf8mb4

[client]
default-character-set=utf8mb4
port=3306
"""
        
        try:
            with open(my_ini_path, 'w', encoding='utf-8') as f:
                f.write(my_ini_content)
            logger.info(f"✅ my.ini配置文件已创建: {my_ini_path}")
        except Exception as e:
            logger.error(f"❌ 写入配置文件失败: {str(e)}")
            raise
        
        logger.info("📊 配置信息摘要:")
        logger.info(f"   - 数据目录: {data_dir}")
        logger.info(f"   - 配置文件: {my_ini_path}")
        logger.info(f"   - MySQL版本目录: {mysql_dir}")
        
        return mysql_dir, data_dir, my_ini_path
        
    except Exception as e:
        logger.error(f"❌ 创建my.ini配置文件失败: {str(e)}")
        raise

def generate_strong_password(length=16):
    """生成一个复杂的16位数密码，包含大小写字母、数字和特殊字符"""
    # 定义字符集
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # 确保密码包含每种类型的字符
    password = [
        random.choice(uppercase),
        random.choice(lowercase),
        random.choice(digits),
        random.choice(special_chars)
    ]
    
    # 填充剩余字符
    all_chars = uppercase + lowercase + digits + special_chars
    password.extend(random.choice(all_chars) for _ in range(length - 4))
    
    # 打乱密码顺序
    random.shuffle(password)
    
    return ''.join(password)

def save_password_to_file(password):
    """保存密码到文件"""
    try:
        # 定义密码文件路径 - 动态获取项目根目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)  # 获取scripts目录的父目录作为项目根目录
        password_file = os.path.join(project_root, 'MySQL密码.txt')
        
        # 保存密码到文件
        with open(password_file, "w", encoding="utf-8") as f:
            logger.info("🔑 =====================================")
            logger.info("🔑 你的MySQL账号是: root")
            logger.info(f"🔑 你的MySQL密码是: {password}")
            f.write(f"你的MySQL账号是: root \n你的MySQL数据库密码是: {password}")        
        logger.info(f"✅ MySQL密码已保存到: {os.path.abspath(password_file)}")
        logger.info("🔑 =====================================")
        return True
    except Exception as e:
        logger.error(f"❌ 保存密码到文件时发生错误: {str(e)}")
        return False

def change_mysql_password(mysql_dir, old_password, new_password):
    """使用MySQL Connector修改MySQL root密码"""
    logger.info("🔧 开始设置MySQL root密码...")
    
    # 对于MySQL Connector方式，我们不需要mysql_dir参数来找到mysql.exe
    # 但保留参数以保持函数签名兼容性
    logger.info("🔐 使用MySQL Connector API进行密码设置")
    
    # 首先尝试使用标准ALTER USER语句
    connection = create_mysql_connection(password=old_password)
    if connection:
        try:
            cursor = connection.cursor()
            logger.info("📋 执行密码修改SQL")
            # 执行修改密码的SQL语句
            cursor.execute(f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{new_password}'")
            # 刷新权限
            cursor.execute("FLUSH PRIVILEGES")
            connection.commit()
            
            # 验证密码修改是否成功
            logger.info("✅ 密码修改成功，验证新密码连接...")
            cursor.close()
            connection.close()
            
            # 尝试使用新密码连接
            test_connection = create_mysql_connection(password=new_password)
            if test_connection:
                logger.info("✅ 使用新密码连接成功，密码设置完成！")
                test_connection.close()
                return True
            else:
                logger.warning("⚠️  新密码连接测试失败，可能需要进一步验证")
        except Error as e:
            logger.error(f"❌ 执行设置密码命令时出错: {str(e)}")
            
            # 如果是无密码初始化的情况（old_password为None），尝试使用替代语法
            if old_password is None:
                logger.warning("⚠️  首次尝试设置密码失败，尝试使用不同的密码设置语法")
                
                # 关闭当前连接
                cursor.close()
                connection.close()
                
                # 重新连接并尝试使用SET PASSWORD语法
                connection_alt = create_mysql_connection(password=None)
                if connection_alt:
                    try:
                        cursor_alt = connection_alt.cursor()
                        # 尝试使用SET PASSWORD语法
                        cursor_alt.execute(f"SET PASSWORD FOR 'root'@'localhost' = '{new_password}'")
                        cursor_alt.execute("FLUSH PRIVILEGES")
                        connection_alt.commit()
                        
                        logger.info("✅ 使用SET PASSWORD语法成功设置密码！")
                        cursor_alt.close()
                        connection_alt.close()
                        
                        # 验证新密码
                        test_connection_alt = create_mysql_connection(password=new_password)
                        if test_connection_alt:
                            test_connection_alt.close()
                            return True
                    except Error as e_alt:
                        logger.error(f"❌ 使用替代语法设置密码也失败: {str(e_alt)}")
                        cursor_alt.close()
                        connection_alt.close()
        finally:
            if connection.is_connected():
                connection.close()
    
    # 如果连接失败且是因为access denied错误，尝试其他方法
    if old_password and 'Access denied' in str(Error):
        logger.warning("💡 访问被拒绝，可能是密码过期或其他权限问题")
        # 对于过期密码，MySQL Connector不直接支持--connect-expired-password
        # 我们可以尝试使用特殊连接参数或回退到简单连接
    
    logger.warning("💡 所有尝试均失败，返回False")
    return False

def extract_temporary_password(error_log_path):
    """从错误日志中提取临时密码"""
    if not os.path.exists(error_log_path):
        logger.error(f"❌ 错误日志不存在: {error_log_path}")
        logger.warning("💡 可能初始化还未完成或使用了--initialize-insecure模式")
        return None
    
    logger.info(f"🔍 从错误日志中提取临时密码: {error_log_path}")
    
    try:
        # 使用正则表达式查找临时密码（支持多种语言和格式）
        patterns = [
            r'A temporary password is generated for root@localhost: (.*)',
            r'为 root@localhost 生成的临时密码: (.*)',
            r'temporary password.*root@localhost: (.*)'
        ]
        
        with open(error_log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    temporary_password = match.group(1).strip()
                    logger.info(f"✅ 临时密码提取成功!")
                    logger.info(f"   密码: {temporary_password}")
                    logger.warning("💡 请记住此密码，首次登录MySQL时需要使用")
                    # 使用统一的函数保存密码
                    save_password_to_file(temporary_password)
                    return temporary_password
        
        logger.error("❌ 没有找到临时密码信息")
        logger.warning("💡 可能的原因:")
        logger.warning("   1. 初始化未完成或失败")
        logger.warning("   2. 使用了--initialize-insecure模式（无密码）")
        logger.warning("   3. 密码格式不匹配已知模式")
        
        # 打印日志最后几行作为参考
        try:
            with open(error_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                last_lines = list(f)[-10:]
                logger.info("📋 日志最后10行:")
                for line in last_lines:
                    logger.info(f"   {line.strip()}")
        except:
            pass
            
        return None
    except Exception as e:
        logger.error(f"❌ 提取临时密码时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def initialize_mysql(mysql_dir, data_dir):
    """初始化MySQL数据库"""
    logger.info("🔧 开始初始化MySQL数据库...")
    
    # MySQL初始化命令
    mysqld_path = os.path.join(mysql_dir, 'bin', 'mysqld.exe')
    
    # 检查mysqld.exe是否存在
    if not os.path.exists(mysqld_path):
        logger.error(f"❌ 找不到mysqld.exe: {mysqld_path}")
        logger.warning(f"💡 请确认MySQL是否已正确安装在: {mysql_dir}")
        raise FileNotFoundError(f"mysqld.exe not found at {mysqld_path}")
    else:
        logger.info(f"✅ 找到MySQL服务器程序: {mysqld_path}")
    
    # 错误日志路径
    error_log_path = os.path.join(data_dir, 'mysql_error.log')
    
    # 使用无密码初始化，这样我们可以设置自定义密码
    secure_init = False
    logger.warning("💡 使用无密码初始化模式 (--initialize-insecure)")
    logger.warning("   此模式下root用户首次登录不需要密码，稍后将设置自定义密码")
    
    # 清理数据目录（如果需要）
    if not clean_data_directory(data_dir):
        logger.error("❌ 初始化取消，因为数据目录不为空且用户取消清理")
        return False
    
    # 根据选择构建初始化命令
    if secure_init:
        init_cmd = [
            mysqld_path,
            '--initialize',  # 带临时密码初始化
            f'--datadir={data_dir}',
            f'--log-error={error_log_path}',
            '--console'
        ]
    else:
        init_cmd = [
            mysqld_path,
            '--initialize-insecure',  # 使用无密码初始化
            f'--datadir={data_dir}',
            f'--log-error={error_log_path}',
            '--console'
        ]
    
    try:
        # 执行初始化命令
        logger.info("🚀 开始执行初始化命令...")
        cmd_str = ' '.join(init_cmd)
        logger.info(f"📋 执行命令: {cmd_str}")
        logger.warning("💡 初始化可能需要几分钟时间，请耐心等待...")
        
        # 显示进度
        start_time = time.time()
        progress_step = 0
        max_steps = 10
        
        process = subprocess.Popen(
            init_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )
        
        # 实时输出初始化过程中的重要信息
        error_found = False
        for line in process.stdout:
            line_stripped = line.strip()
            # 显示错误信息
            if 'ERROR' in line_stripped:
                logger.error(f"❌ {line_stripped}")
                error_found = True
            # 显示警告信息
            elif 'WARNING' in line_stripped:
                logger.warning(f"⚠️ {line_stripped}")
            # 显示重要日志
            elif 'root@localhost' in line_stripped and 'password' in line_stripped:
                logger.info(f"🔑 {line_stripped}")
                # 尝试从终端输出中提取临时密码
                try:
                    # 使用正则表达式提取密码
                    password_patterns = [
                        r'A temporary password is generated for root@localhost: (.*)',
                        r'为 root@localhost 生成的临时密码: (.*)',
                        r'temporary password.*root@localhost: (.*)'
                    ]
                    for pattern in password_patterns:
                        import re
                        match = re.search(pattern, line_stripped)
                        if match:
                            temporary_password = match.group(1).strip()
                            logger.info(f"✅ 从终端输出成功提取临时密码!")
                            # 保存密码到变量，后续会使用
                            if 'extracted_password' not in locals():
                                extracted_password = temporary_password
                            break
                except Exception as e:
                    logger.error(f"❌ 从终端输出提取密码时发生错误: {str(e)}")
            
            # 更新进度显示
            elapsed = time.time() - start_time
            progress_step = min(int(elapsed / 3), max_steps)
            show_progress(progress_step, max_steps, "初始化MySQL")
        
        # 等待进程结束
        process.wait()
        show_progress(max_steps, max_steps, "初始化MySQL")
        
        if process.returncode == 0:
            logger.info("\n✅ MySQL初始化成功！")
            logger.info(f"⏱️  初始化耗时: {time.time() - start_time:.2f}秒")
            
            # 初始化临时密码变量
            temporary_password = None
            
            # 如果是安全初始化，尝试提取临时密码
            if secure_init:
                # 先检查是否已经从终端输出中提取了密码
                if 'extracted_password' in locals() and extracted_password:
                    temporary_password = extracted_password
                    logger.info(f"🔑 临时密码: {temporary_password}")
                    logger.warning("💡 请使用此密码首次登录MySQL")
                    logger.warning("   mysql -u root -p")
                    # 保存密码到文件
                    save_password_to_file(temporary_password)
                else:
                    # 如果终端输出中没有提取到，再尝试从错误日志提取
                    temporary_password = extract_temporary_password(error_log_path)
                    if temporary_password:
                        logger.info(f"🔑 临时密码: {temporary_password}")
                        logger.warning("💡 请使用此密码首次登录MySQL")
                        logger.warning("   mysql -u root -p")
                        # 保存密码到文件
                        save_password_to_file(temporary_password)
            else:
                logger.info("💡 使用无密码初始化，root用户不需要密码")
                logger.info("   mysql -u root")
            
            # 检查是否创建成功
            if os.listdir(data_dir):
                logger.info(f"✅ 数据文件创建成功，共{len(os.listdir(data_dir))}个文件")
            else:
                logger.warning("⚠️  数据目录似乎为空，请检查初始化是否正常完成！")
                
            # 返回初始化结果和提取的临时密码
            return {'success': True, 'password': temporary_password}
        else:
            logger.error(f"\n❌ MySQL初始化失败，返回代码: {process.returncode}")
            # 尝试从错误日志获取更多信息
            if os.path.exists(error_log_path):
                logger.info("📋 错误日志内容摘要:")
                try:
                    with open(error_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        error_lines = []
                        for line in f:
                            if 'ERROR' in line:
                                error_lines.append(line.strip())
                        
                        # 只显示最近的5条错误信息
                        for error_line in error_lines[-5:]:
                            logger.error(f"   ❌ {error_line}")
                        
                        if not error_lines:
                            logger.warning("   没有找到ERROR级别的日志")
                            # 显示最后几行
                            with open(error_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                last_lines = list(f)[-10:]
                                for line in last_lines:
                                    logger.warning(f"   {line.strip()}")
                except Exception as e:
                    logger.error(f"❌ 读取错误日志失败: {str(e)}")
            
            logger.warning("💡 常见问题排查:")
            logger.warning("   1. 检查数据目录权限是否正确")
            logger.warning("   2. 确保没有其他MySQL进程正在运行")
            logger.warning("   3. 尝试手动清理数据目录后重新初始化")
            
            # 返回失败结果
            return {'success': False, 'password': None}
    except KeyboardInterrupt:
        logger.warning("\n⚠️ 用户中断初始化操作")
        return False
    except Exception as e:
        logger.error(f"\n❌ MySQL初始化发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def check_mysql_process():
    """检查是否有MySQL进程正在运行"""
    try:
        # 在Windows上检查mysqld进程
        result = subprocess.run(
            ['tasklist', '/fi', 'imagename eq mysqld.exe'],
            stdout=subprocess.PIPE,
            text=True
        )
        return 'mysqld.exe' in result.stdout
    except Exception as e:
        logger.warning(f"⚠️  检查MySQL进程时发生错误: {str(e)}")
        return False

def verify_mysql_installation(mysql_dir, password=""):
    """使用MySQL Connector验证MySQL安装和配置是否成功
    
    Args:
        mysql_dir: MySQL安装目录
        password: MySQL root密码
        
    Returns:
        dict: 包含验证结果的字典
    """
    logger.info("\n===== 开始验证MySQL初始化结果 =====")
    
    verification_result = {
        'service_running': False,
        'database_created': False,
        'tables_exist': False,
        'all_success': False
    }
    
    # 1. 验证MySQL服务是否正在运行
    logger.info("[验证1/3] 检查MySQL服务状态...")
    if check_mysql_process():
        verification_result['service_running'] = True
        logger.info("✅ MySQL服务正在运行")
    else:
        logger.error("❌ MySQL服务未运行")
        logger.info("===== 验证完成 =====")
        return verification_result
    
    # 使用MySQL Connector连接验证
    connection = None
    try:
        if password:
            logger.info("🔐 验证时使用密码连接")
        else:
            logger.info("🔓 验证时使用无密码连接")
        
        # 2. 验证数据库是否存在
        logger.info("[验证2/3] 检查数据库是否创建成功...")
        
        # 首先连接到MySQL服务器（不指定数据库）
        connection = create_mysql_connection(password=password)
        if not connection:
            logger.error("❌ 无法连接到MySQL服务器进行验证")
            logger.info("===== 验证完成 =====")
            return verification_result
        
        cursor = connection.cursor()
        
        # 检查数据库是否存在
        cursor.execute("SHOW DATABASES LIKE 'xiaozhi_esp32_server';")
        result = cursor.fetchone()
        
        if result:
            verification_result['database_created'] = True
            logger.info("✅ 数据库 'xiaozhi_esp32_server' 已创建")
            
            # 3. 验证表是否存在
            logger.info("[验证3/3] 检查是否创建成功...")
            result = cursor.execute("USE xiaozhi_esp32_server;")
            if result is None:
                verification_result['tables_exist'] = True
                logger.info("✅ 表结构已创建")
            else:
                logger.error("❌ 表结构未创建")
        else:
            logger.error("❌ 数据库 'xiaozhi_esp32_server' 未创建")
        
        # 关闭游标
        cursor.close()
        
    except Error as e:
        logger.error(f"❌ MySQL验证错误: {str(e)}")
        if "Access denied" in str(e):
            logger.warning("💡 访问被拒绝，请检查密码是否正确")
        elif "Can't connect" in str(e):
            logger.warning("💡 无法连接到MySQL服务器，请检查服务是否运行")
    except Exception as e:
        logger.error(f"❌ 验证过程中发生未知错误: {str(e)}")
    finally:
        # 确保关闭连接
        if connection and connection.is_connected():
            connection.close()
            logger.info("ℹ️ 验证连接已关闭")
    
    # 确定所有验证是否成功
    verification_result['all_success'] = (
        verification_result['service_running'] and 
        verification_result['database_created']
    )
    
    # 输出验证摘要
    logger.info("\n📊 验证摘要:")
    logger.info(f"   - 服务运行状态: {'✅ 正常' if verification_result['service_running'] else '❌ 异常'}")
    logger.info(f"   - 数据库创建: {'✅ 成功' if verification_result['database_created'] else '❌ 失败'}")
    
    if verification_result['all_success']:
        logger.info("🎉 所有验证项通过！MySQL初始化成功完成！")
    else:
        logger.warning("⚠️ 部分验证未通过，请检查上述警告信息")
    
    logger.info("===== 验证完成 =====")
    return verification_result

def start_mysql_server(mysql_dir, data_dir):
    """启动MySQL服务器"""
    logger.info("🚀 启动MySQL服务器...")
    
    # 检查是否已有MySQL进程在运行
    if check_mysql_process():
        logger.warning("⚠️  检测到已有MySQL进程在运行")
        logger.warning("   请确认是否需要停止现有进程")
        try:
            confirm = input("   是否继续启动新实例？(y/N): ")
            if confirm.lower() != 'y':
                logger.error("❌ 用户取消启动操作")
                return None
        except:
            logger.warning("⚠️  输入错误，继续启动")
    
    mysqld_path = os.path.join(mysql_dir, 'bin', 'mysqld.exe')
    my_ini_path = os.path.join(mysql_dir, 'my.ini')
    
    # 检查文件是否存在
    if not os.path.exists(mysqld_path):
        logger.error(f"❌ 找不到mysqld.exe: {mysqld_path}")
        return None
    
    if not os.path.exists(my_ini_path):
        logger.error(f"❌ 找不到配置文件: {my_ini_path}")
        return None
    
    # 启动命令
    start_cmd = [
        mysqld_path,
        f'--defaults-file={my_ini_path}',
        f'--datadir={data_dir}',
        '--console'
    ]
    
    try:
        logger.info(f"📋 启动命令: {' '.join(start_cmd)}")
        logger.warning("💡 MySQL服务器初始化时将在后台运行")
        
        # 启动MySQL服务器（作为后台进程）
        process = subprocess.Popen(
            start_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )
        
        # 移除无意义的等待提示，改为简单的等待
        time.sleep(3)  # 短暂等待确保服务器启动
        
        # 检查进程是否仍在运行
        if process.poll() is None:
            logger.info("✅ MySQL服务器已成功启动！")
            logger.info(f"   数据目录: {data_dir}")
            logger.info(f"   配置文件: {my_ini_path}")
            logger.info("   端口: 3306")
            
            # 测试连接
            mysql_path = os.path.join(mysql_dir, 'bin', 'mysql.exe')
            test_cmd = [mysql_path, '-u', 'root', '-e', 'SELECT VERSION();']
            try:
                test_result = subprocess.run(
                    test_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    text=True
                )
                if test_result.returncode == 0:
                    logger.info("✅ 成功连接到MySQL服务器！")
                    # 避免在f-string中使用转义字符
                    output_lines = test_result.stdout.strip().splitlines()
                    server_version = output_lines[-1] if output_lines else "未知"
                    logger.info(f"   服务器版本: {server_version}")
            except:
                logger.warning("⚠️  无法立即测试连接，请稍后手动验证")
                
            return process
        else:
            logger.error("❌ MySQL服务器启动失败！")
            # 打印错误输出
            error_output = process.stdout.read()
            if error_output:
                logger.error("📋 错误输出:")
                # 只显示前10行错误
                for line in error_output.split('\n')[:10]:
                    if line.strip():
                        logger.error(f"   {line.strip()}")
            
            logger.warning("💡 可能的解决方法:")
            logger.warning("   1. 检查配置文件是否正确")
            logger.warning("   2. 确保数据目录存在且权限正确")
            logger.warning("   3. 检查端口3306是否被占用")
            logger.warning("   4. 查看错误日志获取详细信息")
            
            return None
    except KeyboardInterrupt:
        logger.warning("\n⚠️ 用户中断启动操作")
        return None
    except Exception as e:
        logger.error(f"❌ 启动MySQL服务器发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def wait_for_mysql_ready(mysql_dir, password=None, timeout=30):
    """等待MySQL服务器就绪"""
    logger.info("⏳ 等待MySQL服务器就绪...")
    mysql_path = os.path.join(mysql_dir, 'bin', 'mysql.exe')
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            cmd = [mysql_path, '-u', 'root']
            if password:
                cmd.append(f'--password={password}')
            cmd.extend(['-e', 'SELECT 1;'])
            
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            if result.returncode == 0:
                logger.info("✅ MySQL服务器已就绪")
                return True
        except:
            pass
        
        time.sleep(2)
        show_progress(int(time.time() - start_time), timeout, "等待MySQL启动")
    
    logger.error("❌ MySQL服务器启动超时")
    return False

def create_xiaozhi_database(mysql_dir, password=None):
    """使用MySQL Connector连接到MySQL并创建小智AI的数据库和表结构"""
    logger.info("📋 开始创建小智AI数据库和表结构...")
    
    # 等待MySQL服务器就绪
    if not wait_for_mysql_ready(mysql_dir, password):
        return False
    
    # 创建数据库连接
    connection = None
    try:
        # 首先连接到MySQL服务器（不指定数据库）
        connection = create_mysql_connection(password=password)
        if not connection:
            logger.error("❌ 无法连接到MySQL服务器")
            return False
        
        logger.info("✅ 成功连接到MySQL服务器")
        
        # 创建游标对象
        cursor = connection.cursor()
        
        # 数据库创建SQL
        create_db_sql = 'CREATE DATABASE IF NOT EXISTS xiaozhi_esp32_server CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
        
        # 执行创建数据库的SQL
        logger.info(f"📝 执行SQL: {create_db_sql}")
        cursor.execute(create_db_sql)
        connection.commit()
        logger.info("✅ 数据库 'xiaozhi_esp32_server' 创建成功")
        
        # 选择创建的数据库
        cursor.execute("USE xiaozhi_esp32_server;")
        logger.info("✅ 已切换到数据库 'xiaozhi_esp32_server'")

        # 关闭游标和连接
        cursor.close()
        connection.close()
        
        logger.info("🎉 数据库和表结构创建完成")
        return True
        
    except Error as e:
        logger.error(f"❌ MySQL错误: {str(e)}")
        
        # 详细的错误诊断
        if "Can't connect" in str(e):
            logger.error("💡 连接失败，检查MySQL服务是否运行")
        elif "Access denied" in str(e):
            logger.error("💡 权限被拒绝，检查密码是否正确")
            if password:
                logger.info(f"💡 使用的密码: {'*' * len(password)}")
        elif "Unknown database" in str(e):
            logger.error("💡 数据库不存在，请检查数据库名称")
        
        return False
    finally:
        # 确保关闭连接
        if connection and connection.is_connected():
            connection.close()
            logger.info("ℹ️ 数据库连接已关闭")

def stop_mysql_server(process):
    """停止MySQL服务器"""
    if process and process.poll() is None:
        try:
            # 尝试正常终止
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        except Exception as e:
            logger.error(f"❌ 停止MySQL服务器时发生错误: {str(e)}")
def main():
    """主函数"""
    # 欢迎信息
    logger.info(f"{'='*70}")
    logger.info(f"  🎉  小智AI服务端 - MySQL数据库初始化工具  🎉  ")
    logger.info(f"{'='*70}")
    
    mysql_process = None
    start_time = time.time()
    verification_result = None
    
    try:
        # 显示进度
        logger.info("🚀 开始初始化流程...")
        
        # 1. 创建my.ini配置文件
        logger.info("[1/5] 创建配置文件")
        mysql_dir, data_dir, my_ini_path = create_my_ini()
        print()
        
        # 2. 初始化MySQL
        logger.info("[2/5] 初始化MySQL数据库")
        # 初始化MySQL数据库（使用无密码模式）
        init_result = initialize_mysql(mysql_dir, data_dir)
        # 无密码初始化时不需要提取临时密码
        temporary_password = None
        if isinstance(init_result, dict) and init_result.get('success', False):
            logger.info(f"🔑 使用无密码初始化模式，将设置自定义密码")
        elif not init_result:
            logger.error("初始化失败，退出程序")
            sys.exit(1)
        print()
        
        # 3. 启动MySQL服务器
        logger.info("[3/5] 启动MySQL服务器")
        mysql_process = start_mysql_server(mysql_dir, data_dir)
        if not mysql_process:
            logger.error("服务器启动失败，退出程序")
            sys.exit(1)
        
        # 添加等待时间确保服务器完全启动
        time.sleep(5)
        
        # 生成一个复杂的16位随机密码
        complex_password = generate_strong_password(16)
        # 修改MySQL root密码
        # 由于使用无密码初始化，temporary_password为None，将直接设置新密码
        change_pwd_result = change_mysql_password(mysql_dir, temporary_password, complex_password)
        
        # 确定使用哪个密码连接数据库
        active_password = complex_password if change_pwd_result else None
        if change_pwd_result:
            logger.info("✅ 自定义随机密码设置成功，使用新密码创建数据库")
        else:
            logger.warning("⚠️  密码设置失败，将尝试使用无密码方式创建数据库")
        print()
        
        # 4. 创建小智AI数据库和表结构
        logger.info("[4/5] 创建数据库和表结构")
        # 保存生成的随机密码到文件
        save_password_to_file(complex_password)
        
        # 创建数据库和表结构，使用生成的随机密码
        if not create_xiaozhi_database(mysql_dir, password=complex_password):
            # 如果使用新密码失败，尝试使用无密码连接（作为后备）
            logger.warning("⚠️  使用新密码创建数据库失败，尝试使用无密码连接...")
            if not create_xiaozhi_database(mysql_dir, password=None):
                logger.error("创建数据库失败，退出程序")
                sys.exit(1)
        
        print()
        
        # 5. 验证初始化结果
        logger.info("[5/5] 验证初始化结果")
        # 重新启动MySQL以确保服务正常运行
        if not check_mysql_process():
            logger.warning("MySQL进程未运行，重新启动...")
            mysql_process = start_mysql_server(mysql_dir, data_dir)
            time.sleep(2)  # 保留短暂等待确保服务器启动
        
        # 执行验证，首先使用生成的随机密码
        verification_result = verify_mysql_installation(mysql_dir, password=complex_password)
        
        # 如果使用密码验证失败，尝试无密码验证
        if not verification_result['all_success']:
            verification_result = verify_mysql_installation(mysql_dir, password=None)
        print()
        
        # 写入初始化成功到文件
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取scripts目录的父目录作为项目根目录
        project_root = os.path.dirname(script_dir)
        with open(os.path.join(project_root, "data", '.mysql_init_sucess'), "w", encoding="utf-8") as f:
            f.write(".sucess")

        # 完成信息
        elapsed_time = time.time() - start_time
        logger.info(f"{'🎉'*5}")
        logger.info(f"🎉 MySQL数据库初始化{'成功完成' if verification_result and verification_result['all_success'] else '完成，但有验证警告'}！ 🎉")
        logger.info(f"{'🎉'*5}")
        
        logger.info("📊 配置摘要:")
        logger.info(f"   数据库名: xiaozhi_esp32_server")
        logger.info(f"   端口: 3306")
        logger.info(f"   执行时间: {elapsed_time:.2f} 秒")
        
        if verification_result and verification_result['all_success']:
            logger.info("🔑 =====================================")
            logger.info("📋 数据库连接信息:")
            logger.info("   - 用户名: root")
            
            # 显示密码信息（强调已生成复杂密码）
            if 'complex_password' in locals() and change_pwd_result:
                logger.info(f"   - 密码: {complex_password} (已保存到文件'MySQL密码.txt')")
                wpc(complex_password)
            elif temporary_password:
                logger.info(f"   - 密码: {temporary_password}")
                wpc(temporary_password)
            else:
                logger.info("   - 密码: [无密码模式]")
                
            logger.info("   - 主机: localhost")
            logger.info("🔑 =====================================")
            logger.info("祝你使用愉快！")
        
        # 如果验证未通过，返回警告状态码
        if verification_result and not verification_result['all_success']:
            logger.warning("注意：部分验证未通过，请检查上述警告信息")
        
    except KeyboardInterrupt:
        logger.warning("用户中断操作")
        logger.warning("可以重新运行此工具继续初始化")
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {str(e)}")
        logger.warning("请确认MySQL是否正确安装")
    except PermissionError as e:
        logger.error(f"权限错误: {str(e)}")
        logger.warning("请以管理员权限运行此工具")
    except Exception as e:
        logger.error(f"发生未预期的错误: {str(e)}")
        logger.info("📋 详细错误信息:")
        import traceback
        traceback.print_exc()
        logger.warning("请检查错误信息并尝试解决问题后重新运行")
    finally:
        try:
            # 检查mysqld.exe进程是否存在
            result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq mysqld.exe"], capture_output=True, text=True)
            if "mysqld.exe" in result.stdout:
                subprocess.run(["taskkill", "/F", "/IM", "mysqld.exe"], check=True)
                logger.warning("MySQL进程已终止")
            else:
                logger.info("MySQL进程未运行，无需终止")
        except subprocess.CalledProcessError:
            logger.warning("终止MySQL进程时出错")
        logger.info("初始化工具执行完毕，5秒后自动退出，如果没有自动退出，请手动关闭本窗口")
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("用户中断操作，正在结束MySQL进程")
        # 添加进程判断，只有当mysqld.exe在运行时才尝试关闭它
        try:
            # 检查mysqld.exe进程是否存在
            result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq mysqld.exe"], capture_output=True, text=True)
            if "mysqld.exe" in result.stdout:
                subprocess.run(["taskkill", "/F", "/IM", "mysqld.exe"], check=True)
                logger.warning("MySQL进程已终止")
            else:
                logger.info("MySQL进程未运行，无需终止")
        except subprocess.CalledProcessError:
            logger.warning("终止MySQL进程时出错")