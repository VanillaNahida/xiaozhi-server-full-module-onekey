# -*- coding: utf-8 -*-
import os
import sys
import re
import traceback
from ruamel.yaml import YAML

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QFileDialog, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

class MySQLConfigWorker(QThread):
    log_signal = Signal(str)
    status_signal = Signal(str)
    finished_signal = Signal(bool, str)
    password_updated_signal = Signal(bool, str)
    datadir_updated_signal = Signal(bool, str)
    username_updated_signal = Signal(bool, str)

    def __init__(self, project_root, config_path, my_ini_path):
        super().__init__()
        self.project_root = project_root
        self.config_path = config_path
        self.my_ini_path = my_ini_path
        self.new_password = None
        self.new_datadir = None
        self.new_username = None
        self.update_password = False
        self.update_datadir = False
        self.update_username = False

    def run(self):
        try:
            if self.update_username and self.new_username:
                self.update_mysql_username(self.new_username)
            
            if self.update_password and self.new_password:
                self.update_mysql_password(self.new_password)
                self.username_updated_signal.emit(True, "MySQL账号密码更新成功！")
            
            if self.update_datadir and self.new_datadir:
                self.update_mysql_datadir(self.new_datadir)
            
            self.finished_signal.emit(True, "配置更新完成")
        except Exception as e:
            self.log_signal.emit(f"❌ 配置更新过程中发生错误: {str(e)}")
            self.log_signal.emit(traceback.format_exc())
            self.finished_signal.emit(False, f"发生错误: {str(e)}")

    def log(self, message):
        self.log_signal.emit(message)

    def update_mysql_username(self, new_username):
        """
        更新配置文件中的MySQL账号
        """
        try:
            self.log(f"正在更新MySQL账号: {self.config_path}...")
            
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.indent(mapping=2, sequence=4, offset=2)
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.load(f)
            
            if config and 'spring' in config and 'datasource' in config['spring'] and 'druid' in config['spring']['datasource']:
                config['spring']['datasource']['druid']['username'] = new_username
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f)
                
                self.log(f"✅ MySQL账号已成功更新")
            else:
                raise Exception("配置文件格式不正确，无法更新MySQL账号")
        except Exception as e:
            self.log(f"❌ 更新MySQL账号失败: {str(e)}")
            self.username_updated_signal.emit(False, f"更新MySQL账号失败: {str(e)}")
            raise

    def update_mysql_password(self, new_password):
        """
        更新配置文件中的MySQL密码
        """
        try:
            self.log(f"正在更新MySQL密码: {self.config_path}...")
            
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.indent(mapping=2, sequence=4, offset=2)
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.load(f)
            
            if config and 'spring' in config and 'datasource' in config['spring'] and 'druid' in config['spring']['datasource']:
                config['spring']['datasource']['druid']['password'] = new_password
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f)
                
                self.log(f"✅ MySQL密码已成功更新")
            else:
                raise Exception("配置文件格式不正确，无法更新MySQL密码")
        except Exception as e:
            self.log(f"❌ 更新MySQL密码失败: {str(e)}")
            self.password_updated_signal.emit(False, f"更新MySQL密码失败: {str(e)}")
            raise

    def update_mysql_datadir(self, new_datadir):
        """
        更新my.ini文件中的datadir路径
        """
        try:
            self.log(f"正在更新MySQL数据目录: {self.my_ini_path}...")
            
            if not os.path.exists(self.my_ini_path):
                raise Exception(f"my.ini文件不存在: {self.my_ini_path}")
            
            with open(self.my_ini_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith('datadir='):
                    indent = len(line) - len(line.lstrip())
                    lines[i] = ' ' * indent + f'datadir={new_datadir}\n'
                    updated = True
                    break
            
            if not updated:
                raise Exception("未找到datadir配置项")
            
            with open(self.my_ini_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            self.log(f"✅ MySQL数据目录已成功更新为: {new_datadir}")
            self.datadir_updated_signal.emit(True, "MySQL数据目录更新成功")
        except Exception as e:
            self.log(f"❌ 更新MySQL数据目录失败: {str(e)}")
            self.datadir_updated_signal.emit(False, f"更新MySQL数据目录失败: {str(e)}")
            raise

class MySQLConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MySQL配置修改工具")
        self.setFixedSize(600, 550)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(
            Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint
        )
        self.center()
        
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.config_path = os.path.join(self.project_root, "src", "main", "manager-api", "src", "main", "resources", "application-dev.yml")
        self.my_ini_path = os.path.join(self.project_root, "runtime", "mysql-8.4.7", "my.ini")
        
        self.worker = None
        self.init_ui()
        self.load_current_config()

    def center(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("MySQL配置修改工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        password_group = QGroupBox("MySQL账号密码配置")
        password_layout = QGridLayout()
        
        username_label = QLabel("当前账号:")
        self.current_username_label = QLineEdit()
        self.current_username_label.setReadOnly(True)
        self.current_username_label.setStyleSheet("color: #666; background-color: #f5f5f5;")
        password_layout.addWidget(username_label, 0, 0)
        password_layout.addWidget(self.current_username_label, 0, 1)
        
        new_username_label = QLabel("新账号:")
        self.new_username_input = QLineEdit()
        self.new_username_input.setPlaceholderText("请输入新的MySQL账号")
        password_layout.addWidget(new_username_label, 1, 0)
        password_layout.addWidget(self.new_username_input, 1, 1)
        
        password_label = QLabel("当前密码:")
        self.current_password_label = QLineEdit()
        self.current_password_label.setReadOnly(True)
        self.current_password_label.setStyleSheet("color: #666; background-color: #f5f5f5;")
        password_layout.addWidget(password_label, 2, 0)
        password_layout.addWidget(self.current_password_label, 2, 1)
        
        new_password_label = QLabel("新密码:")
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("请输入新的MySQL密码")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(new_password_label, 3, 0)
        password_layout.addWidget(self.new_password_input, 3, 1)
        
        self.auto_fill_button = QPushButton("一键填充MySQL密码")
        self.auto_fill_button.setMinimumHeight(30)
        self.auto_fill_button.clicked.connect(self.auto_fill_mysql_password)
        password_layout.addWidget(self.auto_fill_button, 4, 0, 1, 2)
        
        self.save_password_button = QPushButton("保存账号密码")
        self.save_password_button.setMinimumHeight(30)
        self.save_password_button.clicked.connect(self.save_account)
        password_layout.addWidget(self.save_password_button, 5, 0, 1, 2)
        
        password_group.setLayout(password_layout)
        main_layout.addWidget(password_group)
        
        datadir_group = QGroupBox("MySQL数据目录配置")
        datadir_layout = QGridLayout()
        
        current_datadir_label = QLabel("当前路径:")
        self.current_datadir_label = QLineEdit()
        self.current_datadir_label.setReadOnly(True)
        self.current_datadir_label.setStyleSheet("color: #666; background-color: #f5f5f5;")
        datadir_layout.addWidget(current_datadir_label, 0, 0)
        datadir_layout.addWidget(self.current_datadir_label, 0, 1)
        
        new_datadir_label = QLabel("新路径:")
        self.new_datadir_input = QLineEdit()
        self.new_datadir_input.setPlaceholderText("请输入新的MySQL数据目录路径")
        datadir_layout.addWidget(new_datadir_label, 1, 0)
        datadir_layout.addWidget(self.new_datadir_input, 1, 1)
        
        browse_button = QPushButton("浏览...")
        browse_button.setMinimumHeight(30)
        browse_button.clicked.connect(self.browse_datadir)
        datadir_layout.addWidget(browse_button, 1, 2)
        
        self.auto_set_button = QPushButton("一键设置为当前路径")
        self.auto_set_button.setMinimumHeight(30)
        self.auto_set_button.clicked.connect(self.auto_set_current_path)
        datadir_layout.addWidget(self.auto_set_button, 2, 0, 1, 3)
        
        self.save_datadir_button = QPushButton("保存数据目录")
        self.save_datadir_button.setMinimumHeight(30)
        self.save_datadir_button.clicked.connect(self.save_datadir)
        datadir_layout.addWidget(self.save_datadir_button, 3, 0, 1, 3)
        
        datadir_group.setLayout(datadir_layout)
        main_layout.addWidget(datadir_group)
        
        main_layout.addStretch()
        
        self.save_all_button = QPushButton("保存全部配置")
        self.save_all_button.setStyleSheet("font-size: 14px; font-weight: bold; padding: 1px;")
        self.save_all_button.setMinimumHeight(35)
        self.save_all_button.clicked.connect(self.save_all)
        main_layout.addWidget(self.save_all_button)

    def load_current_config(self):
        try:
            yaml = YAML()
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.load(f)
            
            if config and 'spring' in config and 'datasource' in config['spring'] and 'druid' in config['spring']['datasource']:
                current_username = config['spring']['datasource']['druid'].get('username', '')
                self.current_username_label.setText(str(current_username))
                current_password = config['spring']['datasource']['druid'].get('password', '')
                self.current_password_label.setText(str(current_password))
            
            if os.path.exists(self.my_ini_path):
                with open(self.my_ini_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('datadir='):
                            current_datadir = line.split('=', 1)[1].strip()
                            self.current_datadir_label.setText(str(current_datadir))
                            break
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载配置失败: {str(e)}")

    def browse_datadir(self):
        datadir = QFileDialog.getExistingDirectory(self, "选择MySQL数据目录")
        if datadir:
            self.new_datadir_input.setText(datadir.replace('\\', '\\\\'))

    def auto_set_current_path(self):
        current_path = os.path.join(self.project_root, 'data', 'mysql')
        self.new_datadir_input.setText(current_path.replace('\\', '\\\\'))
        QMessageBox.information(self, "提示", f"已自动设置为当前路径:\n{current_path}")

    def auto_fill_mysql_password(self):
        """
        从MySQL密码.txt文件中读取账号密码并自动填充
        """
        password_file_path = os.path.join(self.project_root, 'MySQL密码.txt')
        
        try:
            if not os.path.exists(password_file_path):
                raise FileNotFoundError("MySQL密码.txt文件不存在")
            
            with open(password_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                raise ValueError("MySQL密码.txt文件格式不正确，至少需要两行")
            
            username_line = lines[0].strip()
            password_line = lines[1].strip()
            
            if ':' not in username_line or ':' not in password_line:
                raise ValueError("MySQL密码.txt文件格式不正确，每行应包含':'分隔符")
            
            username = username_line.split(':', 1)[1].strip()
            password = password_line.split(':', 1)[1].strip()
            
            self.new_username_input.setText(username)
            self.new_password_input.setText(password)
            
            QMessageBox.information(self, "成功", f"已自动填充MySQL账号和密码\n\n账号: {username}\n密码: {password}")
            
        except Exception as e:
            QMessageBox.warning(self, "警告", "无法自动填写MySQL账号密码。\n请确认项目根目录是否存在“MySQL密码.txt”文件，或者txt文件内格式正确？")

    def save_account(self):
        new_username = self.new_username_input.text().strip()
        new_password = self.new_password_input.text().strip()
        
        if not new_username and not new_password:
            QMessageBox.warning(self, "警告", "新账号或新密码不能为空！")
            return
        
        confirm_message = "确定要将MySQL账号密码修改为:\n\n"
        if new_username:
            confirm_message += f"账号: {new_username}\n"
        if new_password:
            confirm_message += f"密码: {new_password}\n"
        
        reply = QMessageBox.question(
            self, "确认", 
            confirm_message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.worker = MySQLConfigWorker(self.project_root, self.config_path, self.my_ini_path)
            if new_username:
                self.worker.new_username = new_username
                self.worker.update_username = True
            if new_password:
                self.worker.new_password = new_password
                self.worker.update_password = True
            
            self.worker.username_updated_signal.connect(self.on_account_updated)
            self.worker.password_updated_signal.connect(self.on_account_updated)
            self.worker.start()

    def on_account_updated(self, success, message):
        if success:
            QMessageBox.information(self, "成功", message)
            self.load_current_config()
            self.new_username_input.clear()
            self.new_password_input.clear()
        else:
            QMessageBox.critical(self, "错误", message)

    def save_datadir(self):
        new_datadir = self.new_datadir_input.text().strip()
        if not new_datadir:
            QMessageBox.warning(self, "警告", "新路径不能为空！")
            return
        
        reply = QMessageBox.question(
            self, "确认", 
            f"确定要将MySQL数据目录修改为:\n{new_datadir} 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.worker = MySQLConfigWorker(self.project_root, self.config_path, self.my_ini_path)
            self.worker.new_datadir = new_datadir
            self.worker.update_datadir = True
            self.worker.datadir_updated_signal.connect(self.on_datadir_updated)
            self.worker.start()

    def on_datadir_updated(self, success, message):
        if success:
            QMessageBox.information(self, "成功", message)
            self.current_datadir_label.setText(self.new_datadir_input.text())
            self.new_datadir_input.clear()
        else:
            QMessageBox.critical(self, "错误", message)

    def save_all(self):
        new_username = self.new_username_input.text().strip()
        new_password = self.new_password_input.text().strip()
        new_datadir = self.new_datadir_input.text().strip()
        
        if not new_username and not new_password and not new_datadir:
            QMessageBox.warning(self, "警告", "没有需要保存的配置！")
            return
        
        confirm_message = "确定要保存以下配置?\n\n"
        if new_username:
            confirm_message += f"MySQL账号: {new_username}\n"
        if new_password:
            confirm_message += f"MySQL密码: {new_password}\n"
        if new_datadir:
            confirm_message += f"MySQL数据目录: {new_datadir}\n"
        
        reply = QMessageBox.question(
            self, "确认保存全部配置", 
            confirm_message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.worker = MySQLConfigWorker(self.project_root, self.config_path, self.my_ini_path)
            if new_username:
                self.worker.new_username = new_username
                self.worker.update_username = True
            if new_password:
                self.worker.new_password = new_password
                self.worker.update_password = True
            if new_datadir:
                self.worker.new_datadir = new_datadir
                self.worker.update_datadir = True
            
            self.worker.finished_signal.connect(self.on_all_saved)
            self.worker.start()

    def on_all_saved(self, success, message):
        if success:
            QMessageBox.information(self, "成功", message)
            self.load_current_config()
            self.new_username_input.clear()
            self.new_password_input.clear()
            self.new_datadir_input.clear()
        else:
            QMessageBox.critical(self, "错误", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MySQLConfigWindow()
    window.show()
    sys.exit(app.exec())
