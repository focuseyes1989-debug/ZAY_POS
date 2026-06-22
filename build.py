# build.py
"""
Build script for ZAY POS with proper database handling.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Application version
APP_VERSION = "1.0.0"
APP_NAME = "ZAY_POS"

def clean_build():
    """Clean build directories."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Removed: {dir_name}")
    
    # Clean .spec files
    for file in Path('.').glob('*.spec'):
        file.unlink()
        print(f"✅ Removed: {file}")

def create_dist_folder():
    """Create distribution folder structure."""
    dist_folder = Path('dist')
    
    # Create necessary folders
    folders = ['database', 'logs', 'temp']
    for folder in folders:
        (dist_folder / folder).mkdir(exist_ok=True)
        
        # Create .gitkeep file to keep empty folder
        if folder == 'database':
            (dist_folder / folder / '.gitkeep').touch()
    
    print("✅ Distribution folder structure created")

def copy_assets():
    """Copy assets to dist folder."""
    dist_folder = Path('dist')
    
    # Copy assets
    if os.path.exists('assets'):
        shutil.copytree('assets', dist_folder / 'assets', dirs_exist_ok=True)
        print("✅ Assets copied")
    
    # Copy fonts
    if os.path.exists('assets/fonts'):
        shutil.copytree('assets/fonts', dist_folder / 'assets/fonts', dirs_exist_ok=True)
        print("✅ Fonts copied")
    
    # Copy icons
    if os.path.exists('assets/icons'):
        shutil.copytree('assets/icons', dist_folder / 'assets/icons', dirs_exist_ok=True)
        print("✅ Icons copied")

def create_version_file():
    """Create version.txt for Windows executable."""
    version_content = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'ZAY POS'),
            StringStruct(u'FileDescription', u'ZAY POS Application'),
            StringStruct(u'FileVersion', u'1.0.0'),
            StringStruct(u'InternalName', u'ZAY_POS'),
            StringStruct(u'LegalCopyright', u'ZAY POS'),
            StringStruct(u'OriginalFilename', u'ZAY_POS.exe'),
            StringStruct(u'ProductName', u'ZAY POS'),
            StringStruct(u'ProductVersion', u'1.0.0')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    with open('version.txt', 'w', encoding='utf-8') as f:
        f.write(version_content)
    print("✅ Version file created")

def build_exe():
    """Build executable with PyInstaller."""
    print("🚀 Building ZAY POS...")
    
    # Check if icon exists
    icon_path = "assets/icons/app_icon.ico"
    if not os.path.exists(icon_path):
        print(f"⚠️ Icon not found: {icon_path}")
        icon_path = "NONE"
    
    # PyInstaller command
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        f'--name={APP_NAME}',
    ]
    
    # Add icon if exists
    if icon_path != "NONE":
        cmd.append(f'--icon={icon_path}')
    
    # Add data files
    cmd.extend([
        '--add-data=assets;assets',
        '--add-data=database;database',
    ])
    
    # Add hidden imports
    cmd.extend([
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=loguru',
        '--hidden-import=packaging',
        '--hidden-import=packaging.version',
        '--hidden-import=sqlite3',
    ])
    
    # ✅ Fixed: Use --version-file instead of -v
    cmd.extend([
        f'--version-file=version.txt',
    ])
    
    # Add main script
    cmd.append('main.py')
    
    # Run PyInstaller
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build successful!")
            return True
        else:
            print(f"❌ Build failed: {result.stderr}")
            # Print stdout for debugging
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return False
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False

def create_release_zip():
    """Create release zip file without database files."""
    import zipfile
    from datetime import datetime
    
    zip_name = f'{APP_NAME}_v{APP_VERSION}.zip'
    dist_folder = Path('dist')
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add executable
        exe_file = dist_folder / f'{APP_NAME}.exe'
        if exe_file.exists():
            zipf.write(exe_file, f'{APP_NAME}.exe')
            print(f"✅ Added: {APP_NAME}.exe")
        else:
            print(f"⚠️ Executable not found: {exe_file}")
        
        # Add assets (skip database files)
        assets_folder = dist_folder / 'assets'
        if assets_folder.exists():
            for file in assets_folder.rglob('*'):
                if file.is_file():
                    # Skip database files
                    if '.db' in file.suffix.lower():
                        continue
                    arcname = str(file.relative_to(dist_folder))
                    zipf.write(file, arcname)
                    print(f"✅ Added: {arcname}")
        
        # Add empty database folder with .gitkeep
        gitkeep = dist_folder / 'database' / '.gitkeep'
        if gitkeep.exists():
            zipf.write(gitkeep, 'database/.gitkeep')
            print(f"✅ Added: database/.gitkeep")
        
        # Add README with instructions
        readme_content = f"""
ZAY POS Installation
====================

Version: {APP_VERSION}
Date: {datetime.now().strftime('%Y-%m-%d')}

1. Extract the zip file to a folder
2. Run ZAY_POS.exe
3. The application will create database files automatically on first run

⚠️ Important:
- Database files will be created in the database/ folder on first run
- Do not share your database/ folder with others
- Backup your database regularly

Default Login:
- Username: admin
- Password: admin

System Requirements:
- Windows 7 or later
- 2GB RAM minimum
- 100MB free disk space

For support, contact your system administrator.

Changelog:
- Initial release version {APP_VERSION}
"""
        zipf.writestr('README.txt', readme_content)
        print("✅ Added: README.txt")
    
    print(f"✅ Release zip created: {zip_name}")
    return zip_name

def main():
    """Main build process."""
    print("=" * 60)
    print("ZAY POS BUILD SYSTEM")
    print("=" * 60)
    print(f"Version: {APP_VERSION}")
    print("=" * 60)
    
    # Step 1: Clean
    print("\n📦 Step 1: Cleaning build directories...")
    clean_build()
    
    # Step 2: Create version file
    print("\n📦 Step 2: Creating version file...")
    create_version_file()
    
    # Step 3: Build
    print("\n📦 Step 3: Building executable...")
    if not build_exe():
        print("\n❌ Build failed! Please check the error above.")
        sys.exit(1)
    
    # Step 4: Create distribution structure
    print("\n📦 Step 4: Creating distribution structure...")
    create_dist_folder()
    
    # Step 5: Copy assets
    print("\n📦 Step 5: Copying assets...")
    copy_assets()
    
    # Step 6: Create release zip
    print("\n📦 Step 6: Creating release zip...")
    zip_name = create_release_zip()
    
    print("\n" + "=" * 60)
    print("✅ BUILD COMPLETE!")
    print("=" * 60)
    print(f"\n📁 Release file: {zip_name}")
    print(f"📁 Location: {os.path.abspath(zip_name)}")
    print("\n📝 Remember:")
    print("   - Database files will be created on first run")
    print("   - Do not include database/ folder in distribution")
    print("   - Default login: admin / admin")

if __name__ == '__main__':
    main()