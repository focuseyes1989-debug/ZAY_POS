# ui/settings/update_setting.py
"""
Update settings tab for ZAY POS.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QCheckBox, QMessageBox, QProgressBar,
    QTextEdit, QDialog, QDialogButtonBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from loguru import logger

from updater.update_manager import UpdateManager
from updater.version_manager import VersionManager
from utils.language import lang
from utils.permissions import PermissionManager, Permission


class UpdateSettingWidget(QWidget):
    """Update settings widget."""
    
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.update_manager = UpdateManager(self)
        self.version_manager = VersionManager()
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
        """Check for updates manually."""
        self.btn_check.setEnabled(False)
        self.status_label.setText("🔄 Checking for updates...")
        self.status_label.setStyleSheet("color: #f39c12;")
        QApplication.processEvents()
        
        # Run in background
        try:
            QTimer.singleShot(100, self._perform_update_check)
        except Exception as e:
            self.btn_check.setEnabled(True)
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c;")
    
    def _perform_update_check(self):
        """Perform the actual update check."""
        try:
            has_update = self.update_manager.check_for_updates(show_no_update_msg=True)
            
            if has_update:
                self.status_label.setText("🔄 Update available! Please install.")
                self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                
                # Get update info from manager
                if hasattr(self.update_manager, 'update_info'):
                    info = self.update_manager.update_info
                    if info:
                        self.update_info_label.setText(
                            f"Version {info.get('version')} available"
                        )
                        self.notes_text.setPlainText(
                            info.get('release_notes', 'No release notes available.')
                        )
            else:
                self.status_label.setText("✅ You are using the latest version.")
                self.status_label.setStyleSheet("color: #27ae60;")
                self.update_info_label.setText("")
                self.notes_text.clear()
                
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c;")
            logger.error(f"Update check failed: {e}")
        finally:
            self.btn_check.setEnabled(True)
    
    def retranslateUi(self):
        """Translate UI."""
        # Check if widgets exist before setting text
        if lang.get_current() == "my":
            if hasattr(self, 'version_group'):
                self.version_group.setTitle("ဗားရှင်းအချက်အလက်")
            if hasattr(self, 'check_group'):
                self.check_group.setTitle("အပ်ဒိတ်စစ်ဆေးခြင်း")
            if hasattr(self, 'btn_check'):
                self.btn_check.setText("အပ်ဒိတ်စစ်ဆေးရန်")
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
            if hasattr(self, 'chk_auto_check'):
                self.chk_auto_check.setText("Check for updates automatically")
            if hasattr(self, 'status_group'):
                self.status_group.setTitle("Status")
            if hasattr(self, 'notes_group'):
                self.notes_group.setTitle("Release Notes")
        
        # Reload version info to update language
        self.load_current_version()