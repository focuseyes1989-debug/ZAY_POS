# ui/receipts_page/receipts_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QLineEdit, QComboBox, QFileDialog, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from utils.permissions import PermissionManager, Permission
from ui.receipt_detail_dialog import ReceiptDetailDialog
from ui.receipt_dialog import ReceiptDialog
from ui.widgets.pagination_widget import PaginationWidget
import csv
from datetime import datetime


class ReceiptsTab(QWidget):
    def __init__(self, user_id=None, user_role=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.user_role = user_role
        layout = QVBoxLayout()

        # ====== Quick Filter Buttons ======
        quick_filter_layout = QHBoxLayout()
        quick_filter_layout.setSpacing(5)
        
        self.btn_today = QPushButton("Today")
        self.btn_today.setFixedWidth(80)
        self.btn_today.clicked.connect(lambda: self.set_quick_filter(0))
        quick_filter_layout.addWidget(self.btn_today)
        
        self.btn_week = QPushButton("This Week")
        self.btn_week.setFixedWidth(80)
        self.btn_week.clicked.connect(lambda: self.set_quick_filter(7))
        quick_filter_layout.addWidget(self.btn_week)
        
        self.btn_month = QPushButton("This Month")
        self.btn_month.setFixedWidth(80)
        self.btn_month.clicked.connect(lambda: self.set_quick_filter(30))
        quick_filter_layout.addWidget(self.btn_month)
        
        self.btn_3months = QPushButton("3 Months")
        self.btn_3months.setFixedWidth(80)
        self.btn_3months.clicked.connect(lambda: self.set_quick_filter(90))
        quick_filter_layout.addWidget(self.btn_3months)
        
        self.btn_6months = QPushButton("6 Months")
        self.btn_6months.setFixedWidth(80)
        self.btn_6months.clicked.connect(lambda: self.set_quick_filter(180))
        quick_filter_layout.addWidget(self.btn_6months)
        
        self.btn_year = QPushButton("This Year")
        self.btn_year.setFixedWidth(80)
        self.btn_year.clicked.connect(self.set_year_filter)
        quick_filter_layout.addWidget(self.btn_year)
        
        quick_filter_layout.addStretch()
        layout.addLayout(quick_filter_layout)

        # Top bar: search and filters
        top_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by invoice no...")
        self.search_input.textChanged.connect(self.reset_and_load)
        top_layout.addWidget(self.search_input, 2)
        
        # ====== ✅ PAYMENT TYPE FILTER (from general settings) ======
        top_layout.addWidget(QLabel("Payment:"))
        
        self.payment_filter = QComboBox()
        # Load from database later
        self.payment_filter.currentTextChanged.connect(self.reset_and_load)
        top_layout.addWidget(self.payment_filter)
        
        # ====== ✅ CUSTOMER TYPE FILTER ======
        top_layout.addWidget(QLabel("Customer:"))
        
        self.customer_filter = QComboBox()
        self.customer_filter.addItems(["All", "Walk-in", "Registered", "Credit"])
        self.customer_filter.currentTextChanged.connect(self.reset_and_load)
        top_layout.addWidget(self.customer_filter)
        
        # Date range filters
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.dateChanged.connect(self.reset_and_load)
        top_layout.addWidget(QLabel("From:"))
        top_layout.addWidget(self.from_date)
        
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.dateChanged.connect(self.reset_and_load)
        top_layout.addWidget(QLabel("To:"))
        top_layout.addWidget(self.to_date)
        
        # Export buttons
        self.btn_export_list = QPushButton("📋 Export List")
        self.btn_export_list.clicked.connect(self.export_receipt_list)
        top_layout.addWidget(self.btn_export_list)
        
        self.btn_export_range = QPushButton("📊 Export Range")
        self.btn_export_range.clicked.connect(self.export_receipt_range)
        top_layout.addWidget(self.btn_export_range)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Table (10 columns)
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setColumnHidden(0, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self.show_receipt_detail)
        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()
        for col in range(1, 8):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(45)
        
        self.table.setColumnWidth(8, 100)
        self.table.setColumnWidth(9, 100)
        
        layout.addWidget(self.table)

        # Pagination
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)
        layout.addWidget(self.pagination)

        self.setLayout(layout)
        self.retranslateUi()
        
        # Load payment types from database
        self.load_payment_types()

    # ---------- Load Payment Types from General Settings ----------
    def load_payment_types(self):
        """Load payment types from database (same as general_setting.py)"""
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM payment_types ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        
        # Clear and add "All" as first item
        self.payment_filter.clear()
        lang = self.get_lang()
        self.payment_filter.addItem("All" if lang != "my" else "အားလုံး")
        
        for row in rows:
            self.payment_filter.addItem(row[0])

    # ---------- Language support ----------
    def get_lang(self):
        from utils.language import lang
        return lang.get_current()

    def retranslateUi(self):
        lang = self.get_lang()
        if lang == "my":
            self.search_input.setPlaceholderText("ပြေစာအမှတ်ဖြင့် ရှာရန်...")
            self.btn_export_list.setText("📋 စာရင်းထုတ်မည်")
            self.btn_export_range.setText("📊 ရက်ကား အလိုက် ထုတ်မည်")
            self.btn_today.setText("ယနေ့")
            self.btn_week.setText("ဤတစ်ပတ်")
            self.btn_month.setText("ဤတစ်လ")
            self.btn_3months.setText("၃ လ")
            self.btn_6months.setText("၆ လ")
            self.btn_year.setText("ဤတစ်နှစ်")
            
            # Customer filter - Myanmar
            self.customer_filter.setItemText(0, "အားလုံး")
            self.customer_filter.setItemText(1, "လမ်းဘေးဝယ်")
            self.customer_filter.setItemText(2, "မှတ်ပုံတင်ထားသူ")
            self.customer_filter.setItemText(3, "အကြွေး")
            
            headers = [
                "ID", "ပြေစာအမှတ်", "ရက်စွဲ", "စုစုပေါင်း", "ငွေပေးချေမှု", 
                "ပြန်အမ်းငွေ", "ဝယ်ယူသူ", "ငွေပေးချေမှုအမျိုးအစား", "ပြန်အမ်းမည်", "ပြေစာထုတ်မည်"
            ]
        else:
            self.search_input.setPlaceholderText("Search by invoice no...")
            self.btn_export_list.setText("📋 Export List")
            self.btn_export_range.setText("📊 Export Range")
            self.btn_today.setText("Today")
            self.btn_week.setText("This Week")
            self.btn_month.setText("This Month")
            self.btn_3months.setText("3 Months")
            self.btn_6months.setText("6 Months")
            self.btn_year.setText("This Year")
            
            # Customer filter - English
            self.customer_filter.setItemText(0, "All")
            self.customer_filter.setItemText(1, "Walk-in")
            self.customer_filter.setItemText(2, "Registered")
            self.customer_filter.setItemText(3, "Credit")
            
            headers = [
                "ID", "Invoice No", "Date", "Total", "Payment", "Change", 
                "Customer", "Payment Type", "Refund", "Print"
            ]
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setColumnWidth(8, 100)
        self.table.setColumnWidth(9, 100)
        
        self.load_sales()

    def set_quick_filter(self, days):
        today = QDate.currentDate()
        from_date = today.addDays(-days)
        self.from_date.setDate(from_date)
        self.to_date.setDate(today)
        self.reset_and_load()
    
    def set_year_filter(self):
        today = QDate.currentDate()
        from_date = QDate(today.year(), 1, 1)
        self.from_date.setDate(from_date)
        self.to_date.setDate(today)
        self.reset_and_load()

    def on_page_changed(self, page: int, page_size: int):
        self.load_sales(page, page_size)

    def reset_and_load(self):
        self.pagination.set_current_page(1)
        self.load_sales()

    def get_date_range(self):
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        return from_date, to_date

    def get_currency_symbol(self):
        from utils.currency import get_currency_symbol
        return get_currency_symbol()

    # ---------- LOAD SALES WITH PAYMENT AND CUSTOMER FILTERS ----------
    def load_sales(self, page=1, page_size=50):
        symbol = get_currency_symbol()
        search_text = self.search_input.text().strip()
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        lang = self.get_lang()
        
        # Get payment type filter
        payment_type = self.payment_filter.currentText()
        
        # Get customer filter
        customer_filter = self.customer_filter.currentText()
        
        conn = connect_db()
        cursor = conn.cursor()
        like = f'%{search_text}%'
        
        # ✅ FIX: Use LOWER() for case-insensitive comparison
        payment_condition = ""
        if payment_type and payment_type not in ["All", "အားလုံး"]:
            # Get the actual payment type name from database (case-insensitive)
            cursor.execute("SELECT name FROM payment_types WHERE LOWER(name) = LOWER(?)", (payment_type,))
            result = cursor.fetchone()
            if result:
                actual_name = result[0]
                payment_condition = f"AND LOWER(s.payment_type) = LOWER('{actual_name}')"
            else:
                payment_condition = f"AND LOWER(s.payment_type) = LOWER('{payment_type}')"
        
        # Build customer condition
        customer_condition = ""
        if customer_filter == "Walk-in" or customer_filter == "လမ်းဘေးဝယ်":
            customer_condition = "AND s.customer_id IS NULL"
        elif customer_filter == "Registered" or customer_filter == "မှတ်ပုံတင်ထားသူ":
            customer_condition = "AND s.customer_id IS NOT NULL"
        elif customer_filter == "Credit" or customer_filter == "အကြွေး":
            customer_condition = "AND LOWER(s.payment_type) = 'credit'"
        
        # Count total with filters
        if search_text:
            cursor.execute(f"""
                SELECT COUNT(*) FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status='completed' 
                  AND date(s.created_at) BETWEEN ? AND ?
                  AND (s.invoice_no LIKE ? OR c.name LIKE ?)
                  {payment_condition}
                  {customer_condition}
            """, (from_date, to_date, like, like))
        else:
            cursor.execute(f"""
                SELECT COUNT(*) FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status='completed' 
                  AND date(s.created_at) BETWEEN ? AND ?
                  {payment_condition}
                  {customer_condition}
            """, (from_date, to_date))
        total_items = cursor.fetchone()[0]
        self.pagination.set_total_items(total_items, emit_signal=False)
        
        offset = (page - 1) * page_size
        
        # Main query with filters
        if search_text:
            cursor.execute(f"""
                SELECT s.id, s.invoice_no, s.created_at, s.total, s.payment, s.change_amount, 
                       c.name, s.payment_type
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status='completed' 
                  AND date(s.created_at) BETWEEN ? AND ?
                  AND (s.invoice_no LIKE ? OR c.name LIKE ?)
                  {payment_condition}
                  {customer_condition}
                ORDER BY s.created_at DESC
                LIMIT ? OFFSET ?
            """, (from_date, to_date, like, like, page_size, offset))
        else:
            cursor.execute(f"""
                SELECT s.id, s.invoice_no, s.created_at, s.total, s.payment, s.change_amount, 
                       c.name, s.payment_type
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status='completed' 
                  AND date(s.created_at) BETWEEN ? AND ?
                  {payment_condition}
                  {customer_condition}
                ORDER BY s.created_at DESC
                LIMIT ? OFFSET ?
            """, (from_date, to_date, page_size, offset))
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(0)
        for row_data in rows:
            sale_id, invoice_no, created_at, total, payment, change_amount, customer_name, payment_type_db = row_data
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(sale_id)))
            self.table.setItem(row, 1, QTableWidgetItem(invoice_no))
            self.table.setItem(row, 2, QTableWidgetItem(str(created_at)))
            self.table.setItem(row, 3, QTableWidgetItem(format_money(total, symbol)))
            self.table.setItem(row, 4, QTableWidgetItem(format_money(payment, symbol)))
            self.table.setItem(row, 5, QTableWidgetItem(format_money(change_amount, symbol)))
            self.table.setItem(row, 6, QTableWidgetItem(customer_name if customer_name else "-"))
            self.table.setItem(row, 7, QTableWidgetItem(payment_type_db if payment_type_db else "-"))

            btn_refund = QPushButton("ပြန်အမ်းမည်" if lang == "my" else "Refund")
            btn_refund.setFixedSize(90, 30)
            btn_refund.clicked.connect(lambda _, sid=sale_id: self.refund_sale(sid))
            self.table.setCellWidget(row, 8, btn_refund)

            btn_print = QPushButton("ထုတ်မည်" if lang == "my" else "Print")
            btn_print.setFixedSize(90, 30)
            btn_print.clicked.connect(lambda _, sid=sale_id: self.print_receipt(sid))
            self.table.setCellWidget(row, 9, btn_print)

    def show_receipt_detail(self, row, column):
        sale_id_item = self.table.item(row, 0)
        if sale_id_item:
            sale_id = int(sale_id_item.text())
            dialog = ReceiptDetailDialog(sale_id)
            dialog.exec()

    def print_receipt(self, sale_id):
        try:
            dialog = ReceiptDialog(sale_id, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Could not print receipt: {e}")

    def refund_sale(self, sale_id):
        """Refund a sale - restore stock and adjust customer points"""
        lang = self.get_lang()
        
        if self.user_id:
            has_permission = PermissionManager.user_has_permission(self.user_id, Permission.REFUND_RECEIPT)
            if not has_permission:
                QMessageBox.warning(self, "Access Denied", "You don't have permission to refund sales.")
                return
        
        if lang == "my":
            confirm_title = "အတည်ပြုရန်"
            confirm_text = "ဤရောင်းချမှုကို ပြန်အမ်းမည်လား?\nစတော့ပြန်လည်သိုလှောင်ပေးမည်ဖြစ်ပြီး အမှတ်များကို ပြန်လည်ချိန်ညှိပေးမည်။"
            success_msg = "အောင်မြင်စွာ ပြန်အမ်းပြီးပါပြီ။"
            error_msg = "ပြန်အမ်းခြင်း မအောင်မြင်ပါ: {e}"
        else:
            confirm_title = "Confirm Refund"
            confirm_text = "Refund this sale? Stock will be restored and customer points adjusted."
            success_msg = "Sale refunded successfully."
            error_msg = "Refund failed: {e}"

        confirm = QMessageBox.question(
            self, confirm_title, confirm_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT status FROM sales WHERE id=?", (sale_id,))
            result = cursor.fetchone()
            if not result:
                QMessageBox.warning(self, "Error", "Sale not found.")
                return
                
            if result[0] != 'completed':
                QMessageBox.warning(self, "Error", "This sale has already been refunded.")
                return

            cursor.execute("SELECT customer_id, total, invoice_no, payment_type FROM sales WHERE id=?", (sale_id,))
            sale_data = cursor.fetchone()
            if not sale_data:
                QMessageBox.warning(self, "Error", "Sale data not found.")
                return
                
            customer_id, total, invoice_no, payment_type = sale_data

            cursor.execute("SELECT product_name, qty FROM sale_items WHERE sale_id=?", (sale_id,))
            items = cursor.fetchall()
            
            for product_name, qty in items:
                cursor.execute("SELECT id, sold_by FROM products WHERE name=?", (product_name,))
                prod = cursor.fetchone()
                if prod and prod[1] != 'Service':
                    cursor.execute("UPDATE products SET stock = stock + ? WHERE id=?", (qty, prod[0]))

            if customer_id:
                cursor.execute("SELECT value FROM settings WHERE key='loyalty_points_per_dollar'")
                res = cursor.fetchone()
                points_per_dollar = float(res[0]) if res else 0.0
                points_earned = int(total * points_per_dollar)
                
                cursor.execute("""
                    UPDATE customers 
                    SET total_visit = total_visit - 1,
                        total_spent = total_spent - ?,
                        points = points - ?
                    WHERE id = ?
                """, (total, points_earned, customer_id))

            if customer_id and (payment_type or "").lower() == "credit":
                cursor.execute("""
                    SELECT id, balance_amount, status
                    FROM credit_sales
                    WHERE sale_id = ?
                    LIMIT 1
                """, (sale_id,))
                credit_sale = cursor.fetchone()

                if not credit_sale and invoice_no:
                    cursor.execute("""
                        SELECT id, balance_amount, status
                        FROM credit_sales
                        WHERE invoice_no = ? AND customer_id = ?
                        LIMIT 1
                    """, (invoice_no, customer_id))
                    credit_sale = cursor.fetchone()

                if credit_sale:
                    credit_sale_id, balance_amount, credit_status = credit_sale
                    balance_to_remove = max(float(balance_amount or 0), 0)

                    if credit_status != "refunded":
                        if balance_to_remove > 0:
                            cursor.execute("""
                                UPDATE customers
                                SET current_balance = CASE
                                    WHEN COALESCE(current_balance, 0) - ? < 0 THEN 0
                                    ELSE COALESCE(current_balance, 0) - ?
                                END
                                WHERE id = ?
                            """, (balance_to_remove, balance_to_remove, customer_id))

                        cursor.execute("""
                            UPDATE credit_sales
                            SET balance_amount = 0, status = 'refunded'
                            WHERE id = ?
                        """, (credit_sale_id,))

            cursor.execute("UPDATE sales SET status='refunded' WHERE id=?", (sale_id,))
            conn.commit()
            
            QMessageBox.information(self, "Success", success_msg)

            main_window = self.window()
            if hasattr(main_window, 'check_stock_alerts'):
                main_window.check_stock_alerts()
            if hasattr(main_window, 'customers_page'):
                main_window.customers_page.load_customers()

            self.load_sales()

            parent_page = self.parent()
            if hasattr(parent_page, 'refund_tab'):
                parent_page.refund_tab.load_refunded_sales()

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", error_msg.format(e=str(e)))
        finally:
            conn.close()

    # ---------- EXPORT FUNCTIONS ----------
    def export_receipt_list(self):
        """Export current receipt list to CSV"""
        from_date, to_date = self.get_date_range()
        payment_type = self.payment_filter.currentText()
        customer_filter = self.customer_filter.currentText()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Receipt List", 
            f"receipt_list_{from_date}_to_{to_date}.csv", 
            "CSV Files (*.csv)"
        )
        if not file_path:
            return
        
        try:
            symbol = self.get_currency_symbol()
            search_text = self.search_input.text().strip()
            
            conn = connect_db()
            cursor = conn.cursor()
            
            like = f'%{search_text}%'
            
            # Build payment condition
            payment_condition = ""
            if payment_type and payment_type != "All" and payment_type != "အားလုံး":
                payment_condition = f"AND s.payment_type = '{payment_type.lower()}'"
            
            # Build customer condition
            customer_condition = ""
            if customer_filter == "Walk-in" or customer_filter == "လမ်းဘေးဝယ်":
                customer_condition = "AND s.customer_id IS NULL"
            elif customer_filter == "Registered" or customer_filter == "မှတ်ပုံတင်ထားသူ":
                customer_condition = "AND s.customer_id IS NOT NULL"
            elif customer_filter == "Credit" or customer_filter == "အကြွေး":
                customer_condition = "AND s.payment_type = 'credit'"
            
            if search_text:
                cursor.execute(f"""
                    SELECT s.invoice_no, s.created_at, s.total, s.payment, s.change_amount, 
                           c.name, s.payment_type
                    FROM sales s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    WHERE s.status='completed' 
                      AND date(s.created_at) BETWEEN ? AND ?
                      AND (s.invoice_no LIKE ? OR c.name LIKE ?)
                      {payment_condition}
                      {customer_condition}
                    ORDER BY s.created_at DESC
                """, (from_date, to_date, like, like))
            else:
                cursor.execute(f"""
                    SELECT s.invoice_no, s.created_at, s.total, s.payment, s.change_amount, 
                           c.name, s.payment_type
                    FROM sales s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    WHERE s.status='completed' 
                      AND date(s.created_at) BETWEEN ? AND ?
                      {payment_condition}
                      {customer_condition}
                    ORDER BY s.created_at DESC
                """, (from_date, to_date))
            rows = cursor.fetchall()
            conn.close()
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["=" * 80])
                writer.writerow(["RECEIPT LIST REPORT"])
                writer.writerow(["=" * 80])
                writer.writerow([])
                writer.writerow(["Report Period:", f"{from_date} to {to_date}"])
                writer.writerow(["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                if search_text:
                    writer.writerow(["Search Filter:", search_text])
                if payment_type and payment_type != "All" and payment_type != "အားလုံး":
                    writer.writerow(["Payment Type:", payment_type])
                if customer_filter and customer_filter != "All" and customer_filter != "အားလုံး":
                    writer.writerow(["Customer Type:", customer_filter])
                writer.writerow([])
                writer.writerow(["Invoice No", "Date", "Total", "Payment", "Change", "Customer", "Payment Type"])
                writer.writerow(["-" * 80])
                
                total_amount = 0
                total_payment = 0
                total_change = 0
                
                for row in rows:
                    invoice_no, created_at, total, payment, change_amount, customer_name, payment_type_db = row
                    writer.writerow([
                        invoice_no,
                        created_at[:16] if created_at else "",
                        format_money(total, symbol),
                        format_money(payment, symbol),
                        format_money(change_amount, symbol),
                        customer_name if customer_name else "Walk-in",
                        payment_type_db or ""
                    ])
                    total_amount += total
                    total_payment += payment
                    total_change += change_amount
                
                writer.writerow([])
                writer.writerow(["TOTAL", "", 
                               format_money(total_amount, symbol),
                               format_money(total_payment, symbol),
                               format_money(total_change, symbol), "", ""])
                writer.writerow([])
                writer.writerow(["=" * 80])
                writer.writerow(["End of Report"])
            
            lang = self.get_lang()
            msg = f"Receipt list exported successfully to:\n{file_path}" if lang != "my" else f"ပြေစာစာရင်း အောင်မြင်စွာ ထုတ်ယူပြီးပါပြီ:\n{file_path}"
            QMessageBox.information(self, "Export Complete", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export receipt list: {e}")

    def export_receipt_range(self):
        """Export all receipts within date range to CSV"""
        from_date, to_date = self.get_date_range()
        payment_type = self.payment_filter.currentText()
        customer_filter = self.customer_filter.currentText()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Receipt Range", 
            f"receipt_range_{from_date}_to_{to_date}.csv", 
            "CSV Files (*.csv)"
        )
        if not file_path:
            return
        
        try:
            symbol = self.get_currency_symbol()
            
            conn = connect_db()
            cursor = conn.cursor()
            
            # Build payment condition
            payment_condition = ""
            if payment_type and payment_type != "All" and payment_type != "အားလုံး":
                payment_condition = f"AND s.payment_type = '{payment_type.lower()}'"
            
            # Build customer condition
            customer_condition = ""
            if customer_filter == "Walk-in" or customer_filter == "လမ်းဘေးဝယ်":
                customer_condition = "AND s.customer_id IS NULL"
            elif customer_filter == "Registered" or customer_filter == "မှတ်ပုံတင်ထားသူ":
                customer_condition = "AND s.customer_id IS NOT NULL"
            elif customer_filter == "Credit" or customer_filter == "အကြွေး":
                customer_condition = "AND s.payment_type = 'credit'"
            
            cursor.execute(f"""
                SELECT s.invoice_no, s.created_at, s.total, s.payment, s.change_amount, 
                       c.name, s.payment_type, s.discount_amount
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status='completed' 
                  AND date(s.created_at) BETWEEN ? AND ?
                  {payment_condition}
                  {customer_condition}
                ORDER BY s.created_at DESC
            """, (from_date, to_date))
            rows = cursor.fetchall()
            
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_count,
                    COALESCE(SUM(total), 0) as total_sales,
                    COALESCE(SUM(payment), 0) as total_payments,
                    COALESCE(SUM(change_amount), 0) as total_change,
                    COALESCE(AVG(total), 0) as avg_sale
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status='completed' 
                  AND date(s.created_at) BETWEEN ? AND ?
                  {payment_condition}
                  {customer_condition}
            """, (from_date, to_date))
            stats = cursor.fetchone()
            conn.close()
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["=" * 90])
                writer.writerow(["RECEIPT DETAIL REPORT"])
                writer.writerow(["=" * 90])
                writer.writerow([])
                writer.writerow(["Report Period:", f"{from_date} to {to_date}"])
                writer.writerow(["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                if payment_type and payment_type != "All" and payment_type != "အားလုံး":
                    writer.writerow(["Payment Type Filter:", payment_type])
                if customer_filter and customer_filter != "All" and customer_filter != "အားလုံး":
                    writer.writerow(["Customer Type:", customer_filter])
                writer.writerow([])
                
                writer.writerow(["SUMMARY STATISTICS"])
                writer.writerow(["-" * 50])
                writer.writerow(["Total Receipts:", stats[0] if stats else 0])
                writer.writerow(["Total Sales:", format_money(stats[1] if stats else 0, symbol)])
                writer.writerow(["Total Payments:", format_money(stats[2] if stats else 0, symbol)])
                writer.writerow(["Total Change:", format_money(stats[3] if stats else 0, symbol)])
                writer.writerow(["Average Sale:", format_money(stats[4] if stats else 0, symbol)])
                writer.writerow([])
                
                writer.writerow(["DETAILED RECEIPTS"])
                writer.writerow(["Invoice No", "Date", "Total", "Payment", "Change", "Customer", "Payment Type", "Discount"])
                writer.writerow(["-" * 90])
                
                total_sales = 0
                total_payments = 0
                total_change = 0
                total_discount = 0
                
                for row in rows:
                    invoice_no, created_at, total, payment, change_amount, customer_name, payment_type_db, discount = row
                    writer.writerow([
                        invoice_no,
                        created_at[:16] if created_at else "",
                        format_money(total, symbol),
                        format_money(payment, symbol),
                        format_money(change_amount, symbol),
                        customer_name if customer_name else "Walk-in",
                        payment_type_db or "",
                        format_money(discount or 0, symbol)
                    ])
                    total_sales += total
                    total_payments += payment
                    total_change += change_amount
                    total_discount += discount or 0
                
                writer.writerow([])
                writer.writerow(["GRAND TOTALS", "", 
                               format_money(total_sales, symbol),
                               format_money(total_payments, symbol),
                               format_money(total_change, symbol), "", "",
                               format_money(total_discount, symbol)])
                writer.writerow([])
                writer.writerow(["=" * 90])
                writer.writerow(["End of Report"])
            
            lang = self.get_lang()
            msg = f"Receipt range exported successfully to:\n{file_path}" if lang != "my" else f"ပြေစာရက်ကား အောင်မြင်စွာ ထုတ်ယူပြီးပါပြီ:\n{file_path}"
            QMessageBox.information(self, "Export Complete", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export receipt range: {e}")

    def showEvent(self, event):
        self.load_payment_types()  # Reload payment types from DB
        self.load_sales()
        super().showEvent(event)