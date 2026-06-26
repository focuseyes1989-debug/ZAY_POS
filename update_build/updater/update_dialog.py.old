# updater/update_dialog.py
"""
Update dialogs for ZAY POS.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QGroupBox,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon


class UpdateDialog(QDialog):
    """Dialog showing update availability."""
    
    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("Update Available")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Title
        title_layout = QHBoxLayout()
        icon_label = QLabel("🔄")
        icon_label.setStyleSheet("font-size: 36pt;")
        title_layout.addWidget(icon_label)
        
        title_text = QLabel(f"Update Available: v{update_info.get('version', '')}")
        title_text.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2c3e50;")
        title_layout.addWidget(title_text)
        layout.addLayout(title_layout)
        
        # Version info
        info_group = QGroupBox("Version Information")
        info_layout = QVBoxLayout()
        
        info_layout.addWidget(QLabel(f"Current Version: {self._get_current_version()}"))
        info_layout.addWidget(QLabel(f"New Version: {update_info.get('version', '')}"))
        info_layout.addWidget(QLabel(f"Release Date: {update_info.get('release_date', '')}"))
        info_layout.addWidget(QLabel(f"File Size: {self._format_size(update_info.get('file_size', 0))}"))
        
        if update_info.get('mandatory'):
            mandatory_label = QLabel("⚠️ This is a mandatory update")
            mandatory_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            info_layout.addWidget(mandatory_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Release notes
        notes_group = QGroupBox("Release Notes")
        notes_layout = QVBoxLayout()
        
        notes_text = QTextEdit()
        notes_text.setPlainText(update_info.get('release_notes', 'No release notes available.'))
        notes_text.setReadOnly(True)
        notes_text.setMaximumHeight(150)
        notes_layout.addWidget(notes_text)
        
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        # Buttons
        button_box = QDialogButtonBox()
        btn_update = QPushButton("Download & Install")
        btn_update.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        btn_update.clicked.connect(self.accept)
        
        btn_skip = QPushButton("Skip")
        btn_skip.clicked.connect(self.reject)
        
        btn_later = QPushButton("Remind Later")
        btn_later.clicked.connect(self.reject)
        
        button_box.addButton(btn_skip, QDialogButtonBox.ButtonRole.RejectRole)
        button_box.addButton(btn_later, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(btn_update, QDialogButtonBox.ButtonRole.AcceptRole)
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        self.retranslateUi()
    
    def _get_current_version(self) -> str:
        """Get current application version."""
        try:
            from updater.version_manager import VersionManager
            return VersionManager().get_current_version()
        except:
            return "1.0.0"
    
    def _format_size(self, size: int) -> str:
        """Format file size."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
    
    def retranslateUi(self):
        """Translate UI."""
        pass


class UpdateProgressDialog(QDialog):
    """Dialog showing update progress."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Installing Update")
        self.setMinimumSize(500, 300)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("📦 Installing Update")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Status
        self.status_label = QLabel("Preparing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Log
        log_group = QGroupBox("Details")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 10pt;")
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Cancel button
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._cancel)
        layout.addWidget(self.btn_cancel, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
        self._is_cancelled = False
    
    def update_progress(self, value: int, status: str):
        """Update progress bar and status."""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
    
    def add_log(self, message: str):
        """Add log message."""
        self.log_text.append(message)
        # Auto scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def show_complete(self, message: str):
        """Show completion status."""
        self.status_label.setText("✅ " + message)
        self.status_label.setStyleSheet("color: #27ae60;")
        self.btn_cancel.setText("Close")
        self.btn_cancel.setEnabled(True)
    
    def show_error(self, message: str):
        """Show error status."""
        self.status_label.setText("❌ " + message)
        self.status_label.setStyleSheet("color: #e74c3c;")
        self.btn_cancel.setText("Close")
        self.btn_cancel.setEnabled(True)
    
    def _cancel(self):
        """Cancel the update."""
        self._is_cancelled = True
        self.accept()