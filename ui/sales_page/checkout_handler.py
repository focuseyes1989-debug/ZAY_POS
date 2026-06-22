# ui/sales_page/checkout_handler.py
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QPushButton, QMessageBox, QRadioButton, QHBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal, QObject
from datetime import datetime, timedelta
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from ui.receipt_dialog import ReceiptDialog
from ui.sales_page.cart_widget import delete_cart_backup
from loguru import logger
from utils.customer_utils import load_customers
from utils.language import lang


def load_customers():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, points FROM customers ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return rows


class CheckoutHandler(QObject):
    checkout_completed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.selected_customer_id = None
        self.points_available = 0
        self.credit_balance = 0
        self.credit_limit = 0
        self.tax_rate = 0.0
        self.tax_enabled = False
        self.points_per_dollar = 0.0
        self.points_expiry_months = 12
        self.credit_payment_type = "Credit"

        # Action group
        self.action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout()
        
        # Payment type selection for credit sales
        payment_type_layout = QHBoxLayout()
        self.cash_radio = QRadioButton("Cash")
        self.credit_radio = QRadioButton("Credit")
        self.cash_radio.setChecked(True)
        self.cash_radio.toggled.connect(self.on_payment_type_changed)
        self.credit_radio.toggled.connect(self.on_payment_type_changed)
        payment_type_layout.addWidget(self.cash_radio)
        payment_type_layout.addWidget(self.credit_radio)
        payment_type_layout.addStretch()
        action_layout.addLayout(payment_type_layout)
        
        self.btn_clear_cart = QPushButton("Clear Cart")
        self.btn_clear_cart.setFixedHeight(35)
        self.btn_clear_cart.clicked.connect(self.clear_cart)
        action_layout.addWidget(self.btn_clear_cart)
        
        self.btn_checkout = QPushButton("Checkout")
        self.btn_checkout.setFixedHeight(40)
        self.btn_checkout.clicked.connect(self.checkout)
        action_layout.addWidget(self.btn_checkout)
        action_layout.addStretch()
        self.action_group.setLayout(action_layout)

    def on_payment_type_changed(self):
        if self.credit_radio.isChecked():
            self.parent.payment_widget.setEnabled(False)
            self.parent.payment_widget.payment_input.setValue(0)
            self.show_credit_info()
        else:
            self.parent.payment_widget.setEnabled(True)
            grand_total = self.parent.totals_widget.get_current_grand_total()
            self.parent.payment_widget.auto_set_payment(grand_total)

    def show_credit_info(self):
        if self.selected_customer_id and self.credit_balance > 0:
            symbol = get_currency_symbol()
            lang_code = lang.get_current()
            if lang_code == "my":
                msg = f"ဤဝယ်ယူသူအတွက် လက်ကျန်အကြွေး: {format_money(self.credit_balance, symbol)}"
            else:
                msg = f"Current credit balance for this customer: {format_money(self.credit_balance, symbol)}"
            
            if self.credit_limit > 0:
                if lang_code == "my":
                    msg += f"\nခရက်ဒစ်ကန့်သတ်ချက်: {format_money(self.credit_limit, symbol)}"
                else:
                    msg += f"\nCredit limit: {format_money(self.credit_limit, symbol)}"
            
            QMessageBox.information(self.parent, "Credit Info", msg)

    def load_customer_points(self):
        if self.selected_customer_id:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM customers WHERE id = ?", (self.selected_customer_id,))
            row = cursor.fetchone()
            self.points_available = row[0] if row else 0
            conn.close()
        else:
            self.points_available = 0
        self.parent.totals_widget.set_customer_points(self.points_available)

    def load_customer_credit_balance(self):
        if self.selected_customer_id:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT current_balance, credit_limit FROM customers WHERE id = ?", (self.selected_customer_id,))
            row = cursor.fetchone()
            if row:
                self.credit_balance = row[0] if row[0] else 0
                self.credit_limit = row[1] if row[1] else 0
            else:
                self.credit_balance = 0
                self.credit_limit = 0
            conn.close()
        else:
            self.credit_balance = 0
            self.credit_limit = 0

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
                self.cash_radio.setChecked(True)
                self.parent.payment_widget.setEnabled(True)
                self.parent.product_grid.focus_search()
                # Reset customer selection to Walk-in
                self.parent.customer_combo.setCurrentIndex(0)
                self.selected_customer_id = None

    def check_credit_limit(self, amount):
        if not self.selected_customer_id:
            return True
        
        self.load_customer_credit_balance()
        
        if self.credit_limit > 0:
            new_balance = self.credit_balance + amount
            
            if new_balance > self.credit_limit:
                symbol = get_currency_symbol()
                lang_code = lang.get_current()
                if lang_code == "my":
                    msg = (f"ခရက်ဒစ်ကန့်သတ်ချက် ကျော်လွန်နေသည်!\n\n"
                           f"ကန့်သတ်ချက်: {format_money(self.credit_limit, symbol)}\n"
                           f"လက်ရှိကျန်: {format_money(self.credit_balance, symbol)}\n"
                           f"ဤရောင်းချမှု: {format_money(amount, symbol)}\n"
                           f"အသစ်ကျန်: {format_money(new_balance, symbol)}\n\n"
                           f"ဆက်လုပ်မည်လား?")
                else:
                    msg = (f"Credit limit exceeded!\n\n"
                           f"Limit: {format_money(self.credit_limit, symbol)}\n"
                           f"Current: {format_money(self.credit_balance, symbol)}\n"
                           f"This sale: {format_money(amount, symbol)}\n"
                           f"New balance: {format_money(new_balance, symbol)}\n\n"
                           f"Proceed anyway?")
                
                reply = QMessageBox.warning(self.parent, "Credit Limit Warning", msg,
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                return reply == QMessageBox.StandardButton.Yes
        return True

    def checkout(self):
        cart = self.parent.cart_widget.get_cart()
        if not cart:
            QMessageBox.warning(self.parent, "Empty Cart", "Cart is empty")
            return

        symbol = get_currency_symbol()
        grand_total = self.parent.totals_widget.get_current_grand_total()
        
        # Check if credit sale
        is_credit_sale = self.credit_radio.isChecked() and self.selected_customer_id
        
        if is_credit_sale:
            if not self.check_credit_limit(grand_total):
                return
            payment = 0
            change = 0
            payment_type = "Credit"
        else:
            payment = self.parent.payment_widget.get_payment_amount()
            if payment < grand_total:
                QMessageBox.warning(self.parent, "Insufficient Payment", f"Payment ({format_money(payment, symbol)}) < Total ({format_money(grand_total, symbol)})")
                return
            change = payment - grand_total
            payment_type = self.parent.payment_widget.get_selected_payment_type()

        invoice_no = datetime.now().strftime("INV%Y%m%d%H%M%S")
        local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        subtotal = self.parent.cart_widget.compute_subtotal()
        reg_discount = self.parent.totals_widget.compute_regular_discount(subtotal)
        points_discount = self.parent.totals_widget.compute_points_discount(subtotal)
        total_discount = reg_discount + points_discount

        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")

            # Check stock and get location info
            for item in cart:
                if not item.get("is_service", False):
                    # Check total stock
                    cursor.execute("SELECT stock FROM products WHERE id = ?", (item["id"],))
                    row = cursor.fetchone()
                    if not row or row[0] < item["qty"]:
                        QMessageBox.warning(self.parent, "Stock Error", f"Insufficient stock for {item['name']}.")
                        conn.rollback()
                        return

            # Insert sale
            cursor.execute("""
                INSERT INTO sales (invoice_no, total, payment, change_amount, customer_id, status, payment_type, created_at, discount_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (invoice_no, grand_total, payment, change, self.selected_customer_id, 'completed', payment_type, local_now, total_discount))
            sale_id = cursor.lastrowid

            # Insert items, update stock, and update product_locations
            for item in cart:
                total = item["price"] * item["qty"]
                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_name, qty, price, total)
                    VALUES (?, ?, ?, ?, ?)
                """, (sale_id, item["name"], item["qty"], item["price"], total))
                
                if not item.get("is_service", False):
                    # Update total product stock
                    cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (item["qty"], item["id"]))
                    
                    # Update product_locations - use the location stored in cart
                    location = item.get("location")
                    if location:
                        cursor.execute("""
                            UPDATE product_locations 
                            SET quantity = quantity - ?
                            WHERE product_id = ? AND location = ?
                        """, (item["qty"], item["id"], location))
                        
                        # Check if location quantity becomes 0, delete it
                        cursor.execute("SELECT quantity FROM product_locations WHERE product_id = ? AND location = ?", 
                                     (item["id"], location))
                        remaining = cursor.fetchone()
                        if remaining and remaining[0] <= 0:
                            cursor.execute("DELETE FROM product_locations WHERE product_id = ? AND location = ?", 
                                         (item["id"], location))
                    
                    # Record stock movement with location
                    cursor.execute("""
                        INSERT INTO stock_movements 
                        (product_id, type, quantity, old_stock, new_stock, reason, reference, created_by, location)
                        VALUES (?, 'sale', ?, ?, ?, 'Sale', ?, ?, ?)
                    """, (item["id"], item["qty"], 0, 0, invoice_no, "", location))

            # Handle credit sale
            if is_credit_sale:
                due_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
                cursor.execute("""
                    INSERT INTO credit_sales (invoice_no, customer_id, total_amount, paid_amount, balance_amount, sale_date, due_date, status, sale_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (invoice_no, self.selected_customer_id, grand_total, 0, grand_total, local_now[:10], due_date, 'pending', sale_id))
                
                cursor.execute("""
                    UPDATE customers SET current_balance = current_balance + ?
                    WHERE id = ?
                """, (grand_total, self.selected_customer_id))
                
                lang_code = lang.get_current()
                if lang_code == "my":
                    QMessageBox.information(self.parent, "အောင်မြင်ပါသည်", 
                                           f"အကြွေးရောင်းချမှု အောင်မြင်ပါသည်။\n"
                                           f"ပြေစာအမှတ်: {invoice_no}\n"
                                           f"ကျန်ရှိငွေ: {format_money(grand_total, symbol)}\n"
                                           f"ပေးရမည့်ရက်: {due_date}")
                else:
                    QMessageBox.information(self.parent, "Success", 
                                           f"Credit sale completed successfully.\n"
                                           f"Invoice: {invoice_no}\n"
                                           f"Balance due: {format_money(grand_total, symbol)}\n"
                                           f"Due date: {due_date}")
            else:
                # Loyalty points for cash sales only
                if self.selected_customer_id:
                    earned = int(grand_total * self.parent.totals_widget.points_per_dollar)
                    if earned > 0:
                        expiry_date = (datetime.now() + timedelta(days=self.parent.totals_widget.points_expiry_months * 30)).strftime("%Y-%m-%d")
                        cursor.execute("""
                            INSERT INTO customer_points_log (customer_id, points, type, reference, expiry_date)
                            VALUES (?, ?, 'earn', ?, ?)
                        """, (self.selected_customer_id, earned, invoice_no, expiry_date))
                        cursor.execute("UPDATE customers SET points = points + ? WHERE id = ?", (earned, self.selected_customer_id))
                    if self.parent.totals_widget.points_use_check.isChecked():
                        points_used = self.parent.totals_widget.points_spin.value()
                        if points_used > 0:
                            cursor.execute("UPDATE customers SET points = points - ? WHERE id = ?", (points_used, self.selected_customer_id))
                            cursor.execute("""
                                INSERT INTO customer_points_log (customer_id, points, type, reference)
                                VALUES (?, ?, 'redeem', ?)
                            """, (self.selected_customer_id, points_used, invoice_no))
                    cursor.execute("""
                        UPDATE customers
                        SET total_visit = total_visit + 1,
                            total_spent = total_spent + ?
                        WHERE id = ?
                    """, (grand_total, self.selected_customer_id))

            conn.commit()
            logger.info(f"Sale completed. Invoice: {invoice_no}")

            # Delete cart backup
            delete_cart_backup()

            # Show receipt dialog for cash sales
            if not is_credit_sale:
                receipt_dialog = ReceiptDialog(sale_id, self.parent)
                receipt_dialog.exec()

            # Reset customer selection to Walk-in
            self.parent.customer_combo.setCurrentIndex(0)
            self.selected_customer_id = None
            self.points_available = 0
            self.credit_balance = 0

            # Refresh UI and data
            self.parent.product_grid.load_products()
            self.parent.load_customers()
            main_window = self.parent.window()
            if hasattr(main_window, 'inventory_page'):
                main_window.inventory_page.refresh_all()
            if hasattr(main_window, 'check_stock_alerts'):
                main_window.check_stock_alerts()
            if hasattr(main_window, 'customers_page'):
                main_window.customers_page.load_customers()

        except Exception as e:
            conn.rollback()
            logger.error(f"Checkout failed: {e}", exc_info=True)
            QMessageBox.critical(self.parent, "Error", f"Checkout failed: {e}")
        finally:
            conn.close()

        # Clear cart and reset UI
        self.parent.cart_widget.clear()
        self.parent.totals_widget.discount_checkbox.setChecked(False)
        self.parent.totals_widget.points_use_check.setChecked(False)
        self.parent.payment_widget.reset_manual_override()
        
        # Reset payment widget to default (Cash, 0 amount)
        self.parent.payment_widget.reset_to_default()
        
        # Reset payment type radio buttons
        self.cash_radio.setChecked(True)
        self.parent.payment_widget.setEnabled(True)
        self.parent.product_grid.focus_search()

    def retranslateUi(self):
        from utils.language import lang
        if lang.get_current() == "my":
            self.action_group.setTitle("လုပ်ဆောင်ချက်များ")
            self.btn_clear_cart.setText("ဈေးခြင်းရှင်း")
            self.btn_checkout.setText("ငွေရှင်းမည်")
            self.cash_radio.setText("ငွေသား")
            self.credit_radio.setText("အကြွေး")
        else:
            self.action_group.setTitle("Actions")
            self.btn_clear_cart.setText("Clear Cart")
            self.btn_checkout.setText("Checkout")
            self.cash_radio.setText("Cash")
            self.credit_radio.setText("Credit")