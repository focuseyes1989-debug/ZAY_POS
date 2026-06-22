# updater/version_manager.py
"""
Version management for ZAY POS.
"""

import os
import json
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class VersionInfo:
    """Version information for the application."""
    version: str
    release_date: str
    release_notes: str
    download_url: str
    file_size: int
    file_hash: str
    mandatory: bool = False
    min_required_version: str = "1.0.0"
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class CurrentVersion:
    """Current application version information."""
    version: str
    build_date: str
    build_number: int
    db_version: str


class VersionManager:
    """Handle version comparison and management."""
    
    VERSION_FILE = "version.txt"
    UPDATE_METADATA_FILE = "update_metadata.json"
    
    def __init__(self):
        self.current_version = None
        self._load_current_version()
    
    def _load_current_version(self):
        """Load current version from version.txt."""
        try:
            if os.path.exists(self.VERSION_FILE):
                with open(self.VERSION_FILE, 'r') as f:
                    content = f.read()
                    # Parse version from file
                    match = re.search(r'ProductVersion\s*=\s*["\']([\d.]+)["\']', content)
                    if match:
                        self.current_version = match.group(1)
                    else:
                        self.current_version = "1.0.0"
            else:
                self.current_version = "1.0.0"
        except Exception as e:
            logger.error(f"Failed to load version: {e}")
            self.current_version = "1.0.0"
    
    def get_current_version(self) -> str:
        """Get current application version."""
        return self.current_version
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.
        
        Returns:
            -1 if v1 < v2
            0 if v1 == v2
            1 if v1 > v2
        """
        def normalize(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = normalize(v1)
        v2_parts = normalize(v2)
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            a = v1_parts[i] if i < len(v1_parts) else 0
            b = v2_parts[i] if i < len(v2_parts) else 0
            if a < b:
                return -1
            elif a > b:
                return 1
        return 0
    
    def is_update_available(self, latest_version: str) -> bool:
        """Check if update is available."""
        return self.compare_versions(self.current_version, latest_version) < 0
    
    def get_update_metadata_path(self) -> str:
        """Get path to update metadata file."""
        return os.path.join(os.path.dirname(__file__), '..', self.UPDATE_METADATA_FILE)
    
    def save_update_metadata(self, metadata: Dict):
        """Save update metadata."""
        path = self.get_update_metadata_path()
        try:
            with open(path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Update metadata saved to: {path}")
        except Exception as e:
            logger.error(f"Failed to save update metadata: {e}")
    
    def load_update_metadata(self) -> Dict:
        """Load update metadata."""
        path = self.get_update_metadata_path()
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load update metadata: {e}")
        return {}
    
    def get_db_version(self) -> str:
        """Get current database version from app_metadata."""
        try:
            from models.database import connect_db
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT db_version FROM app_metadata 
                ORDER BY id DESC LIMIT 1
            """)
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "0.0.0"
        except Exception as e:
            logger.error(f"Failed to get DB version: {e}")
            return "0.0.0"