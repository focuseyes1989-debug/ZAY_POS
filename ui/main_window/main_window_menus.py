# ui/main_window/main_window_menus.py
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction, QKeySequence
from utils.translations import tr
from utils.permissions import PermissionManager, Permission
from loguru import logger


class MainWindowMenus:
    """Handle menu bar creation for MainWindow"""
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        user_id = self.current_user["id"]
        
        # ========== FILE MENU ==========
        self.file_menu = menubar.addMenu(tr("file"))
        self._create_file_menu()
        
        # ========== PRODUCTS MENU ==========
        if PermissionManager.user_can_view_page(user_id, "products"):
            self.products_menu = menubar.addMenu(tr("products"))
            self.products_action = QAction(tr("products"), self)
            self.products_action.triggered.connect(lambda: self.switch_to_page(2))
            self.products_menu.addAction(self.products_action)

        # ========== INVENTORY MENU ==========
        if PermissionManager.user_can_view_page(user_id, "inventory"):
            self.inventory_menu = menubar.addMenu(tr("inventory"))
            self.inventory_action = QAction(tr("inventory"), self)
            self.inventory_action.triggered.connect(lambda: self.switch_to_page(3))
            self.inventory_menu.addAction(self.inventory_action)

        # ========== RECEIPTS MENU ==========
        if PermissionManager.user_can_view_page(user_id, "receipts"):
            self.receipts_menu = menubar.addMenu(tr("receipts"))
            self.receipts_action = QAction(tr("receipts"), self)
            self.receipts_action.triggered.connect(lambda: self.switch_to_page(4))
            self.receipts_menu.addAction(self.receipts_action)

        # ========== CUSTOMERS MENU ==========
        if PermissionManager.user_can_view_page(user_id, "customers"):
            self.customers_menu = menubar.addMenu(tr("customers"))
            self.customers_action = QAction(tr("customers"), self)
            self.customers_action.triggered.connect(lambda: self.switch_to_page(6))
            self.customers_menu.addAction(self.customers_action)

        # ========== CREDIT MENU ==========
        if PermissionManager.user_has_permission(user_id, Permission.VIEW_CREDIT):
            self.credit_menu = menubar.addMenu(tr("credit"))
            self.outstanding_report_action = QAction(tr("outstanding_report"), self)
            self.outstanding_report_action.triggered.connect(self.open_outstanding_report)
            self.credit_menu.addAction(self.outstanding_report_action)
            
            if self.current_user["role"] == "admin":
                self.role_management_action = QAction(tr("role_management"), self)
                self.role_management_action.triggered.connect(self.open_role_management)
                self.credit_menu.addAction(self.role_management_action)

        # ========== EXPENSE MENU ==========
        if PermissionManager.user_can_view_page(user_id, "expense"):
            self.expense_menu = menubar.addMenu(tr("expense"))
            self.expense_action = QAction(tr("expense"), self)
            self.expense_action.triggered.connect(lambda: self.switch_to_page(7))
            self.expense_menu.addAction(self.expense_action)

        # ========== REPORTS MENU ==========
        if PermissionManager.user_has_permission(user_id, Permission.VIEW_REPORTS):
            self.reports_menu = menubar.addMenu(tr("reports"))
            self._create_reports_menu()

        # ========== TOOLS MENU ==========
        if PermissionManager.user_has_permission(user_id, Permission.BACKUP):
            self.tools_menu = menubar.addMenu(tr("tools"))
            self.auto_backup_action = QAction(tr("auto_backup"), self)
            self.auto_backup_action.triggered.connect(self.open_auto_backup)
            self.tools_menu.addAction(self.auto_backup_action)

        # ========== THEMES MENU (Updated) ==========
        self.themes_menu = menubar.addMenu(tr("themes"))
        self._create_themes_menu()

        # ========== ADMIN MENU ==========
        if self.current_user["role"] == "admin":
            self.admin_menu = menubar.addMenu(tr("admin"))
            self.activity_log_action = QAction(tr("activity_log"), self)
            self.activity_log_action.triggered.connect(self.show_activity_log)
            self.admin_menu.addAction(self.activity_log_action)

    def _create_file_menu(self):
        """Create File menu items"""
        self.refresh_action = QAction(tr("refresh"), self)
        self.refresh_action.setShortcut(QKeySequence("F5"))
        self.refresh_action.setStatusTip("Refresh all pages")
        self.refresh_action.triggered.connect(self.refresh_all_pages)
        self.file_menu.addAction(self.refresh_action)
        
        self.file_menu.addSeparator()
        
        self.logout_action = QAction(tr("logout"), self)
        self.logout_action.triggered.connect(self.logout)
        self.file_menu.addAction(self.logout_action)
        
        self.settings_action = QAction(tr("settings"), self)
        self.settings_action.triggered.connect(lambda: self.switch_to_page(8))
        self.file_menu.addAction(self.settings_action)
        
        self.file_menu.addSeparator()
        
        self.exit_action = QAction(tr("exit"), self)
        self.exit_action.triggered.connect(self.exit_app)
        self.file_menu.addAction(self.exit_action)

    def _create_reports_menu(self):
        """Create Reports menu items - Show only Profit Report and Financial Summary"""
        
        # Profit Report (Detailed)
        self.profit_report_action = QAction(tr("profit_report"), self)
        self.profit_report_action.triggered.connect(self.open_profit_report)
        self.reports_menu.addAction(self.profit_report_action)
        
        # Financial Summary
        self.financial_summary_action = QAction(tr("financial_summary"), self)
        self.financial_summary_action.triggered.connect(self.open_financial_summary)
        self.reports_menu.addAction(self.financial_summary_action)

    # In _create_themes_menu method

    def _create_themes_menu(self):
        """Create Themes menu items with all available themes"""
        
        # Discord style themes
        self.dark_theme_action = QAction("Dark", self)
        self.dark_theme_action.triggered.connect(lambda: self.apply_theme("Dark"))
        self.themes_menu.addAction(self.dark_theme_action)
        
        self.light_theme_action = QAction("Light", self)
        self.light_theme_action.triggered.connect(lambda: self.apply_theme("Light"))
        self.themes_menu.addAction(self.light_theme_action)
        
        self.light_gray_theme_action = QAction("Light Gray", self)
        self.light_gray_theme_action.triggered.connect(lambda: self.apply_theme("Light Gray"))
        self.themes_menu.addAction(self.light_gray_theme_action)
        
        self.themes_menu.addSeparator()
        
        # Ubuntu themes
        self.ubuntu_theme_action = QAction("Ubuntu", self)
        self.ubuntu_theme_action.triggered.connect(lambda: self.apply_theme("Ubuntu"))
        self.themes_menu.addAction(self.ubuntu_theme_action)
        
        self.ubuntu_dark_theme_action = QAction("Ubuntu Dark", self)
        self.ubuntu_dark_theme_action.triggered.connect(lambda: self.apply_theme("Ubuntu Dark"))
        self.themes_menu.addAction(self.ubuntu_dark_theme_action)
        
        self.themes_menu.addSeparator()
        
        # Windows XP Theme
        self.windows_xp_theme_action = QAction("Windows XP", self)
        self.windows_xp_theme_action.triggered.connect(lambda: self.apply_theme("Windows XP"))
        self.themes_menu.addAction(self.windows_xp_theme_action)
        
        self.themes_menu.addSeparator()
        
        # PyQt6 Original Themes
        self.pyqt6_light_theme_action = QAction("PyQt6 Light", self)
        self.pyqt6_light_theme_action.triggered.connect(lambda: self.apply_theme("PyQt6 Light"))
        self.themes_menu.addAction(self.pyqt6_light_theme_action)
        
        self.pyqt6_dark_theme_action = QAction("PyQt6 Dark", self)
        self.pyqt6_dark_theme_action.triggered.connect(lambda: self.apply_theme("PyQt6 Dark"))
        self.themes_menu.addAction(self.pyqt6_dark_theme_action)