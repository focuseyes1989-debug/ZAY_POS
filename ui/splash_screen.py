# ui/splash_screen.py
from PyQt6.QtWidgets import QSplashScreen, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont
import os


class CustomSplashScreen(QSplashScreen):
    def __init__(self):
        # Create a pixmap for the splash screen
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create a label for the background
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 500, 300)
        self.bg_label.setStyleSheet("""
            background-color: #2f3136;
            border-radius: 12px;
            border: 1px solid #40444b;
        """)
        
        # Logo
        self.logo_label = QLabel(self)
        self.logo_label.setGeometry(175, 30, 150, 80)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = "assets/icons/zaypos.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(scaled)
        self.logo_label.setStyleSheet("background-color: transparent;")
        
        # Title
        self.title_label = QLabel("ZAY POS Lite", self)
        self.title_label.setGeometry(0, 120, 500, 30)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #dcddde; background-color: transparent;")
        
        # Status label
        self.status_label = QLabel("Initializing...", self)
        self.status_label.setGeometry(0, 170, 500, 25)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(9)
        status_font.setItalic(True)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #b9bbbe; background-color: transparent;")
        
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 220, 400, 10)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #40444b;
                border-radius: 5px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #5865f2;
                border-radius: 5px;
            }
        """)
        
        # Show the splash screen
        self.show()
        QApplication.processEvents()
    
    def set_status(self, text):
        """Update status text"""
        self.status_label.setText(text)
        QApplication.processEvents()