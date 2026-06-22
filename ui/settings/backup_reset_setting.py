# ui/backup_reset_setting.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QMessageBox, QFileDialog, QInputDialog, QProgressBar,
    QDialog, QLineEdit, QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon
from models.database import connect_db, close_all_connections
from utils.language import lang
from utils.permissions import PermissionManager, Permission
from loguru import logger
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
import time


DB_PATH = "database/pos.db"
PRODUCT_IMAGES_DIR = "database/product_images"
BACKUP_DB_NAME = "pos.db"
BACKUP_IMAGES_DIR = "product_images"


def _database_sidecar_paths(db_path):
    return (f"{db_path}-wal", f"{db_path}-shm")


def _ensure_database_exists():
    """Ensure database directory and file exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    if not os.path.exists(DB_PATH):
        logger.info("Database file not found, creating new database...")
        from models.database import create_tables
        create_tables()
        logger.info("Database created successfully.")
        return True
    return False


def _force_close_all_connections():
    """Force close all database connections and wait for release."""
    logger.info("Force closing all database connections...")
    close_all_connections()
    time.sleep(0.3)
    import gc
    gc.collect()
    
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=1)
            conn.close()
        except:
            pass
    logger.info("All connections closed.")


def _wait_for_file_release(file_path, max_wait=3):
    """Wait for a file to be released by the OS."""
    for i in range(max_wait * 10):
        try:
            with open(file_path, 'rb') as f:
                f.read(1)
            return True
        except PermissionError:
            time.sleep(0.1)
            continue
        except FileNotFoundError:
            return True
    return False


def _backup_database_file(source_path, backup_path):
    if not os.path.exists(source_path):
        logger.warning(f"Source database not found: {source_path}")
        os.makedirs(os.path.dirname(source_path), exist_ok=True)
        from models.database import create_tables
        create_tables()
        logger.info("Created new database for backup.")

    backup_dir = os.path.dirname(os.path.abspath(backup_path))
    if backup_dir:
        os.makedirs(backup_dir, exist_ok=True)

    source = sqlite3.connect(source_path)
    try:
        source.execute("PRAGMA wal_checkpoint(FULL)")
        dest = sqlite3.connect(backup_path)
        try:
            source.backup(dest)
            dest.commit()
        finally:
            dest.close()
    finally:
        source.close()


def _ensure_backup_extension(file_path):
    if os.path.splitext(file_path)[1]:
        return file_path
    return f"{file_path}.zaybackup"


def _create_backup_package(backup_path, db_path=DB_PATH, product_images_dir=PRODUCT_IMAGES_DIR):
    backup_path = _ensure_backup_extension(backup_path)

    if os.path.splitext(backup_path)[1].lower() == ".db":
        _backup_database_file(db_path, backup_path)
        return backup_path

    backup_dir = os.path.dirname(os.path.abspath(backup_path))
    if backup_dir:
        os.makedirs(backup_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_db = os.path.join(tmp_dir, BACKUP_DB_NAME)
        _backup_database_file(db_path, temp_db)

        with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(temp_db, BACKUP_DB_NAME)

            if os.path.isdir(product_images_dir):
                for root, _, files in os.walk(product_images_dir):
                    for filename in files:
                        source = os.path.join(root, filename)
                        relative = os.path.relpath(source, product_images_dir)
                        archive.write(source, os.path.join(BACKUP_IMAGES_DIR, relative))

    return backup_path


def _restore_backup_package(backup_path, db_path=DB_PATH, product_images_dir=PRODUCT_IMAGES_DIR):
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    _force_close_all_connections()
    
    if os.path.exists(db_path):
        _wait_for_file_release(db_path, max_wait=3)
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    for sidecar in _database_sidecar_paths(db_path):
        if os.path.exists(sidecar):
            try:
                os.remove(sidecar)
            except:
                pass
    
    if zipfile.is_zipfile(backup_path):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(backup_path, "r") as archive:
                names = set(archive.namelist())
                if BACKUP_DB_NAME not in names:
                    raise FileNotFoundError("Backup package does not contain pos.db.")
                archive.extractall(tmp_dir)

            extracted_db = os.path.join(tmp_dir, BACKUP_DB_NAME)
            
            if not os.path.exists(extracted_db):
                raise FileNotFoundError(f"Extracted database not found: {extracted_db}")
            
            _validate_database_file(extracted_db)
            _restore_database_file(extracted_db, db_path)

            extracted_images = os.path.join(tmp_dir, BACKUP_IMAGES_DIR)
            if os.path.isdir(extracted_images):
                if os.path.isdir(product_images_dir):
                    shutil.rmtree(product_images_dir)
                os.makedirs(os.path.dirname(product_images_dir), exist_ok=True)
                shutil.copytree(extracted_images, product_images_dir)
            else:
                os.makedirs(product_images_dir, exist_ok=True)
    else:
        _validate_database_file(backup_path)
        _restore_database_file(backup_path, db_path)


def _validate_database_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        conn = sqlite3.connect(file_path)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0].lower() != "ok":
                raise sqlite3.DatabaseError("Database integrity check failed.")
            
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if not tables:
                raise sqlite3.DatabaseError("Database has no tables.")
            
            table_names = [t[0] for t in tables]
            essential_tables = ['settings', 'users', 'products']
            missing_tables = [t for t in essential_tables if t not in table_names]
            if missing_tables:
                raise sqlite3.DatabaseError(f"Missing essential tables: {missing_tables}")
            
        finally:
            conn.close()
    except sqlite3.DatabaseError as e:
        raise sqlite3.DatabaseError(f"Invalid database file: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to validate database: {str(e)}")


def _restore_database_file(backup_path, db_path=DB_PATH):
    if not os.path.exists(backup_path):
        raise FileNotFoundError("Backup file not found.")

    _validate_database_file(backup_path)

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    _force_close_all_connections()
    
    if os.path.exists(db_path):
        _wait_for_file_release(db_path, max_wait=3)

    if os.path.exists(db_path):
        temp_backup = os.path.join(os.path.dirname(db_path), "pos_backup_before_restore.db")
        try:
            _backup_database_file(db_path, temp_backup)
        except:
            pass

    for sidecar in _database_sidecar_paths(db_path):
        if os.path.exists(sidecar):
            try:
                os.remove(sidecar)
            except:
                pass

    retry_count = 3
    for i in range(retry_count):
        try:
            shutil.copy2(backup_path, db_path)
            break
        except PermissionError:
            if i < retry_count - 1:
                time.sleep(0.5)
                _force_close_all_connections()
            else:
                raise PermissionError(f"Could not restore database: {e}")

    for sidecar in _database_sidecar_paths(db_path):
        if os.path.exists(sidecar):
            try:
                os.remove(sidecar)
            except:
                pass


# ========== WORKER THREADS WITH PROPER PROGRESS ==========

class BackupWorker(QThread):
    """Worker thread for backup operation with progress."""
    progress = pyqtSignal(int, str)  # value, status
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, backup_path):
        super().__init__()
        self.backup_path = backup_path
        
    def run(self):
        try:
            self.progress.emit(5, "Checking database...")
            _ensure_database_exists()
            
            self.progress.emit(10, "Preparing backup...")
            time.sleep(0.1)
            
            self.progress.emit(20, "Creating database backup...")
            
            # Create backup with progress
            _create_backup_package(self.backup_path)
            
            self.progress.emit(90, "Finalizing...")
            time.sleep(0.1)
            
            self.progress.emit(100, "Backup completed!")
            self.finished.emit(True, self.backup_path)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            self.finished.emit(False, str(e))


class RestoreWorker(QThread):
    """Worker thread for restore operation with progress."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, restore_path):
        super().__init__()
        self.restore_path = restore_path
        
    def run(self):
        try:
            self.progress.emit(5, "Validating backup file...")
            
            if not os.path.exists(self.restore_path):
                raise FileNotFoundError("Backup file not found")
            
            self.progress.emit(10, "Closing database connections...")
            _force_close_all_connections()
            time.sleep(0.2)
            
            self.progress.emit(20, "Restoring database...")
            
            # Restore with progress
            _restore_backup_package(self.restore_path)
            
            self.progress.emit(90, "Finalizing...")
            time.sleep(0.1)
            
            self.progress.emit(100, "Restore completed!")
            self.finished.emit(True, "Restore completed successfully")
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            self.finished.emit(False, str(e))


