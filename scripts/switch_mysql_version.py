import os
import shutil
import requests
import zipfile
import tempfile
import sys

# 定义路径和URL
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_DIR = os.path.join(BASE_DIR, 'runtime')
OLD_MYSQL_DIR = os.path.join(RUNTIME_DIR, 'mysql-9.4.0')
NEW_MYSQL_URL = 'https://drive.xcnahida.cn/f/d/nqIG/mysql-8.4.7-winx64.zip'
NEW_MYSQL_NAME = 'mysql-8.4.7'

# 创建tmp目录（如果不存在）
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
        
        with open(ZIP_FILE_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print_info(f"下载完成，文件保存至: {ZIP_FILE_PATH}")
        return True
    except Exception as e:
        print_error(f"下载MySQL压缩包失败: {e}")
        return False


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
    try:
        # 删除下载的zip文件
        if os.path.exists(ZIP_FILE_PATH):
            os.remove(ZIP_FILE_PATH)
            print_info(f"已删除下载的压缩包: {ZIP_FILE_PATH}")
        
        # 删除临时目录
        if os.path.exists(TMP_DIR):
            shutil.rmtree(TMP_DIR)
            print_info(f"已删除临时目录: {TMP_DIR}")
        
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
    
    # 步骤2: 下载MySQL压缩包
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