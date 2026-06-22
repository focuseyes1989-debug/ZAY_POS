# ui/dashboard/dashboard_backup.py
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer
from datetime import datetime
from loguru import logger


class DashboardBackupStatus:
    """Handle backup status display and updates"""
    
    @staticmethod
    def update_backup_status(parent, backup_manager):
        """Update the backup status display on dashboard"""
        try:
            if not hasattr(parent, 'backup_card'):
                return
            
            last_backup = backup_manager.get_last_backup_time_str()
            parent.backup_card.status_label.setText(f"Last Backup: {last_backup}")
            
            # Set icon based on backup age
            last_time = backup_manager.get_last_backup_time()
            if last_time:
                days_since = (datetime.now() - last_time).days
                if days_since > 7:
                    parent.backup_card.icon_label.setText("⚠️")
                    parent.backup_card.icon_label.setStyleSheet("font-size: 24pt;")
                    parent.backup_card.status_label.setStyleSheet("font-size: 10pt; color: #e67e22;")
                    parent.backup_card.status_label.setText(f"Last Backup: {last_backup} (⚠️ {days_since} days ago)")
                elif days_since > 1:
                    parent.backup_card.icon_label.setText("🕐")
                    parent.backup_card.icon_label.setStyleSheet("font-size: 24pt;")
                    parent.backup_card.status_label.setStyleSheet("font-size: 10pt; color: #f39c12;")
                else:
                    parent.backup_card.icon_label.setText("✅")
                    parent.backup_card.icon_label.setStyleSheet("font-size: 24pt;")
                    parent.backup_card.status_label.setStyleSheet("font-size: 10pt; color: #27ae60;")
            else:
                parent.backup_card.icon_label.setText("❌")
                parent.backup_card.icon_label.setStyleSheet("font-size: 24pt;")
                parent.backup_card.status_label.setStyleSheet("font-size: 10pt; color: #e74c3c;")
        except Exception as e:
            logger.error(f"Failed to update backup status: {e}")