class FactoryResetWorker(QThread):
    """Worker thread for factory reset with detailed progress."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, backup_path):
        super().__init__()
        self.backup_path = backup_path
        
    def run(self):
        try:
            # Step 1: Check database
            self.progress.emit(5, "Checking database...")
            _ensure_database_exists()
            time.sleep(0.1)
            
            # Step 2: Close connections
            self.progress.emit(8, "Closing database connections...")
            _force_close_all_connections()
            time.sleep(0.2)
            
            # Step 3: Create backup
            self.progress.emit(10, "Creating backup...")
            _create_backup_package(self.backup_path)
            self.progress.emit(25, "Backup created")
            time.sleep(0.1)
            
            # Step 4: Connect to database
            self.progress.emit(30, "Connecting to database...")
            conn = None
            for i in range(3):
                try:
                    conn = sqlite3.connect(DB_PATH, timeout=5)
                    break
                except sqlite3.OperationalError:
                    if i < 2:
                        time.sleep(0.5)
                        _force_close_all_connections()
                    else:
                        raise
            
            if conn is None:
                raise Exception("Could not connect to database")
            
            cursor = conn.cursor()
            
            # Step 5: Clear tables
            self.progress.emit(35, "Clearing data...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            total_tables = len(tables)
            for i, (table_name,) in enumerate(tables):
                if table_name not in ['sqlite_sequence', 'migration_history']:
                    cursor.execute(f"DELETE FROM {table_name}")
                progress_value = 35 + int((i / max(total_tables, 1)) * 25)
                self.progress.emit(progress_value, f"Clearing: {table_name}")
                QApplication.processEvents()
            
            # Step 6: Reset settings
            self.progress.emit(60, "Resetting settings...")
            default_settings = [
                ('tax_rate', '0'), ('tax_enabled', '0'),
                ('loyalty_points_per_dollar', '0'), ('loyalty_min_points_for_reward', '100'),
                ('loyalty_reward_discount', '5'), ('discount_enabled', '0'),
                ('discount_type', 'percentage'), ('discount_value', '0'),
                ('currency', 'Kyats (Ks)'),
                ('shop_name', 'ZAY POS'), ('shop_logo', ''),
                ('shop_phone', ''), ('shop_address', ''), ('shop_footer_message', ''),
                ('receipt_header', ''), ('receipt_footer', ''), ('show_customer_name', '1'),
                ('language', 'en'), ('theme', 'Light'),
                ('points_expiry_months', '12'), ('points_dollar_value', '0.01'),
                ('follow_system_theme', '1'),
                ('auto_backup_enabled', '0'), ('auto_backup_interval', '24'), ('auto_backup_max', '30')
            ]
            
            cursor.execute("DELETE FROM settings")
            for key, val in default_settings:
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, val))
            
            # Step 7: Reset users
            self.progress.emit(68, "Resetting users...")
            cursor.execute("DELETE FROM users")
            import hashlib
            salt = os.urandom(32).hex()
            password_hash = hashlib.pbkdf2_hmac('sha256', 'admin'.encode(), bytes.fromhex(salt), 100000).hex()
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, full_name, salt, force_password_change, is_active) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("admin", password_hash, "Admin", "Administrator", salt, 0, 1))
            
            # Step 8: Reset user roles
            self.progress.emit(73, "Resetting user roles...")
            cursor.execute("DELETE FROM user_roles")
            default_roles = [
                ('Admin', 'Full access to all features', 
                 'dashboard,sales,sales_summary,products,inventory,receipts,customers,expense,reports,credit,users,settings,backup,add_product,edit_product,delete_product,add_customer,edit_customer,delete_customer,add_user,edit_user,delete_user,edit_settings,stock_in,stock_out,adjustment,refund_sale,delete_sale,view_users',
                 1),
                ('Manager', 'Can manage sales, products, inventory, customers, expenses',
                 'dashboard,sales,sales_summary,products,inventory,receipts,customers,expense,reports,credit,add_product,edit_product,add_customer,edit_customer,stock_in,stock_out,adjustment,refund_sale',
                 0),
                ('Cashier', 'Can process sales and view receipts',
                 'dashboard,sales,receipts,customers,add_customer,refund_sale',
                 0),
                ('Viewer', 'Read-only access',
                 'dashboard,sales_summary,reports',
                 0),
            ]
            for name, desc, perms, is_system in default_roles:
                cursor.execute("""
                    INSERT INTO user_roles (name, description, permissions, is_system)
                    VALUES (?, ?, ?, ?)
                """, (name, desc, perms, is_system))
            
            # Step 9: Reset categories
            self.progress.emit(78, "Resetting categories...")
            cursor.execute("DELETE FROM categories")
            cursor.execute("INSERT INTO categories (name) VALUES ('General')")
            
            # Step 10: Reset payment types
            self.progress.emit(82, "Resetting payment types...")
            cursor.execute("DELETE FROM payment_types")
            cursor.executemany("INSERT INTO payment_types (name, is_active) VALUES (?, 1)", 
                               [("Cash",), ("Card",), ("Mobile Money",)])
            
            # Step 11: Reset expense categories
            self.progress.emit(86, "Resetting expense categories...")
            cursor.execute("DELETE FROM expense_categories")
            default_expense_categories = [
                ('Rent', 'Office/Shop rent', 1),
                ('Utilities', 'Electricity, Water, Internet', 1),
                ('Salaries', 'Employee salaries', 1),
                ('Marketing', 'Advertising, Promotion', 1),
                ('Maintenance', 'Equipment repair', 1),
                ('Transport', 'Delivery, Fuel', 1),
                ('Office Supplies', 'Stationery, Printing', 1),
                ('Taxes', 'Government taxes', 1),
                ('Other', 'Miscellaneous expenses', 1)
            ]
            for name, description, is_active in default_expense_categories:
                cursor.execute("""
                    INSERT INTO expense_categories (name, description, is_active) 
                    VALUES (?, ?, ?)
                """, (name, description, is_active))
            
            conn.commit()
            conn.close()
            
            # Step 12: Clean temporary files
            self.progress.emit(92, "Cleaning temporary files...")
            temp_dirs = ["temp", "logs", "attachments", "database/backups"]
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for filename in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                        except:
                            pass
            
            self.progress.emit(100, "Reset completed!")
            self.finished.emit(True, self.backup_path)
            
        except Exception as e:
            logger.error(f"Factory reset failed: {e}")
            self.finished.emit(False, str(e))


# ========== PROGRESS DIALOG ==========

class ProgressDialog(QDialog):
    """Progress dialog with status and progress bar."""
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(450, 180)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | 
                           Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Status label
        self.status_label = QLabel("Starting...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12pt;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                height: 25px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Cancel button (optional)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedWidth(100)
        self.btn_cancel.setEnabled(False)  # Disabled by default
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def update_progress(self, value, status):
        """Update progress bar and status."""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
        QApplication.processEvents()


class BackupResetSettingWidget(QWidget):
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.worker = None
        self.progress_dialog = None
        self.setup_ui()
        self.apply_permissions()

    def apply_permissions(self):
        if self.user_id:
            if not PermissionManager.user_has_permission(self.user_id, Permission.BACKUP):
                self.btn_backup.setEnabled(False)
                self.btn_backup.setToolTip("You don't have permission to backup database")
                self.btn_restore.setEnabled(False)
                self.btn_restore.setToolTip("You don't have permission to restore database")
            
            if not PermissionManager.user_has_permission(self.user_id, Permission.FACTORY_RESET):
                self.btn_reset.setEnabled(False)
                self.btn_reset.setToolTip("You don't have permission to perform factory reset")

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.backup_group = QGroupBox()
        backup_layout = QVBoxLayout()
        self.backup_desc = QLabel()
        self.backup_desc.setWordWrap(True)
        backup_layout.addWidget(self.backup_desc)
        self.btn_backup = QPushButton()
        self.btn_backup.clicked.connect(self.backup_database)
        backup_layout.addWidget(self.btn_backup)
        self.btn_restore = QPushButton()
        self.btn_restore.clicked.connect(self.restore_database)
        backup_layout.addWidget(self.btn_restore)
        self.backup_group.setLayout(backup_layout)
        left_layout.addWidget(self.backup_group)
        left_layout.addStretch()

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.reset_group = QGroupBox()
        reset_layout = QVBoxLayout()
        self.reset_desc = QLabel()
        self.reset_desc.setWordWrap(True)
        reset_layout.addWidget(self.reset_desc)
        self.btn_reset = QPushButton()
        self.btn_reset.clicked.connect(self.start_factory_reset)
        reset_layout.addWidget(self.btn_reset)
        self.reset_group.setLayout(reset_layout)
        right_layout.addWidget(self.reset_group)
        right_layout.addStretch()

        columns_layout.addWidget(left_column)
        columns_layout.addWidget(right_column)
        layout.addLayout(columns_layout)
        self.setLayout(layout)
        self.retranslateUi()

    def retranslateUi(self):
        if lang.get_current() == "my":
            self.backup_group.setTitle("Database Backup")
            self.backup_desc.setText("သင်၏ database ကို backup ဖိုင်အဖြစ် သိမ်းဆည်းရန်။")
            self.btn_backup.setText("Backup ပြုလုပ်မည်")
            self.btn_restore.setText("Restore ပြုလုပ်မည်")
            self.reset_group.setTitle("စက်ရုံပြန်လည်သတ်မှတ်ခြင်း")
            self.reset_desc.setText(
                "⚠️ သတိပေးချက် ⚠️\n\n"
                "ဤလုပ်ဆောင်ချက်သည် အောက်ပါအချက်များအားလုံးကို အပြီးတိုင်ဖျက်ပစ်မည်:\n"
                "• ရောင်းအားမှတ်တမ်းများ\n"
                "• ဝယ်ယူသူများ\n"
                "• ပေးသွင်းသူများ\n"
                "• စတော့ပြောင်းလဲမှုများ\n"
                "• ပစ္စည်းများ\n"
                "• အသုံးစရိတ်များ\n\n"
                "**Backup ဖိုင်အလိုအလျောက် သိမ်းဆည်းပေးမည်။**\n"
                "ဤလုပ်ဆောင်ချက်ကို နောက်ပြန်မလှန်နိုင်ပါ။"
            )
            self.btn_reset.setText("စက်ရုံပြန်လည်သတ်မှတ်ခြင်း လုပ်ဆောင်ရန်")
        else:
            self.backup_group.setTitle("Database Backup")
            self.backup_desc.setText("Save a backup copy of your current database.")
            self.btn_backup.setText("Perform Backup")
            self.btn_restore.setText("Perform Restore")
            self.reset_group.setTitle("Factory Reset")
            self.reset_desc.setText(
                "⚠️ WARNING ⚠️\n\n"
                "This will permanently delete ALL:\n"
                "• Sales history\n"
                "• Customers\n"
                "• Suppliers\n"
                "• Stock movements\n"
                "• Products\n"
                "• Expenses\n\n"
                "**A backup will be automatically created before reset.**\n"
                "This action CANNOT be undone!"
            )
            self.btn_reset.setText("Perform Factory Reset")

    def _show_progress_dialog(self, title):
        """Show progress dialog."""
        self.progress_dialog = ProgressDialog(title, self)
        self.progress_dialog.show()
        QApplication.processEvents()
        return self.progress_dialog

    def _close_progress_dialog(self):
        """Close progress dialog."""
        if self.progress_dialog:
            self.progress_dialog.accept()
            self.progress_dialog = None
        QApplication.processEvents()

    def _on_backup_progress(self, value, status):
        """Update backup progress."""
        if self.progress_dialog:
            self.progress_dialog.update_progress(value, status)

    def _on_backup_finished(self, success, result):
        """Handle backup completion."""
        self._close_progress_dialog()
        self.btn_backup.setEnabled(True)
        
        if success:
            msg = f"Backup saved to:\n{result}" if lang.get_current() != "my" else f"Backup ဖိုင်ကို ဤနေရာတွင် သိမ်းဆည်းပြီးပါပြီ:\n{result}"
            QMessageBox.information(self, "Backup Complete" if lang.get_current() != "my" else "Backup ပြီးပါပြီ", msg)
        else:
            QMessageBox.critical(self, "Error", f"Backup failed: {result}")

    def _on_restore_progress(self, value, status):
        """Update restore progress."""
        if self.progress_dialog:
            self.progress_dialog.update_progress(value, status)

    def _on_restore_finished(self, success, result):
        """Handle restore completion."""
        self._close_progress_dialog()
        self.btn_restore.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self,
                "Restore Complete" if lang.get_current() != "my" else "Restore ပြီးပါပြီ",
                "Database restored. The application will now close.\nPlease restart manually."
                if lang.get_current() != "my" else
                "Database ပြန်လည် restore ပြီးပါပြီ။ Application ပိတ်သွားပါမည်။ ကျေးဇူးပြု၍ ပြန်ဖွင့်ပါ။"
            )
            import sys
            sys.exit(0)
        else:
            QMessageBox.critical(self, "Error", f"Restore failed: {result}")

    def _on_reset_progress(self, value, status):
        """Update reset progress."""
        if self.progress_dialog:
            self.progress_dialog.update_progress(value, status)

    def _on_reset_finished(self, success, result):
        """Handle factory reset completion."""
        self._close_progress_dialog()
        self.btn_reset.setEnabled(True)
        
        if success:
            backup_dialog = BackupInfoDialog(result, self)
            backup_dialog.exec()
            import sys
            sys.exit(0)
        else:
            QMessageBox.critical(self, "Factory Reset Failed", f"Error: {result}")

    def backup_database(self):
        """Create a database backup."""
        _ensure_database_exists()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"pos_backup_{timestamp}.zaybackup"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Backup Database" if lang.get_current() != "my" else "Database Backup သိမ်းရန်",
            default_filename,
            "ZAY POS Backup (*.zaybackup);;Database Files (*.db)"
        )
        if not file_path:
            return
        
        # Disable button
        self.btn_backup.setEnabled(False)
        
        # Show progress dialog
        self._show_progress_dialog("Backing up database...")
        
        # Start worker
        self.worker = BackupWorker(file_path)
        self.worker.progress.connect(self._on_backup_progress)
        self.worker.finished.connect(self._on_backup_finished)
        self.worker.start()

    def restore_database(self):
        """Restore database from backup."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Database" if lang.get_current() != "my" else "Database Backup ဖိုင်ရွေးရန်",
            "",
            "ZAY POS Backup (*.zaybackup);;Database Files (*.db);;Zip Files (*.zip)"
        )
        if not file_path:
            return
        
        confirm_msg = (
            "Are you sure you want to restore this backup?\n"
            "Your current database will be overwritten and all recent changes may be lost.\n"
            "The application will close after restore. Please restart manually."
            if lang.get_current() != "my" else
            "ဤ backup ဖိုင်ကို ပြန်လည် restore လုပ်မည်လား?\n"
            "လက်ရှိ database အဟောင်း ပျက်သွားမည်။\n"
            "Restore ပြီးပါက application ပိတ်သွားမည်။ ကျေးဇူးပြု၍ ပြန်ဖွင့်ပါ။"
        )
        reply = QMessageBox.question(
            self,
            "Confirm Restore" if lang.get_current() != "my" else "Restore လုပ်ရန်အတည်ပြုပါ",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable button
        self.btn_restore.setEnabled(False)
        
        # Show progress dialog
        self._show_progress_dialog("Restoring database...")
        
        # Start worker
        self.worker = RestoreWorker(file_path)
        self.worker.progress.connect(self._on_restore_progress)
        self.worker.finished.connect(self._on_restore_finished)
        self.worker.start()

    def start_factory_reset(self):
        """Start factory reset process with confirmation and backup."""
        if self.user_id and not PermissionManager.user_has_permission(self.user_id, Permission.FACTORY_RESET):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to perform factory reset.")
            return
        
        _ensure_database_exists()
        
        confirm_dialog = ConfirmResetDialog(self)
        if confirm_dialog.exec() != QDialog.DialogCode.Accepted or not confirm_dialog.confirmed:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"factory_reset_backup_{timestamp}.zaybackup"
        backup_dir = "database/backups"
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Disable button
        self.btn_reset.setEnabled(False)
        
        # Show progress dialog
        self._show_progress_dialog("Factory reset in progress...")
        
        # Start worker
        self.worker = FactoryResetWorker(backup_path)
        self.worker.progress.connect(self._on_reset_progress)
        self.worker.finished.connect(self._on_reset_finished)
        self.worker.start()


# ========== DIALOGS ==========

class BackupInfoDialog(QDialog):
    def __init__(self, backup_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Backup Created")
        self.setMinimumSize(500, 350)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        title_layout = QHBoxLayout()
        icon_label = QLabel("✅")
        icon_label.setStyleSheet("font-size: 48pt;")
        title_layout.addWidget(icon_label)
        
        self.title_text = QLabel("Factory Reset Completed Successfully!")
        self.title_text.setStyleSheet("font-size: 14pt; font-weight: bold; color: #27ae60;")
        title_layout.addWidget(self.title_text)
        layout.addLayout(title_layout)
        
        info_group = QGroupBox("Backup Information")
        info_layout = QVBoxLayout()
        backup_label = QLabel("Backup saved at:")
        backup_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(backup_label)
        backup_path_label = QLabel(backup_path)
        backup_path_label.setWordWrap(True)
        backup_path_label.setStyleSheet("color: #3498db; font-family: monospace;")
        info_layout.addWidget(backup_path_label)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        instruction_group = QGroupBox("What to do next?")
        instruction_layout = QVBoxLayout()
        instructions = QLabel(
            "1. The application will now close.\n"
            "2. Please restart the application manually.\n"
            "3. Login with: admin / admin\n"
            "4. Your backup is saved in the database/backups folder.\n"
            "5. To restore, use the Restore button in Backup & Reset settings."
        )
        instructions.setWordWrap(True)
        instruction_layout.addWidget(instructions)
        instruction_group.setLayout(instruction_layout)
        layout.addWidget(instruction_group)
        
        btn_layout = QHBoxLayout()
        self.btn_open_folder = QPushButton("Open Backup Folder")
        self.btn_open_folder.clicked.connect(lambda: self.open_folder(os.path.dirname(backup_path)))
        self.btn_close = QPushButton("Close Application")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_open_folder)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.retranslateUi()
    
    def open_folder(self, path):
        import subprocess
        import sys
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])
    
    def retranslateUi(self):
        lang_code = self.get_lang()
        if lang_code == "my":
            self.setWindowTitle("Backup ဖိုင်သိမ်းဆည်းပြီးပါပြီ")
            self.title_text.setText("Factory Reset အောင်မြင်စွာ ပြီးဆုံးပါပြီ!")
            backup_label.setText("Backup ဖိုင်သိမ်းဆည်းရာနေရာ:")
            self.btn_open_folder.setText("Backup ဖိုင်တွဲဖွင့်ရန်")
            self.btn_close.setText("Application ပိတ်ရန်")
    
    def get_lang(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='language'")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "en"
        except:
            return "en"


class ConfirmResetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Factory Reset")
        self.setMinimumSize(500, 450)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)
        self.confirmed = False
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        warning_layout = QHBoxLayout()
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 48pt;")
        warning_layout.addWidget(warning_icon)
        
        self.warning_text = QLabel("WARNING: This action cannot be undone!")
        self.warning_text.setStyleSheet("font-size: 14pt; font-weight: bold; color: #e74c3c;")
        warning_layout.addWidget(self.warning_text)
        layout.addLayout(warning_layout)
        
        delete_group = QGroupBox("The following data will be PERMANENTLY DELETED:")
        delete_layout = QVBoxLayout()
        delete_items = [
            "• All sales records and receipts",
            "• All customer data and points",
            "• All supplier information",
            "• All product inventory",
            "• All stock movements",
            "• All expenses and budgets",
            "• All credit sales and payments",
            "• All purchase orders"
        ]
        for item in delete_items:
            delete_layout.addWidget(QLabel(item))
        delete_group.setLayout(delete_layout)
        layout.addWidget(delete_group)
        
        keep_group = QGroupBox("The following will be preserved:")
        keep_layout = QVBoxLayout()
        keep_items = [
            "✓ A backup will be created before reset",
            "✓ User accounts (only admin will remain)",
            "✓ System settings (reset to defaults)",
            "✓ Categories and payment types (reset to defaults)"
        ]
        for item in keep_items:
            keep_layout.addWidget(QLabel(item))
        keep_group.setLayout(keep_layout)
        layout.addWidget(keep_group)
        
        confirm_layout = QVBoxLayout()
        confirm_label = QLabel("Type 'RESET ALL' to confirm:")
        confirm_label.setStyleSheet("font-weight: bold;")
        confirm_layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("RESET ALL")
        confirm_layout.addWidget(self.confirm_input)
        layout.addLayout(confirm_layout)
        
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_confirm = QPushButton("Confirm Reset")
        self.btn_confirm.setStyleSheet("background-color: #e74c3c; color: white;")
        self.btn_confirm.clicked.connect(self.check_confirmation)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.retranslateUi()
    
    def check_confirmation(self):
        if self.confirm_input.text() == "RESET ALL":
            self.confirmed = True
            self.accept()
        else:
            QMessageBox.warning(self, "Invalid Input", "Please type 'RESET ALL' to confirm.")
    
    def retranslateUi(self):
        lang_code = self.get_lang()
        if lang_code == "my":
            self.setWindowTitle("Factory Reset အတည်ပြုရန်")
            self.warning_text.setText("သတိပေးချက်: ဤလုပ်ဆောင်ချက်ကို နောက်ပြန်မလှန်နိုင်ပါ!")
            delete_group.setTitle("အောက်ပါဒေတာများ အပြီးတိုင်ဖျက်ပစ်မည်:")
            keep_group.setTitle("အောက်ပါအချက်များ ထိန်းသိမ်းမည်:")
            confirm_label.setText("အတည်ပြုရန် 'RESET ALL' ရိုက်ထည့်ပါ:")
            self.btn_cancel.setText("မလုပ်တော့")
            self.btn_confirm.setText("အတည်ပြုဖျက်မည်")
    
    def get_lang(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='language'")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "en"
        except:
            return "en"