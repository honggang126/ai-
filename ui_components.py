from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QGridLayout, QTabWidget, QTextEdit,
    QComboBox, QGroupBox, QFormLayout, QFileDialog, QSpinBox, QSplitter, QProgressBar,
    QStackedWidget, QScrollArea, QToolBar, QAction, QMenu, QStatusBar, QToolTip,
    QDialog, QDialogButtonBox
)
from PyQt5.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QBrush, QLinearGradient,
    QFontDatabase
)

class GradientFrame(QFrame):
    """自定义渐变背景框架"""
    def __init__(self, start_color=None, end_color=None, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.start_color = start_color if start_color else QColor(45, 52, 54)
        self.end_color = end_color if end_color else QColor(29, 43, 83)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self.start_color)
        gradient.setColorAt(1, self.end_color)
        painter.setBrush(gradient)
        painter.drawRect(self.rect())

class CustomButton(QPushButton):
    """自定义按钮"""
    def __init__(self, text, parent=None, size=(180, 50)):
        super().__init__(text, parent)
        self.setMinimumSize(*size)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c5ce7, stop:1 #8c7ae6);
                color: white;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #5f27cd;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8c7ae6, stop:1 #6c5ce7);
                border: 2px solid #70a1ff;
            }
            QPushButton:pressed {
                background-color: #5f27cd;
                border: 2px solid #70a1ff;
            }
        """)

class CustomInput(QLineEdit):
    """自定义输入框"""
    def __init__(self, placeholder="请输入内容", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumSize(300, 45)
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                color: white;
                padding: 10px 15px;
                font-size: 14px;
                selection-background-color: #8c7ae6;
            }
            QLineEdit:focus {
                border: 2px solid #8c7ae6;
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        self.setEchoMode(QLineEdit.Normal)