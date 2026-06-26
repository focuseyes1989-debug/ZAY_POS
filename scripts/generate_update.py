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
import re
from datetime import datetime
from pathlib import Path

# 🔥 Get the project root directory
def get_project_root():
    """Get the project root directory."""
    # If running from scripts folder, go up one level
    current_dir = Path(__file__).parent
    if current_dir.name == "scripts":
        return current_dir.parent
    return current_dir

PROJECT_ROOT = get_project_root()

def get_version_input():
    """Get version from user input."""
    print("\n" + "=" * 60)
    print("🔢 ENTER VERSION NUMBER FOR UPDATE")
    print("=" * 60)
    print("Format: x.y.z (e.g., 1.0.8, 1.1.0, 2.0.0)")
    print("-" * 60)
    
    while True:
        version = input("Enter version: ").strip()
        if re.match(r'^\d+\.\d+\.\d+$', version):
            return version
        else:
            print("❌ Invalid version format! Please use format: x.y.z")

def find_versioned_folder(version):
    """Find the versioned folder in dist directory."""
    # 🔥 Use project root for dist folder
    dist_folder = PROJECT_ROOT / "dist"
    
    print(f"📂 Looking in: {dist_folder}")
    
    if not dist_folder.exists():
        print(f"❌ dist folder not found at: {dist_folder}")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Project root: {PROJECT_ROOT}")
        return None
    
    print(f"✅ Found dist folder: {dist_folder}")
    
    # 🔥 Check all possible locations
    possible_locations = [
        dist_folder / f"ZAY_POS_v{version}",
        dist_folder / f"ZAY_POS_{version}",
        dist_folder / f"ZAY_POS_v{version}_update",
        dist_folder / f"ZAY_POS_{version}_update",
        dist_folder / f"{version}",
    ]
    
    # Also check for any folder containing the version
    for folder in dist_folder.iterdir():
        if folder.is_dir() and version in folder.name:
            possible_locations.append(folder)
    
    # Check each location
    for location in possible_locations:
        if location.exists() and location.is_dir():
            exe_path = location / "ZAY_POS.exe"
            if exe_path.exists():
                print(f"✅ Found versioned folder: {location}")
                return location
    
    # 🔥 If not found, ask user for location
    print(f"\n⚠️ Could not find versioned folder automatically.")
    print(f"   Looking for: ZAY_POS_v{version}")
    print("\n📂 Available folders in dist:")
    for item in dist_folder.iterdir():
        if item.is_dir():
            print(f"   - {item.name}")
        elif item.is_file() and item.suffix == '.exe':
            print(f"   - {item.name} (file)")
    
    manual_path = input(f"\n📁 Enter the folder path manually (or press Enter to cancel): ").strip()
    if manual_path:
        manual_folder = Path(manual_path)
        if not manual_folder.is_absolute():
            manual_folder = PROJECT_ROOT / manual_folder
        if manual_folder.exists() and manual_folder.is_dir():
            return manual_folder
    
    return None

