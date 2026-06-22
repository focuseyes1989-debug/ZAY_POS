# ui/sales_page/__init__.py
import ctypes

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QMessageBox, QApplication, QComboBox, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtPrintSupport import QPrinterInfo
from loguru import logger

from ui.sales_page.product_grid import ProductGrid
from ui.sales_page.cart_widget import CartWidget, load_cart_from_file, delete_cart_backup
from ui.sales_page.totals_widget import TotalsWidget
from ui.sales_page.payment_widget import PaymentWidget
from ui.sales_page.checkout_handler import CheckoutHandler
from ui.customer_display import CustomerDisplayWindow

from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from utils.language import lang
from utils.customer_utils import load_customers


class SalesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.shop_name = "ZAY POS"
        self.receipt_header_text = ""
        self.receipt_footer_text = ""
        self.show_customer_name = True
        self.customer_display = None  # Customer display window reference

        # Create sub‑widgets
        self.product_grid = ProductGrid(self)
        self.cart_widget = CartWidget(self)
        self.totals_widget = TotalsWidget(self)
        self.payment_widget = PaymentWidget(self)
        self.checkout_handler = CheckoutHandler(self)

        # Connect signals
        self.product_grid.product_selected.connect(self.cart_widget.add_product)
        self.product_grid.service_selected.connect(self.cart_widget.add_service)
        self.product_grid.barcode_scanned.connect(self.cart_widget.add_product_by_barcode)
        self.cart_widget.cart_changed.connect(self.totals_widget.update_totals)
        self.cart_widget.cart_changed.connect(self.payment_widget.update_change)
        self.cart_widget.cart_changed.connect(self.refresh_customer_display)  # Refresh customer display when cart changes
        self.totals_widget.grand_total_changed.connect(self.payment_widget.auto_set_payment)
        self.payment_widget.payment_amount_changed.connect(self.totals_widget.update_change_display)
        self.payment_widget.checkout_requested.connect(self.checkout_handler.checkout)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Customer section with display button
        self.setup_customer_section()
        main_layout.addLayout(self.customer_layout)

        # Two‑column layout: product grid (left) and cart (right)
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(10)
        tables_layout.addWidget(self.product_grid, stretch=3)
        tables_layout.addWidget(self.cart_widget, stretch=2)
        main_layout.addLayout(tables_layout, stretch=10)

        # Bottom row: discount, loyalty, totals, payment, action
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)
        bottom_layout.setContentsMargins(0, 2, 0, 2)
        
        self._make_group_compact(self.totals_widget.discount_group, hide_title=True)
        self._make_group_compact(self.totals_widget.loyalty_group, hide_title=True)
        self._make_group_compact(self.totals_widget.totals_group, hide_title=True)
        self._make_group_compact(self.payment_widget, hide_title=True)
        self._make_group_compact(self.checkout_handler.action_group, hide_title=True)
        
        bottom_layout.addWidget(self.totals_widget.discount_group, 1)
        bottom_layout.addWidget(self.totals_widget.loyalty_group, 1)
        bottom_layout.addWidget(self.totals_widget.totals_group, 1)
        bottom_layout.addWidget(self.payment_widget, 1)
        bottom_layout.addWidget(self.checkout_handler.action_group, 1)
        main_layout.addLayout(bottom_layout, stretch=1)

        self.setLayout(main_layout)

        # Restore cart from backup
        restored_cart = load_cart_from_file()
        if restored_cart:
            conn = connect_db()
            cursor = conn.cursor()
            valid_items = []
            for item in restored_cart:
                cursor.execute("SELECT name, price, stock, sold_by FROM products WHERE id=?", (item['id'],))
                row = cursor.fetchone()
                if row:
                    db_name, db_price, db_stock, sold_by = row
                    item['name'] = db_name
                    item['price'] = db_price
                    if not item.get('is_service', False) and db_stock < item['qty']:
                        item['qty'] = db_stock
                    valid_items.append(item)
            conn.close()
            if valid_items:
                self.cart_widget.cart = valid_items
                self.cart_widget.refresh_table()
                logger.info(f"Restored cart with {len(valid_items)} items from backup")
            else:
                delete_cart_backup()

        # Load data
        self.load_settings()
        self.load_customers()
        self.load_receipt_settings()
        self.load_payment_types()
        self.product_grid.load_products()

        # Shortcuts
        self.focus_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.focus_shortcut.activated.connect(self.product_grid.focus_search)
        
        self.display_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.display_shortcut.activated.connect(self.toggle_customer_display)

        self.cash_drawer_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        self.cash_drawer_shortcut.activated.connect(self.open_cash_drawer)

        lang.language_changed.connect(self.retranslateUi)
        self.retranslateUi()

    def _make_group_compact(self, group, hide_title=False):
        """Make a group box compact with reduced padding and spacing"""
        if isinstance(group, QGroupBox):
            if hide_title:
                group.setStyleSheet("""
                    QGroupBox {
                        font-weight: bold;
                        padding-top: 0px;
                        margin-top: 0px;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: -9999px;
                        padding: 0px;
                    }
                """)
            else:
                group.setStyleSheet("""
                    QGroupBox {
                        font-weight: bold;
                        padding-top: 3px;
                        margin-top: 2px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 5px;
                        padding: 0 3px 0 3px;
                    }
                """)
            if group.layout():
                group.layout().setSpacing(2)
                group.layout().setContentsMargins(5, 3, 5, 3)

    def refresh_categories(self):
        """Refresh categories in product grid"""
        if hasattr(self, 'product_grid'):
            self.product_grid.load_categories()
            logger.info("Sales page product grid categories refreshed")

    def setup_customer_section(self):
        """Setup customer section with combo box and display button"""
        self.customer_layout = QHBoxLayout()
        self.customer_layout.setSpacing(5)
        
        # Customer label
        self.customer_label = QLabel("Customer:")
        self.customer_layout.addWidget(self.customer_label)
        
        # Customer combo box
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Walk-in Customer (no loyalty)", None)
        self.customer_combo.currentIndexChanged.connect(self.on_customer_changed)
        self.customer_combo.setMinimumWidth(200)
        self.customer_layout.addWidget(self.customer_combo)
        
        # Customer Display button (small, compact)
        self.btn_customer_display = QPushButton("🖥️")
        self.btn_customer_display.setFixedSize(32, 32)
        self.btn_customer_display.setToolTip("Show/Hide Customer Display (Ctrl+D)")
        self.btn_customer_display.setStyleSheet("""
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7d6ff0;
            }
            QPushButton:checked {
                background-color: #e94560;
            }
        """)
        self.btn_customer_display.setCheckable(True)
        self.btn_customer_display.clicked.connect(self.toggle_customer_display)
        self.customer_layout.addWidget(self.btn_customer_display)

        # Cash drawer button (sends drawer kick command to default receipt printer)
        self.btn_cash_drawer = QPushButton("💵")
        self.btn_cash_drawer.setFixedSize(32, 32)
        self.btn_cash_drawer.setToolTip("Open Cash Drawer (Ctrl+Shift+D)")
        self.btn_cash_drawer.setStyleSheet("""
            QPushButton {
                background-color: #00a86b;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #12b87a;
            }
            QPushButton:pressed {
                background-color: #087f56;
            }
        """)
        self.btn_cash_drawer.clicked.connect(self.open_cash_drawer)
        self.customer_layout.addWidget(self.btn_cash_drawer)
        
        # Add stretch to push everything to the left
        self.customer_layout.addStretch()

    def load_settings(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='tax_enabled'")
            res = cursor.fetchone()
            self.tax_enabled = res[0] == '1' if res else False
            cursor.execute("SELECT value FROM settings WHERE key='tax_rate'")
            res = cursor.fetchone()
            self.tax_rate = float(res[0]) if res else 0.0
            cursor.execute("SELECT value FROM settings WHERE key='discount_enabled'")
            res = cursor.fetchone()
            self.discount_enabled = res[0] == '1' if res else False
            cursor.execute("SELECT value FROM settings WHERE key='discount_type'")
            res = cursor.fetchone()
            self.discount_type = res[0] if res else "percentage"
            cursor.execute("SELECT value FROM settings WHERE key='discount_value'")
            res = cursor.fetchone()
            self.discount_default_value = float(res[0]) if res else 0.0
            conn.close()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
        self.totals_widget.load_discount_settings(self.discount_enabled, self.discount_type, self.discount_default_value)

    def load_loyalty_settings(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='loyalty_points_per_dollar'")
            row = cursor.fetchone()
            points_per_dollar = float(row[0]) if row else 0.0
            cursor.execute("SELECT value FROM settings WHERE key='points_expiry_months'")
            row = cursor.fetchone()
            expiry_months = int(row[0]) if row else 12
            cursor.execute("SELECT value FROM settings WHERE key='points_dollar_value'")
            row = cursor.fetchone()
            point_value = float(row[0]) if row else 0.01
            conn.close()
            self.totals_widget.set_loyalty_params(points_per_dollar, expiry_months, point_value)
        except Exception as e:
            logger.error(f"Failed to load loyalty settings: {e}")

    def load_customers(self):
        self.customer_combo.blockSignals(True)
        self.customer_combo.clear()
        self.customer_combo.addItem("Walk-in Customer (no loyalty)", None)
        customers = load_customers()
        for cust_id, name, points in customers:
            self.customer_combo.addItem(f"{name} (Points: {points})", cust_id)
        self.customer_combo.blockSignals(False)

    def load_payment_types(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM payment_types ORDER BY name")
            rows = cursor.fetchall()
            conn.close()
            types = [row[0] for row in rows] if rows else ["Cash", "Card", "Mobile Money"]
            self.payment_widget.load_payment_types(types)
        except Exception as e:
            logger.error(f"Failed to load payment types: {e}")
            self.payment_widget.load_payment_types(["Cash", "Card", "Mobile Money"])

    def on_customer_changed(self):
        data = self.customer_combo.currentData()
        self.checkout_handler.selected_customer_id = data if data is not None else None
        self.checkout_handler.load_customer_points()
        # Check if customer has credit balance
        self.checkout_handler.load_customer_credit_balance()
        self.totals_widget.update_totals()

    def load_receipt_settings(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='shop_name'")
            row = cursor.fetchone()
            self.shop_name = row[0] if row else "ZAY POS"
            cursor.execute("SELECT value FROM settings WHERE key='receipt_header'")
            row = cursor.fetchone()
            self.receipt_header_text = row[0] if row else ""
            cursor.execute("SELECT value FROM settings WHERE key='receipt_footer'")
            row = cursor.fetchone()
            self.receipt_footer_text = row[0] if row else ""
            cursor.execute("SELECT value FROM settings WHERE key='show_customer_name'")
            row = cursor.fetchone()
            self.show_customer_name = (row[0] == '1') if row else True
            conn.close()
        except Exception as e:
            logger.error(f"Failed to load receipt settings: {e}")

    def load_cart(self):
        if hasattr(self, 'cart_widget'):
            self.cart_widget.refresh_table()

    def update_totals(self):
        if hasattr(self, 'totals_widget'):
            self.totals_widget.update_totals()

    def show_customer_display(self):
        """Show the customer display window"""
        if self.customer_display is None:
            self.customer_display = CustomerDisplayWindow(self)
            self.customer_display.show()
            self.btn_customer_display.setChecked(True)
            self.btn_customer_display.setToolTip("Hide Customer Display (Ctrl+D)")
            logger.info("Customer display opened")
        else:
            self.close_customer_display()

    def close_customer_display(self):
        """Close the customer display window"""
        if self.customer_display:
            self.customer_display.close()
            self.customer_display = None
            self.btn_customer_display.setChecked(False)
            self.btn_customer_display.setToolTip("Show Customer Display (Ctrl+D)")
            logger.info("Customer display closed")

    def toggle_customer_display(self):
        """Toggle customer display on/off"""
        if self.customer_display:
            self.close_customer_display()
        else:
            self.show_customer_display()

    def open_cash_drawer(self):
        """Open the cash drawer through the default receipt printer."""
        default_printer = QPrinterInfo.defaultPrinter()
        if default_printer.isNull():
            QMessageBox.warning(self, "Cash Drawer", "No default printer found.")
            logger.warning("Cash drawer open failed: no default printer found")
            return

        printer_name = default_printer.printerName()
        try:
            self._send_cash_drawer_pulse(printer_name)
            logger.info(f"Cash drawer open command sent to printer: {printer_name}")
        except Exception as e:
            logger.error(f"Cash drawer open failed: {e}")
            QMessageBox.warning(
                self,
                "Cash Drawer",
                "Could not open cash drawer. Check the receipt printer connection and default printer setting.",
            )

    def _send_cash_drawer_pulse(self, printer_name):
        """Send ESC/POS drawer kick command to a Windows printer queue."""
        drawer_kick_command = b"\x1b\x70\x00\x19\xfa"
        winspool = ctypes.WinDLL("winspool.drv", use_last_error=True)

        class DOC_INFO_1(ctypes.Structure):
            _fields_ = [
                ("pDocName", ctypes.c_wchar_p),
                ("pOutputFile", ctypes.c_wchar_p),
                ("pDatatype", ctypes.c_wchar_p),
            ]

        h_printer = ctypes.c_void_p()
        if not winspool.OpenPrinterW(ctypes.c_wchar_p(printer_name), ctypes.byref(h_printer), None):
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            doc_info = DOC_INFO_1("Open Cash Drawer", None, "RAW")
            if not winspool.StartDocPrinterW(h_printer, 1, ctypes.byref(doc_info)):
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                if not winspool.StartPagePrinter(h_printer):
                    raise ctypes.WinError(ctypes.get_last_error())
                try:
                    written = ctypes.c_ulong(0)
                    buffer = ctypes.create_string_buffer(drawer_kick_command)
                    if not winspool.WritePrinter(
                        h_printer,
                        buffer,
                        len(drawer_kick_command),
                        ctypes.byref(written),
                    ):
                        raise ctypes.WinError(ctypes.get_last_error())
                finally:
                    winspool.EndPagePrinter(h_printer)
            finally:
                winspool.EndDocPrinter(h_printer)
        finally:
            winspool.ClosePrinter(h_printer)

    def refresh_customer_display(self):
        """Refresh customer display when cart changes"""
        if self.customer_display:
            self.customer_display.refresh_display()

    def customer_display_closed(self):
        """Called when customer display is closed"""
        self.customer_display = None
        self.btn_customer_display.setChecked(False)
        self.btn_customer_display.setToolTip("Show Customer Display (Ctrl+D)")
        logger.info("Customer display closed by user")

    def retranslateUi(self):
        lang_code = lang.get_current()
        if lang_code == "my":
            self.customer_label.setText("ဝယ်ယူသူ:")
            self.btn_customer_display.setToolTip("ဝယ်ယူသူမျက်နှာပြင် ပြရန်/ဖျောက်ရန် (Ctrl+D)")
            self.btn_cash_drawer.setToolTip("ငွေသေတ္တာ ဖွင့်ရန် (Ctrl+Shift+D)")
        else:
            self.customer_label.setText("Customer:")
            self.btn_customer_display.setToolTip("Show/Hide Customer Display (Ctrl+D)")
            self.btn_cash_drawer.setToolTip("Open Cash Drawer (Ctrl+Shift+D)")
        self.product_grid.retranslateUi()
        self.cart_widget.retranslateUi()
        self.totals_widget.retranslateUi()
        self.payment_widget.retranslateUi()
        self.checkout_handler.retranslateUi()

    def showEvent(self, event):
        self.product_grid.load_products()
        self.load_customers()
        self.load_payment_types()
        self.product_grid.focus_search()
        super().showEvent(event)

    def clear_cart(self):
        if self.parent.cart_widget.cart:
            reply = QMessageBox.question(self.parent, "Clear Cart", "Remove all items?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.parent.cart_widget.clear()
                self.parent.totals_widget.discount_checkbox.setChecked(False)
                self.parent.totals_widget.points_use_check.setChecked(False)
                self.parent.payment_widget.payment_input.setValue(0.0)
                self.parent.payment_widget.reset_manual_override()
                
                # Reset payment widget to default (Cash, 0 amount)
                self.parent.payment_widget.reset_to_default()
                
                self.cash_radio.setChecked(True)
                self.parent.payment_widget.setEnabled(True)
                self.parent.product_grid.focus_search()
                # Reset customer selection to Walk-in
                self.parent.customer_combo.setCurrentIndex(0)
                self.selected_customer_id = None