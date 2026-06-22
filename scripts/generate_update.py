# scripts/generate_update.py
"""
Generate update package for ZAY POS.
"""

import os
import sys
import json
import hashlib
import zipfile
import shutil
from datetime import datetime
from pathlib import Path


def generate_update():
    """Generate update package."""
    print("=" * 60)
    print("ZAY POS Update Generator")
    print("=" * 60)
    
    # Version
    version = input("Enter version (e.g., 1.0.1): ").strip()
    if not version:
        version = "1.0.1"
    
    print(f"Generating update for version: {version}")
    
    # Create update directory
    update_dir = Path("update_build")
    if update_dir.exists():
        shutil.rmtree(update_dir)
    update_dir.mkdir()
    
    # Copy necessary files
    files_to_include = [
        "ZAY_POS.exe",
        "assets/",
        "main.py",
        "version.txt",
    ]
    
    # Copy files
    for item in files_to_include:
        src = Path(item)
        if src.exists():
            dst = update_dir / src.name
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            print(f"✅ Added: {item}")
    
    # Create update zip
    zip_name = f"ZAY_POS_v{version}.zip"
    zip_path = update_dir / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in update_dir.rglob('*'):
            if file.name == zip_name:
                continue
            arcname = file.relative_to(update_dir)
            zipf.write(file, arcname)
    
    print(f"✅ Created: {zip_name}")
    
    # Calculate hash
    sha256 = hashlib.sha256()
    with open(zip_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    file_hash = sha256.hexdigest()
    
    # Create version.json
    version_info = {
        "version": version,
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "release_notes": f"Version {version} released",
        "download_url": f"http://localhost:8000/update/{zip_name}",
        "file_hash": file_hash,
        "file_size": os.path.getsize(zip_path),
        "mandatory": False,
        "min_required_version": "1.0.0"
    }
    
    with open(update_dir / "version.json", 'w') as f:
        json.dump(version_info, f, indent=2)
    
    print(f"✅ Created: version.json")
    print("=" * 60)
    print("Update package created successfully!")
    print(f"📁 Location: {update_dir}")
    print(f"📦 File: {zip_path}")
    print(f"🔐 Hash: {file_hash}")
    print("=" * 60)
    
    # Ask to upload
    upload = input("Upload to server? (y/n): ").strip().lower()
    if upload == 'y':
        upload_update(update_dir, version)


def upload_update(update_dir, version):
    """Upload update to server."""
    # This can be customized for your server
    print(f"Uploading version {version}...")
    
    # Example: Copy to local server folder
    server_dir = Path("update_server/releases")
    server_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy zip
    zip_file = update_dir / f"ZAY_POS_v{version}.zip"
    if zip_file.exists():
        shutil.copy2(zip_file, server_dir / zip_file.name)
        print(f"✅ Copied to server: {server_dir / zip_file.name}")
    
    # Copy version.json
    version_file = update_dir / "version.json"
    if version_file.exists():
        shutil.copy2(version_file, server_dir.parent / "version.json")
        print(f"✅ Copied to server: {server_dir.parent / 'version.json'}")
    
    print("Upload completed!")


if __name__ == "__main__":
    generate_update()