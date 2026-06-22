# ui/main_window_ui.py
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QStatusBar, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QSize
from utils.translations import tr
from utils.permissions import PermissionManager, Permission
from loguru import logger


class MainWindowUI:
    """Handle UI setup for MainWindow"""
    
    def setup_ui(self):
        # Get screen geometry for dynamic sizing
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        # Set window size based on screen (85% of screen)
        self.resize(int(screen_width * 0.85), int(screen_height * 0.85))
        
        # Set minimum size
        self.setMinimumSize(1024, 600)
        
        self.base_style = """
            QLineEdit::placeholder { color: #888888; }
            QWidget { font-size: 9pt; }
        """
        self.setStyleSheet(self.base_style)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top bar - responsive
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(35, 35)
        self.logo_label.setScaledContents(True)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.logo_label)
        
        self.title_label = QLabel("")
        self.title_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        
        # Navigation buttons - responsive
        self._create_nav_buttons()
        
        nav_frame = QFrame()
        nav_frame.setObjectName("navBar")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(5)
        
        # Add buttons with size policy
        for btn in [self.btn_sales, self.btn_dashboard, self.btn_sales_summary, 
                    self.btn_expense, self.btn_settings]:
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            nav_layout.addWidget(btn)

        top_layout.addWidget(nav_frame)
        main_layout.addLayout(top_layout)

        # Pages - takes remaining space
        self._create_pages()
        self.pages.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.pages)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        self.status_bar.setSizeGripEnabled(False)

        self.apply_role_permissions()
        self.switch_to_page(5)

    def _create_nav_buttons(self):
        """Create navigation buttons with dynamic sizing"""
        self.btn_sales = QPushButton(tr("sales"))
        self.btn_dashboard = QPushButton(tr("dashboard"))
        self.btn_sales_summary = QPushButton(tr("sales_summary"))
        self.btn_expense = QPushButton(tr("expense"))
        self.btn_settings = QPushButton(tr("settings"))

        all_buttons = [self.btn_sales, self.btn_dashboard, self.btn_sales_summary,
                       self.btn_expense, self.btn_settings]
        
        # Set minimum width and size policy
        for btn in all_buttons:
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setMinimumWidth(70)
            btn.setMaximumWidth(120)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.btn_dashboard.clicked.connect(lambda: self.switch_to_page(0))
        self.btn_sales_summary.clicked.connect(lambda: self.switch_to_page(1))
        self.btn_sales.clicked.connect(lambda: self.switch_to_page(5))
        self.btn_expense.clicked.connect(lambda: self.switch_to_page(7))
        self.btn_settings.clicked.connect(lambda: self.switch_to_page(8))

    def _create_pages(self):
        """Create all page widgets"""
        from ui.dashboard_page import DashboardPage
        from ui.sales_summary import SalesSummaryPage
        from ui.products_page import ProductsPage
        from ui.inventory_page import InventoryPage
        from ui.receipts_page import ReceiptsPage
        from ui.sales_page import SalesPage
        from ui.customers_page import CustomersPage
        from ui.expense import ExpensePage
        from ui.settings import SettingsPage  # <-- IMPORTANT: Change this line
        
        self.pages = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.sales_summary_page = SalesSummaryPage()
        
        # Products Page - pass user_id for permission checks
        self.products_page = ProductsPage(
            user_role=self.current_user["role"], 
            user_id=self.current_user["id"]
        )
        
        # Connect categories changed signal to refresh sales page
        self.products_page.categories_changed.connect(self.refresh_sales_categories)
        
        self.inventory_page = InventoryPage(self.current_user["role"])
        
        # Receipts Page - pass user_id for permission checks
        self.receipts_page = ReceiptsPage(
            user_id=self.current_user["id"],
            user_role=self.current_user["role"]
        )
        
        self.sales_page = SalesPage()
        self.customers_page = CustomersPage(self.current_user["role"])
        self.expense_page = ExpensePage(self.current_user["role"])
        
        # Settings Page - pass user_id for permission checks
        self.settings_page = SettingsPage(
            current_user_role=self.current_user["role"], 
            user_id=self.current_user["id"]
        )

        self.pages.addWidget(self.dashboard_page)      # index 0
        self.pages.addWidget(self.sales_summary_page)  # index 1
        self.pages.addWidget(self.products_page)       # index 2
        self.pages.addWidget(self.inventory_page)      # index 3
        self.pages.addWidget(self.receipts_page)       # index 4
        self.pages.addWidget(self.sales_page)          # index 5
        self.pages.addWidget(self.customers_page)      # index 6
        self.pages.addWidget(self.expense_page)        # index 7
        self.pages.addWidget(self.settings_page)       # index 8
        
        # Debug output
        logger.info(f"Pages created - user_id: {self.current_user['id']}, role: {self.current_user['role']}")
        logger.info(f"Settings page created with user_id: {self.current_user['id']}")

    def refresh_sales_categories(self):
        """Refresh categories in sales page when products page categories change"""
        if hasattr(self, 'sales_page') and hasattr(self.sales_page, 'refresh_categories'):
            self.sales_page.refresh_categories()
            logger.info("Sales page categories refreshed")

    def apply_role_permissions(self):
        user_id = self.current_user["id"]
        allowed_pages = self._get_allowed_pages_for_role(user_id)
        self.btn_expense.setVisible(7 in allowed_pages)
        self.btn_settings.setVisible(8 in allowed_pages)
        
        # Debug output
        logger.info(f"Allowed pages for user {user_id}: {allowed_pages}")

    def _get_allowed_pages_for_role(self, user_id):
        allowed = []
        if PermissionManager.user_can_view_page(user_id, "dashboard"):
            allowed.append(0)
        if PermissionManager.user_can_view_page(user_id, "sales_summary"):
            allowed.append(1)
        if PermissionManager.user_can_view_page(user_id, "products"):
            allowed.append(2)
        if PermissionManager.user_can_view_page(user_id, "inventory"):
            allowed.append(3)
        if PermissionManager.user_can_view_page(user_id, "receipts"):
            allowed.append(4)
        if PermissionManager.user_can_view_page(user_id, "sales"):
            allowed.append(5)
        if PermissionManager.user_can_view_page(user_id, "customers"):
            allowed.append(6)
        if PermissionManager.user_can_view_page(user_id, "expense"):
            allowed.append(7)
        if PermissionManager.user_can_view_page(user_id, "settings"):
            allowed.append(8)
        return allowed

    def switch_to_page(self, index):
        from PyQt6.QtWidgets import QMessageBox
        from utils.translations import tr
        allowed = self._get_allowed_pages_for_role(self.current_user["id"])
        if index not in allowed:
            QMessageBox.warning(self, tr("access_denied"), tr("permission_denied"))
            return
        self.pages.setCurrentIndex(index)
        all_buttons = [self.btn_sales, self.btn_dashboard, self.btn_sales_summary,
                       self.btn_expense, self.btn_settings]
        for btn in all_buttons:
            btn.setChecked(False)
        button_map = {0: self.btn_dashboard, 1: self.btn_sales_summary,
                      5: self.btn_sales, 7: self.btn_expense, 8: self.btn_settings}
        if index in button_map:
            button_map[index].setChecked(True)