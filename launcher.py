# launcher.py
"""
ZAY POS Launcher - Modern Design with Logo
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
import hashlib
import zipfile
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Try importing requests with fallback
try:
    import requests
except ImportError:
    print("⚠️ requests not found, installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTextEdit, QMessageBox,
    QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QLinearGradient, QBrush, QPalette, QFontDatabase

# Configuration
GITHUB_REPO = "focuseyes1989-debug/ZAY_POS"

# Try to get current version from version.txt
def get_current_version():
    """Get current version from version.txt file."""
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.getcwd()
        
        version_file = os.path.join(app_dir, 'version.txt')
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'ProductVersion\s*=\s*["\']([\d.]+)["\']', content)
                if match:
                    return match.group(1)
    except:
        pass
    return "1.0.7"

CURRENT_VERSION = get_current_version()
APP_NAME = "ZAY_POS"


# ============================================================================
# MODERN STYLESHEET
# ============================================================================
STYLESHEET = """
/* Main Window */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
    border: none;
}

/* Central Widget */
QWidget#centralWidget {
    background: transparent;
}

/* Title Label */
QLabel#titleLabel {
    color: #ffffff;
    font-size: 22pt;
    font-weight: bold;
    font-family: 'Segoe UI', 'Arial';
    letter-spacing: 1px;
}

QLabel#subTitleLabel {
    color: #a8b2d1;
    font-size: 10pt;
    font-family: 'Segoe UI', 'Arial';
}

/* Version Group */
QGroupBox {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    margin-top: 10px;
    padding-top: 12px;
    padding-bottom: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 18px;
    padding: 0 10px;
    color: #64ffda;
    font-size: 10pt;
    font-weight: bold;
}

/* Version Labels */
QLabel#versionCurrent {
    color: #ffffff;
    font-size: 16pt;
    font-weight: bold;
}

QLabel#versionLatest {
    color: #64ffda;
    font-size: 16pt;
    font-weight: bold;
}

QLabel#versionLabel {
    color: #8892b0;
    font-size: 9pt;
}

/* Status Group */
QGroupBox#statusGroup {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    margin-top: 10px;
    padding-top: 12px;
    padding-bottom: 8px;
}

QGroupBox#statusGroup::title {
    color: #64ffda;
}

QLabel#statusLabel {
    color: #64ffda;
    font-size: 11pt;
    padding: 5px;
}

/* Progress Bar */
QProgressBar {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #64ffda, stop:1 #00b4d8);
    border-radius: 6px;
}

/* Log Group */
QGroupBox#logGroup {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    margin-top: 10px;
    padding-top: 12px;
    padding-bottom: 8px;
}

QGroupBox#logGroup::title {
    color: #8892b0;
}

QTextEdit {
    background: rgba(0, 0, 0, 0.3);
    border: none;
    border-radius: 8px;
    color: #ccd6f6;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
    padding: 8px;
}

QTextEdit:focus {
    border: none;
}

/* Buttons */
QPushButton {
    border: none;
    border-radius: 8px;
    padding: 12px 25px;
    font-size: 11pt;
    font-weight: bold;
    font-family: 'Segoe UI', 'Arial';
    color: white;
}

QPushButton#startBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00b894, stop:1 #00cec9);
}

QPushButton#startBtn:hover:!disabled {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d2d3, stop:1 #55efc4);
}

QPushButton#startBtn:disabled {
    background: #2d3436;
    color: #636e72;
}

QPushButton#updateBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0984e3, stop:1 #6c5ce7);
}

QPushButton#updateBtn:hover:!disabled {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #74b9ff, stop:1 #a29bfe);
}

QPushButton#updateBtn:disabled {
    background: #2d3436;
    color: #636e72;
}

QPushButton#skipBtn {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

QPushButton#skipBtn:hover:!disabled {
    background: rgba(255, 255, 255, 0.2);
}

QPushButton#skipBtn:disabled {
    background: rgba(255, 255, 255, 0.03);
    color: #636e72;
}

/* Note Label */
QLabel#noteLabel {
    color: #495670;
    font-size: 9pt;
    font-style: italic;
}

