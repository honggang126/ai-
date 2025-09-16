import sys
import os
import json
from datetime import datetime, timedelta, timezone 
from PyQt5.QtCore import Qt, QTimer, QUrl, QObject
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QFrame, QTabWidget, QTextEdit, QComboBox,
    QFormLayout, QProgressBar, QStatusBar
)
from PyQt5.QtGui import QFont, QIcon

from api_client import ApiCallThread
from ui_components import GradientFrame, CustomButton, CustomInput

class NovelWriterWindow(QMainWindow):
    """小说写作软件主窗口"""
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # API调用线程
        self.api_thread = None
        
    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle('小说助手')
        self.setMinimumSize(1000, 700)
        
        # 设置窗口图标（可选）
        try:
            self.setWindowIcon(QIcon('icon.png'))
        except:
            pass
        
        # 主框架和布局
        main_frame = GradientFrame()
        self.setCentralWidget(main_frame)
        
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel('小说写作助手')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('SimHei', 20, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        main_layout.addWidget(title_label)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: rgba(255, 255, 255, 0.3);")
        main_layout.addWidget(line)
        
        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #5f27cd;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 0.05);
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #6c5ce7;
            }
        """)
        
        # 写作标签页
        self.write_tab = QWidget()
        self.init_write_tab()
        self.tabs.addTab(self.write_tab, "写作")
        
        # 设置标签页
        self.settings_tab = QWidget()
        self.init_settings_tab()
        self.tabs.addTab(self.settings_tab, "设置")
        
        main_layout.addWidget(self.tabs)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
            }
            QProgressBar::chunk {
                background-color: #6c5ce7;
                width: 20px;
            }
        """)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 状态条
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
        
        # 居中窗口
        self.center_window()
    
    def init_write_tab(self):
        """初始化写作标签页"""
        layout = QVBoxLayout(self.write_tab)
        
        # 上部：提示输入
        prompt_group = QFrame()
        prompt_group.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 5px;")
        prompt_layout = QVBoxLayout(prompt_group)
        
        prompt_label = QLabel("请输入写作提示：")
        prompt_label.setStyleSheet("color: white; font-size: 14px;")
        prompt_layout.addWidget(prompt_label)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.prompt_input.setMinimumHeight(100)
        prompt_layout.addWidget(self.prompt_input)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.generate_button = CustomButton("生成内容")
        self.generate_button.clicked.connect(self.generate_content)
        button_layout.addWidget(self.generate_button)
        
        self.stop_button = CustomButton("停止生成", size=(120, 50))
        self.stop_button.clicked.connect(self.stop_generation)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.clear_button = CustomButton("清空内容", size=(120, 50))
        self.clear_button.clicked.connect(self.clear_content)
        button_layout.addWidget(self.clear_button)
        
        prompt_layout.addLayout(button_layout)
        layout.addWidget(prompt_group)
        
        # 下部：结果显示
        result_label = QLabel("生成结果：")
        result_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(result_label)
        
        self.result_display = QTextEdit()
        self.result_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)
    
    def init_settings_tab(self):
        """初始化设置标签页"""
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # API设置
        api_group = QFrame()
        api_group.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 5px; padding: 10px;")
        api_layout = QFormLayout()
        api_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
        api_layout.setLabelAlignment(Qt.AlignLeft)
        api_layout.setSpacing(15)
        
        # API类型选择
        api_layout.addRow(QLabel("API类型：", styleSheet="color: white;"))
        self.api_type_combo = QComboBox()
        self.api_type_combo.addItems(["Ollama", "SiliconFlow", "自定义"])
        self.api_type_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        api_layout.addRow(self.api_type_combo)
        
        # API地址
        api_layout.addRow(QLabel("API地址：", styleSheet="color: white;"))
        self.api_url_input = CustomInput("例如: http://localhost:11434/api/generate")
        api_layout.addRow(self.api_url_input)
        
        # API密钥
        api_layout.addRow(QLabel("API密钥：", styleSheet="color: white;"))
        self.api_key_input = CustomInput("不需要时可留空")
        api_layout.addRow(self.api_key_input)
        
        # 模型名称
        api_layout.addRow(QLabel("模型名称：", styleSheet="color: white;"))
        self.model_name_input = CustomInput("例如: llama3")
        api_layout.addRow(self.model_name_input)
        
        # API格式（仅自定义API显示）
        api_layout.addRow(QLabel("API格式：", styleSheet="color: white;"))
        self.api_format_combo = QComboBox()
        self.api_format_combo.addItems(["OpenAI格式", "Ollama格式"])
        self.api_format_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        api_layout.addRow(self.api_format_combo)
        
        # 自定义请求头
        api_layout.addRow(QLabel("自定义请求头(JSON)：", styleSheet="color: white;"))
        self.custom_headers_input = QTextEdit()
        self.custom_headers_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.custom_headers_input.setMinimumHeight(80)
        self.custom_headers_input.setPlaceholderText('例如: {"Authorization": "Bearer your_token"}')
        api_layout.addRow(self.custom_headers_input)
        
        # 保存设置按钮
        save_button = CustomButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        api_layout.addRow(save_button)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 加载保存的设置
        self.load_settings()
    
    def center_window(self):
        """将窗口居中显示"""
        frame_geometry = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
    
    def generate_content(self):
        """生成小说内容"""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "提示", "请输入写作提示")
            return
            
        # 获取API设置
        api_type = self.api_type_combo.currentText()
        api_url = self.api_url_input.text().strip()
        api_key = self.api_key_input.text().strip()
        model_name = self.model_name_input.text().strip()
        api_format = self.api_format_combo.currentText() if api_type == "自定义" else None
        custom_headers = self.custom_headers_input.toPlainText().strip() or None
        
        if not api_url or not model_name:
            QMessageBox.warning(self, "提示", "请填写API地址和模型名称")
            return
            
        # 准备生成
        self.result_display.append("\n\n" + "="*50 + "\n")
        self.result_display.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始生成...\n")
        
        # 启动API调用线程
        self.api_thread = ApiCallThread(
            api_type, api_url, api_key, prompt, 
            model_name, api_format, custom_headers
        )
        self.api_thread.progress.connect(self.update_progress)
        self.api_thread.finished.connect(self.on_generation_finished)
        self.api_thread.error.connect(self.on_generation_error)
        self.api_thread.start()
        
        # 更新UI状态
        self.generate_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar.showMessage("正在生成内容...")
    
    def stop_generation(self):
        """停止生成内容"""
        if self.api_thread and self.api_thread.isRunning():
            self.api_thread.running = False
            self.statusBar.showMessage("正在停止生成...")
    
    def clear_content(self):
        """清空生成结果"""
        self.result_display.clear()
        self.statusBar.showMessage("内容已清空")
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def on_generation_finished(self, result, status):
        """生成完成处理"""
        self.result_display.append(result)
        self.result_display.append(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 生成完成\n")
        self._reset_generation_state()
        self.statusBar.showMessage("生成完成")
    
    def on_generation_error(self, error_msg):
        """生成错误处理"""
        self.result_display.append(f"\n错误: {error_msg}\n")
        self._reset_generation_state()
        self.statusBar.showMessage("生成失败")
        QMessageBox.warning(self, "错误", error_msg)
    
    def _reset_generation_state(self):
        """重置生成状态"""
        self.generate_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.api_thread = None
    
    def save_settings(self):
        """保存设置"""
        settings = {
            "api_type": self.api_type_combo.currentText(),
            "api_url": self.api_url_input.text().strip(),
            "api_key": self.api_key_input.text().strip(),
            "model_name": self.model_name_input.text().strip(),
            "api_format": self.api_format_combo.currentText(),
            "custom_headers": self.custom_headers_input.toPlainText().strip()
        }
        
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "设置已保存")
            self.statusBar.showMessage("设置已保存")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置失败: {str(e)}")
    
    def load_settings(self):
        """加载设置"""
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                
                self.api_type_combo.setCurrentText(settings.get("api_type", "Ollama"))
                self.api_url_input.setText(settings.get("api_url", ""))
                self.api_key_input.setText(settings.get("api_key", ""))
                self.model_name_input.setText(settings.get("model_name", ""))
                self.api_format_combo.setCurrentText(settings.get("api_format", "OpenAI格式"))
                self.custom_headers_input.setText(settings.get("custom_headers", ""))
            except Exception as e:
                print(f"加载设置失败: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("SimHei")
    app.setFont(font)
    
    window = NovelWriterWindow()
    window.show()
    
    sys.exit(app.exec_())