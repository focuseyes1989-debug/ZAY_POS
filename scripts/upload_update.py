# scripts/upload_update.py
"""
Upload update to GitHub Releases.
"""

import os
import sys
import json
import requests
import argparse
import re
from pathlib import Path

# 🔥 Get the project root directory
def get_project_root():
    """Get the project root directory."""
    current_dir = Path(__file__).parent
    if current_dir.name == "scripts":
        return current_dir.parent
    return current_dir

PROJECT_ROOT = get_project_root()

def upload_to_github(version, zip_path, token, repo="focuseyes1989-debug/ZAY_POS"):
    """Upload to GitHub Releases."""
    print("\n" + "=" * 60)
    print("📤 UPLOADING TO GITHUB")
    print("=" * 60)
    
    url = f"https://api.github.com/repos/{repo}/releases"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Check if release already exists
    print(f"🔍 Checking if release v{version} already exists...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to GitHub: {e}")
        print("   Please check your internet connection and token.")
        return False
    
    releases = response.json()
    for release in releases:
        if release.get('tag_name') == f"v{version}":
            print(f"⚠️ Release v{version} already exists.")
            choice = input("Delete and recreate? (y/n): ").strip().lower()
            if choice == 'y':
                delete_url = release['url']
                delete_response = requests.delete(delete_url, headers=headers)
                if delete_response.status_code == 204:
                    print(f"✅ Deleted existing release v{version}")
                else:
                    print(f"❌ Failed to delete: {delete_response.status_code}")
                    return False
            else:
                print("❌ Upload cancelled")
                return False
    
    # Create release
    print(f"📦 Creating release v{version}...")
    data = {
        "tag_name": f"v{version}",
        "name": f"ZAY POS v{version}",
        "body": f"# ZAY POS v{version}\n\n## Installation\n1. Download the update zip\n2. Extract to your ZAY POS folder\n3. Run the launcher\n\n## Changes\n- Updated to version {version}\n- Bug fixes and improvements",
        "draft": False,
        "prerelease": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create release: {e}")
        return False
    
    release_data = response.json()
    upload_url = release_data['upload_url'].replace('{?name,label}', '')
    print(f"✅ Release created: {release_data['html_url']}")
    
    # Upload asset
    print(f"\n📤 Uploading {os.path.basename(zip_path)}...")
    with open(zip_path, 'rb') as f:
        files = {
            'file': (os.path.basename(zip_path), f, 'application/zip')
        }
        try:
            response = requests.post(
                upload_url + f"?name={os.path.basename(zip_path)}",
                headers=headers,
                files=files
            )
            response.raise_for_status()
            print(f"✅ Uploaded: {os.path.basename(zip_path)}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to upload zip: {e}")
            return False
    
    # Upload launcher if exists in versioned folder
    launcher_path = PROJECT_ROOT / f"dist/ZAY_POS_v{version}/ZAY_POS_Launcher.exe"
    if launcher_path.exists():
        print(f"\n📤 Uploading ZAY_POS_Launcher.exe...")
        with open(launcher_path, 'rb') as f:
            files = {
                'file': ('ZAY_POS_Launcher.exe', f, 'application/x-msdownload')
            }
            try:
                response = requests.post(
                    upload_url + f"?name=ZAY_POS_Launcher.exe",
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                print(f"✅ Uploaded: ZAY_POS_Launcher.exe")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Failed to upload launcher: {e}")
    
    print("\n" + "=" * 60)
    print("✅ UPLOAD COMPLETE!")
    print("=" * 60)
    print(f"\n🔗 Release URL: {release_data['html_url']}")
    print(f"📦 Update zip uploaded: {os.path.basename(zip_path)}")
    print("\n📝 Next Steps:")
    print("   1. Test the release by downloading the zip")
    print("   2. Run the launcher to test update")
    print("   3. Verify the update works")
    print("=" * 60)
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Upload ZAY POS update to GitHub")
    parser.add_argument("--version", help="Version to upload (e.g., 1.0.8)")
    parser.add_argument("--zip", help="Path to zip file")
    parser.add_argument("--token", help="GitHub token")
    
    args = parser.parse_args()
    
    # If no args, ask interactively
    if not args.version:
        while True:
            version = input("Enter version to upload (e.g., 1.0.8): ").strip()
            if re.match(r'^\d+\.\d+\.\d+$', version):
                args.version = version
                break
            print("❌ Invalid version format!")
    
    if not args.zip:
        default_zip = PROJECT_ROOT / f"update_build/ZAY_POS_v{args.version}_update.zip"
        if default_zip.exists():
            args.zip = str(default_zip)
            print(f"📂 Using: {args.zip}")
        else:
            args.zip = input("Enter path to zip file: ").strip()
    
    if not os.path.exists(args.zip):
        print(f"❌ Zip file not found: {args.zip}")
        sys.exit(1)
    
    if not args.token:
        print("\n" + "=" * 60)
        print("🔑 GITHUB TOKEN REQUIRED")
        print("=" * 60)
        print("1. Go to: https://github.com/settings/tokens")
        print("2. Generate new token (classic)")
        print("3. Select 'repo' scope")
        print("4. Copy the token")
        print("-" * 60)
        args.token = input("Enter GitHub token: ").strip()
    
    if not args.token:
        print("❌ GitHub token required!")
        sys.exit(1)
    
    # Upload
    upload_to_github(args.version, args.zip, args.token)

if __name__ == "__main__":
    # 🔥 Change to project root if running from scripts folder
    if Path(__file__).parent.name == "scripts":
        os.chdir(PROJECT_ROOT)
        print(f"📂 Changed directory to: {os.getcwd()}")
    
    main()