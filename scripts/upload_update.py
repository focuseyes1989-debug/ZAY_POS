# scripts/upload_update.py
"""
Upload update to GitHub Releases or local server.
"""

import os
import json
import requests
from pathlib import Path


def upload_to_github(version, zip_path, token):
    """Upload to GitHub Releases."""
    repo = "YOUR_USERNAME/ZAY_POS"
    url = f"https://api.github.com/repos/{repo}/releases"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Create release
    data = {
        "tag_name": f"v{version}",
        "name": f"ZAY POS v{version}",
        "body": f"ZAY POS version {version}",
        "draft": False,
        "prerelease": False
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    release_data = response.json()
    upload_url = release_data['upload_url'].replace('{?name,label}', '')
    
    # Upload asset
    with open(zip_path, 'rb') as f:
        files = {
            'file': (os.path.basename(zip_path), f, 'application/zip')
        }
        response = requests.post(
            upload_url + f"?name={os.path.basename(zip_path)}",
            headers=headers,
            files=files
        )
        response.raise_for_status()
    
    print(f"✅ Uploaded to GitHub: v{version}")


def upload_to_local_server(version, zip_path):
    """Upload to local server."""
    server_dir = Path("update_server/releases")
    server_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy zip
    import shutil
    shutil.copy2(zip_path, server_dir / os.path.basename(zip_path))
    print(f"✅ Copied to local server: {server_dir / os.path.basename(zip_path)}")
    
    # Update version.json
    version_info = {
        "version": version,
        "release_date": "2026-01-01",
        "release_notes": f"Version {version}",
        "download_url": f"http://localhost:8000/update/{os.path.basename(zip_path)}",
        "file_hash": "",
        "file_size": os.path.getsize(zip_path),
        "mandatory": False
    }
    
    with open(server_dir.parent / "version.json", 'w') as f:
        json.dump(version_info, f, indent=2)
    print(f"✅ Updated version.json")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True, help="Version to upload")
    parser.add_argument("--zip", required=True, help="Path to zip file")
    parser.add_argument("--github", action="store_true", help="Upload to GitHub")
    parser.add_argument("--token", help="GitHub token")
    
    args = parser.parse_args()
    
    if args.github:
        if not args.token:
            print("GitHub token required")
            sys.exit(1)
        upload_to_github(args.version, args.zip, args.token)
    else:
        upload_to_local_server(args.version, args.zip)