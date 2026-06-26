# main.py
"""
ZAY POS Main Application Entry Point
Supports both direct launch and launcher-based update system.
"""

import sys
import os
import warnings
import time
import subprocess
import json
from pathlib import Path

# ==============================================================================
# 🔥 FIX: Ensure Python can find PyQt6 when running as EXE
# ==============================================================================
def fix_pyqt6_import():
    """Fix PyQt6 import issues when running as frozen executable."""
    if getattr(sys, 'frozen', False):
        # When running as EXE, add the application directory to sys.path
        app_dir = os.path.dirname(sys.executable)
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)
        
        # Also add the _MEIPASS directory if it exists
        if hasattr(sys, '_MEIPASS'):
            meipass_dir = sys._MEIPASS
            if meipass_dir not in sys.path:
                sys.path.insert(0, meipass_dir)

# Call the fix function BEFORE any other imports
fix_pyqt6_import()

# ==============================================================================
# 🔥 FIX MATPLOTLIB IMPORT & ENVIRONMENT SETUP
# ==============================================================================
def fix_matplotlib():
    """Fix matplotlib import issues before application starts."""
    try:
        # Set backend before importing matplotlib
        os.environ['MPLBACKEND'] = 'QtAgg'
        
        # Set custom configuration/cache directory for matplotlib
        cache_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp', 'matplotlib_cache')
        os.environ['MPLCONFIGDIR'] = cache_dir
        os.environ['PYTHONWARNINGS'] = 'ignore'
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Suppress warnings
        warnings.filterwarnings("ignore", category=ImportWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=UserWarning)
        
        # ✅ Force matplotlib to use QtAgg backend
        try:
            import matplotlib
            matplotlib.use('QtAgg', force=True)
            import matplotlib.pyplot as plt
            print("✅ Matplotlib initialized successfully")
        except Exception as e:
            print(f"⚠️ Matplotlib init warning: {e}")
            
    except Exception as e:
        print(f"⚠️ Matplotlib fix error: {e}")

# Call the fix function
fix_matplotlib()

# ✅ Also set Qt environment for High DPI Scaling
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "Round"

# ==============================================================================
# PYINSTALLER RUNTIME BOOTSTRAPPING
# ==============================================================================
def _bootstrap_runtime_paths():
    """Prepare writable folders and bundled data when running as a PyInstaller EXE."""
    import shutil
    
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
        bundle_dir = getattr(sys, "_MEIPASS", app_dir)
        os.chdir(app_dir)

        # ✅ Copy assets folder
        for folder in ("assets",):
            source = os.path.join(bundle_dir, folder)
            target = os.path.join(app_dir, folder)
            if os.path.isdir(source) and not os.path.exists(target):
                shutil.copytree(source, target)

    # Create writable folders
    for folder in ("database", "logs", "temp"):
        try:
            # ✅ Use absolute path based on executable location
            if getattr(sys, "frozen", False):
                folder_path = os.path.join(os.path.dirname(sys.executable), folder)
            else:
                folder_path = folder
            
            os.makedirs(folder_path, exist_ok=True)
            
            # Test write permissions
            test_file = os.path.join(folder_path, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"✅ Created folder: {folder_path}")
            
        except Exception as e:
            print(f"⚠️ Could not create folder {folder}: {e}")
            # Fallback to user directory
            fallback_dir = os.path.join(os.path.expanduser('~'), 'ZAY_POS', folder)
            os.makedirs(fallback_dir, exist_ok=True)
            print(f"✅ Using fallback folder: {fallback_dir}")

_bootstrap_runtime_paths()

# ========== Windows DPI Awareness ==========
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

# ========== FIX FOR PKG_RESOURCES & SETUPTOOLS ==========
try:
    import pkg_resources
