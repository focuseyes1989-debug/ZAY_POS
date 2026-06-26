# utils/cleanup.py

import os
import sys
import subprocess
import tempfile

def cleanup_mei_folders():
    """Clean up orphaned _MEI folders."""
    try:
        temp_dir = tempfile.gettempdir()
        
        # Find all _MEI folders
        mei_folders = []
        for item in os.listdir(temp_dir):
            if item.startswith('_MEI') and os.path.isdir(os.path.join(temp_dir, item)):
                mei_folders.append(os.path.join(temp_dir, item))
        
        if mei_folders:
            print(f"Found {len(mei_folders)} _MEI folders")
            
            # Create a batch file to delete on next boot
            batch_path = os.path.join(temp_dir, 'cleanup_mei.bat')
            with open(batch_path, 'w') as f:
                f.write('@echo off\n')
                f.write('timeout /t 2 /nobreak > nul\n')
                for folder in mei_folders:
                    f.write(f'rmdir /s /q "{folder}"\n')
                f.write(f'del "%~f0"\n')
            
            # Run batch file
            subprocess.Popen(
                [batch_path],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print(f"✅ Created cleanup script: {batch_path}")
            
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

# Call on startup
cleanup_mei_folders()