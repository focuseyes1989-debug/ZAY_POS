# ui/settings/update_setting.py
"""
Update settings tab for ZAY POS - Now uses launcher-based update system.
"""

import os
import sys
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QCheckBox, QMessageBox, QProgressBar,
    QTextEdit, QDialog, QDialogButtonBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon
from loguru import logger

from updater.version_manager import VersionManager
from utils.language import lang
from utils.permissions import PermissionManager, Permission


class UpdateCheckerThread(QThread):
    """Background thread for checking updates via launcher."""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            # Check if launcher exists
            launcher_path = self.find_launcher()
            if not launcher_path:
                self.error.emit("Launcher not found")
                return
            
            # Check for updates by running launcher with --check-only flag
            result = subprocess.run(
                [launcher_path, '--check-only'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse output for version info
                output = result.stdout
                version_info = self.parse_output(output)
                self.finished.emit(version_info)
            else:
                self.error.emit("Update check failed")
                
        except subprocess.TimeoutExpired:
            self.error.emit("Update check timed out")
        except Exception as e:
            self.error.emit(str(e))
    
    def find_launcher(self) -> str:
        """Find launcher executable."""
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.getcwd()
        
        launcher_names = [
            'ZAY_POS_Launcher.exe',
            'launcher.exe',
            'ZAY_Launcher.exe'
        ]
        
        for name in launcher_names:
            launcher_path = os.path.join(app_dir, name)
            if os.path.exists(launcher_path):
                return launcher_path
        
        # Check parent directory
        parent_dir = os.path.dirname(app_dir)
        for name in launcher_names:
            launcher_path = os.path.join(parent_dir, name)
            if os.path.exists(launcher_path):
                return launcher_path
        
        return None
    
    def parse_output(self, output: str) -> dict:
        """Parse launcher output for version info."""
        info = {
            'version': '',
            'release_notes': '',
            'download_url': '',
            'file_size': 0
        }
        
        lines = output.split('\n')
        for line in lines:
            if 'version:' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    info['version'] = parts[1].strip()
            elif 'notes:' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    info['release_notes'] = parts[1].strip()
            elif 'url:' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    info['download_url'] = ':'.join(parts[1:]).strip()
            elif 'size:' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        info['file_size'] = int(parts[1].strip())
                    except:
                        pass
        
        return info


class UpdateSettingWidget(QWidget):
    """Update settings widget."""
    
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.version_manager = VersionManager()
        self.checker_thread = None
        self.setup_ui()
        self.load_current_version()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Version Information Group
        self.version_group = QGroupBox()
        version_layout = QVBoxLayout()
        
        # Current version
        self.current_version_label = QLabel()
        self.current_version_label.setStyleSheet("font-size: 12pt;")
        version_layout.addWidget(self.current_version_label)
        
        # Database version
        self.db_version_label = QLabel()
        self.db_version_label.setStyleSheet("font-size: 10pt; color: #7f8c8d;")
        version_layout.addWidget(self.db_version_label)
        
        # Last update check
        self.last_check_label = QLabel()
        self.last_check_label.setStyleSheet("font-size: 10pt; color: #7f8c8d;")
        version_layout.addWidget(self.last_check_label)
        
        # Launcher status
        self.launcher_status_label = QLabel()
        self.launcher_status_label.setStyleSheet("font-size: 10pt; color: #3498db;")
        version_layout.addWidget(self.launcher_status_label)
        
        self.version_group.setLayout(version_layout)
        layout.addWidget(self.version_group)
        
        # Update Check Group
        self.check_group = QGroupBox()
        check_layout = QVBoxLayout()
        
        # Check for updates button
        btn_layout = QHBoxLayout()
        self.btn_check = QPushButton()
        self.btn_check.clicked.connect(self.check_for_updates)
        self.btn_check.setFixedWidth(200)
        btn_layout.addWidget(self.btn_check)
        
        self.btn_launcher = QPushButton()
        self.btn_launcher.clicked.connect(self.open_launcher)
        self.btn_launcher.setFixedWidth(150)
        btn_layout.addWidget(self.btn_launcher)
        
        btn_layout.addStretch()
        check_layout.addLayout(btn_layout)
        
        # Auto-check checkbox
        self.chk_auto_check = QCheckBox()
        self.chk_auto_check.toggled.connect(self.toggle_auto_check)
        check_layout.addWidget(self.chk_auto_check)
        
        self.check_group.setLayout(check_layout)
        layout.addWidget(self.check_group)
        
        # Update Status Group
        self.status_group = QGroupBox()
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #27ae60;")
        status_layout.addWidget(self.status_label)
        
        self.update_info_label = QLabel()
        self.update_info_label.setWordWrap(True)
        self.update_info_label.setStyleSheet("color: #3498db; font-size: 10pt;")
        status_layout.addWidget(self.update_info_label)
        
        self.status_group.setLayout(status_layout)
        layout.addWidget(self.status_group)
        
        # Release Notes
        self.notes_group = QGroupBox()
        notes_layout = QVBoxLayout()
        
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setMaximumHeight(150)
        self.notes_text.setPlaceholderText("No release notes available.")
        notes_layout.addWidget(self.notes_text)
        
        self.notes_group.setLayout(notes_layout)
        layout.addWidget(self.notes_group)
        
        layout.addStretch()
        self.setLayout(layout)
        self.retranslateUi()
        
        # Load auto-check setting
        self.load_auto_check_setting()
        
        # Check launcher status
        self.check_launcher_status()
    
    def check_launcher_status(self):
        """Check if launcher is available."""
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.getcwd()
        
        launcher_path = os.path.join(app_dir, 'ZAY_POS_Launcher.exe')
        if os.path.exists(launcher_path):
            self.launcher_status_label.setText("✅ Launcher available")
            self.launcher_status_label.setStyleSheet("color: #27ae60;")
            self.btn_launcher.setEnabled(True)
        else:
            self.launcher_status_label.setText("⚠️ Launcher not found")
            self.launcher_status_label.setStyleSheet("color: #f39c12;")
            self.btn_launcher.setEnabled(False)
    
    def open_launcher(self):
        """Open the launcher directly."""
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.getcwd()
        
        launcher_path = os.path.join(app_dir, 'ZAY_POS_Launcher.exe')
        if os.path.exists(launcher_path):
            try:
                subprocess.Popen([launcher_path])
                logger.info("Launcher opened from settings")
                QMessageBox.information(
                    self,
                    "Launcher",
                    "Launcher is now running in the background.\n"
                    "It will check for updates and restart the app if needed."
                )
            except Exception as e:
                logger.error(f"Failed to open launcher: {e}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to open launcher: {e}"
                )
    
    def load_current_version(self):
        """Load and display current version information."""
        try:
            current_version = self.version_manager.get_current_version()
            self.current_version_label.setText(
                f"Current Version: v{current_version}"
            )
            
            # Get database version
            db_version = self.version_manager.get_db_version()
            self.db_version_label.setText(
                f"Database Version: v{db_version}"
            )
            
            # Get last update check
            metadata = self.version_manager.load_update_metadata()
            last_update = metadata.get('last_update', '')
            if last_update:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_update)
                    self.last_check_label.setText(
                        f"Last Update Check: {dt.strftime('%Y-%m-%d %H:%M')}"
                    )
                except:
                    self.last_check_label.setText("Last Update Check: Never")
            else:
                self.last_check_label.setText("Last Update Check: Never")
                
        except Exception as e:
            logger.error(f"Failed to load version info: {e}")
    
    def load_auto_check_setting(self):
        """Load auto-check setting from database."""
        try:
            from models.database import get_setting
            auto_check = get_setting('auto_update_check', '1')
            self.chk_auto_check.setChecked(auto_check == '1')
        except Exception as e:
            logger.error(f"Failed to load auto-check setting: {e}")
            self.chk_auto_check.setChecked(True)
    
    def toggle_auto_check(self, checked):
        """Toggle auto-check setting."""
        try:
            from models.database import update_setting
            update_setting('auto_update_check', '1' if checked else '0')
            logger.info(f"Auto-update check set to: {checked}")
        except Exception as e:
            logger.error(f"Failed to save auto-check setting: {e}")
    
    def check_for_updates(self):
        """Check for updates using launcher."""
        self.btn_check.setEnabled(False)
        self.status_label.setText("🔄 Checking for updates...")
        self.status_label.setStyleSheet("color: #f39c12;")
        QApplication.processEvents()
        
        # Run in background thread
        self.checker_thread = UpdateCheckerThread()
        self.checker_thread.finished.connect(self.on_check_finished)
        self.checker_thread.error.connect(self.on_check_error)
        self.checker_thread.start()
    
    def on_check_finished(self, version_info):
        """Handle update check completion."""
        self.btn_check.setEnabled(True)
        
        if version_info and version_info.get('version'):
            current_version = self.version_manager.get_current_version()
            latest_version = version_info.get('version', '')
            
            if self.version_manager.compare_versions(current_version, latest_version) < 0:
                self.status_label.setText(f"🔄 Update available: v{latest_version}")
                self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.update_info_label.setText(
                    f"Version {latest_version} available\n"
                    "Click 'Open Launcher' to install the update"
                )
                self.notes_text.setPlainText(
                    version_info.get('release_notes', 'No release notes available.')
                )
            else:
                self.status_label.setText("✅ You are using the latest version.")
                self.status_label.setStyleSheet("color: #27ae60;")
                self.update_info_label.setText("")
                self.notes_text.clear()
        else:
            self.status_label.setText("ℹ️ No update information available.")
            self.status_label.setStyleSheet("color: #3498db;")
    
    def on_check_error(self, error):
        """Handle update check error."""
        self.btn_check.setEnabled(True)
        self.status_label.setText(f"❌ Error: {error}")
        self.status_label.setStyleSheet("color: #e74c3c;")
        logger.error(f"Update check failed: {error}")
    
    def retranslateUi(self):
        """Translate UI."""
        if lang.get_current() == "my":
            if hasattr(self, 'version_group'):
                self.version_group.setTitle("ဗားရှင်းအချက်အလက်")
            if hasattr(self, 'check_group'):
                self.check_group.setTitle("အပ်ဒိတ်စစ်ဆေးခြင်း")
            if hasattr(self, 'btn_check'):
                self.btn_check.setText("အပ်ဒိတ်စစ်ဆေးရန်")
            if hasattr(self, 'btn_launcher'):
                self.btn_launcher.setText("Launcher ဖွင့်ရန်")
            if hasattr(self, 'chk_auto_check'):
                self.chk_auto_check.setText("အလိုအလျောက်အပ်ဒိတ်စစ်ဆေးရန်")
            if hasattr(self, 'status_group'):
                self.status_group.setTitle("အခြေအနေ")
            if hasattr(self, 'notes_group'):
                self.notes_group.setTitle("ထုတ်ပြန်ချက်များ")
        else:
            if hasattr(self, 'version_group'):
                self.version_group.setTitle("Version Information")
            if hasattr(self, 'check_group'):
                self.check_group.setTitle("Update Check")
            if hasattr(self, 'btn_check'):
                self.btn_check.setText("Check for Updates")
            if hasattr(self, 'btn_launcher'):
                self.btn_launcher.setText("Open Launcher")
            if hasattr(self, 'chk_auto_check'):
                self.chk_auto_check.setText("Check for updates automatically")
            if hasattr(self, 'status_group'):
                self.status_group.setTitle("Status")
            if hasattr(self, 'notes_group'):
                self.notes_group.setTitle("Release Notes")
        
        self.load_current_version()