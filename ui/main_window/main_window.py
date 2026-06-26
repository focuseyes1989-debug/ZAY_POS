# ui/main_window/main_window.py
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QIcon
from models.database import create_tables
from utils.language import lang
from utils.system_theme import system_theme
from utils.auto_backup import AutoBackupManager
from utils.expense_notification_checker import ExpenseNotificationChecker
from ui.main_window.main_window_ui import MainWindowUI
from ui.main_window.main_window_menus import MainWindowMenus
from ui.main_window.main_window_actions import MainWindowActions
from ui.main_window.main_window_handlers import MainWindowHandlers
from loguru import logger
from ui.reports.profit_loss_report_dialog import ProfitLossReportDialog


class MainWindow(QMainWindow, MainWindowUI, MainWindowMenus, MainWindowActions, MainWindowHandlers):
    logout_signal = pyqtSignal()

    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.user_id = current_user["id"]
        self.logout_triggered = False
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        create_tables()
        self.current_language = lang.get_current()
        
        # Set constants for scaling
        self._keep_aspect_ratio = Qt.AspectRatioMode.KeepAspectRatio
        self._smooth_transform = Qt.TransformationMode.SmoothTransformation
        
        self.create_menu_bar()
        self.setup_ui()
        self.apply_language()
        self.update_shop_logo()
        self.update_shop_title()
        self.setFixedWindowTitle()

        self.setup_refresh_shortcut()

        self.auto_backup_manager = AutoBackupManager(self)
        self.auto_backup_manager.start()

        lang.language_changed.connect(self.on_language_changed)

        # Connect settings page signals
        if hasattr(self, 'settings_page'):
            self.settings_page.receipt_settings_changed.connect(self.refresh_shop_info)
            self.settings_page.general_settings_changed.connect(self.refresh_general_settings)
            self.settings_page.currency_changed.connect(self.refresh_currency)
            self.settings_page.general_tab.follow_system_theme_changed.connect(self.on_follow_system_theme_changed)

        self.follow_system_theme = self.load_follow_system_theme()
        system_theme.theme_changed.connect(self.on_system_theme_changed)

        # Stock alert notification
        self._init_notification_icon()
        
        QTimer.singleShot(500, self.check_stock_alerts)
        
        self.expense_notification_checker = ExpenseNotificationChecker(self)
        self.expense_notification_checker.alert_triggered.connect(self.show_expense_alert)
        
        self.apply_theme_from_settings()
        
        logger.info(f"MainWindow initialised for user: {self.current_user['username']} (role: {self.current_user['role']})")

    def _init_notification_icon(self):
        from PyQt6.QtWidgets import QLabel
        
        self.notification_icon = QLabel()
        self.notification_icon.setFixedSize(16, 16)
        self.notification_icon.setStyleSheet("background-color: #ed4245; border-radius: 8px;")
        self.notification_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notification_icon.mousePressEvent = self.show_notification_dialog
        self.status_bar.addPermanentWidget(self.notification_icon)
        self.notification_icon.hide()
        
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.toggle_notification_icon)
        self.blink_state = False
        self.has_alerts = False

    def setFixedWindowTitle(self):
        """Set window title with version number."""
        from updater.version_manager import VersionManager
        
        try:
            version_manager = VersionManager()
            version = version_manager.get_current_version()
            self.setWindowTitle(f"ZAY POS Lite v{version}")
            logger.info(f"Window title set: ZAY POS Lite v{version}")
        except Exception as e:
            logger.warning(f"Could not get version for window title: {e}")
            self.setWindowTitle("ZAY POS Lite")
            logger.info("Window title set: ZAY POS Lite (no version)")

    def load_follow_system_theme(self):
        from models.database import connect_db
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='follow_system_theme'")
            row = cursor.fetchone()
            conn.close()
            return row[0] == '1' if row else True
        except:
            return True

    def apply_theme_from_settings(self):
        if self.follow_system_theme:
            theme = system_theme.get_system_theme()
            self.apply_theme(theme)
            self.set_theme_menu_enabled(False)
        else:
            from models.database import connect_db
            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key='theme'")
                row = cursor.fetchone()
                saved_theme = row[0] if row else "Light"
                conn.close()
            except:
                saved_theme = "Light"
            self.apply_theme(saved_theme)
            self.set_theme_menu_enabled(True)

    def on_follow_system_theme_changed(self, checked):
        self.follow_system_theme = checked
        self.apply_theme_from_settings()

    def on_system_theme_changed(self, theme_name):
        if self.follow_system_theme:
            self.apply_theme(theme_name)

    def apply_language(self):
        from utils.translations import tr
        
        # Update navigation buttons
        self.btn_sales.setText(tr("sales"))
        self.btn_dashboard.setText(tr("dashboard"))
        self.btn_sales_summary.setText(tr("sales_summary"))
        self.btn_expense.setText(tr("expense"))
        self.btn_settings.setText(tr("settings"))
        
        # Update menu texts
        self._update_menu_texts()
    
    def _update_menu_texts(self):
        """Update all menu texts - called from apply_language"""
        from utils.translations import tr
        
        # File menu
        if hasattr(self, 'file_menu'):
            self.file_menu.setTitle(tr("file"))
            if hasattr(self, 'refresh_action'):
                self.refresh_action.setText(tr("refresh"))
            if hasattr(self, 'logout_action'):
                self.logout_action.setText(tr("logout"))
            if hasattr(self, 'settings_action'):
                self.settings_action.setText(tr("settings"))
            if hasattr(self, 'exit_action'):
                self.exit_action.setText(tr("exit"))
        
        # Products menu
        if hasattr(self, 'products_menu'):
            self.products_menu.setTitle(tr("products"))
            if hasattr(self, 'products_action'):
                self.products_action.setText(tr("products"))
        
        # Inventory menu
        if hasattr(self, 'inventory_menu'):
            self.inventory_menu.setTitle(tr("inventory"))
            if hasattr(self, 'inventory_action'):
                self.inventory_action.setText(tr("inventory"))
        
        # Receipts menu
        if hasattr(self, 'receipts_menu'):
            self.receipts_menu.setTitle(tr("receipts"))
            if hasattr(self, 'receipts_action'):
                self.receipts_action.setText(tr("receipts"))
        
        # Customers menu
        if hasattr(self, 'customers_menu'):
            self.customers_menu.setTitle(tr("customers"))
            if hasattr(self, 'customers_action'):
                self.customers_action.setText(tr("customers"))
        
        # Credit menu
        if hasattr(self, 'credit_menu'):
            self.credit_menu.setTitle(tr("credit"))
            if hasattr(self, 'outstanding_report_action'):
                self.outstanding_report_action.setText(tr("outstanding_report"))
            if hasattr(self, 'role_management_action'):
                self.role_management_action.setText(tr("role_management"))
        
        # Expense menu
        if hasattr(self, 'expense_menu'):
            self.expense_menu.setTitle(tr("expense"))
            if hasattr(self, 'expense_action'):
                self.expense_action.setText(tr("expense"))
        
        # Reports menu
        if hasattr(self, 'reports_menu'):
            self.reports_menu.setTitle(tr("reports"))
            if hasattr(self, 'sales_report_action'):
                self.sales_report_action.setText(tr("sales_report"))
            if hasattr(self, 'expense_report_action'):
                self.expense_report_action.setText(tr("expense_report"))
            if hasattr(self, 'profit_loss_report_action'):
                self.profit_loss_report_action.setText(tr("profit_loss_report"))
            if hasattr(self, 'profit_report_action'):
                self.profit_report_action.setText(tr("profit_report"))
            if hasattr(self, 'financial_summary_action'):
                self.financial_summary_action.setText(tr("financial_summary"))
        
        # Tools menu
        if hasattr(self, 'tools_menu'):
            self.tools_menu.setTitle(tr("tools"))
            if hasattr(self, 'auto_backup_action'):
                self.auto_backup_action.setText(tr("auto_backup"))
        
        # Themes menu
        if hasattr(self, 'themes_menu'):
            self.themes_menu.setTitle(tr("themes"))
            if hasattr(self, 'dark_theme_action'):
                self.dark_theme_action.setText(tr("dark"))
            if hasattr(self, 'light_theme_action'):
                self.light_theme_action.setText(tr("light"))
        
        # Admin menu
        if hasattr(self, 'admin_menu'):
            self.admin_menu.setTitle(tr("admin"))
            if hasattr(self, 'activity_log_action'):
                self.activity_log_action.setText(tr("activity_log"))

    def refresh_shop_info(self):
        """Refresh shop logo and title"""
        self.update_shop_logo()
        self.update_shop_title()
        logger.info("Shop info refreshed")