except ImportError:
    # Create a complete dummy pkg_resources module
    import types
    
    class DummyDistribution:
        def __init__(self, name="dummy", version="0.0.0"):
            self.project_name = name
            self.version = version
            self.key = name.lower()
            self.location = ""
            self.PKG_INFO = f"Metadata-Version: 1.0\nName: {name}\nVersion: {version}\n"
        
        def get_metadata_lines(self, metadata):
            return []
        
        def get_metadata(self, metadata):
            return ""
        
        def has_metadata(self, metadata):
            return False
        
        def requires(self, *args):
            return []
        
        def __eq__(self, other):
            return False
        
        def __repr__(self):
            return f"<DummyDistribution {self.project_name} {self.version}>"
    
    class DummyPkgResources:
        def __init__(self):
            self.working_set = []
            self.egg_info = None
            self._distributions = {}
            self._entry_points = {}
            self.Distribution = DummyDistribution
        
        def require(self, *args, **kwargs):
            pass
        
        def iter_entry_points(self, group=None, name=None):
            return []
        
        def get_distribution(self, dist_name):
            return DummyDistribution(dist_name)
        
        def resource_stream(self, package, resource):
            return None
        
        def resource_string(self, package, resource):
            return b''
        
        def resource_exists(self, package, resource):
            return False
        
        def resource_isdir(self, package, resource):
            return False
        
        def resource_listdir(self, package, resource):
            return []
        
        def get_metadata_lines(self, dist_name, metadata):
            return []
        
        def get_metadata(self, dist_name, metadata):
            return ""
        
        def has_metadata(self, dist_name, metadata):
            return False
        
        def parse_version(self, version):
            return version
        
        def yield_lines(self, *args):
            return []
        
        def find_distributions(self, *args, **kwargs):
            return []
        
        def cleanup_resources(self):
            pass
        
        def get_provider(self, module):
            return None
        
        def load_entry_point(self, group, name):
            return None
        
        def get_entry_map(self, dist):
            return {}
        
        def get_metadata_version(self):
            return "1.0"
        
        def get_default_cache(self):
            return ""
    
    dummy_pkg = DummyPkgResources()
    sys.modules['pkg_resources'] = dummy_pkg

# ✅ Also fix setuptools
try:
    import setuptools
except ImportError:
    import types
    dummy_setuptools = types.ModuleType('setuptools')
    dummy_setuptools.__path__ = []
    sys.modules['setuptools'] = dummy_setuptools

# ========== NORMAL IMPORTS ==========
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import QTimer
from loguru import logger

from ui.main_window import MainWindow
from ui.login_dialog import LoginDialog
from ui.loading_dialog import LoadingDialog

from models.database import (
    create_tables, 
    run_migrations, 
    get_migration_status,
    get_database_stats, 
    optimize_database,
    check_and_recover,
    connect_db,
    check_and_run_migrations
)

from ui.themes import apply_theme
from utils.ui_icons import install_ui_icons

# ==============================================================================
# 🔥 UPDATED: Version Manager only (no auto-update in main app)
# ==============================================================================
#from updater.version_manager import VersionManager

