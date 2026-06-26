# ui/receipts_page/credit_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QLineEdit, QDateEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from ui.receipt_detail_dialog import ReceiptDetailDialog
from ui.widgets.pagination_widget import PaginationWidget
from datetime import datetime


class CreditTab(QWidget):
    def __init__(self, user_id=None, user_role=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.user_role = user_role
        self.parent_page = parent
        
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
        
        # Status filter
        quick_filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Partial", "Paid", "Overdue"])
        self.status_filter.currentTextChanged.connect(self.reset_and_load)
        quick_filter_layout.addWidget(self.status_filter)
        
        quick_filter_layout.addStretch()
        layout.addLayout(quick_filter_layout)
        
        # Top bar: search and filters
        top_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by invoice no or customer...")
        self.search_input.textChanged.connect(self.reset_and_load)
        top_layout.addWidget(self.search_input, 2)
        
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
        
        # Export button
        self.btn_export = QPushButton("📊 Export Excel")
        self.btn_export.clicked.connect(self.export_to_excel)
        top_layout.addWidget(self.btn_export)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Table (8 columns)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setColumnHidden(0, True)  # hide ID column
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self.show_receipt_detail)
        self.table.setAlternatingRowColors(True)
        
        header = self.table.horizontalHeader()
        for col in range(1, 8):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(45)
        
        layout.addWidget(self.table)
        
        # Pagination
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)
        layout.addWidget(self.pagination)
        
        self.setLayout(layout)
        self.retranslateUi()
    
    def get_lang(self):
        from utils.language import lang
        return lang.get_current()
    
    def retranslateUi(self):
        lang = self.get_lang()
        if lang == "my":
            self.search_input.setPlaceholderText("ပြေစာအမှတ် သို့မဟုတ် ဝယ်ယူသူဖြင့် ရှာရန်...")
            self.btn_export.setText("📊 Excel ထုတ်မည်")
            self.btn_today.setText("ယနေ့")
            self.btn_week.setText("ဤတစ်ပတ်")
            self.btn_month.setText("ဤတစ်လ")
            self.btn_3months.setText("၃ လ")
            self.btn_6months.setText("၆ လ")
            self.btn_year.setText("ဤတစ်နှစ်")
            self.status_filter.setItemText(0, "အားလုံး")
            self.status_filter.setItemText(1, "ဆိုင်းငံ့")
            self.status_filter.setItemText(2, "တစ်ပိုင်း")
            self.status_filter.setItemText(3, "ပြီးစီး")
            self.status_filter.setItemText(4, "သက်တမ်းလွန်")
            headers = ["ID", "ပြေစာအမှတ်", "ရက်စွဲ", "စုစုပေါင်း", 
                      "ဝယ်ယူသူ", "ကျန်ငွေ", "အခြေအနေ", "သတ်မှတ်ရက်"]
        else:
            self.search_input.setPlaceholderText("Search by invoice no or customer...")
            self.btn_export.setText("📊 Export Excel")
            self.btn_today.setText("Today")
            self.btn_week.setText("This Week")
            self.btn_month.setText("This Month")
            self.btn_3months.setText("3 Months")
            self.btn_6months.setText("6 Months")
            self.btn_year.setText("This Year")
            self.status_filter.setItemText(0, "All")
            self.status_filter.setItemText(1, "Pending")
            self.status_filter.setItemText(2, "Partial")
            self.status_filter.setItemText(3, "Paid")
            self.status_filter.setItemText(4, "Overdue")
            headers = ["ID", "Invoice No", "Date", "Total", 
                      "Customer", "Balance", "Status", "Due Date"]
        self.table.setHorizontalHeaderLabels(headers)
        self.load_credit_receipts()
    
    def set_quick_filter(self, days):
        """Set date range for quick filters"""
        today = QDate.currentDate()
        from_date = today.addDays(-days)
        self.from_date.setDate(from_date)
        self.to_date.setDate(today)
        self.reset_and_load()
    
    def set_year_filter(self):
        """Set date range for this year"""
        today = QDate.currentDate()
        from_date = QDate(today.year(), 1, 1)
        self.from_date.setDate(from_date)
        self.to_date.setDate(today)
        self.reset_and_load()
    
    def on_page_changed(self, page: int, page_size: int):
        self.load_credit_receipts(page, page_size)
    
    def reset_and_load(self):
        self.pagination.set_current_page(1)
        self.load_credit_receipts()
    
    def get_date_range(self):
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        return from_date, to_date
    
    def load_credit_receipts(self, page=1, page_size=50):
        """
        Load credit sales with status filter.
        """
        symbol = get_currency_symbol()
        search_text = self.search_input.text().strip()
        from_date, to_date = self.get_date_range()
        status_filter = self.status_filter.currentText()
        lang = self.get_lang()
        
        conn = connect_db()
        cursor = conn.cursor()
        like = f'%{search_text}%'
        
        # Build status filter
        status_condition = ""
        if status_filter == "Pending" or status_filter == "ဆိုင်းငံ့":
            status_condition = "AND cs.status = 'pending'"
        elif status_filter == "Partial" or status_filter == "တစ်ပိုင်း":
            status_condition = "AND cs.status = 'partial'"
        elif status_filter == "Paid" or status_filter == "ပြီးစီး":
            status_condition = "AND cs.status = 'paid'"
        elif status_filter == "Overdue" or status_filter == "သက်တမ်းလွန်":
            status_condition = "AND cs.due_date < date('now') AND cs.balance_amount > 0"
        
        # Count total
        if search_text:
            cursor.execute(f"""
                SELECT COUNT(*) FROM credit_sales cs
                LEFT JOIN customers c ON cs.customer_id = c.id
                WHERE cs.sale_date BETWEEN ? AND ?
                  AND (cs.invoice_no LIKE ? OR c.name LIKE ?)
                  {status_condition}
            """, (from_date, to_date, like, like))
        else:
            cursor.execute(f"""
                SELECT COUNT(*) FROM credit_sales cs
                WHERE cs.sale_date BETWEEN ? AND ?
                  {status_condition}
            """, (from_date, to_date))
        total_items = cursor.fetchone()[0]
        self.pagination.set_total_items(total_items, emit_signal=False)
        
        offset = (page - 1) * page_size
        
        # Main query
        if search_text:
            cursor.execute(f"""
                SELECT cs.id, cs.invoice_no, cs.sale_date, cs.total_amount,
                       c.name, cs.balance_amount, cs.status, cs.due_date
                FROM credit_sales cs
                LEFT JOIN customers c ON cs.customer_id = c.id
                WHERE cs.sale_date BETWEEN ? AND ?
                  AND (cs.invoice_no LIKE ? OR c.name LIKE ?)
                  {status_condition}
                ORDER BY cs.sale_date DESC
                LIMIT ? OFFSET ?
            """, (from_date, to_date, like, like, page_size, offset))
        else:
            cursor.execute(f"""
                SELECT cs.id, cs.invoice_no, cs.sale_date, cs.total_amount,
                       c.name, cs.balance_amount, cs.status, cs.due_date
                FROM credit_sales cs
                LEFT JOIN customers c ON cs.customer_id = c.id
                WHERE cs.sale_date BETWEEN ? AND ?
                  {status_condition}
                ORDER BY cs.sale_date DESC
                LIMIT ? OFFSET ?
            """, (from_date, to_date, page_size, offset))
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(0)
        today = QDate.currentDate()
        
        for row_data in rows:
            sale_id, invoice_no, sale_date, total, customer_name, balance, status, due_date = row_data
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(sale_id)))
            self.table.setItem(row, 1, QTableWidgetItem(invoice_no))
            self.table.setItem(row, 2, QTableWidgetItem(str(sale_date)[:16]))
            self.table.setItem(row, 3, QTableWidgetItem(format_money(total, symbol)))
            self.table.setItem(row, 4, QTableWidgetItem(customer_name if customer_name else "Walk-in"))
            
            # Balance with color
            balance_item = QTableWidgetItem(format_money(balance, symbol))
            if balance > 0:
                balance_item.setForeground(QColor(231, 76, 60))  # Red
            else:
                balance_item.setForeground(QColor(46, 204, 113))  # Green
            self.table.setItem(row, 5, balance_item)
            
            # Status with color coding (NO BACKGROUND COLOR)
            status_display = status
            if lang == "my":
                if status == "pending":
                    status_display = "ဆိုင်းငံ့"
                elif status == "partial":
                    status_display = "တစ်ပိုင်း"
                elif status == "paid":
                    status_display = "ပြီးစီး"
            
            status_item = QTableWidgetItem(status_display)
            
            # Check overdue
            is_overdue = False
            if due_date and balance > 0:
                try:
                    due_qdate = QDate.fromString(due_date, "yyyy-MM-dd")
                    if due_qdate < today:
                        is_overdue = True
                except:
                    pass
            
            # ✅ Set only text color, NO background color
            if status == "paid":
                status_item.setForeground(QColor(46, 204, 113))  # Green
            elif is_overdue:
                status_item.setForeground(QColor(231, 76, 60))  # Red
                status_display = "Overdue" if lang != "my" else "သက်တမ်းလွန်"
                status_item.setText(status_display)
            elif status == "pending" or status == "partial":
                status_item.setForeground(QColor(230, 126, 34))  # Orange
            
            # ✅ NO BACKGROUND COLOR SET
            # status_item.setBackground() - REMOVED
            
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, status_item)
            
            # Due Date
            due_item = QTableWidgetItem(due_date if due_date else "-")
            if is_overdue:
                due_item.setForeground(QColor(231, 76, 60))  # Red
            self.table.setItem(row, 7, due_item)
    
    def show_receipt_detail(self, row, column):
        """Handle double click on table row - show receipt detail dialog."""
        id_item = self.table.item(row, 0)
        if id_item:
            try:
                sale_id = int(id_item.text())
                dialog = ReceiptDetailDialog(sale_id)
                dialog.exec()
            except ValueError as e:
                QMessageBox.warning(self, "Error", f"Invalid sale ID: {e}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open receipt details: {e}")
    
    def load_credits(self):
        """Alias for load_credit_receipts (called from parent)"""
        self.load_credit_receipts()
    
    def export_to_excel(self):
        """Export credit receipts to Excel"""
        QMessageBox.information(self, "Export", "Export function will be implemented")
    
    def refresh(self):
        """Refresh the tab data"""
        self.load_credit_receipts()
    
    def showEvent(self, event):
        self.load_credit_receipts()
        super().showEvent(event)