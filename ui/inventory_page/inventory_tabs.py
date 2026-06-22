# ui/inventory_page/inventory_tabs.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from models.database import connect_db
from utils.translations import tr
from utils.currency import get_currency_symbol, format_money
from utils.excel_exporter import ExcelExporter
from datetime import datetime

from ui.inventory_page.current_stock_tab import CurrentStockTab
from ui.inventory_page.low_stock_tab import LowStockTab
from ui.inventory_page.suppliers_tab import SuppliersTab
from ui.inventory_page.purchase_history_tab import PurchaseHistoryTab
from ui.inventory_page.expiry_tab import ExpiryTab
from ui.inventory_page.logs_tab import LogsTab
from ui.inventory_page.warehouse_dialog import WarehouseDialog
from ui.inventory_page.stock_by_location_tab import StockByLocationTab  # Add this import


class InventoryPage(QWidget):
    def __init__(self, user_role=None, parent=None):
        super().__init__(parent)
        self.user_role = user_role
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Export and Location button row
        btn_layout = QHBoxLayout()
        
        self.btn_export_excel = QPushButton("📊 Export Excel")
        self.btn_export_excel.clicked.connect(self.export_to_excel)
        
        self.btn_manage_locations = QPushButton("📍 Manage Locations")
        self.btn_manage_locations.clicked.connect(self.open_warehouse_dialog)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_export_excel)
        btn_layout.addWidget(self.btn_manage_locations)
        layout.addLayout(btn_layout)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.current_stock_tab = CurrentStockTab(self)
        self.low_stock_tab = LowStockTab(self)
        self.suppliers_tab = SuppliersTab(self)
        self.purchase_history_tab = PurchaseHistoryTab(self)
        self.expiry_tab = ExpiryTab(self)
        self.logs_tab = LogsTab(self)
        self.stock_by_location_tab = StockByLocationTab(self)  # Add new tab

        self.tabs.addTab(self.current_stock_tab, "")
        self.tabs.addTab(self.low_stock_tab, "")
        self.tabs.addTab(self.suppliers_tab, "")
        self.tabs.addTab(self.purchase_history_tab, "")
        self.tabs.addTab(self.expiry_tab, "")
        self.tabs.addTab(self.logs_tab, "")
        self.tabs.addTab(self.stock_by_location_tab, "")  # Add new tab

        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.retranslateUi()

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

    def get_current_theme(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='theme'")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "Light"
        except:
            return "Light"

    def open_warehouse_dialog(self):
        """Open warehouse/location management dialog"""
        dialog = WarehouseDialog(self)
        dialog.warehouses_changed.connect(self.refresh_all)
        dialog.exec()

    def on_tab_changed(self, index):
        if index == 0:
            self.current_stock_tab.refresh()
        elif index == 1:
            self.low_stock_tab.refresh()
        elif index == 2:
            self.suppliers_tab.refresh()
        elif index == 3:
            self.purchase_history_tab.refresh()
        elif index == 4:
            self.expiry_tab.refresh()
        elif index == 5:
            self.logs_tab.refresh()
        elif index == 6:
            self.stock_by_location_tab.refresh()

    def retranslateUi(self):
        lang = self.get_lang()
        
        tab_titles = [
            (tr("current_stock"), "လက်ရှိစတော့"),
            (tr("low_stock_alert_tab"), "စတော့နည်းနေသောသတိပေးချက်"),
            (tr("supplier"), "ပေးသွင်းသူ"),
            (tr("purchase_history"), "ဝယ်ယူမှုမှတ်တမ်း"),
            (tr("expiry_date"), "သက်တမ်းကုန်ရက်"),
            (tr("inventory_logs"), "စတော့မှတ်တမ်းများ"),
            ("Stock by Location", "နေရာအလိုက်စတော့")
        ]
        for i, (en, my) in enumerate(tab_titles):
            self.tabs.setTabText(i, my if lang == "my" else en)
        
        if lang == "my":
            self.btn_export_excel.setText("📊 Excel ထုတ်မည်")
            self.btn_manage_locations.setText("📍 နေရာများ စီမံရန်")
        else:
            self.btn_export_excel.setText("📊 Export Excel")
            self.btn_manage_locations.setText("📍 Manage Locations")
        
        # Update current stock tab (including status filter)
        self.current_stock_tab.retranslateUi()
        
        self.refresh_all()

    def refresh_all(self):
        self.current_stock_tab.refresh()
        self.low_stock_tab.refresh()
        self.suppliers_tab.refresh()
        self.purchase_history_tab.refresh()
        self.expiry_tab.refresh()
        self.logs_tab.refresh()
        self.stock_by_location_tab.refresh()
        main_window = self.window()
        if hasattr(main_window, 'check_stock_alerts'):
            main_window.check_stock_alerts()

    def export_to_excel(self):
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:
            self.current_stock_tab.export_to_excel()
        elif current_tab == 1:
            self.low_stock_tab.export_to_excel()
        elif current_tab == 2:
            self.suppliers_tab.export_to_excel()
        elif current_tab == 3:
            self.purchase_history_tab.export_to_excel()
        elif current_tab == 4:
            self.expiry_tab.export_to_excel()
        elif current_tab == 5:
            self.logs_tab.export_to_excel()
        elif current_tab == 6:
            self.stock_by_location_tab.export_to_excel()