# ---------- Setup Logging ----------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger.remove()
if sys.stdout is not None:
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
logger.add(
    os.path.join(LOG_DIR, "zaypos_{time:YYYY-MM-DD}.log"),
    rotation="1 day",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# ---------- Global Exception Hook ----------
def handle_exception(exc_type, exc_value, exc_traceback):
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical("Unhandled exception")
    import traceback
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("An unexpected error occurred.")
    msg.setInformativeText(str(exc_value))
    msg.setDetailedText("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    msg.setWindowTitle("System Error")
    msg.exec()
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

# ==============================================================================
# 🔥 NEW: Launcher Detection and Management
# ==============================================================================
def is_running_from_launcher() -> bool:
    """Check if the application was started by the launcher."""
    # Check for launcher marker file
    marker_file = os.path.join(os.path.dirname(sys.executable), '.launcher_ran')
    if os.path.exists(marker_file):
        return True
    
    # Check command line arguments
    if '--from-launcher' in sys.argv:
        return True
    
    # Check environment variable
    if os.environ.get('ZAY_LAUNCHER', '0') == '1':
        return True
    
    return False

def find_launcher() -> str:
    """Find the launcher executable."""
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
        
        # Check for launcher in same directory
        launcher_names = [
            'ZAY_POS_Launcher.exe',
            'launcher.exe',
            'ZAY_Launcher.exe'
        ]
        
        for name in launcher_names:
            launcher_path = os.path.join(app_dir, name)
            if os.path.exists(launcher_path):
                return launcher_path
        
        # Check parent directory
        parent_dir = os.path.dirname(app_dir)
        for name in launcher_names:
            launcher_path = os.path.join(parent_dir, name)
            if os.path.exists(launcher_path):
                return launcher_path
    
    return None

def should_run_launcher() -> bool:
    """Determine if we should run the launcher instead of the main app."""
    
    # If already running from launcher, skip
    if is_running_from_launcher():
        logger.info("Running from launcher, skipping launcher check")
        return False
    
    # If running as script (development), skip launcher
    if not getattr(sys, 'frozen', False):
        logger.info("Running as script, skipping launcher")
        return False
    
    # Check if launcher exists
    if not find_launcher():
        logger.info("Launcher not found, starting directly")
        return False
    
    # Check if update check is needed (check metadata)
    metadata_file = os.path.join(os.path.dirname(sys.executable), 'update_metadata.json')
    need_update_check = True
    
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            last_check = data.get('last_check', 0)
            current_time = time.time()
            
            # Check if last check was within 24 hours
            if current_time - last_check < 86400:  # 24 hours
                need_update_check = False
                logger.info(f"Last update check was {int((current_time - last_check) / 3600)} hours ago")
        except:
            pass
    
    # Always run launcher if update check is needed or on first run
    if need_update_check:
        logger.info("Running launcher for update check")
        return True
    
    # Also check if launcher was run recently
    launcher_marker = os.path.join(os.path.dirname(sys.executable), '.launcher_ran')
    if os.path.exists(launcher_marker):
        try:
            mtime = os.path.getmtime(launcher_marker)
            # If launcher ran within last hour, skip
            if time.time() - mtime < 3600:
                logger.info("Launcher ran recently, skipping")
                return False
        except:
            pass
    
    # Default: run launcher
    return True

def run_launcher_and_exit() -> None:
    """Run the launcher and exit current process."""
    launcher_path = find_launcher()
    if not launcher_path:
        logger.error("Launcher not found")
        return
    
    try:
        logger.info(f"🚀 Starting launcher: {launcher_path}")
        
        # Create marker file to indicate launcher is running
        marker_file = os.path.join(os.path.dirname(sys.executable), '.launcher_ran')
        with open(marker_file, 'w') as f:
            f.write(str(time.time()))
        
        # Start launcher
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(
                [launcher_path],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            subprocess.Popen([launcher_path])
        
        logger.info("✅ Launcher started successfully")
        
        # Exit current process
        QTimer.singleShot(500, lambda: sys.exit(0))
        
    except Exception as e:
        logger.error(f"Failed to start launcher: {e}")
        # Continue with normal startup if launcher fails

# ==============================================================================
# DATABASE INITIALIZATION
# ==============================================================================
def initialize_database():
    """Initialize database and run migrations on startup."""
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 60)
    
    try:
        db_dir = "database"
        
        # 🔥 Ensure directory exists with proper permissions
        try:
            os.makedirs(db_dir, exist_ok=True)
            # 🔥 Test write permissions
            test_file = os.path.join(db_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info(f"✅ Database directory is writable: {os.path.abspath(db_dir)}")
        except Exception as e:
            logger.error(f"❌ Database directory not writable: {e}")
            # 🔥 Fallback to AppData
            appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'ZAY_POS')
            os.makedirs(appdata_dir, exist_ok=True)
            db_dir = appdata_dir
            logger.info(f"✅ Using fallback database directory: {db_dir}")
        
        db_path = os.path.join(db_dir, "pos.db")
        is_new_db = not os.path.exists(db_path)
        
        if is_new_db:
            logger.info("📝 New database detected. Creating initial database...")
        else:
            logger.info(f"📂 Existing database found: {db_path}")
        
        # 🔥 Step 1: Test database connection with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()
                logger.info("✅ Database connection successful")
                break
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise
        
        logger.info("Step 1: Creating/verifying database tables...")
        create_tables()
        logger.info("✅ Database tables created/verified.")
        
        logger.info("Step 2: Checking for pending migrations...")
        try:
            check_and_run_migrations()
            logger.info("✅ Migrations check completed.")
        except Exception as e:
            logger.error(f"❌ MIGRATION FAILED: {e}")
            logger.exception(e)
            raise RuntimeError(f"Database migration failed: {e}")
        
        logger.info("Step 3: Getting database status...")
        try:
            status = get_migration_status()
            if status:
                logger.info(f"📊 App Version    : {status.get('app_version', 'Unknown')}")
                logger.info(f"📊 DB Version     : {status['current_version']}")
                logger.info(f"📊 Applied        : {len(status['applied'])} migrations")
                logger.info(f"📊 Pending        : {len(status['pending'])} migrations")
                if status.get('last_updated'):
                    logger.info(f"📊 Last Updated   : {status['last_updated']}")
            else:
                logger.warning("Could not get migration status")
        except Exception as e:
            logger.warning(f"Could not get migration status: {e}")
        
        logger.info("Step 4: Running crash recovery check...")
        try:
            if check_and_recover(show_gui=False):
                logger.info("✅ Crash recovery actions performed.")
        except Exception as e:
            logger.error(f"Crash recovery check failed: {e}")
        
        logger.info("Step 5: Optimizing database...")
        try:
            stats = get_database_stats()
            if stats and stats.get('size_mb', 0) > 100:
                logger.info("Database is large, running optimization...")
                optimize_database()
        except Exception as e:
            logger.debug(f"Database optimization skipped: {e}")
        
        logger.info("=" * 60)
        logger.info("✅ DATABASE INITIALIZATION COMPLETE")
        logger.info("=" * 60)
        
        return status
        
    except Exception as e:
        logger.error(f"❌ DATABASE INITIALIZATION FAILED: {e}")
        logger.exception(e)
        logger.info("=" * 60)
        logger.info("❌ DATABASE INITIALIZATION FAILED - APPLICATION WILL NOT START")
        logger.info("=" * 60)
        raise

# ==============================================================================
# UPDATE CLEANUP - Remove old update code
# ==============================================================================
def cleanup_old_update_files():
    """Remove old update-related files that are no longer needed."""
    try:
        # These files are now handled by launcher
        old_files = [
            'update_manager.py',
            'update_worker.py', 
            'update_dialog.py',
        ]
        
        updater_dir = 'updater'
        if os.path.exists(updater_dir):
            for file in old_files:
                file_path = os.path.join(updater_dir, file)
                if os.path.exists(file_path):
                    # Rename to .old instead of deleting
                    backup_path = file_path + '.old'
                    if not os.path.exists(backup_path):
                        os.rename(file_path, backup_path)
                        logger.info(f"✅ Archived old update file: {file_path}")
        
        # Check for orphaned files in root
        root_files = [
            'version.txt',
            'update_metadata.json'
        ]
        for file in root_files:
            if os.path.exists(file):
                # Keep version.txt and metadata for launcher
                logger.info(f"ℹ️ Keeping file for launcher: {file}")
                
    except Exception as e:
        logger.warning(f"Cleanup warning: {e}")

# ==============================================================================
# START APPLICATION
# ==============================================================================
def start_app():
    """Start the main application."""
    app = QApplication(sys.argv)
    install_ui_icons()
    
    try:
        db_status = initialize_database()
    except Exception as e:
        error_msg = str(e)
        logger.critical(f"Database initialization failed: {error_msg}")
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Database Error")
        msg.setText("Database initialization failed!")
        msg.setInformativeText(
            "The application cannot start because the database could not be initialized.\n\n"
            f"Error: {error_msg}\n\n"
            "Please check the logs for more details.\n"
            "Contact your system administrator for assistance."
        )
        msg.setDetailedText(
            "Possible causes:\n"
            "1. Database file is corrupted\n"
            "2. Migration failed\n"
            "3. Insufficient disk space\n"
            "4. Permission issues\n\n"
            "Solution:\n"
            "1. Restore from backup\n"
            "2. Contact support"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        sys.exit(1)
    
    # Load custom fonts
    fonts_dir = "assets/fonts"
    if os.path.exists(fonts_dir):
        for filename in os.listdir(fonts_dir):
            if filename.lower().endswith(('.ttf', '.otf')):
                font_path = os.path.join(fonts_dir, filename)
                QFontDatabase.addApplicationFont(font_path)
                logger.debug(f"Loaded font: {filename}")
    
    # Load saved theme from database
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='theme'")
        row = cursor.fetchone()
        saved_theme = row[0] if row else "Light"
        conn.close()
    except Exception as e:
        logger.error(f"Failed to load theme: {e}")
        saved_theme = "Light"
    
    apply_theme(app, saved_theme)
    logger.info(f"Theme loaded: {saved_theme}")
    
    # Set Myanmar font if available
    if "Noto Sans Myanmar" in QFontDatabase.families():
        app.setFont(QFont("Noto Sans Myanmar", 10))
    else:
        app.setFont(QFont("Segoe UI", 10))
    
    # ---------- Main application loop with logout support ----------
    def run():
        while True:
            login = LoginDialog()
            if login.exec() != LoginDialog.DialogCode.Accepted:
                logger.info("User cancelled login, exiting application.")
                sys.exit(0)
    
            logger.info(f"User logged in: {login.user_info['username']} (role: {login.user_info['role']})")
            
            loading = LoadingDialog("Please wait...")
            loading.show()
            QApplication.processEvents()
            
            try:
                loading.set_status("Loading database...")
                QApplication.processEvents()
                
                window = MainWindow(login.user_info)
                
                loading.set_status("Loading dashboard...")
                QApplication.processEvents()
                
                window.showMaximized()
                loading.accept()
                QApplication.processEvents()
                
            except Exception as e:
                loading.accept()
                logger.error(f"Failed to initialize main window: {e}")
                QMessageBox.critical(None, "Error", f"Failed to initialize application: {e}")
                continue
            
            app.exec()
    
            if window.logout_triggered:
                logger.info("User logged out, showing login screen again.")
                continue
            else:
                logger.info("Application closed normally.")
                break
    
    return run

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
def main():
    """Main entry point with launcher detection."""
    
    # Clean up old update files
    cleanup_old_update_files()
    
    # Check if we should run launcher
    if should_run_launcher():
        logger.info("🔄 Starting launcher for update check...")
        run_launcher_and_exit()
        # If launcher fails to start, continue with normal startup
        logger.warning("Launcher failed to start or was cancelled, continuing with normal startup")
    
    # Start the application
    logger.info("🚀 Starting ZAY POS...")
    
    # Display version info
    try:
        version_manager = VersionManager()
        current_version = version_manager.get_current_version()
        logger.info(f"📌 ZAY POS Version: {current_version}")
    except Exception as e:
        logger.warning(f"Could not get version: {e}")
    
    # Start the app
    run_app = start_app()
    run_app()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        raise
    finally:
        logger.info("Application shutdown.")
        sys.exit(0)