/* Scrollbar */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.3);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Logo label */
QLabel#logoLabel {
    background: transparent;
}
"""


def load_logo():
    """Load logo from assets/icons/zaypos.png."""
    logo_paths = [
        "assets/icons/zaypos.png",
        "assets/icons/zaypos.ico",
        "assets/icons/app_icon.png",
        "../assets/icons/zaypos.png",
    ]
    
    # If running as frozen exe
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
        logo_paths = [
            os.path.join(app_dir, "assets/icons/zaypos.png"),
            os.path.join(app_dir, "assets/icons/zaypos.ico"),
            os.path.join(app_dir, "assets/icons/app_icon.png"),
        ]
    
    for path in logo_paths:
        if os.path.exists(path):
            try:
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    # Scale logo to fit
                    return pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            except:
                pass
    return None


def load_window_icon():
    """Load window icon from assets/icons/app_icon.ico."""
    icon_paths = [
        "assets/icons/app_icon.ico",
        "assets/icons/zaypos.ico",
        "assets/icons/app_icon.png",
        "../assets/icons/app_icon.ico",
    ]
    
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
        icon_paths = [
            os.path.join(app_dir, "assets/icons/app_icon.ico"),
            os.path.join(app_dir, "assets/icons/zaypos.ico"),
            os.path.join(app_dir, "assets/icons/app_icon.png"),
        ]
    
    for path in icon_paths:
        if os.path.exists(path):
            try:
                icon = QIcon(path)
                if not icon.isNull():
                    return icon
            except:
                pass
    return None


class UpdateCheckerThread(QThread):
    """Background thread for checking updates."""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._is_cancelled = False
        
    def run(self):
        try:
            self.log.emit("🔄 Checking for updates...")
            
            urls = [
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/update_build/version.json"
            ]
            
            for url in urls:
                try:
                    self.log.emit(f"📡 Fetching: {url}")
                    response = requests.get(
                        url,
                        timeout=10,
                        headers={'User-Agent': 'ZAY-POS-Launcher/1.0'}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'tag_name' in data:
                            latest_version = data.get('tag_name', '').replace('v', '')
                            self.finished.emit({
                                'version': latest_version,
                                'data': data,
                                'available': self.compare_versions(latest_version, CURRENT_VERSION) > 0
                            })
                            return
                        elif 'version' in data:
                            latest_version = data.get('version', '')
                            self.finished.emit({
                                'version': latest_version,
                                'data': data,
                                'available': self.compare_versions(latest_version, CURRENT_VERSION) > 0
                            })
                            return
                except Exception as e:
                    self.log.emit(f"⚠️ Failed: {e}")
                    continue
            
            self.error.emit("All update sources failed")
                
        except Exception as e:
            self.error.emit(str(e))
    
    def compare_versions(self, v1: str, v2: str) -> int:
        def parse(v):
            try:
                return [int(x) for x in v.split('.')]
            except:
                return [0, 0, 0]
        
        try:
            a = parse(v1)
            b = parse(v2)
            for i in range(max(len(a), len(b))):
                av = a[i] if i < len(a) else 0
                bv = b[i] if i < len(b) else 0
                if av < bv:
                    return -1
                elif av > bv:
                    return 1
            return 0
        except:
            return 0


class DownloadThread(QThread):
    """Thread for downloading updates."""
    
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    
    def __init__(self, download_url: str, version: str):
        super().__init__()
        self.download_url = download_url
        self.version = version
        self._is_cancelled = False
        self.download_path = None
        
    def run(self):
        try:
            self.log.emit(f"📥 Downloading update v{self.version}...")
            
            temp_dir = tempfile.mkdtemp(prefix='zay_update_')
            self.download_path = os.path.join(temp_dir, 'update.zip')
            
            response = requests.get(
                self.download_url,
                stream=True,
                timeout=30,
                headers={'User-Agent': 'ZAY-POS-Launcher/1.0'}
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(self.download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self._is_cancelled:
                        self.finished.emit(False, "Download cancelled")
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress.emit(progress, f"Downloading... {progress}%")
            
            self.log.emit(f"✅ Download complete: {downloaded // 1024} KB")
            self.finished.emit(True, self.download_path)
            
        except Exception as e:
            self.log.emit(f"❌ Download failed: {e}")
            self.finished.emit(False, str(e))
    
    def cancel(self):
        self._is_cancelled = True


class InstallThread(QThread):
    """Thread for installing updates - skips launcher files."""
    
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    
    def __init__(self, zip_path: str):
        super().__init__()
        self.zip_path = zip_path
        self._is_cancelled = False
        
    def run(self):
        try:
            self.log.emit("📦 Installing update...")
            
            extract_dir = os.path.join(os.path.dirname(self.zip_path), 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                total = len(zip_ref.namelist())
                for i, file_info in enumerate(zip_ref.infolist()):
                    if self._is_cancelled:
                        self.finished.emit(False, "Installation cancelled")
                        return
                    zip_ref.extract(file_info, extract_dir)
                    progress = int((i + 1) / total * 100)
                    self.progress.emit(progress, f"Extracting... {progress}%")
            
            self.log.emit("✅ Extraction complete")
            
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.getcwd()
            
            skip_files = [
                'ZAY_POS_Launcher.exe',
                'ZAY_POS_Launcher',
            ]
            
            self.log.emit(f"📂 Copying to: {app_dir}")
            copied = 0
            total_files = 0
            skipped = 0
            
            for root, dirs, files in os.walk(extract_dir):
                total_files += len(files)
            
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if self._is_cancelled:
                        self.finished.emit(False, "Installation cancelled")
                        return
                    
                    src = os.path.join(root, file)
                    rel_path = os.path.relpath(src, extract_dir)
                    dest = os.path.join(app_dir, rel_path)
                    
                    should_skip = False
                    for skip in skip_files:
                        if skip in file or skip in rel_path:
                            should_skip = True
                            break
                    
                    if should_skip:
                        skipped += 1
                        continue
                    
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    
                    try:
                        shutil.copy2(src, dest)
                    except PermissionError:
                        if os.path.exists(dest):
                            try:
                                old_path = dest + '.old'
                                if os.path.exists(old_path):
                                    os.remove(old_path)
                                os.rename(dest, old_path)
                                shutil.copy2(src, dest)
                            except:
                                continue
                    except:
                        continue
                    
                    copied += 1
                    
                    if total_files > 0:
                        progress = 90 + int((copied / total_files) * 10)
                        self.progress.emit(progress, f"Copying files... {copied}/{total_files}")
            
            self.log.emit(f"✅ Copied {copied} files ({skipped} skipped)")
            
            try:
                shutil.rmtree(os.path.dirname(self.zip_path))
            except:
                pass
            
            global CURRENT_VERSION
            version_file = os.path.join(app_dir, 'version.txt')
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'ProductVersion\s*=\s*["\']([\d.]+)["\']', content)
                    if match:
                        CURRENT_VERSION = match.group(1)
            
            self.finished.emit(True, f"Installed version {CURRENT_VERSION}")
            
        except Exception as e:
            self.log.emit(f"❌ Installation failed: {e}")
            self.finished.emit(False, str(e))
    
    def cancel(self):
        self._is_cancelled = True


class ModernButton(QPushButton):
    """Modern animated button."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._opacity = 1.0
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def enterEvent(self, event):
        self.animation.stop()
        self.animation.setEndValue(0.8)
        self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.animation.stop()
        self.animation.setEndValue(1.0)
        self.animation.start()
        super().leaveEvent(event)
    
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.setStyleSheet(f"QPushButton {{ opacity: {value}; }}")
    
    opacity = pyqtProperty(float, get_opacity, set_opacity)


