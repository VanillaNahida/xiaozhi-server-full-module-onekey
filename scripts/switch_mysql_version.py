import os
import shutil
import requests
import zipfile
import tempfile
import sys
import time
import hashlib

# 定义路径和URL
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_DIR = os.path.join(BASE_DIR, 'runtime')
OLD_MYSQL_DIR = os.path.join(RUNTIME_DIR, 'mysql-9.4.0')
NEW_MYSQL_URL = 'https://dev.mysql.com/get/Downloads/MySQL-8.4/mysql-8.4.7-winx64.zip'
FILE_SHA256 = 'FD9BDBD4B5A878D31C8E4067078BD60665B1B3C4677FA1F099416D194B458AFF'
NEW_MYSQL_NAME = 'mysql-8.4.7'

# 下载保存目录
TMP_DIR = os.path.join(tempfile.gettempdir(), 'mysql_update')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

ZIP_FILE_PATH = os.path.join(TMP_DIR, 'mysql-8.4.7-winx64.zip')


def print_info(message):
    """打印信息"""
    print(f"[INFO] {message}")


def print_error(message):
    """打印错误信息"""
    print(f"[ERROR] {message}")


def check_and_delete_old_mysql():
    """检查并删除旧的MySQL目录"""
    print_info("检查MySQL目录...")
    if os.path.exists(OLD_MYSQL_DIR):
        print_info(f"发现不符合要求的MySQL目录: {OLD_MYSQL_DIR}")
        try:
            shutil.rmtree(OLD_MYSQL_DIR)
            print_info("已删除不符合要求的MySQL目录")
            return True
        except Exception as e:
            print_error(f"删除MySQL目录失败: {e}")
            return False
    else:
        print_info("未发现不符合要求的MySQL")
        return True


