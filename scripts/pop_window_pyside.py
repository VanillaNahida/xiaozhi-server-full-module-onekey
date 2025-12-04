import re
import json
import os
import sys
import requests
import subprocess
import webbrowser
from datetime import datetime, timedelta

# 导入PySide6，如果报错则安装
try:
    from PySide6 import QtWidgets, QtGui, QtCore
except ImportError:
    print("PySide6未安装，正在尝试安装...")
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PySide6"])
        print("PySide6安装成功！")
    except subprocess.CalledProcessError:
        print("PySide6安装失败！")


from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                              QWidget, QTextEdit, QPushButton, QCheckBox, QMessageBox,
                              QScrollArea, QLabel, QFrame, QDialog)
from PySide6.QtCore import Qt, QTimer, QUrl, QPoint
from PySide6.QtGui import (QFont, QCursor, QDesktopServices, QTextCursor, 
                          QTextCharFormat, QColor, QMouseEvent)
# GitHub仓库信息
GITHUB_REPO_OWNER = "VanillaNahida"
GITHUB_REPO_NAME = "xiaozhi-server-full-module-onekey"
# 本地存储文件路径，用于记录用户查看状态
STATE_FILE = "./data/release_check_state.json"

class ClickableTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
        """)
        
        # 存储链接位置信息
        self.links = []
        
    def setTextWithLinks(self, text):
        """设置文本并标记链接"""
        self.setPlainText(text)
        self.highlight_links(text)
    
    def highlight_links(self, text):
        """高亮文本中的所有链接"""
        # 清除之前的链接信息
        self.links = []
        
        # 更严格的链接匹配正则表达式
        # 匹配纯URL：http://或https://开头的完整URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]()]+[^\s<>"{}|\\^`\[\]().,!?]'
        
        # 匹配Markdown格式的链接：[描述](URL)
        markdown_link_pattern = r'\[([^\]]+)\]\(((https?://[^\s<>"{}|\\^`\[\]()]+[^\s<>"{}|\\^`\[\]().,!?])|([^)]+))\)'
        
        # 创建链接格式
        link_format = QTextCharFormat()
        link_format.setForeground(QColor(0, 0, 255))  # 蓝色
        link_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        # 先处理Markdown格式的链接
        markdown_matches = list(re.finditer(markdown_link_pattern, text))
        for match in markdown_matches:
            full_match = match.group(0)  # 整个匹配，如 [描述](URL)
            link_text = match.group(1)  # 链接文本，如 "描述"
            url = match.group(2)        # 实际URL
            
            # 只处理以http://或https://开头的有效URL
            if url.startswith(('http://', 'https://')):
                start = match.start()
                # Markdown链接的显示文本是从 [ 到 ] 的部分
                link_text_start = start + 1  # 跳过 [
                link_text_end = link_text_start + len(link_text)
                
                # 保存链接位置信息（指向显示文本部分）
                self.links.append({
                    'url': url,
                    'start': link_text_start,
                    'end': link_text_end,
                    'type': 'markdown'
                })
                
                # 高亮显示文本部分（不包括方括号）
                cursor.setPosition(link_text_start)
                cursor.setPosition(link_text_end, QTextCursor.KeepAnchor)
                cursor.setCharFormat(link_format)
        
        # 然后处理纯URL链接（但要排除已经在Markdown链接中的URL）
        url_matches = list(re.finditer(url_pattern, text))
        excluded_ranges = []
        
        # 收集Markdown链接中URL的位置范围，避免重复处理
        for match in markdown_matches:
            url_match = match.group(2)
            url_start = text.find(url_match, match.start())
            if url_start != -1:
                excluded_ranges.append((url_start, url_start + len(url_match)))
        
        for match in url_matches:
            url = match.group(0)
            start = match.start()
            end = match.end()
            
            # 检查这个URL是否已经在Markdown链接中被处理过
            is_excluded = False
            for excluded_start, excluded_end in excluded_ranges:
                if start >= excluded_start and end <= excluded_end:
                    is_excluded = True
                    break
            
            if not is_excluded:
                # 保存纯URL链接位置信息
                self.links.append({
                    'url': url,
                    'start': start,
                    'end': end,
                    'type': 'plain'
                })
                
                # 高亮纯URL
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                cursor.setCharFormat(link_format)
        
        # 重置光标位置
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.Start)
        self.setTextCursor(cursor)
    
    def get_link_at_position(self, pos):
        """获取指定位置的链接"""
        cursor = self.cursorForPosition(pos)
        position = cursor.position()
        
        # 按起始位置排序，优先匹配较长的链接
        sorted_links = sorted(self.links, key=lambda x: x['start'])
        
        for link in sorted_links:
            if link['start'] <= position < link['end']:
                return link['url']
        return None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 使用position()替代已弃用的pos()
            if hasattr(event, 'position'):
                pos = event.position().toPoint()
            else:
                # 兼容旧版本
                pos = event.pos()
            
            url = self.get_link_at_position(pos)
            if url:
                QDesktopServices.openUrl(QUrl(url))
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        # 使用position()替代已弃用的pos()
        if hasattr(event, 'position'):
            pos = event.position().toPoint()
        else:
            # 兼容旧版本
            pos = event.pos()
        
        url = self.get_link_at_position(pos)
        
        if url:
            self.viewport().setCursor(QCursor(Qt.PointingHandCursor))
        else:
            self.viewport().setCursor(QCursor(Qt.IBeamCursor))
        
        super().mouseMoveEvent(event)

class GitHubReleaseChecker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.latest_release = {}
        self.popup_result = False
        
        self.setWindowTitle("小智AI全模块服务端一键包 - 正在获取更新信息...")
        self.setMinimumSize(800, 600)
        
        # 设置窗口标志：置顶
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 创建UI
        self.create_widgets()
        self.create_layouts()
        
        # 居中显示
        self.center_window()
        
        # 获取GitHub最新Release信息
        self.fetch_latest_release()
    
    def create_widgets(self):
        # 创建文本显示区域
        self.text_edit = ClickableTextEdit()
        self.text_edit.setFont(QFont("Microsoft YaHei UI", 13))
        
        # 创建复选框
        self.no_today_checkbox = QCheckBox("今日内不再提示")
        self.no_today_checkbox.setFont(QFont("Microsoft YaHei UI", 10))
        
        # 创建按钮
        self.update_now_button = QPushButton("立即更新")
        self.update_now_button.setFont(QFont("Microsoft YaHei UI", 13))
        self.update_now_button.setMinimumHeight(40)
        self.update_now_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        self.skip_update_button = QPushButton("暂不更新")
        self.skip_update_button.setFont(QFont("Microsoft YaHei UI", 13))
        self.skip_update_button.setMinimumHeight(40)
        self.skip_update_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c41408;
            }
        """)
        
        # 连接信号
        self.update_now_button.clicked.connect(self.on_update_now)
        self.skip_update_button.clicked.connect(self.on_skip_update)
    
    def create_layouts(self):
        main_layout = QVBoxLayout(self)
        
        # 文本区域
        main_layout.addWidget(self.text_edit)
        
        # 底部区域
        bottom_layout = QHBoxLayout()
        
        # 左侧：复选框
        bottom_layout.addWidget(self.no_today_checkbox)
        
        # 中间：弹性空间
        bottom_layout.addStretch()
        
        # 右侧：按钮
        bottom_layout.addWidget(self.update_now_button)
        bottom_layout.addWidget(self.skip_update_button)
        
        main_layout.addLayout(bottom_layout)
    
    def fetch_latest_release(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
            response = requests.get(url)
            response.raise_for_status()
            
            release_data = response.json()
            self.latest_release = release_data
            
            if 'tag_name' in release_data:
                self.setWindowTitle(f"小智AI全模块服务端一键包 - 发现新版本！{release_data['tag_name']}")
            
            release_text = self.format_release_info(release_data)
            self.display_release_info(release_text)
            
        except requests.exceptions.RequestException as e:
            error_message = f"获取信息失败:\n{e}"
            self.setWindowTitle("小智AI全模块服务端一键包 - 获取更新信息失败！")
            self.display_release_info(error_message)
        except Exception as e:
            error_message = f"程序运行出错:\n{str(e)}"
            self.display_release_info(error_message)
    
    def format_release_info(self, release_data):
        tag_name = release_data.get("tag_name", "未知版本")
        name = release_data.get("name", "无标题")
        body = release_data.get("body", "无更新说明")
        published_at = release_data.get("published_at", "")
        html_url = release_data.get("html_url", "")
        
        if published_at:
            published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            # 转换为北京时间（UTC+8）
            beijing_date = published_date + timedelta(hours=8)
            local_date = beijing_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            local_date = "未知"
        
        release_info = f"【新版本发布】{name}\n"
        release_info += f"版本号: {tag_name}\n"
        release_info += f"发布时间: {local_date}\n"
        if html_url:
            release_info += f"查看详情: {html_url}\n\n"
        release_info += "【更新内容】\n"
        release_info += body
        
        return release_info
    
    def display_release_info(self, text):
        # 使用新的方法设置文本并高亮链接
        self.text_edit.setTextWithLinks(text)
        # 滚动到顶部
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.text_edit.setTextCursor(cursor)
    
    def on_update_now(self):
        self.popup_result = True

        # 获取项目根目录并构建路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_exe = os.path.join(project_root, "runtime", "conda_env", "python.exe")
        update_script = os.path.join(project_root, "scripts", "update_onekey_pack.py")
        
        # 启动更新脚本
        cmd = rf'start "小智AI服务端更新脚本" "{python_exe}" "{update_script}" --auto_update'
        subprocess.Popen(cmd, cwd=os.path.join(project_root, "scripts"), shell=True)
        
        # 如果勾选了今日内不再提示，保存状态
        if self.no_today_checkbox.isChecked():
            self.save_state()
        
        self.accept()
    
    def on_skip_update(self):
        self.popup_result = False
        
        # 如果勾选了今日内不再提示，保存状态
        if self.no_today_checkbox.isChecked():
            self.save_state()
        
        self.reject()
    
    def center_window(self):
        # 获取屏幕几何信息
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        
        # 计算居中位置
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        
        self.move(x, y)
    
    def save_state(self):
        try:
            state = {
                "last_view_date": datetime.now().isoformat()
            }
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f)
        except Exception:
            pass
    
    @property
    def result(self):
        return self.popup_result

class PopupWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.popup_result = False
        self.countdown_seconds = 20
        self.countdown_active = True
        
        self.setWindowTitle("小智AI一键包 By：香草味的纳西妲喵 - 必看说明")
        self.setMinimumSize(1024, 768)
        
        # 创建UI
        self.create_widgets()
        self.create_layouts()
        
        # 居中显示
        self.center_window()
        
        # 启动倒计时
        self.start_countdown()
    
    def create_widgets(self):
        # 创建文本显示区域
        self.text_edit = ClickableTextEdit()
        self.text_edit.setFont(QFont("Microsoft YaHei", 12))
        
        # 添加文本内容
        self.add_text_content()
        
        # 创建按钮
        self.confirm_button = QPushButton(f"请看提示({self.countdown_seconds}s)")
        self.confirm_button.setFont(QFont("Microsoft YaHei", 12))
        self.confirm_button.setMinimumHeight(40)
        self.confirm_button.setEnabled(False)
        self.confirm_button.setStyleSheet("""
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover:enabled {
                background-color: #45a049;
            }
            QPushButton:pressed:enabled {
                background-color: #3d8b40;
            }
        """)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFont(QFont("Microsoft YaHei", 12))
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c41408;
            }
        """)
        
        # 连接信号
        self.confirm_button.clicked.connect(self.on_confirm)
        self.cancel_button.clicked.connect(self.on_cancel)
    
    def create_layouts(self):
        main_layout = QVBoxLayout(self)
        
        # 文本区域
        main_layout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def add_text_content(self):
        content = self.get_readme_content()
        # 使用新的方法设置文本并高亮链接
        self.text_edit.setTextWithLinks(content)
    
    def get_readme_content(self):
        try:
            with open("必看说明.txt", "r", encoding="utf-8") as file:
                return file.read()
        except Exception:
            return "无法读取必看说明文件，请确保文件存在且格式正确。"
    
    def on_confirm(self):
        if not self.is_scrolled_to_bottom():
            self.show_warning()
            return
        
        # 创建data目录并写入确认文件
        os.makedirs("./data", exist_ok=True)
        with open("./data/.is_first_run", "w") as f:
            f.write("yes")
        
        self.popup_result = True
        self.accept()
    
    def is_scrolled_to_bottom(self):
        scrollbar = self.text_edit.verticalScrollBar()
        return scrollbar.value() >= scrollbar.maximum() * 0.98
    
    def show_warning(self):
        QMessageBox.warning(self, "警告", 
                           "请先阅读完本提示信息！\n看到这个提示说明你没完全阅读完本提示！（滚动条不在最底下）")
    
    def on_cancel(self):
        self.popup_result = False
        self.reject()
    
    def start_countdown(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
    
    def update_countdown(self):
        if self.countdown_active and self.countdown_seconds > 0:
            self.countdown_seconds -= 1
            self.confirm_button.setText(f"请看上方提示({self.countdown_seconds}s)")
        elif self.countdown_seconds == 0:
            self.on_countdown_complete()
    
    def on_countdown_complete(self):
        self.countdown_active = False
        self.timer.stop()
        self.confirm_button.setText("已阅读并确认")
        self.confirm_button.setEnabled(True)
    
    def center_window(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    @property
    def result(self):
        return self.popup_result

def show_github_release():
    """显示GitHub更新信息弹窗并返回用户选择结果"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    dialog = GitHubReleaseChecker()
    result = dialog.exec()
    
    if result == QDialog.Accepted:
        return True  # 用户选择了立即更新
    else:
        return False  # 用户选择了暂不更新

def first_run():
    """显示必看说明弹窗"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    dialog = PopupWindow()
    result = dialog.exec()
    
    return dialog.result

def should_show_update():
    """检查是否应该显示更新提示"""
    try:
        if not os.path.exists(STATE_FILE):
            return True
        
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        last_view_date = datetime.fromisoformat(state.get("last_view_date", ""))
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        return last_view_date < one_day_ago
    
    except Exception:
        return True

if __name__ == "__main__":
    # 创建QApplication实例
    app = QApplication([])
    
    # 测试链接匹配
    test_text = """
    这是一个测试文本：
    纯URL链接：https://pan.quark.cn/s/df8836579369
    Markdown链接：[点击这里下载](https://pan.quark.cn/s/df8836579369)
    另一个纯URL：http://example.com/path
    另一个Markdown：[示例链接](http://example.com)
    """
    
    # 测试GitHub更新窗口
    result = show_github_release()
    print(f"GitHub更新结果: {result}")
    
    # 测试首次运行窗口
    result = first_run()
    print(f"首次运行结果: {result}")
    
    sys.exit()