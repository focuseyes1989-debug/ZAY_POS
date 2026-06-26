# utils/paths.py
import os
import sys


def get_app_root():
    """Return the writable application root for source and PyInstaller runs."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def app_path(*parts):
    """Join parts with the application root directory."""
    return os.path.join(get_app_root(), *parts)


def app_relative_path(path):
    """Convert an absolute path to a relative path from the application root."""
    return os.path.relpath(path, get_app_root()).replace("\\", "/")