def download_mysql_zip():
    """下载MySQL压缩包"""
    print_info(f"开始下载MySQL压缩包: {NEW_MYSQL_URL}")
    try:
        response = requests.get(NEW_MYSQL_URL, stream=True)
        response.raise_for_status()  # 检查下载是否成功
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        start_time = time.time()
        last_time = start_time
        
        with open(ZIP_FILE_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # 计算进度和速度
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    chunk_time = current_time - last_time
                    
                    # 每0.5秒更新一次进度条
                    if chunk_time > 0.5 or downloaded_size == total_size:
                        last_time = current_time
                        
                        # 计算进度百分比
                        progress = downloaded_size / total_size if total_size > 0 else 0
                        percentage = round(progress * 100, 2)
                        
                        # 计算下载速度
                        speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
                        
                        # 格式化速度显示
                        if speed < 1024:
                            speed_str = f"{speed:.2f} B/s"
                        elif speed < 1024 * 1024:
                            speed_str = f"{speed / 1024:.2f} KB/s"
                        else:
                            speed_str = f"{speed / (1024 * 1024):.2f} MB/s"
                        
                        # 格式化下载大小
                        if downloaded_size < 1024:
                            downloaded_str = f"{downloaded_size} B"
                        elif downloaded_size < 1024 * 1024:
                            downloaded_str = f"{downloaded_size / 1024:.2f} KB"
                        else:
                            downloaded_str = f"{downloaded_size / (1024 * 1024):.2f} MB"
                        
                        if total_size > 0:
                            total_str = f"{total_size / (1024 * 1024):.2f} MB"
                        else:
                            total_str = "unknown"
                        
                        # 打印进度条
                        bar_length = 50
                        filled_length = int(bar_length * progress)
                        bar = "#" * filled_length + "-" * (bar_length - filled_length)
                        
                        # 使用回车符覆盖当前行
                        print(f"[INFO] [{'{:<50}'.format(bar)}] {percentage:.2f}% | {downloaded_str}/{total_str} | {speed_str}", end="\r")
        
        # 下载完成后换行
        print()
        print_info(f"下载完成，文件保存至: {ZIP_FILE_PATH}")
        
        # 下载完成后校验哈希值
        print_info("校验下载的文件哈希值中...")
        file_hash = calculate_sha256(ZIP_FILE_PATH)
        if file_hash and file_hash == FILE_SHA256:
            print_info("哈希值校验通过，文件完整")
            return True
        else:
            print_error("下载的文件哈希值校验失败，文件可能损坏")
            # 删除损坏的文件
            if os.path.exists(ZIP_FILE_PATH):
                os.remove(ZIP_FILE_PATH)
            return False
    except Exception as e:
        print_error(f"下载MySQL压缩包失败: {e}")
        return False


def calculate_sha256(file_path):
    """计算文件的SHA256哈希值"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # 分块读取文件，避免内存占用过大
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest().upper()
    except Exception as e:
        print_error(f"计算文件哈希值失败: {e}")
        return None


def extract_and_rename():
    """解压并重新命名MySQL文件夹"""
    print_info("开始解压MySQL压缩包...")
    try:
        # 解压到临时目录
        with zipfile.ZipFile(ZIP_FILE_PATH, 'r') as zip_ref:
            zip_ref.extractall(TMP_DIR)
        
        # 获取解压后的文件夹名称
        extracted_items = os.listdir(TMP_DIR)
        extracted_dirs = [item for item in extracted_items if os.path.isdir(os.path.join(TMP_DIR, item))]
        
        if not extracted_dirs:
            print_error("解压后未找到文件夹")
            return False
        
        extracted_dir = os.path.join(TMP_DIR, extracted_dirs[0])
        new_dir_name = os.path.join(TMP_DIR, NEW_MYSQL_NAME)
        
        # 重命名文件夹
        os.rename(extracted_dir, new_dir_name)
        print_info(f"已将解压后的文件夹重命名为: {NEW_MYSQL_NAME}")
        
        return new_dir_name
    except Exception as e:
        print_error(f"解压或重命名失败: {e}")
        return False


def move_to_runtime(extracted_dir):
    """将MySQL文件夹移动到runtime目录"""
    print_info("开始移动MySQL文件夹到runtime目录...")
    try:
        target_path = os.path.join(RUNTIME_DIR, NEW_MYSQL_NAME)
        
        # 如果目标目录已存在，先删除
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
            print_info(f"已删除已存在的目标目录: {target_path}")
        
        # 移动文件夹
        shutil.move(extracted_dir, RUNTIME_DIR)
        print_info(f"已将MySQL文件夹移动到: {target_path}")
        return True
    except Exception as e:
        print_error(f"移动MySQL文件夹失败: {e}")
        return False


def clean_up():
    """清理临时文件和目录"""
    print_info("开始清理临时文件...")
    parent_zip_path = os.path.join(BASE_DIR, "mysql-8.4.7-winx64.zip")
    try:
        # 删除下载的zip文件
        if os.path.exists(ZIP_FILE_PATH):
            os.remove(ZIP_FILE_PATH)
            print_info(f"已删除下载的压缩包: {ZIP_FILE_PATH}")
        
        # 删除临时目录
        if os.path.exists(TMP_DIR):
            shutil.rmtree(TMP_DIR)
            print_info(f"已删除临时目录: {TMP_DIR}")

        # 删除zip文件
        if os.path.exists(parent_zip_path):
            os.remove(parent_zip_path)
            print_info(f"已删除压缩包: {parent_zip_path}")
        
        return True
    except Exception as e:
        print_error(f"清理临时文件失败: {e}")
        return False


def main():
    """主函数"""
    print_info("MySQL版本切换开始")
    
    # 步骤1: 检查并删除旧的MySQL目录
    if not check_and_delete_old_mysql():
        sys.exit(1)
    
    # 检查新版本是否已经存在
    new_mysql_dir = os.path.join(RUNTIME_DIR, NEW_MYSQL_NAME)
    if os.path.exists(new_mysql_dir):
        print_info(f"新版本MySQL目录 {NEW_MYSQL_NAME} 已经存在，跳过下载！")
        print_info(f"MySQL已安装到: {new_mysql_dir}")
        sys.exit(0)
    else:
        print_info(f"MySQL目录 {NEW_MYSQL_NAME} 不存在，继续安装！")
    
    # 步骤2: 检查MySQL压缩包
    # 先检查脚本所在的上一级目录
    parent_zip_path = os.path.join(BASE_DIR, "mysql-8.4.7-winx64.zip")
    
    # 标记是否需要下载
    need_download = True
    
    if os.path.exists(parent_zip_path):
        print_info(f"在项目根目录发现MySQL压缩包: mysql-8.4.7-winx64.zip")
        print_info("校验哈希值中...")
        
        # 计算哈希值
        file_hash = calculate_sha256(parent_zip_path)
        if file_hash and file_hash == FILE_SHA256:
            print_info("哈希值校验通过，开始使用该压缩包")
            # 复制到临时目录
            shutil.copy2(parent_zip_path, ZIP_FILE_PATH)
            need_download = False
        else:
            print_error("哈希值校验失败，删除损坏的压缩包")
            os.remove(parent_zip_path)
    
    # 如果需要下载
    if need_download:
        if os.path.exists(ZIP_FILE_PATH):
            print_info(f"发现临时目录中的MySQL压缩包: mysql-8.4.7-winx64.zip")
            print_info("校验哈希值中...")
            
            # 计算哈希值
            file_hash = calculate_sha256(ZIP_FILE_PATH)
            if file_hash and file_hash == FILE_SHA256:
                print_info("哈希值校验通过，开始使用该压缩包")
                need_download = False
            else:
                print_error("哈希值校验失败，删除损坏的压缩包")
                os.remove(ZIP_FILE_PATH)
        
        # 如果仍然需要下载
        if need_download:
            print_info(f"未发现有效的MySQL压缩包，正在开始下载...")
            if not download_mysql_zip():
                sys.exit(1)
    
    # 步骤3: 解压并重新命名
    extracted_dir = extract_and_rename()
    if not extracted_dir:
        sys.exit(1)
    
    # 步骤4: 移动到runtime目录
    if not move_to_runtime(extracted_dir):
        sys.exit(1)
    
    # 步骤5: 清理临时文件
    if not clean_up():
        sys.exit(1)
    
    print_info("MySQL版本切换完成！")
    print_info(f"新版本MySQL已安装到: {os.path.join(RUNTIME_DIR, NEW_MYSQL_NAME)}")


if __name__ == "__main__":
    main()
    print_info("即将在5秒后自动退出...")
    time.sleep(5)