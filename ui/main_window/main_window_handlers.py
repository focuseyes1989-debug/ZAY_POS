# ui/main_window/main_window_handlers.py
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox
from ui.stock_notification_dialog import StockNotificationDialog
from utils.translations import tr
from loguru import logger


class MainWindowHandlers:
    """Handle event handlers for MainWindow"""
    
    def setup_refresh_shortcut(self):
        from PyQt6.QtGui import QShortcut, QKeySequence
        self.refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        self.refresh_shortcut.activated.connect(self.refresh_all_pages)
        self.refresh_shortcut2 = QShortcut(QKeySequence("Ctrl+R"), self)
        self.refresh_shortcut2.activated.connect(self.refresh_all_pages)

    def refresh_all_pages(self):
        logger.info("Manual refresh triggered")
        
        # Dashboard
        if hasattr(self, 'dashboard_page'):
            if hasattr(self.dashboard_page, 'refresh_dashboard'):
                self.dashboard_page.refresh_dashboard()
        
        # Sales Summary
        if hasattr(self, 'sales_summary_page') and hasattr(self.sales_summary_page, 'load_all_tabs'):
            self.sales_summary_page.load_all_tabs()
        
        # Products
        if hasattr(self, 'products_page'):
            if hasattr(self.products_page, 'load_products'):
                self.products_page.load_products()
            if hasattr(self.products_page, 'update_cards'):
                self.products_page.update_cards()
        
        # Inventory
        if hasattr(self, 'inventory_page') and hasattr(self.inventory_page, 'refresh_all'):
            self.inventory_page.refresh_all()
        
        # Receipts
        if hasattr(self, 'receipts_page') and hasattr(self.receipts_page, 'load_sales'):
            self.receipts_page.load_sales()
        
        # Sales
        if hasattr(self, 'sales_page'):
            if hasattr(self.sales_page, 'product_grid') and hasattr(self.sales_page.product_grid, 'load_products'):
                self.sales_page.product_grid.load_products()
            if hasattr(self.sales_page, 'load_customers'):
                self.sales_page.load_customers()
            if hasattr(self.sales_page, 'load_payment_types'):
                self.sales_page.load_payment_types()
        
        # Customers
        if hasattr(self, 'customers_page') and hasattr(self.customers_page, 'load_customers'):
            self.customers_page.load_customers()
        
        # Expense
        if hasattr(self, 'expense_page'):
            if hasattr(self.expense_page, 'load_expenses'):
                self.expense_page.load_expenses()
            if hasattr(self.expense_page, 'update_card_totals'):
                self.expense_page.update_card_totals()
        
        lang_code = self.current_language
        msg = "စာမျက်နှာအားလုံး ပြန်လည်စတင်ပြီးပါပြီ" if lang_code == "my" else "All pages refreshed"
        self.status_bar.showMessage(msg, 3000)
        
        # Check stock alerts after refresh
        self.check_stock_alerts()

    def check_stock_alerts(self):
        from models.database import connect_db
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM products 
            WHERE (sold_by IS NULL OR sold_by != 'Service') 
              AND stock > 0 AND stock <= low_stock
        """)
        low_count = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM products 
            WHERE (sold_by IS NULL OR sold_by != 'Service') 
              AND stock = 0
        """)
        out_count = cursor.fetchone()[0]
        conn.close()

        self.has_alerts = (low_count + out_count) > 0

        if self.has_alerts:
            self.notification_icon.show()
            if not self.blink_timer.isActive():
                self.blink_timer.start(500)
            
            lang_code = self.current_language
            if lang_code == "my":
                parts = []
                if low_count > 0:
                    parts.append(f"စတော့နည်းနေသောပစ္စည်း {low_count} မျိုး")
                if out_count > 0:
                    parts.append(f"ကုန်သွားသောပစ္စည်း {out_count} မျိုး")
                msg = "⚠️ " + "၊ ".join(parts) + " ရှိပါသည်။"
                popup_title = "စတော့သတိပေးချက်"
            else:
                parts = []
                if low_count > 0:
                    parts.append(f"{low_count} low stock product(s)")
                if out_count > 0:
                    parts.append(f"{out_count} out of stock product(s)")
                msg = "⚠️ " + ", ".join(parts) + "."
                popup_title = "Stock Alert"

            self.status_bar.showMessage(msg, 10000)

            if not hasattr(self, '_alert_shown') or not self._alert_shown:
                self._alert_shown = True
                QMessageBox.warning(self, popup_title, msg)
        else:
            self.blink_timer.stop()
            self.notification_icon.hide()
            self.status_bar.showMessage(tr("ok_stock"), 5000)
            self._alert_shown = False

    def toggle_notification_icon(self):
        if not self.has_alerts:
            return
        if self.notification_icon.isVisible():
            self.notification_icon.hide()
        else:
            self.notification_icon.show()

    def show_notification_dialog(self, event):
        if self.has_alerts:
            dialog = StockNotificationDialog(self)
            dialog.exec()
        else:
            QMessageBox.information(self, tr("info"), tr("ok_stock"))

    def show_expense_alert(self, alert_data):
        lang_code = self.current_language
        title = "ဘတ်ဂျက်သတိပေးချက်" if lang_code == "my" else "Budget Alert"
        QMessageBox.warning(self, title, alert_data['message'])

    def on_language_changed(self, lang_code):
        logger.info(f"Language changed to: {lang_code}")
        self.current_language = lang_code
        self.apply_language()
        for page in [self.dashboard_page, self.sales_summary_page, self.products_page,
                     self.inventory_page, self.receipts_page, self.sales_page,
                     self.customers_page, self.expense_page, self.settings_page]:
            if page and hasattr(page, 'retranslateUi'):
                try:
                    page.retranslateUi()
                except Exception as e:
                    logger.error(f"Error in retranslateUi for {page}: {e}")
        self.check_stock_alerts()