def generate_update():
    """Generate update package."""
    print("=" * 60)
    print("📦 ZAY POS UPDATE GENERATOR")
    print("=" * 60)
    
    print(f"📂 Project root: {PROJECT_ROOT}")
    print(f"📂 Current directory: {os.getcwd()}")
    
    # Get version
    version = get_version_input()
    print(f"\n📌 Generating update for version: {version}")
    
    # GitHub repository
    github_repo = "focuseyes1989-debug/ZAY_POS"
    
    # 🔥 Create update directory in project root
    update_dir = PROJECT_ROOT / "update_build"
    if update_dir.exists():
        shutil.rmtree(update_dir)
    update_dir.mkdir()
    print(f"✅ Created: {update_dir}")
    
    # 🔥 Find the versioned folder
    versioned_folder = find_versioned_folder(version)
    
    if not versioned_folder:
        print(f"\n❌ Versioned folder not found!")
        print(f"   Please make sure you have built the application first.")
        print(f"   Run: python build_exe.py")
        print(f"   Or check if dist folder contains the versioned folder.")
        return
    
    print(f"📂 Using: {versioned_folder}")
    
    # 🔥 Copy files from versioned folder
    files_to_copy = []
    
    # Check for main exe
    main_exe = versioned_folder / "ZAY_POS.exe"
    if main_exe.exists():
        files_to_copy.append("ZAY_POS.exe")
        print("✅ Found ZAY_POS.exe")
    else:
        print(f"⚠️ ZAY_POS.exe not found in: {versioned_folder}")
        # Try to find in dist root
        root_exe = PROJECT_ROOT / "dist" / "ZAY_POS.exe"
        if root_exe.exists():
            shutil.copy2(root_exe, update_dir / "ZAY_POS.exe")
            print("✅ Copied ZAY_POS.exe from dist root")
            files_to_copy.append("ZAY_POS.exe")
    
    # Check for launcher
    launcher_path = versioned_folder / "ZAY_POS_Launcher.exe"
    if launcher_path.exists():
        files_to_copy.append("ZAY_POS_Launcher.exe")
        print("✅ Found ZAY_POS_Launcher.exe")
    
    # Check for version.txt
    version_txt = versioned_folder / "version.txt"
    if version_txt.exists():
        shutil.copy2(version_txt, update_dir / "version.txt")
        print("✅ Copied version.txt")
    else:
        # Create version.txt
        with open(update_dir / "version.txt", 'w', encoding='utf-8') as f:
            f.write(f'ProductVersion = "{version}"\nFileVersion = "{version}"\n')
        print("✅ Created version.txt")
    
    # Copy assets if exists
    assets_folder = versioned_folder / "assets"
    if assets_folder.exists():
        shutil.copytree(assets_folder, update_dir / "assets", dirs_exist_ok=True)
        print(f"✅ Added: assets/")
    else:
        # Try from project root
        root_assets = PROJECT_ROOT / "assets"
        if root_assets.exists():
            shutil.copytree(root_assets, update_dir / "assets", dirs_exist_ok=True)
            print(f"✅ Added: assets/ (from project root)")
    
    # Copy updater folder if exists
    updater_folder = PROJECT_ROOT / "updater"
    if updater_folder.exists():
        shutil.copytree(updater_folder, update_dir / "updater", dirs_exist_ok=True)
        print("✅ Added: updater/")
    
    # Copy individual files
    for item in files_to_copy:
        src = versioned_folder / item
        if src.exists():
            shutil.copy2(src, update_dir / item)
            print(f"✅ Copied: {item}")
    
    # Create database structure (empty folders)
    for folder in ["database", "logs", "temp"]:
        (update_dir / folder).mkdir(exist_ok=True)
        if folder == "database":
            (update_dir / folder / "product_images").mkdir(exist_ok=True)
            (update_dir / folder / "backups").mkdir(exist_ok=True)
    print("✅ Added: database/, logs/, temp/ folders")
    
    # Create update zip
    zip_name = f"ZAY_POS_v{version}_update.zip"
    zip_path = update_dir / zip_name
    
    print(f"\n📦 Creating update zip: {zip_name}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in update_dir.rglob('*'):
            if file.name == zip_name:
                continue
            if file.is_file():
                arcname = file.relative_to(update_dir)
                zipf.write(file, arcname)
                print(f"   Added: {arcname}")
    
    print(f"✅ Created: {zip_name}")
    
    # Calculate hash
    sha256 = hashlib.sha256()
    with open(zip_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    file_hash = sha256.hexdigest()
    
    print(f"🔐 File hash: {file_hash[:16]}...")
    
    # Create version.json
    version_info = {
        "version": version,
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "release_notes": f"Version {version} released\n\n## Changes\n- Updated to version {version}\n- Bug fixes and improvements",
        "download_url": f"https://github.com/{github_repo}/releases/download/v{version}/ZAY_POS_v{version}_update.zip",
        "file_hash": file_hash,
        "file_size": os.path.getsize(zip_path),
        "mandatory": False,
        "min_required_version": "1.0.0"
    }
    
    with open(update_dir / "version.json", 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=2)
    
    print(f"✅ Created: version.json")
    
    print("\n" + "=" * 60)
    print("✅ UPDATE PACKAGE CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\n📁 Location: {update_dir}")
    print(f"📦 File: {zip_path}")
    print(f"📊 Size: {os.path.getsize(zip_path) // 1024} KB")
    print(f"🔐 Hash: {file_hash}")
    print(f"📥 Download URL: {version_info['download_url']}")
    print("\n📝 Next Steps:")
    print("   1. Upload to GitHub Releases")
    print("   2. Run: python scripts/upload_update.py")
    print("=" * 60)
    
    return version_info

if __name__ == "__main__":
    # 🔥 Change to project root if running from scripts folder
    if Path(__file__).parent.name == "scripts":
        os.chdir(PROJECT_ROOT)
        print(f"📂 Changed directory to: {os.getcwd()}")
    
    generate_update()