class LauncherWindow(QMainWindow):
    """Main launcher window with modern design and logo."""
    
    def __init__(self):
        super().__init__()
        self.checker_thread = None
        self.download_thread = None
        self.install_thread = None
        self.update_info = None
        self.setup_ui()
        QTimer.singleShot(500, self.check_for_updates)
    
    def setup_ui(self):
        """Setup the modern user interface."""
        self.setWindowTitle("ZAY POS Launcher")
        self.setFixedSize(640, 560)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # 🔥 Set window icon from app_icon.ico
        window_icon = load_window_icon()
        if window_icon:
            self.setWindowIcon(window_icon)
            print("✅ Window icon loaded")
        else:
            print("⚠️ Window icon not found")
        
        # Set stylesheet
        self.setStyleSheet(STYLESHEET)
        
        # Center window
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Main widget
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 25, 30, 25)
        
        # ============================================================
        # HEADER WITH LOGO
        # ============================================================
        header_layout = QHBoxLayout()
        
        # 🔥 Logo from zaypos.png
        logo_pixmap = load_logo()
        if logo_pixmap:
            logo_label = QLabel()
            logo_label.setObjectName("logoLabel")
            logo_label.setPixmap(logo_pixmap)
            header_layout.addWidget(logo_label)
        else:
            # Fallback to emoji if logo not found
            icon_label = QLabel("⚡")
            icon_label.setStyleSheet("font-size: 36pt;")
            header_layout.addWidget(icon_label)
            print("⚠️ Logo not found, using fallback")
        
        # Title
        title_layout = QVBoxLayout()
        title_label = QLabel("ZAY POS")
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        
        sub_title = QLabel("Smart Point of Sale System")
        sub_title.setObjectName("subTitleLabel")
        title_layout.addWidget(sub_title)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Version badge
        version_badge = QLabel(f"v{CURRENT_VERSION}")
        version_badge.setStyleSheet("""
            QLabel {
                background: rgba(100, 255, 218, 0.15);
                color: #64ffda;
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 11pt;
                font-weight: bold;
                border: 1px solid rgba(100, 255, 218, 0.3);
            }
        """)
        header_layout.addWidget(version_badge)
        
        layout.addLayout(header_layout)
        
        # ============================================================
        # VERSION INFO
        # ============================================================
        version_group = QGroupBox("📊 Version Information")
        version_layout = QHBoxLayout()
        version_layout.setSpacing(30)
        
        # Current version
        current_widget = QWidget()
        current_layout = QVBoxLayout(current_widget)
        current_layout.setSpacing(2)
        current_label = QLabel("Current Version")
        current_label.setObjectName("versionLabel")
        current_layout.addWidget(current_label)
        self.current_version_label = QLabel(f"v{CURRENT_VERSION}")
        self.current_version_label.setObjectName("versionCurrent")
        current_layout.addWidget(self.current_version_label)
        version_layout.addWidget(current_widget)
        
        # Arrow
        arrow_label = QLabel("➜")
        arrow_label.setStyleSheet("color: #495670; font-size: 18pt;")
        version_layout.addWidget(arrow_label)
        
        # Latest version
        latest_widget = QWidget()
        latest_layout = QVBoxLayout(latest_widget)
        latest_layout.setSpacing(2)
        latest_label = QLabel("Latest Version")
        latest_label.setObjectName("versionLabel")
        latest_layout.addWidget(latest_label)
        self.latest_version_label = QLabel("Checking...")
        self.latest_version_label.setObjectName("versionLatest")
        latest_layout.addWidget(self.latest_version_label)
        version_layout.addWidget(latest_widget)
        
        version_layout.addStretch()
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        
        # ============================================================
        # STATUS
        # ============================================================
        status_group = QGroupBox("📌 Status")
        status_group.setObjectName("statusGroup")
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)
        
        self.status_label = QLabel("🔄 Initializing...")
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # ============================================================
        # LOG
        # ============================================================
        log_group = QGroupBox("📋 Log")
        log_group.setObjectName("logGroup")
        log_layout = QVBoxLayout()
        log_layout.setSpacing(5)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # ============================================================
        # BUTTONS
        # ============================================================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.start_btn = ModernButton("🚀 Start Application")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setMinimumHeight(45)
        self.start_btn.clicked.connect(self.start_app)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        
        self.update_btn = ModernButton("⬇️ Download Update")
        self.update_btn.setObjectName("updateBtn")
        self.update_btn.setMinimumHeight(45)
        self.update_btn.clicked.connect(self.download_update)
        self.update_btn.setEnabled(False)
        button_layout.addWidget(self.update_btn)
        
        self.skip_btn = ModernButton("⏭️ Skip")
        self.skip_btn.setObjectName("skipBtn")
        self.skip_btn.setMinimumHeight(45)
        self.skip_btn.clicked.connect(self.skip_update)
        self.skip_btn.setEnabled(False)
        button_layout.addWidget(self.skip_btn)
        
        layout.addLayout(button_layout)
        
        # ============================================================
        # FOOTER
        # ============================================================
        note_label = QLabel("ℹ️ Launcher checks for updates before starting the application")
        note_label.setObjectName("noteLabel")
        note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(note_label)
    
    def log(self, message: str):
        """Add log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        QApplication.processEvents()
    
    def check_for_updates(self):
        """Start update check."""
        self.log("🔍 Checking for updates...")
        self.status_label.setText("🔄 Checking for updates...")
        self.start_btn.setEnabled(False)
        self.update_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        
        self.checker_thread = UpdateCheckerThread()
        self.checker_thread.finished.connect(self.on_check_finished)
        self.checker_thread.error.connect(self.on_check_error)
        self.checker_thread.log.connect(self.log)
        self.checker_thread.start()
    
    def on_check_finished(self, result: dict):
        """Handle check completion."""
        latest_version = result.get('version', '')
        available = result.get('available', False)
        
        self.latest_version_label.setText(f"v{latest_version}")
        
        if available:
            self.update_info = result.get('data', {})
            self.status_label.setText("✅ New version available! Click Download Update.")
            self.status_label.setStyleSheet("color: #64ffda; font-size: 11pt;")
            self.update_btn.setEnabled(True)
            self.skip_btn.setEnabled(True)
            self.start_btn.setEnabled(False)
            self.log(f"📢 Update available: v{CURRENT_VERSION} → v{latest_version}")
        else:
            self.status_label.setText("✅ You have the latest version!")
            self.status_label.setStyleSheet("color: #64ffda; font-size: 11pt;")
            self.update_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)
            self.start_btn.setEnabled(True)
            self.log("✅ Application is up to date")
    
    def on_check_error(self, error: str):
        """Handle check error."""
        self.status_label.setText("⚠️ Update check failed")
        self.status_label.setStyleSheet("color: #fdcb6e; font-size: 11pt;")
        self.start_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.latest_version_label.setText("Unknown")
        self.log(f"⚠️ Update check failed: {error}")
        self.log("ℹ️ Starting application without update...")
    
    def download_update(self):
        """Start download process."""
        if not self.update_info:
            return
        
        download_url = None
        if 'assets' in self.update_info:
            for asset in self.update_info.get('assets', []):
                if asset['name'].endswith('.zip'):
                    download_url = asset['browser_download_url']
                    break
        elif 'download_url' in self.update_info:
            download_url = self.update_info['download_url']
        
        if not download_url:
            QMessageBox.warning(self, "Error", "No download URL found!")
            return
        
        version = self.update_info.get('tag_name', '').replace('v', '')
        if not version:
            version = self.update_info.get('version', '1.0.0')
        
        self.update_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.download_thread = DownloadThread(download_url, version)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.log.connect(self.log)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_progress(self, value: int, status: str):
        """Update download progress."""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
    
    def on_download_finished(self, success: bool, result: str):
        """Handle download completion."""
        if success:
            self.log("✅ Download complete")
            self.status_label.setText("📦 Installing update...")
            
            self.install_thread = InstallThread(result)
            self.install_thread.progress.connect(self.on_install_progress)
            self.install_thread.log.connect(self.log)
            self.install_thread.finished.connect(self.on_install_finished)
            self.install_thread.start()
        else:
            self.status_label.setText("❌ Download failed")
            self.status_label.setStyleSheet("color: #ff6b6b; font-size: 11pt;")
            self.update_btn.setEnabled(True)
            self.skip_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_install_progress(self, value: int, status: str):
        """Update install progress."""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
    
    def on_install_finished(self, success: bool, message: str):
        """Handle install completion."""
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("✅ Update installed successfully!")
            self.status_label.setStyleSheet("color: #64ffda; font-size: 11pt;")
            self.current_version_label.setText(f"v{CURRENT_VERSION}")
            
            reply = QMessageBox.question(
                self,
                "✨ Update Complete",
                f"ZAY POS has been updated to version {CURRENT_VERSION}!\n\n"
                "🔄 The launcher will restart to apply changes.\n\n"
                "Would you like to restart now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.restart_launcher()
            else:
                self.start_app()
        else:
            self.status_label.setText("❌ Installation failed")
            self.status_label.setStyleSheet("color: #ff6b6b; font-size: 11pt;")
            self.update_btn.setEnabled(True)
            self.skip_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
    
    def restart_launcher(self):
        """Restart the launcher."""
        self.log("🔄 Restarting launcher...")
        try:
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                subprocess.Popen([exe_path])
            else:
                subprocess.Popen([sys.executable, 'launcher.py'])
            
            QTimer.singleShot(500, self.close)
        except Exception as e:
            self.log(f"❌ Failed to restart: {e}")
            self.start_app()
    
    def start_app(self):
        """Start the main application."""
        self.log("🚀 Starting ZAY POS...")
        
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.getcwd()
        
        app_path = os.path.join(app_dir, 'ZAY_POS.exe')
        
        if os.path.exists(app_path):
            self.log(f"📂 Found: {app_path}")
            try:
                subprocess.Popen([app_path])
                self.log("✅ Application started!")
                QTimer.singleShot(1000, self.close)
            except Exception as e:
                self.log(f"❌ Failed to start: {e}")
                QMessageBox.critical(self, "Error", f"Failed to start application: {e}")
        else:
            self.log(f"❌ Application not found: {app_path}")
            QMessageBox.warning(
                self,
                "Error",
                f"Application not found: {app_path}\n\nPlease check your installation."
            )
    
    def skip_update(self):
        """Skip update and start app."""
        self.log("⏭️ Skipping update...")
        self.start_app()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = LauncherWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()