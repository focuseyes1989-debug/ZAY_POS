# updater/update_manager.py
"""
Main update manager for ZAY POS.
"""

import os
import json
import requests
from typing import Optional, Dict
from datetime import datetime
from loguru import logger
from PyQt6.QtWidgets import QMessageBox

from updater.version_manager import VersionManager, VersionInfo
from updater.update_worker import UpdateWorker
from updater.update_dialog import UpdateDialog


class UpdateManager:
    """Main update manager."""
    
    # ✅ UPDATE: Change this to your actual GitHub repo
    UPDATE_SERVER = "https://api.github.com/repos/YOUR_USERNAME/ZAY_POS/releases/latest"
    # Or local server
    LOCAL_UPDATE_SERVER = "http://localhost:8000/update/version.json"
    
    def __init__(self, parent=None):
        self.parent = parent
        self.version_manager = VersionManager()
        self.worker = None
        self.update_dialog = None
        self.update_info = None  # Store update info
        
        # Check if using GitHub or local
        self.update_url = self.UPDATE_SERVER
        self.use_github = True
    
    def set_update_server(self, url: str):
        """Set custom update server URL."""
        self.update_url = url
        self.use_github = False
    
    def check_for_updates(self, show_no_update_msg: bool = True) -> bool:
        """
        Check for updates on the server.
        
        Returns:
            bool: True if update is available
        """
        try:
            logger.info("Checking for updates...")
            
            # Get version info from server
            version_info = self._fetch_version_info()
            
            if not version_info:
                logger.warning("Could not fetch version info")
                if show_no_update_msg:
                    QMessageBox.information(
                        self.parent,
                        "Check Update",
                        "Could not check for updates. Please check your internet connection."
                    )
                return False
            
            current_version = self.version_manager.get_current_version()
            latest_version = version_info.get('version', '')
            
            # Check if update is available
            is_available = self.version_manager.is_update_available(latest_version)
            
            if is_available:
                logger.info(f"Update available: {current_version} -> {latest_version}")
                
                # Store update info
                self.update_info = {
                    'version': latest_version,
                    'download_url': version_info.get('download_url', ''),
                    'file_hash': version_info.get('file_hash', ''),
                    'file_size': version_info.get('file_size', 0),
                    'release_notes': version_info.get('release_notes', ''),
                    'release_date': version_info.get('release_date', ''),
                    'mandatory': version_info.get('mandatory', False)
                }
                
                # Show update dialog
                self._show_update_dialog(self.update_info)
                return True
                
            else:
                logger.info(f"No update available. Current: {current_version}")
                if show_no_update_msg:
                    QMessageBox.information(
                        self.parent,
                        "Check Update",
                        f"You are using the latest version ({current_version})."
                    )
                return False
                
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            if show_no_update_msg:
                QMessageBox.warning(
                    self.parent,
                    "Check Update",
                    f"Failed to check for updates: {str(e)}"
                )
            return False
    
    def _fetch_version_info(self) -> Optional[Dict]:
        """Fetch version information from server."""
        try:
            if self.use_github:
                response = requests.get(self.update_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Parse GitHub release data
                assets = data.get('assets', [])
                asset = assets[0] if assets else {}
                
                return {
                    'version': data.get('tag_name', '').replace('v', ''),
                    'download_url': asset.get('browser_download_url', ''),
                    'file_hash': '',  # GitHub doesn't provide hash in API
                    'file_size': asset.get('size', 0),
                    'release_notes': data.get('body', 'No release notes available.'),
                    'release_date': data.get('published_at', ''),
                    'mandatory': False
                }
            else:
                # Local server
                response = requests.get(self.update_url, timeout=10)
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def _show_update_dialog(self, update_info: Dict):
        """Show update dialog to user."""
        dialog = UpdateDialog(update_info, self.parent)
        
        if dialog.exec() == UpdateDialog.DialogCode.Accepted:
            # User chose to update
            self._start_update(update_info)
    
    def _start_update(self, update_info: Dict):
        """Start the update process."""
        # Show progress dialog
        from updater.update_dialog import UpdateProgressDialog
        progress_dialog = UpdateProgressDialog(self.parent)
        
        # Create worker
        self.worker = UpdateWorker(update_info)
        self.worker.progress.connect(progress_dialog.update_progress)
        self.worker.log_message.connect(progress_dialog.add_log)
        self.worker.finished.connect(lambda success, msg: self._on_update_finished(success, msg, progress_dialog))
        
        # Show dialog
        progress_dialog.show()
        
        # Start worker
        self.worker.start()
    
    def _on_update_finished(self, success: bool, message: str, progress_dialog):
        """Handle update completion."""
        if success:
            progress_dialog.show_complete(message)
            
            # Update version info
            version_info = self.version_manager.load_update_metadata()
            version_info['last_update'] = datetime.now().isoformat()
            version_info['last_version'] = self.version_manager.get_current_version()
            self.version_manager.save_update_metadata(version_info)
            
            # Show restart message
            QMessageBox.information(
                self.parent,
                "Update Complete",
                f"Update installed successfully!\n\n"
                "The application will restart."
            )
        else:
            progress_dialog.show_error(message)
    
    def get_update_status(self) -> Dict:
        """Get current update status."""
        metadata = self.version_manager.load_update_metadata()
        return {
            'current_version': self.version_manager.get_current_version(),
            'last_update': metadata.get('last_update'),
            'last_version': metadata.get('last_version'),
            'db_version': self.version_manager.get_db_version()
        }