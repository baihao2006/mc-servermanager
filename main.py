#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QCheckBox, QTextEdit, QTabWidget, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt, QProcess, QSettings
from PyQt5.QtGui import QFont, QIcon

class MCServerManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_process = None
        self.server_dir = "lib"
        self.properties_file = os.path.join(self.server_dir, "server.properties")
        self.initUI()
        self.loadProperties()
        
    def initUI(self):
        self.setWindowTitle("Minecraft Bedrock Server Manager")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
                color: #ffffff;
            }
            QTabWidget::pane {
                background-color: #16213e;
                border: 1px solid #0f3460;
            }
            QTabBar::tab {
                background-color: #0f3460;
                color: #ffffff;
                padding: 10px 20px;
                border: 1px solid #e94560;
            }
            QTabBar::tab:selected {
                background-color: #e94560;
            }
            QGroupBox {
                background-color: #16213e;
                color: #ffffff;
                border: 1px solid #0f3460;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #0f3460;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
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
                padding: 5px;
                border-radius: 3px;
            }
            QCheckBox {
                color: #ffffff;
            }
            QTextEdit {
                background-color: #0f3460;
                color: #ffffff;
                border: 1px solid #16537e;
                padding: 5px;
                border-radius: 3px;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.createServerTab()
        self.createConfigTab()
        self.createConsoleTab()
        
        # Server control buttons
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
        
        # Server info group
        info_group = QGroupBox("服务器信息")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("服务器名称:"), 0, 0)
        self.server_name = QLineEdit()
        info_layout.addWidget(self.server_name, 0, 1, 1, 3)
        
        info_layout.addWidget(QLabel("游戏模式:"), 1, 0)
        self.gamemode = QComboBox()
        self.gamemode.addItems(["survival", "creative", "adventure"])
        info_layout.addWidget(self.gamemode, 1, 1)
        
        info_layout.addWidget(QLabel("难度:"), 1, 2)
        self.difficulty = QComboBox()
        self.difficulty.addItems(["peaceful", "easy", "normal", "hard"])
        info_layout.addWidget(self.difficulty, 1, 3)
        
        info_layout.addWidget(QLabel("最大玩家数:"), 2, 0)
        self.max_players = QSpinBox()
        self.max_players.setRange(1, 100)
        info_layout.addWidget(self.max_players, 2, 1)
        
        info_layout.addWidget(QLabel("端口:"), 2, 2)
        self.server_port = QSpinBox()
        self.server_port.setRange(1, 65535)
        self.server_port.setValue(19132)
        info_layout.addWidget(self.server_port, 2, 3)
        
        layout.addWidget(info_group)
        
        # Server settings group
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
    
    def createConfigTab(self):
        config_tab = QWidget()
        layout = QVBoxLayout(config_tab)
        
        # World settings group
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
        
        world_layout.addWidget(QLabel("默认玩家权限:"), 3, 2)
        self.default_player_permission_level = QComboBox()
        self.default_player_permission_level.addItems(["visitor", "member", "operator"])
        world_layout.addWidget(self.default_player_permission_level, 3, 3)
        
        layout.addWidget(world_group)
        
        # Advanced settings group
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QGridLayout(advanced_group)
        
        advanced_layout.addWidget(QLabel("最大线程数:"), 0, 0)
        self.max_threads = QSpinBox()
        self.max_threads.setRange(1, 32)
        self.max_threads.setValue(8)
        advanced_layout.addWidget(self.max_threads, 0, 1)
        
        advanced_layout.addWidget(QLabel("聊天限制:"), 0, 2)
        self.chat_restriction = QComboBox()
        self.chat_restriction.addItems(["None", "Dropped", "Disabled"])
        advanced_layout.addWidget(self.chat_restriction, 0, 3)
        
        layout.addWidget(advanced_group)
        
        self.tab_widget.addTab(config_tab, "高级配置")
    
    def createConsoleTab(self):
        console_tab = QWidget()
        layout = QVBoxLayout(console_tab)
        
        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.console_output)
        
        # Command input
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
            
            # Load properties into UI
            self.server_name.setText(properties.get('server-name', 'Dedicated Server'))
            self.gamemode.setCurrentText(properties.get('gamemode', 'survival'))
            self.force_gamemode.setChecked(properties.get('force-gamemode', 'false') == 'true')
            self.difficulty.setCurrentText(properties.get('difficulty', 'easy'))
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
            self.default_player_permission_level.setCurrentText(properties.get('default-player-permission-level', 'member'))
            self.texturepack_required.setChecked(properties.get('texturepack-required', 'false') == 'true')
            self.max_threads.setValue(int(properties.get('max-threads', '8')))
            self.chat_restriction.setCurrentText(properties.get('chat-restriction', 'None'))
    
    def saveProperties(self):
        """Save server properties to file"""
        properties = {
            'server-name': self.server_name.text(),
            'gamemode': self.gamemode.currentText(),
            'force-gamemode': str(self.force_gamemode.isChecked()).lower(),
            'difficulty': self.difficulty.currentText(),
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
            'default-player-permission-level': self.default_player_permission_level.currentText(),
            'texturepack-required': str(self.texturepack_required.isChecked()).lower(),
            'max-threads': str(self.max_threads.value()),
            'chat-restriction': self.chat_restriction.currentText()
        }
        
        with open(self.properties_file, 'w') as f:
            for key, value in properties.items():
                f.write(f"{key}={value}\n")
        
        self.log("配置已保存")
    
    def startServer(self):
        """Start the Minecraft server"""
        if self.server_process is None or not self.server_process.state() == QProcess.Running:
            server_exe = os.path.join(self.server_dir, "bedrock_server.exe")
            if os.path.exists(server_exe):
                self.server_process = QProcess()
                self.server_process.setWorkingDirectory(self.server_dir)
                self.server_process.readyReadStandardOutput.connect(self.readServerOutput)
                self.server_process.readyReadStandardError.connect(self.readServerError)
                self.server_process.finished.connect(self.serverFinished)
                self.server_process.start(server_exe)
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.log("服务器已启动")
            else:
                self.log("错误: 找不到bedrock_server.exe")
    
    def stopServer(self):
        """Stop the Minecraft server"""
        if self.server_process and self.server_process.state() == QProcess.Running:
            self.server_process.terminate()
            if not self.server_process.waitForFinished(3000):
                self.server_process.kill()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.log("服务器已停止")
    
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
