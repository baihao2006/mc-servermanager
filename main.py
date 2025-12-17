#使用py3版本，由gork重构
import sys
import os
import zipfile
import urllib.request
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QCheckBox, QTextEdit, QTabWidget, QGroupBox, QGridLayout, QProgressBar, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QProcess, QSettings, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class DownloadThread(QThread):
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(bool, str)
    #·下载线程类，用于在后台下载Minecraft服务器包。
    def __init__(self, version, save_path):
        super().__init__()
        self.version = version
        self.save_path = save_path
    #·下载线程的运行方法，用于下载Minecraft服务器包。
    def run(self):
        # 重试次数
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                url = f"https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-{self.version}.zip"
                zip_file_path = os.path.join(self.save_path, f"bedrock-server-{self.version}.zip")
                
                # 添加User-Agent头，确保能访问Minecraft官网
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                # 创建请求对象
                req = urllib.request.Request(url, headers=headers)
                
                # 使用urlopen和自定义请求对象，增加超时设置
                with urllib.request.urlopen(req, timeout=30) as response:
                    # 获取文件大小
                    total_size = int(response.getheader('Content-Length', 0))
                    
                    # 写入文件并更新进度
                    with open(zip_file_path, 'wb') as f:
                        downloaded = 0
                        block_size = 8192
                        while True:
                            buffer = response.read(block_size)
                            if not buffer:
                                break
                            f.write(buffer)
                            downloaded += len(buffer)
                            if total_size > 0:
                                percent = int((downloaded / total_size) * 100)
                                self.progress_updated.emit(percent)
                
                # 验证文件大小
                if os.path.exists(zip_file_path) and os.path.getsize(zip_file_path) < 1024 * 1024:  # 小于1MB可能是错误页面
                    raise Exception(f"下载文件过小，可能是错误页面，文件大小: {os.path.getsize(zip_file_path)} 字节")
                
                # 解压文件
                version_dir = os.path.join(self.save_path, self.version)
                os.makedirs(version_dir, exist_ok=True)
                
                # 解压前验证ZIP文件
                if not zipfile.is_zipfile(zip_file_path):
                    raise zipfile.BadZipFile("文件不是有效的ZIP格式")
                
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    # 检查zip文件内容
                    zip_contents = zip_ref.namelist()
                    if not any('bedrock_server.exe' in item for item in zip_contents):
                        raise Exception("ZIP文件中没有找到bedrock_server.exe")
                    
                    # 解压文件
                    zip_ref.extractall(version_dir)
                
                # 验证解压是否成功
                bedrock_exe_path = os.path.join(version_dir, "bedrock_server.exe")
                if not os.path.exists(bedrock_exe_path):
                    raise Exception("解压失败，未找到bedrock_server.exe")
                
                # 删除临时zip文件
                os.remove(zip_file_path)
                
                self.download_finished.emit(True, "下载完成")
                return  # 成功下载，退出循环
            except urllib.error.HTTPError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    self.download_finished.emit(False, f"HTTP错误: {e.code} {e.reason}，可能是版本号不存在或链接已失效")
                    return
            except urllib.error.URLError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    self.download_finished.emit(False, f"网络错误: {str(e)}, 请检查网络连接或稍后重试")
                    return
            except zipfile.BadZipFile as e:
                retry_count += 1
                if retry_count >= max_retries:
                    self.download_finished.emit(False, f"无效的ZIP文件: {str(e)}, 下载可能被中断或文件损坏")
                    return
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    self.download_finished.emit(False, f"下载失败: {str(e)}")
                    return
            
            # 等待1秒后重试
            import time
            time.sleep(1)


class MCServerManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_process = None
        self.server_dir = "lib"
        self.selected_version = ""
        self.properties_file = ""
        self.initUI()
        self.loadAvailableVersions()
        self.loadProperties()
        # 获取并显示公网IP
        self.updatePublicIP()
        
    def loadAvailableVersions(self):
        """加载可用的服务器版本"""
        self.version_combo.clear()
        if os.path.exists(self.server_dir):
            versions = [d for d in os.listdir(self.server_dir) if os.path.isdir(os.path.join(self.server_dir, d))]
            for version in versions:
                self.version_combo.addItem(version)
            if versions and not self.selected_version:
                self.selected_version = versions[0]
                self.version_combo.setCurrentText(self.selected_version)
                self.updatePropertiesFile()
        
    def updatePropertiesFile(self):
        """更新属性文件路径"""
        if self.selected_version:
            self.properties_file = os.path.join(self.server_dir, self.selected_version, "server.properties")
        else:
            self.properties_file = ""
        
    def initUI(self):
        self.setWindowTitle("Minecraft Bedrock Server Manager")
        self.setGeometry(100, 100, 1200, 900)
        
        # 设置全局字体大小
        font = QFont()
        font.setPointSize(12)
        self.setFont(font)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
                color: #ffffff;
                font-size: 12pt;
            }
            QTabWidget::pane {
                background-color: #16213e;
                border: 1px solid #0f3460;
            }
            QTabBar {
                background-color: #0f3460;
                height: 60px;
                alignment: left;
                font-size: 10pt;
            }
            QTabBar::tab {
                background-color: #0f3460;
                color: #ffffff;
                padding: 15px 15px;
                border: 1px solid #e94560;
                border-bottom: none;
                font-size: 10pt;
                min-width: 140px;
                max-width: 200px;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #e94560;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #16537e;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabWidget::pane {
                background-color: #16213e;
                border: 2px solid #e94560;
                border-radius: 5px;
            }
            QGroupBox {
                background-color: #16213e;
                color: #ffffff;
                border: 1px solid #0f3460;
                border-radius: 5px;
                margin-top: 12px;
                font-size: 12pt;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                font-size: 14pt;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0f3460;
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #16537e;
            }
            QPushButton:pressed {
                background-color: #e94560;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #0f3460;
                color: #ffffff;
                border: 1px solid #16537e;
                padding: 8px;
                border-radius: 3px;
                font-size: 12pt;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 12pt;
            }
            QTextEdit {
                background-color: #0f3460;
                color: #ffffff;
                border: 1px solid #16537e;
                padding: 8px;
                border-radius: 3px;
                font-size: 11pt;
            }
            QLabel {
                color: #ffffff;
                font-size: 12pt;
            }
            QProgressBar {
                background-color: #0f3460;
                color: #ffffff;
                border: 1px solid #16537e;
                padding: 5px;
                border-radius: 3px;
                text-align: center;
                font-weight: bold;
                font-size: 11pt;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #2ed573;
                border-radius: 3px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        self.createServerTab()
        self.createConfigTab()
        self.createConsoleTab()
        
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("启动服务器")
        self.start_btn.clicked.connect(self.startServer)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止服务器")
        self.stop_btn.clicked.connect(self.stopServer)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.saveProperties)
        control_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(control_layout)
    
    def createServerTab(self):
        server_tab = QWidget()
        layout = QVBoxLayout(server_tab)
        
        # 版本管理组
        version_group = QGroupBox("版本管理")
        version_layout = QGridLayout(version_group)
        
        # 版本选择
        version_layout.addWidget(QLabel("选择服务器版本:"), 0, 0)
        self.version_combo = QComboBox()
        self.version_combo.currentTextChanged.connect(self.onVersionChanged)
        version_layout.addWidget(self.version_combo, 0, 1)
        
        # 下载新版本
        version_layout.addWidget(QLabel("输入版本号下载:"), 1, 0)
        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("例如: 1.26.0.25")
        version_layout.addWidget(self.version_input, 1, 1)
        
        self.download_btn = QPushButton("下载版本")
        self.download_btn.clicked.connect(self.downloadVersion)
        version_layout.addWidget(self.download_btn, 1, 2)
        
        # 下载进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        version_layout.addWidget(self.progress_bar, 2, 0, 1, 3)
        
        layout.addWidget(version_group)
        
        # 服务器信息组
        info_group = QGroupBox("服务器信息")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("服务器名称:"), 0, 0)
        self.server_name = QLineEdit()
        info_layout.addWidget(self.server_name, 0, 1, 1, 3)
        
        # 游戏模式（中文显示，英文保存）
        info_layout.addWidget(QLabel("游戏模式:"), 1, 0)
        self.gamemode = QComboBox()
        self.gamemode.addItems(["生存", "创造", "冒险"])
        self.gamemode_map = {"生存": "survival", "创造": "creative", "冒险": "adventure"}
        self.gamemode_reverse_map = {v: k for k, v in self.gamemode_map.items()}
        info_layout.addWidget(self.gamemode, 1, 1)
        
        # 难度（中文显示，英文保存）
        info_layout.addWidget(QLabel("难度:"), 1, 2)
        self.difficulty = QComboBox()
        self.difficulty.addItems(["和平", "简单", "普通", "困难"])
        self.difficulty_map = {"和平": "peaceful", "简单": "easy", "普通": "normal", "困难": "hard"}
        self.difficulty_reverse_map = {v: k for k, v in self.difficulty_map.items()}
        info_layout.addWidget(self.difficulty, 1, 3)
        
        info_layout.addWidget(QLabel("最大玩家数:"), 2, 0)
        self.max_players = QSpinBox()
        self.max_players.setRange(1, 100)
        info_layout.addWidget(self.max_players, 2, 1)
        
        info_layout.addWidget(QLabel("端口:"), 2, 2)
        self.server_port = QSpinBox()
        self.server_port.setRange(1, 65535)
        self.server_port.setValue(19132)
        self.server_port.valueChanged.connect(self.onPortChanged)
        info_layout.addWidget(self.server_port, 2, 3)
        
        layout.addWidget(info_group)
        
        # 服务器状态显示
        status_group = QGroupBox("服务器状态")
        status_layout = QGridLayout(status_group)
        
        status_layout.addWidget(QLabel("运行状态:"), 0, 0)
        self.status_label = QLabel("离线")
        self.status_label.setStyleSheet("color: #ff4757; font-weight: bold; font-size: 14pt;")
        status_layout.addWidget(self.status_label, 0, 1)
        
        status_layout.addWidget(QLabel("服务器IP:"), 0, 2)
        self.ip_label = QLabel("127.0.0.1")
        status_layout.addWidget(self.ip_label, 0, 3)
        
        status_layout.addWidget(QLabel("端口:"), 1, 0)
        self.port_label = QLabel(str(self.server_port.value()))
        status_layout.addWidget(self.port_label, 1, 1)
        
        layout.addWidget(status_group)
        
        # 服务器设置组
        settings_group = QGroupBox("服务器设置")
        settings_layout = QGridLayout(settings_group)
        
        self.force_gamemode = QCheckBox("强制游戏模式")
        settings_layout.addWidget(self.force_gamemode, 0, 0, 1, 2)
        
        self.allow_cheats = QCheckBox("允许作弊")
        settings_layout.addWidget(self.allow_cheats, 0, 2, 1, 2)
        
        self.online_mode = QCheckBox("在线模式")
        settings_layout.addWidget(self.online_mode, 1, 0, 1, 2)
        
        self.allow_list = QCheckBox("白名单")
        settings_layout.addWidget(self.allow_list, 1, 2, 1, 2)
        
        self.texturepack_required = QCheckBox("强制纹理包")
        settings_layout.addWidget(self.texturepack_required, 2, 0, 1, 2)
        
        layout.addWidget(settings_group)
        
        self.tab_widget.addTab(server_tab, "服务器设置")
    
    def onVersionChanged(self, version):
        """版本选择变化时的处理"""
        self.selected_version = version
        self.updatePropertiesFile()
        self.loadProperties()
    
    def onPortChanged(self, port):
        """端口变化时更新显示"""
        self.port_label.setText(str(port))
    
    def downloadVersion(self):
        """下载指定版本的服务器"""
        version = self.version_input.text().strip()
        if not version:
            QMessageBox.warning(self, "错误", "请输入有效的版本号")
            return
        
        # 简单验证版本号格式（例如：1.26.0.25）
        import re
        if not re.match(r'^\d+\.\d+\.\d+\.\d+$', version):
            QMessageBox.warning(self, "错误", "版本号格式不正确，应为：X.X.X.X（例如：1.26.0.25）")
            return
        
        # 检查版本是否已存在
        version_dir = os.path.join(self.server_dir, version)
        if os.path.exists(version_dir):
            QMessageBox.information(self, "提示", f"版本 {version} 已存在")
            self.loadAvailableVersions()
            return
        
        # 创建lib目录（如果不存在）
        os.makedirs(self.server_dir, exist_ok=True)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.download_btn.setEnabled(False)
        
        # 启动下载线程
        self.download_thread = DownloadThread(version, self.server_dir)
        self.download_thread.progress_updated.connect(self.updateProgress)
        self.download_thread.download_finished.connect(self.downloadFinished)
        self.download_thread.start()
    
    def updateProgress(self, percent):
        """更新下载进度"""
        self.progress_bar.setValue(percent)
    
    def downloadFinished(self, success, message):
        """下载完成处理"""
        self.log(message)
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        
        if success:
            # 重新加载版本列表
            self.loadAvailableVersions()
            self.version_input.clear()
            QMessageBox.information(self, "成功", f"版本下载完成")
        else:
            QMessageBox.warning(self, "失败", f"版本下载失败：{message}")
    
    def updatePublicIP(self):
        """获取并更新公网IP"""
        try:
            # 使用ipinfo.io获取公网IP
            with urllib.request.urlopen('https://ipinfo.io/ip') as response:
                public_ip = response.read().decode().strip()
                self.ip_label.setText(public_ip)
        except Exception as e:
            # 如果获取失败，显示错误信息并使用默认值
            self.log(f"获取公网IP失败: {str(e)}")
            self.ip_label.setText("127.0.0.1 (获取公网IP失败)")
    
    def createConfigTab(self):
        config_tab = QWidget()
        layout = QVBoxLayout(config_tab)
        
        
        world_group = QGroupBox("世界设置")
        world_layout = QGridLayout(world_group)
        
        world_layout.addWidget(QLabel("世界名称:"), 0, 0)
        self.level_name = QLineEdit()
        world_layout.addWidget(self.level_name, 0, 1, 1, 3)
        
        world_layout.addWidget(QLabel("世界种子:"), 1, 0)
        self.level_seed = QLineEdit()
        world_layout.addWidget(self.level_seed, 1, 1, 1, 3)
        
        world_layout.addWidget(QLabel("查看距离:"), 2, 0)
        self.view_distance = QSpinBox()
        self.view_distance.setRange(5, 64)
        self.view_distance.setValue(32)
        world_layout.addWidget(self.view_distance, 2, 1)
        
        world_layout.addWidget(QLabel("Tick距离:"), 2, 2)
        self.tick_distance = QSpinBox()
        self.tick_distance.setRange(4, 12)
        self.tick_distance.setValue(4)
        world_layout.addWidget(self.tick_distance, 2, 3)
        
        world_layout.addWidget(QLabel("玩家超时时间(分钟):"), 3, 0)
        self.player_idle_timeout = QSpinBox()
        self.player_idle_timeout.setRange(0, 120)
        self.player_idle_timeout.setValue(30)
        world_layout.addWidget(self.player_idle_timeout, 3, 1)
        
        # 默认玩家权限（中文显示，英文保存）
        world_layout.addWidget(QLabel("默认玩家权限:"), 3, 2)
        self.default_player_permission_level = QComboBox()
        self.default_player_permission_level.addItems(["访客", "成员", "操作员"])
        self.permission_map = {"访客": "visitor", "成员": "member", "操作员": "operator"}
        self.permission_reverse_map = {v: k for k, v in self.permission_map.items()}
        world_layout.addWidget(self.default_player_permission_level, 3, 3)
        
        layout.addWidget(world_group)
        
        
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QGridLayout(advanced_group)
        
        advanced_layout.addWidget(QLabel("最大线程数:"), 0, 0)
        self.max_threads = QSpinBox()
        self.max_threads.setRange(1, 32)
        self.max_threads.setValue(8)
        advanced_layout.addWidget(self.max_threads, 0, 1)
        
        # 聊天限制（中文显示，英文保存）
        advanced_layout.addWidget(QLabel("聊天限制:"), 0, 2)
        self.chat_restriction = QComboBox()
        self.chat_restriction.addItems(["无", "丢弃", "禁用"])
        self.chat_restriction_map = {"无": "None", "丢弃": "Dropped", "禁用": "Disabled"}
        self.chat_restriction_reverse_map = {v: k for k, v in self.chat_restriction_map.items()}
        advanced_layout.addWidget(self.chat_restriction, 0, 3)
        
        layout.addWidget(advanced_group)
        
        self.tab_widget.addTab(config_tab, "高级配置")
    
    def createConsoleTab(self):
        console_tab = QWidget()
        layout = QVBoxLayout(console_tab)
        
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.console_output)
        
        
        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.returnPressed.connect(self.sendCommand)
        cmd_layout.addWidget(self.cmd_input)
        
        self.cmd_btn = QPushButton("发送命令")
        self.cmd_btn.clicked.connect(self.sendCommand)
        cmd_layout.addWidget(self.cmd_btn)
        
        layout.addLayout(cmd_layout)
        
        self.tab_widget.addTab(console_tab, "控制台")
    
    def loadProperties(self):
        """Load server properties from file"""
        if os.path.exists(self.properties_file):
            with open(self.properties_file, 'r') as f:
                lines = f.readlines()
            
            properties = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    properties[key] = value
            
            self.server_name.setText(properties.get('server-name', 'Dedicated Server'))
            
            # 游戏模式（英文转中文显示）
            gamemode = properties.get('gamemode', 'survival')
            self.gamemode.setCurrentText(self.gamemode_reverse_map.get(gamemode, '生存'))
            
            self.force_gamemode.setChecked(properties.get('force-gamemode', 'false') == 'true')
            
            # 难度（英文转中文显示）
            difficulty = properties.get('difficulty', 'easy')
            self.difficulty.setCurrentText(self.difficulty_reverse_map.get(difficulty, '简单'))
            
            self.allow_cheats.setChecked(properties.get('allow-cheats', 'false') == 'true')
            self.max_players.setValue(int(properties.get('max-players', '10')))
            self.online_mode.setChecked(properties.get('online-mode', 'true') == 'true')
            self.allow_list.setChecked(properties.get('allow-list', 'false') == 'true')
            self.server_port.setValue(int(properties.get('server-port', '19132')))
            self.view_distance.setValue(int(properties.get('view-distance', '32')))
            self.tick_distance.setValue(int(properties.get('tick-distance', '4')))
            self.player_idle_timeout.setValue(int(properties.get('player-idle-timeout', '30')))
            self.level_name.setText(properties.get('level-name', 'Bedrock level'))
            self.level_seed.setText(properties.get('level-seed', ''))
            
            # 默认玩家权限（英文转中文显示）
            permission = properties.get('default-player-permission-level', 'member')
            self.default_player_permission_level.setCurrentText(self.permission_reverse_map.get(permission, '成员'))
            
            self.texturepack_required.setChecked(properties.get('texturepack-required', 'false') == 'true')
            self.max_threads.setValue(int(properties.get('max-threads', '8')))
            
            # 聊天限制（英文转中文显示）
            chat_restriction = properties.get('chat-restriction', 'None')
            self.chat_restriction.setCurrentText(self.chat_restriction_reverse_map.get(chat_restriction, '无'))
    
    def saveProperties(self):
        """Save server properties to file"""
        properties = {
            'server-name': self.server_name.text(),
            # 游戏模式（中文转英文保存）
            'gamemode': self.gamemode_map.get(self.gamemode.currentText(), 'survival'),
            'force-gamemode': str(self.force_gamemode.isChecked()).lower(),
            # 难度（中文转英文保存）
            'difficulty': self.difficulty_map.get(self.difficulty.currentText(), 'easy'),
            'allow-cheats': str(self.allow_cheats.isChecked()).lower(),
            'max-players': str(self.max_players.value()),
            'online-mode': str(self.online_mode.isChecked()).lower(),
            'allow-list': str(self.allow_list.isChecked()).lower(),
            'server-port': str(self.server_port.value()),
            'view-distance': str(self.view_distance.value()),
            'tick-distance': str(self.tick_distance.value()),
            'player-idle-timeout': str(self.player_idle_timeout.value()),
            'level-name': self.level_name.text(),
            'level-seed': self.level_seed.text(),
            # 默认玩家权限（中文转英文保存）
            'default-player-permission-level': self.permission_map.get(self.default_player_permission_level.currentText(), 'member'),
            'texturepack-required': str(self.texturepack_required.isChecked()).lower(),
            'max-threads': str(self.max_threads.value()),
            # 聊天限制（中文转英文保存）
            'chat-restriction': self.chat_restriction_map.get(self.chat_restriction.currentText(), 'None')
        }
        
        with open(self.properties_file, 'w') as f:
            for key, value in properties.items():
                f.write(f"{key}={value}\n")
        
        self.log("配置已保存")
    
    def startServer(self):
        """Start the Minecraft server"""
        if not self.selected_version:
            self.log("请先选择服务器版本")
            return
        
        if self.server_process is None or not self.server_process.state() == QProcess.Running:
            server_exe = os.path.join(self.server_dir, self.selected_version, "bedrock_server.exe")
            if os.path.exists(server_exe):
                self.server_process = QProcess()
                self.server_process.setWorkingDirectory(os.path.join(self.server_dir, self.selected_version))
                self.server_process.readyReadStandardOutput.connect(self.readServerOutput)
                self.server_process.readyReadStandardError.connect(self.readServerError)
                self.server_process.finished.connect(self.serverFinished)
                self.server_process.start(server_exe)
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.status_label.setText("在线")
                self.status_label.setStyleSheet("color: #2ed573; font-weight: bold; font-size: 14pt;")
                self.log(f"服务器 {self.selected_version} 已启动")
            else:
                self.log(f"错误: 在 {self.selected_version} 目录中找不到bedrock_server.exe")
    
    def stopServer(self):
        """Stop the Minecraft server"""
        if self.server_process and self.server_process.state() == QProcess.Running:
            self.server_process.terminate()
            if not self.server_process.waitForFinished(3000):
                self.server_process.kill()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("离线")
            self.status_label.setStyleSheet("color: #ff4757; font-weight: bold; font-size: 14pt;")
            self.log("服务器已停止")
    
    def serverFinished(self, exitCode, exitStatus):
        """Handle server finished"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("离线")
        self.status_label.setStyleSheet("color: #ff4757; font-weight: bold; font-size: 14pt;")
        self.log(f"服务器已退出，退出码: {exitCode}")
    
    def sendCommand(self):
        """Send command to the server"""
        cmd = self.cmd_input.text().strip()
        if cmd and self.server_process and self.server_process.state() == QProcess.Running:
            self.server_process.write((cmd + "\n").encode())
            self.cmd_input.clear()
            self.log(f"> {cmd}")
    
    def readServerOutput(self):
        """Read server output"""
        output = self.server_process.readAllStandardOutput().data().decode()
        self.log(output)
    
    def readServerError(self):
        """Read server error"""
        error = self.server_process.readAllStandardError().data().decode()
        self.log(error)
    
    def serverFinished(self, exitCode, exitStatus):
        """Handle server finished"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log(f"服务器已退出，退出码: {exitCode}")
    
    def log(self, message):
        """Log message to console"""
        self.console_output.append(message)
        self.console_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MCServerManager()
    window.show()
    sys.exit(app.exec_())
