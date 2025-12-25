# -*- coding: utf-8 -*-
import os
import shutil
import sys
import time
import re
import traceback
from ruamel.yaml import YAML

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QLineEdit, QMessageBox, QProgressBar, QDialog,
    QGridLayout, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QFont, QIcon, QClipboard
from PySide6.QtGui import QDesktopServices

class ConfigWorker(QThread):
    log_signal = Signal(str)
    status_signal = Signal(str)
    finished_signal = Signal(bool, str)
    secret_required_signal = Signal()
    upgrade_required_signal = Signal()
    secret_update_required_signal = Signal()
    secret_confirm_required_signal = Signal(str)

    def __init__(self, project_root, config_path, config_source_path):
        super().__init__()
        self.project_root = project_root
        self.config_path = config_path
        self.config_source_path = config_source_path
        self.server_secret = None
        self.perform_upgrade = False
        self.perform_secret_update = False

    def run(self):
        try:
            self.log("=" * 60)
            self.log("小智服务端配置文件初始化工具")
            self.log("=" * 60)
            
            # 检查配置文件是否存在
            if not self.check_config_file_exists(self.config_path):
                self.log(f"配置文件不存在: {self.config_path}")
                # 如果配置文件不存在，尝试使用新配置
                if os.path.exists(self.config_source_path):
                    self.log("正在创建新的配置文件...")
                    # 确保data目录存在
                    os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                    shutil.copy2(self.config_source_path, self.config_path)
                    self.log(f"✅ 已创建新的配置文件: {self.config_path}")
                    # 提示用户输入server.secret
                    self.secret_required_signal.emit()
                else:
                    self.log(f"错误：配置源文件不存在: {self.config_source_path}")
                    self.log("请检查小智服务端安装是否完整")
                    self.finished_signal.emit(False, "配置源文件不存在")
                return
            
            # 读取配置文件
            self.log("正在读取配置文件...")
            config_data = self.read_config_file(self.config_path)
            
            if not config_data:
                self.log("错误：配置文件内容为空")
                self.finished_signal.emit(False, "配置文件内容为空")
                return
            
            # 检查是否包含manager-api部分
            if not self.has_manager_api_section(config_data):
                # 提示用户升级
                self.upgrade_required_signal.emit()
            else:
                # 配置文件已包含manager-api部分，检查是否需要更新secret
                manager_api = config_data['manager-api']
                secret_needs_update = False
                
                if not isinstance(manager_api, dict):
                    self.log("错误：manager-api部分格式错误")
                    secret_needs_update = True
                elif 'secret' not in manager_api:
                    self.log("发现manager-api部分缺少secret字段")
                    secret_needs_update = True
                elif not manager_api['secret']:
                    self.log("发现secret字段为空")
                    secret_needs_update = True
                elif manager_api['secret'] == '你的server.secret值':
                    self.log("发现secret字段为默认值")
                    secret_needs_update = True
                else:
                    self.log("✅ 配置文件中的secret字段已存在且有效")
                    current_secret = manager_api['secret'][:8] + "..." if len(manager_api['secret']) > 8 else manager_api['secret']
                    self.secret_confirm_required_signal.emit(current_secret)
                    return
                
                if secret_needs_update:
                    self.secret_required_signal.emit()

        except KeyboardInterrupt:
            self.log("\n\n操作被用户中断")
            self.log("配置文件初始化已取消")
            self.finished_signal.emit(False, "操作被用户中断")
        except Exception as e:
            self.log(f"\n❌ 配置文件初始化过程中发生错误: {str(e)}")
            self.log("详细错误信息:")
            self.log(traceback.format_exc())
            self.log("\n请检查错误信息并尝试手动配置")
            self.finished_signal.emit(False, f"发生错误: {str(e)}")

    def log(self, message):
        self.log_signal.emit(message)

    def create_config_success_marker(self, project_root):
        """
        创建配置初始化成功标记文件
        """
        try:
            # 确保data目录存在
            data_dir = os.path.join(project_root, 'data')
            os.makedirs(data_dir, exist_ok=True)
            # 创建成功标记文件
            success_file_path = os.path.join(data_dir, '.config_init_success')
            with open(success_file_path, 'w', encoding='utf-8') as f:
                f.write(f"配置初始化成功\n日期: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.log(f"✅ 配置初始化成功标记文件已创建: {success_file_path}")
            return True
        except Exception as e:
            self.log(f"警告：创建配置初始化成功标记文件失败: {str(e)}")
            return False

    def check_config_file_exists(self, config_path):
        """
        检查配置文件是否存在
        """
        exists = os.path.exists(config_path)
        self.log(f"检查配置文件: {config_path} {'存在' if exists else '不存在'}")
        return exists

    def read_config_file(self, config_path):
        """
        使用ruamel.yaml读取配置文件
        """
        try:
            yaml = YAML()
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.load(f)
            self.log(f"成功读取配置文件: {config_path}")
            return config_data
        except Exception as e:
            self.log(f"读取配置文件失败: {config_path}")
            self.log(f"错误信息: {str(e)}")
            raise

    def has_manager_api_section(self, config_data):
        """
        检查配置文件是否包含完整的manager-api部分
        """
        if not isinstance(config_data, dict):
            self.log("配置文件数据格式错误：不是有效的字典格式")
            return False
        
        if 'manager-api' not in config_data:
            self.log("配置文件缺少 'manager-api' 部分")
            return False
        
        manager_api = config_data['manager-api']
        if not isinstance(manager_api, dict):
            self.log("'manager-api' 部分格式错误：不是有效的字典格式")
            return False
        
        # 检查是否包含url字段
        if 'url' not in manager_api or not manager_api['url']:
            self.log("'manager-api' 部分缺少或为空的 'url' 字段")
        
        # 检查是否包含secret字段
        if 'secret' not in manager_api or not manager_api['secret'] or manager_api['secret'] == '你的server.secret值':
            self.log("'manager-api' 部分缺少有效的 'secret' 字段")
        
        self.log("配置文件包含 'manager-api' 部分")
        return True

    def backup_and_replace_config(self, old_config_path, new_config_source, new_config_path):
        """
        备份旧配置并替换为新配置
        """
        try:
            self.log("开始配置文件升级流程...")
            
            # 检查新配置源文件是否存在
            if not os.path.exists(new_config_source):
                raise FileNotFoundError(f"新配置源文件不存在: {new_config_source}")
            
            # 备份旧配置
            backup_path = old_config_path + '.old'
            self.log(f"正在备份原配置文件至: {backup_path}...")
            shutil.copy2(old_config_path, backup_path)
            self.log(f"✅ 原配置文件已成功备份")
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(new_config_path), exist_ok=True)
            
            # 复制新配置
            self.log(f"正在复制新配置文件...")
            shutil.copy2(new_config_source, new_config_path)
            self.log(f"✅ 新配置文件已成功复制到: {new_config_path}")
            
            self.log("配置文件升级流程完成！")
            return True
            
        except Exception as e:
            self.log(f"配置文件升级失败: {str(e)}")
            # 如果备份成功但复制失败，尝试恢复
            backup_path = old_config_path + '.old'
            if os.path.exists(backup_path):
                try:
                    self.log("尝试恢复原配置文件...")
                    shutil.copy2(backup_path, old_config_path)
                    self.log("✅ 原配置文件已恢复")
                except:
                    self.log("✗ 原配置文件恢复失败，请手动检查")
            return False

    def update_server_secret(self, config_path, secret):
        """
        更新配置文件中的server.secret，保持原有格式，并确保替换"你的server.secret值"占位文本
        """
        try:
            self.log(f"正在更新配置文件中的服务器密钥: {config_path}...")
            
            # 读取原始文件内容，保持格式
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找secret行并替换，特别是替换"你的server.secret值"占位文本
            updated = False
            
            # 优先查找包含"你的server.secret值"的行并替换
            for i, line in enumerate(lines):
                if '你的server.secret值' in line:
                    # 保留缩进格式
                    indent = len(line) - len(line.lstrip())
                    lines[i] = ' ' * indent + f'secret: {secret}\n'
                    updated = True
                    self.log(f'✅ 已成功写入服务器密钥到配置文件')
                    break
            
            # 如果没有找到占位文本，则查找manager-api部分中的secret行
            if not updated:
                for i, line in enumerate(lines):
                    if 'secret:' in line and 'manager-api:' in ''.join(lines[max(0, i-5):i+1]):
                        # 保留缩进格式
                        indent = len(line) - len(line.lstrip())
                        lines[i] = ' ' * indent + f'secret: {secret}\n'
                        updated = True
                        break
            
            # 如果没有找到secret行，尝试在manager-api部分添加
            if not updated:
                for i, line in enumerate(lines):
                    if 'manager-api:' in line:
                        # 找到manager-api部分，在其下方添加secret
                        indent = 2  # 默认缩进
                        if i + 1 < len(lines):
                            next_line = lines[i+1]
                            if next_line.strip():
                                indent = len(next_line) - len(next_line.lstrip())
                        lines.insert(i+1, ' ' * indent + f'secret: {secret}\n')
                        updated = True
                        break
            
            # 如果还是没有找到，添加整个manager-api部分
            if not updated:
                lines.append('\nmanager-api:\n')
                lines.append('  url: http://127.0.0.1:8002/xiaozhi\n')
                lines.append(f'  secret: {secret}\n')
                updated = True
            
            # 写回文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            self.log("✅ 服务器密钥已成功更新到配置文件")
            return True
            
        except Exception as e:
            self.log(f"错误：更新服务器密钥失败: {str(e)}")
            # 尝试使用ruamel.yaml作为备选方法
            try:
                self.log("尝试使用备选方法更新配置...")
                yaml = YAML()
                yaml.preserve_quotes = True  # 保留引号格式
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.load(f)
                
                if 'manager-api' not in config_data:
                    config_data['manager-api'] = {}
                
                config_data['manager-api']['secret'] = secret
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f)
                
                self.log("✅ 使用备选方法成功更新配置")
                return True
                
            except Exception as e2:
                self.log(f"错误：备选更新方法也失败: {str(e2)}")
                raise

class SecretInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("服务器密钥配置")
        self.setFixedSize(500, 350)  # 增加窗口高度以容纳新按钮
        self.setWindowModality(Qt.ApplicationModal)
        # 设置窗口置顶，并且只保留最小化和关闭按钮
        self.setWindowFlags(
            Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint
        )
        # 设置窗口居中显示
        self.center()
        
    def center(self):
        # 获取屏幕几何信息
        screen_geometry = QApplication.primaryScreen().geometry()
        # 获取窗口几何信息
        window_geometry = self.frameGeometry()
        # 计算窗口居中位置
        window_geometry.moveCenter(screen_geometry.center())
        # 设置窗口位置
        self.move(window_geometry.topLeft())
        
        layout = QVBoxLayout(self)
        
        # 提示信息
        info_label = QLabel("请按照以下步骤操作：\n")
        info_label.setAlignment(Qt.AlignLeft)
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        steps = [
            "1. 打开智控台",
            "2. 使用管理员账号登录",
            "3. 进入【参数管理】->【参数字典】页面",
            "4. 找到【server.secret】参数",
            "5. 复制其参数值",
            "6. 将复制的值粘贴到下方输入框中，或者点击【从剪贴板粘贴密钥】按钮一键粘贴。"
        ]
        
        steps_text = "<br>".join(steps)
        steps_label = QLabel(f"<div style='margin-left: 20px;'>{steps_text}</div>")
        steps_label.setAlignment(Qt.AlignLeft)
        steps_label.setWordWrap(True)
        layout.addWidget(steps_label)
        
        # 密钥输入框
        secret_layout = QHBoxLayout()
        secret_label = QLabel("服务器密钥：")
        self.secret_input = QLineEdit()
        self.secret_input.setPlaceholderText("请在此输入server.secret值")
        self.secret_input.setMinimumWidth(350)
        secret_layout.addWidget(secret_label)
        secret_layout.addWidget(self.secret_input)
        layout.addLayout(secret_layout)
        
        # 功能按钮布局
        function_layout = QHBoxLayout()
        self.open_dashboard_button = QPushButton("一键打开智控台")
        self.paste_button = QPushButton("从剪贴板粘贴密钥")
        
        function_layout.addWidget(self.open_dashboard_button)
        function_layout.addWidget(self.paste_button)
        layout.addLayout(function_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("取消")
        self.ok_button = QPushButton("确定")
        self.ok_button.setEnabled(False)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)
        
        # 信号连接
        self.secret_input.textChanged.connect(self.validate_secret)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.open_dashboard_button.clicked.connect(self.open_dashboard)
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        
        self.server_secret = None
    
    def validate_secret(self):
        secret = self.secret_input.text().strip()
        self.ok_button.setEnabled(len(secret) > 0)
    
    def accept(self):
        secret = self.secret_input.text().strip()
        
        if not secret:
            QMessageBox.warning(self, "警告", "服务器密钥不能为空！")
            return
        
        # 常见的UUID格式正则模式（简化版）
        uuid_pattern = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.IGNORECASE)
        
        # 检查是否看起来像有效的UUID格式（大多数secret是UUID格式）
        if not uuid_pattern.match(secret) and len(secret) < 16:
            reply = QMessageBox.question(
                self, "格式警告", "输入的密钥看起来可能不是有效的server.secret格式，是否确认使用？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self.server_secret = secret
        super().accept()

    def open_dashboard(self):
        """打开智控台页面"""
        url = QUrl("http://localhost:8001/#/params-management")
        QDesktopServices.openUrl(url)
        # QMessageBox.information(self, "提示", "已尝试打开智控台页面，请确保服务已启动")

    def paste_from_clipboard(self):
        """从剪贴板粘贴密钥到输入框"""
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text().strip()
        if clipboard_text:
            self.secret_input.setText(clipboard_text)
            # QMessageBox.information(self, "提示", "已从剪贴板粘贴密钥")
        else:
            QMessageBox.warning(self, "警告", "剪贴板中没有文本内容")

    def get_server_secret(self):
        return self.server_secret

class UpgradeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置文件升级提示")
        self.setFixedSize(500, 300)
        self.setWindowModality(Qt.ApplicationModal)
        # 设置窗口置顶，并且只保留最小化和关闭按钮
        self.setWindowFlags(
            Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint
        )
        # 设置窗口居中显示
        self.center()
        
    def center(self):
        # 获取屏幕几何信息
        screen_geometry = QApplication.primaryScreen().geometry()
        # 获取窗口几何信息
        window_geometry = self.frameGeometry()
        # 计算窗口居中位置
        window_geometry.moveCenter(screen_geometry.center())
        # 设置窗口位置
        self.move(window_geometry.topLeft())
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("配置文件升级提示")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # 提示信息
        info_text = [
            "检测到你的配置文件可能是单模块版服务端配置",
            "升级到全模块版服务端可以获得更多功能支持",
            "",
            "重要提示：",
            "  - 升级后，原有的配置数据不会自动同步",
            "  - 你需要在新的配置文件中手动设置相关参数",
            "  - 升级前会自动备份当前配置文件变为 <原文件名>.old"
        ]
        
        info_label = QLabel("\n".join(info_text))
        info_label.setAlignment(Qt.AlignLeft)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("margin-bottom: 20px;")
        layout.addWidget(info_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("取消升级")
        self.upgrade_button = QPushButton("确认升级")
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.upgrade_button)
        layout.addLayout(button_layout)
        
        # 信号连接
        self.upgrade_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        self.perform_upgrade = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小智服务端配置文件初始化工具")
        self.setGeometry(100, 100, 800, 600)
        # 设置窗口置顶，并且只保留最小化和关闭按钮
        self.setWindowFlags(
            Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint
        )
        # 设置窗口居中显示
        self.center()
        
    def center(self):
        # 获取屏幕几何信息
        screen_geometry = QApplication.primaryScreen().geometry()
        # 获取窗口几何信息
        window_geometry = self.frameGeometry()
        # 计算窗口居中位置
        window_geometry.moveCenter(screen_geometry.center())
        # 设置窗口位置
        self.move(window_geometry.topLeft())
        
        # 获取脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建项目根目录路径 (根据目录结构，上一级目录即为项目根目录)
        self.project_root = os.path.abspath(os.path.join(script_dir, '..'))
        # 动态定义文件路径
        self.config_path = os.path.join(self.project_root, 'src', 'main', 'xiaozhi-server', 'data', '.config.yaml')
        self.config_source_path = os.path.join(self.project_root, 'src', 'main', 'xiaozhi-server', 'config_from_api.yaml')
        
        self.init_ui()
        self.init_worker()
        self.start_config_check()

    def init_ui(self):
        # 主窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部信息区域
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        info_layout = QGridLayout(info_frame)
        
        config_path_label = QLabel("配置文件路径：")
        config_path_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        config_path_value = QLabel(self.config_path)
        config_path_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        config_path_value.setWordWrap(True)
        
        config_source_label = QLabel("配置源文件路径：")
        config_source_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        config_source_value = QLabel(self.config_source_path)
        config_source_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        config_source_value.setWordWrap(True)
        
        info_layout.addWidget(config_path_label, 0, 0)
        info_layout.addWidget(config_path_value, 0, 1)
        info_layout.addWidget(config_source_label, 1, 0)
        info_layout.addWidget(config_source_value, 1, 1)
        
        info_layout.setColumnStretch(1, 1)
        
        main_layout.addWidget(info_frame)
        
        # 日志显示区域
        log_label = QLabel("执行日志：")
        log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 10))
        self.log_text.setStyleSheet("background-color: #f8f8f8;")
        main_layout.addWidget(self.log_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始配置")
        self.start_button.setStyleSheet("font-weight: bold; padding: 8px 20px;")
        
        self.update_secret_button = QPushButton("更新服务器密钥")
        self.update_secret_button.setStyleSheet("padding: 8px 20px;")
        
        self.close_button = QPushButton("关闭")
        self.close_button.setStyleSheet("padding: 8px 20px;")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.update_secret_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        # 底部状态区域
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label.setStyleSheet("margin-top: 5px;")
        main_layout.addWidget(self.status_label)
        
        # 信号连接
        self.start_button.clicked.connect(self.start_config_check)
        self.update_secret_button.clicked.connect(self.manual_secret_update)
        self.close_button.clicked.connect(self.close)

    def init_worker(self):
        self.worker = ConfigWorker(self.project_root, self.config_path, self.config_source_path)
        
        # 信号连接
        self.worker.log_signal.connect(self.append_log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_config_finished)
        self.worker.secret_required_signal.connect(self.request_server_secret)
        self.worker.upgrade_required_signal.connect(self.request_upgrade_confirmation)
        self.worker.secret_confirm_required_signal.connect(self.request_secret_update_confirmation)

    def start_config_check(self):
        self.clear_log()
        self.update_status("正在检查配置文件...")
        self.start_button.setEnabled(False)
        self.worker.start()

    def append_log(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def clear_log(self):
        self.log_text.clear()

    def update_status(self, status):
        self.status_label.setText(status)

    def request_server_secret(self):
        """显示密钥配置对话框，隐藏主窗口"""
        self.hide()  # 隐藏主窗口
        try:
            dialog = SecretInputDialog(self)
            if dialog.exec() == QDialog.Accepted:
                secret = dialog.get_server_secret()
                if secret:
                    self.worker.server_secret = secret
                    self.worker.log(f"✅ 服务器密钥已成功获取（长度: {len(secret)} 字符）")
                    self.continue_config_after_secret()
        finally:
            self.show()  # 确保主窗口始终会被显示

    def request_upgrade_confirmation(self):
        """显示升级对话框，隐藏主窗口"""
        self.hide()  # 隐藏主窗口
        try:
            dialog = UpgradeDialog(self)
            if dialog.exec() == QDialog.Accepted:
                self.worker.perform_upgrade = True
                self.continue_config_after_upgrade()
            else:
                self.worker.log("已取消升级操作")
                self.update_status("配置检查完成，未进行升级")
                self.start_button.setEnabled(True)
        finally:
            self.show()  # 确保主窗口始终会被显示

    def request_secret_update_confirmation(self, current_secret):
        reply = QMessageBox.question(
            self, "更新服务器密钥", 
            f"当前服务器密钥：{current_secret}\n\n是否需要更新配置文件中的server.secret?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.request_server_secret()
        else:
            self.worker.log("\n✅ 配置检查完成，保持当前配置不变")
            self.update_status("配置检查完成，保持当前配置不变")
            self.start_button.setEnabled(True)

    def continue_config_after_secret(self):
        # 更新配置文件中的服务器密钥
        if self.worker.update_server_secret(self.config_path, self.worker.server_secret):
            # 成功更新密钥后创建标记文件
            self.worker.create_config_success_marker(self.project_root)
            self.worker.log("\n🎉 配置文件初始化完成！")
            self.update_status("配置文件初始化完成")
        else:
            self.worker.log("\n❌ 服务器密钥更新失败")
            self.update_status("服务器密钥更新失败")
        self.start_button.setEnabled(True)
        
    def continue_config_after_upgrade(self):
        # 备份并替换配置
        if self.worker.backup_and_replace_config(self.config_path, self.config_source_path, self.config_path):
            # 获取并更新server.secret
            self.hide()  # 隐藏主窗口
            try:
                dialog = SecretInputDialog(self)
                if dialog.exec() == QDialog.Accepted:
                    secret = dialog.get_server_secret()
                    if secret:
                        if self.worker.update_server_secret(self.config_path, secret):
                            # 成功更新密钥后创建标记文件
                            self.worker.create_config_success_marker(self.project_root)
                            self.worker.log("\n🎉 配置文件初始化完成！")
                            self.update_status("配置文件初始化完成")
                        else:
                            self.worker.log("\n❌ 服务器密钥更新失败")
                            self.update_status("服务器密钥更新失败")
                    else:
                        self.worker.log("\n❌ 未提供服务器密钥")
                        self.update_status("未提供服务器密钥")
                else:
                    self.worker.log("\n❌ 已取消服务器密钥配置")
                    self.update_status("已取消服务器密钥配置")
            finally:
                self.show()  # 确保主窗口始终会被显示
        else:
            self.worker.log("\n❌ 配置文件升级失败")
            self.update_status("配置文件升级失败")
        self.start_button.setEnabled(True)

    def manual_secret_update(self):
        self.hide()  # 隐藏主窗口
        try:
            dialog = SecretInputDialog(self)
            if dialog.exec() == QDialog.Accepted:
                secret = dialog.get_server_secret()
                if secret:
                    self.clear_log()
                    self.update_status("正在更新服务器密钥...")
                    self.start_button.setEnabled(False)
                    self.worker.log("🔄 正在更新服务器密钥...")
                    
                    if self.worker.update_server_secret(self.config_path, secret):
                        # 成功更新密钥后创建标记文件
                        self.worker.create_config_success_marker(self.project_root)
                        self.worker.log("\n🎉 服务器密钥更新完成！")
                        self.update_status("服务器密钥更新完成")
                    else:
                        self.worker.log("\n❌ 服务器密钥更新失败")
                        self.update_status("服务器密钥更新失败")
                    
                    self.start_button.setEnabled(True)
        finally:
            self.show()  # 确保主窗口始终会被显示

    def on_config_finished(self, success, message):
        self.start_button.setEnabled(True)
        if success:
            self.update_status("配置完成：" + message)
        else:
            self.update_status("配置失败：" + message)

    def closeEvent(self, event):
        if self.worker.isRunning():
            reply = QMessageBox.question(
                self, "退出确认", 
                "配置检查正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())