# main.py
import sys
import os
import shutil


def _bootstrap_runtime_paths():
    """Prepare writable folders and bundled data when running as a PyInstaller EXE."""
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
        bundle_dir = getattr(sys, "_MEIPASS", app_dir)
        os.chdir(app_dir)

        # Only copy assets folder (NOT database - will be created on first run)
        for folder in ("assets",):
            source = os.path.join(bundle_dir, folder)
            target = os.path.join(app_dir, folder)
            if os.path.isdir(source) and not os.path.exists(target):
                shutil.copytree(source, target)

    # Create writable folders (database will be created on first run)
    for folder in ("database", "logs", "temp"):
        os.makedirs(folder, exist_ok=True)


_bootstrap_runtime_paths()

# ========== Windows DPI Awareness ==========
if sys.platform == 'win32':
    try:
        import ctypes
        # Enable DPI awareness for better scaling on Windows
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Process DPI aware
    except:
        pass

# Force Qt to use high DPI scaling
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "Round"

# ========== FIX for pkg_resources ==========
try:
    import pkg_resources
except ImportError:
    # Create a complete dummy pkg_resources module
    import types
    
    class DummyDistribution:
        """Complete dummy distribution with PKG_INFO"""
        def __init__(self, name="dummy", version="0.0.0"):
            self.project_name = name
            self.version = version
            self.key = name.lower()
            self.location = ""
            self.PKG_INFO = "Metadata-Version: 1.0\nName: dummy\nVersion: 0.0.0\n"
        
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
        """Complete dummy pkg_resources module"""
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
        
        def get_metadata_lines(self, distribution, metadata):
            return []
    
    dummy_pkg = DummyPkgResources()
    sys.modules['pkg_resources'] = dummy_pkg

# ========== NORMAL IMPORTS ==========
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import QTimer
from loguru import logger
from ui.main_window import MainWindow
from ui.login_dialog import LoginDialog
from ui.loading_dialog import LoadingDialog

# Import from models.database with all needed functions
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

# ========== UPDATE SYSTEM IMPORTS ==========
from updater.update_manager import UpdateManager
from updater.version_manager import VersionManager


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
    from PyQt6.QtWidgets import QMessageBox
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


def initialize_database():
    """
    Initialize database and run migrations on startup.
    Database will be created automatically on first run.
    
    ✅ Issue #2 Fixed: Migration failure will block startup
    """
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 60)
    
    try:
        # Step 0: Ensure database directory exists
        db_dir = "database"
        os.makedirs(db_dir, exist_ok=True)
        
        db_path = os.path.join(db_dir, "pos.db")
        is_new_db = not os.path.exists(db_path)
        
        if is_new_db:
            logger.info("📝 New database detected. Creating initial database...")
        else:
            logger.info(f"📂 Existing database found: {db_path}")
        
        # Step 1: Create tables if not exists
        logger.info("Step 1: Creating/verifying database tables...")
        create_tables()
        logger.info("✅ Database tables created/verified.")
        
        # Step 2: Check and run migrations (auto-update)
        # ✅ Issue #2 Fixed: Migration failure will raise exception and block startup
        logger.info("Step 2: Checking for pending migrations...")
        try:
            check_and_run_migrations()
            logger.info("✅ Migrations check completed.")
        except Exception as e:
            logger.error(f"❌ MIGRATION FAILED: {e}")
            logger.exception(e)
            # ✅ Issue #2 Fixed: Re-raise to block startup
            raise RuntimeError(f"Database migration failed: {e}")
        
        # Step 3: Get current status
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
        
        # Step 4: Run crash recovery check
        logger.info("Step 4: Running crash recovery check...")
        try:
            if check_and_recover(show_gui=False):
                logger.info("✅ Crash recovery actions performed.")
        except Exception as e:
            logger.error(f"Crash recovery check failed: {e}")
        
        # Step 5: Optimize database if needed
        logger.info("Step 5: Optimizing database...")
        try:
            stats = get_database_stats()
            if stats and stats.get('size_mb', 0) > 100:  # > 100MB
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
        # ✅ Issue #2 Fixed: Re-raise to block startup
        raise


def check_for_updates_on_startup():
    """Check for updates on startup (background)."""
    try:
        # Check if update check is enabled in settings
        try:
            from models.database import get_setting
            auto_check = get_setting('auto_update_check', '1')
        except:
            auto_check = '1'
        
        if auto_check == '1':
            logger.info("🔍 Checking for updates on startup...")
            update_manager = UpdateManager()
            
            # Use a timer to check after app loads
            QTimer.singleShot(5000, lambda: update_manager.check_for_updates(show_no_update_msg=False))
        else:
            logger.info("Auto-update check is disabled")
            
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")


# ---------- Start Application ----------
app = QApplication(sys.argv)
install_ui_icons()

# ✅ Initialize database with auto-migration
# ✅ Issue #2 Fixed: Migration failure will show error dialog and exit
try:
    db_status = initialize_database()
except Exception as e:
    error_msg = str(e)
    logger.critical(f"Database initialization failed: {error_msg}")
    
    # Show error dialog to user
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
    
    # Exit application with error code
    sys.exit(1)

# Load custom fonts
fonts_dir = "assets/fonts"
if os.path.exists(fonts_dir):
    for filename in os.listdir(fonts_dir):
        if filename.lower().endswith(('.ttf', '.otf')):
            font_path = os.path.join(fonts_dir, filename)
            QFontDatabase.addApplicationFont(font_path)
            logger.debug(f"Loaded font: {filename}")

# ---- Load saved theme from database ----
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

# Apply the saved theme
apply_theme(app, saved_theme)
logger.info(f"Theme loaded: {saved_theme}")

# Set Myanmar font if available
if "Noto Sans Myanmar" in QFontDatabase.families():
    app.setFont(QFont("Noto Sans Myanmar", 10))
else:
    app.setFont(QFont("Segoe UI", 10))

# ---------- Main application loop with logout support ----------
def run():
    # Check for updates after app starts
    QTimer.singleShot(3000, check_for_updates_on_startup)
    
    while True:
        login = LoginDialog()
        if login.exec() != LoginDialog.DialogCode.Accepted:
            logger.info("User cancelled login, exiting application.")
            sys.exit(0)

        logger.info(f"User logged in: {login.user_info['username']} (role: {login.user_info['role']})")
        
        # Show loading dialog
        loading = LoadingDialog("Please wait...")
        loading.show()
        
        # Process events to show the loading dialog
        QApplication.processEvents()
        
        try:
            # Update status messages
            loading.set_status("Loading database...")
            QApplication.processEvents()
            
            # Create main window
            window = MainWindow(login.user_info)
            
            loading.set_status("Loading dashboard...")
            QApplication.processEvents()
            
            # Show main window
            window.showMaximized()
            
            # Close loading dialog
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

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.critical(f"Fatal error in main loop: {e}")
        raise
    finally:
        logger.info("Application shutdown.")
        sys.exit(0)