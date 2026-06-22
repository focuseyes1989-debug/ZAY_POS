# updater/update_worker.py
"""
Background worker for downloading and installing updates.
"""

import os
import sys
import json
import shutil
import hashlib
import tempfile
import zipfile
import subprocess
from datetime import datetime
from typing import Optional, Dict
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from loguru import logger
import requests


class UpdateWorker(QThread):
    """Background worker for update operations."""
    
    # Signals
    progress = pyqtSignal(int, str)  # progress value, status message
    log_message = pyqtSignal(str)    # log message
    finished = pyqtSignal(bool, str) # success, message
    version_info = pyqtSignal(dict)  # version info from server
    
    def __init__(self, update_info: Dict):
        super().__init__()
        self.update_info = update_info
        self.download_path = None
        self.extract_path = None
        self._is_cancelled = False
    
    def cancel(self):
        """Cancel the update process."""
        self._is_cancelled = True
    
    def run(self):
        """Main update process."""
        try:
            # Step 1: Download update
            self.progress.emit(5, "Downloading update...")
            self.log_message.emit("📥 Starting download...")
            
            download_path = self._download_update()
            if self._is_cancelled:
                return
            
            self.progress.emit(40, "Download complete. Extracting...")
            self.log_message.emit("📦 Download complete")
            
            # Step 2: Verify file
            self.progress.emit(45, "Verifying file...")
            if not self._verify_file(download_path):
                raise Exception("File verification failed")
            
            # Step 3: Extract update
            extract_path = self._extract_update(download_path)
            if self._is_cancelled:
                return
            
            self.progress.emit(70, "Extraction complete. Preparing installation...")
            self.log_message.emit("📂 Extraction complete")
            
            # Step 4: Prepare update script
            self.progress.emit(80, "Preparing installation...")
            self.log_message.emit("🔄 Preparing installation")
            
            # Step 5: Create installer script
            installer_path = self._create_installer_script(extract_path)
            if self._is_cancelled:
                return
            
            self.progress.emit(90, "Installation ready. Please wait...")
            self.log_message.emit("✅ Update ready to install")
            
            # Step 6: Run installer
            self.progress.emit(95, "Installing update...")
            self._run_installer(installer_path)
            
            self.progress.emit(100, "Update completed!")
            self.log_message.emit("🎉 Update completed successfully!")
            self.finished.emit(True, "Update installed successfully")
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self.log_message.emit(f"❌ Error: {str(e)}")
            self.finished.emit(False, str(e))
    
    def _download_update(self) -> str:
        """Download the update file."""
        url = self.update_info.get('download_url')
        if not url:
            raise Exception("No download URL provided")
        
        # Create temp directory
        temp_dir = os.path.join(tempfile.gettempdir(), 'zaypos_update')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Get filename from URL
        filename = os.path.basename(url)
        if not filename:
            filename = f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        download_path = os.path.join(temp_dir, filename)
        self.download_path = download_path
        
        # Download with progress
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._is_cancelled:
                        f.close()
                        os.remove(download_path)
                        raise Exception("Download cancelled")
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        self.progress.emit(5 + int(progress * 0.35), f"Downloading: {progress}%")
            
            return download_path
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Download failed: {e}")
    
    def _verify_file(self, file_path: str) -> bool:
        """Verify the downloaded file."""
        expected_hash = self.update_info.get('file_hash')
        if not expected_hash:
            self.log_message.emit("⚠️ No hash provided, skipping verification")
            return True
        
        self.log_message.emit(f"🔐 Verifying file: {expected_hash[:8]}...")
        
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                if self._is_cancelled:
                    return False
                sha256.update(chunk)
        
        actual_hash = sha256.hexdigest()
        is_valid = actual_hash == expected_hash
        
        if is_valid:
            self.log_message.emit("✅ File verification passed")
        else:
            self.log_message.emit(f"❌ File verification failed")
            self.log_message.emit(f"Expected: {expected_hash}")
            self.log_message.emit(f"Actual:   {actual_hash}")
        
        return is_valid
    
    def _extract_update(self, file_path: str) -> str:
        """Extract the update package."""
        extract_dir = os.path.join(os.path.dirname(file_path), 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        self.extract_path = extract_dir
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            files = zip_ref.namelist()
            total = len(files)
            
            for i, file in enumerate(files):
                if self._is_cancelled:
                    shutil.rmtree(extract_dir, ignore_errors=True)
                    raise Exception("Extraction cancelled")
                
                zip_ref.extract(file, extract_dir)
                progress = int((i + 1) / total * 30)
                self.progress.emit(40 + progress, f"Extracting: {file}")
        
        return extract_dir
    
    def _create_installer_script(self, extract_path: str) -> str:
        """Create an installer script for the update."""
        # Look for the executable
        exe_files = []
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if file.endswith('.exe'):
                    exe_files.append(os.path.join(root, file))
                    break
        
        if not exe_files:
            # If no .exe found, use the extracted folder
            installer_script = os.path.join(extract_path, 'update_installer.py')
            
            installer_content = f'''
import os
import sys
import shutil
import subprocess
import time

def main():
    """Install update."""
    app_dir = os.path.dirname(sys.executable)
    update_dir = r"{extract_path}"
    
    # Wait for app to close
    time.sleep(2)
    
    try:
        # Copy all files from update to app directory
        for root, dirs, files in os.walk(update_dir):
            for file in files:
                if file == 'update_installer.py':
                    continue
                src = os.path.join(root, file)
                rel_path = os.path.relpath(src, update_dir)
                dst = os.path.join(app_dir, rel_path)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        
        print("Update installed successfully!")
        
        # Restart application
        exe_path = os.path.join(app_dir, "ZAY_POS.exe")
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path])
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Installation failed: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
            with open(installer_script, 'w') as f:
                f.write(installer_content)
            
            return installer_script
        
        else:
            # Use the extracted .exe
            return exe_files[0]
    
    def _run_installer(self, installer_path: str):
        """Run the installer script."""
        if installer_path.endswith('.py'):
            # Run Python script
            subprocess.Popen([
                sys.executable,
                installer_path
            ], creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0)
        else:
            # Run executable
            subprocess.Popen([installer_path], shell=True)
        
        # Exit the current application
        QTimer.singleShot(1000, lambda: sys.exit(0))