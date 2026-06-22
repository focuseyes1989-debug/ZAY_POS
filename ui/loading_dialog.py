# ui/loading_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QFont
import os


class LoadingDialog(QDialog):
    """Loading dialog shown while initializing main window"""
    
    finished = pyqtSignal()
    
    def __init__(self, message="Loading...", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(400, 250)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo
        logo_label = QLabel()
        logo_path = "assets/icons/zaypos.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, 
                                      Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("ZAY POS Lite")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_font = QFont()
        message_font.setPointSize(10)
        self.message_label.setFont(message_font)
        layout.addWidget(self.message_label)
        
        # Progress bar (indeterminate)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(8)
        status_font.setItalic(True)
        self.status_label.setFont(status_font)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background-color: #2f3136;
                border-radius: 12px;
                border: 1px solid #40444b;
            }
            QLabel {
                color: #dcddde;
            }
            QProgressBar {
                background-color: #40444b;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #5865f2;
                border-radius: 4px;
            }
        """)
    
    def set_status(self, text):
        """Update status text"""
        self.status_label.setText(text)
    
    def set_message(self, text):
        """Update main message"""
        self.message_label.setText(text)