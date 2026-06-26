# ui/receipts_page/discount_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QLineEdit, QDateEdit, QDoubleSpinBox, QCheckBox, QGroupBox,
    QComboBox
)
from PyQt6.QtCore import Qt, QDate
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from utils.permissions import PermissionManager, Permission
from ui.widgets.pagination_widget import PaginationWidget


class DiscountTab(QWidget):
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
        
        # ====== Top bar: search and filters ======
        top_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by invoice no...")
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
        
        # ====== Table (6 columns) ======
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setColumnHidden(0, True)  # hide ID column
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # ✅ Double click to show receipt detail
        self.table.cellDoubleClicked.connect(self.show_receipt_detail)
        self.table.setAlternatingRowColors(True)
        
        header = self.table.horizontalHeader()
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(45)
        
        layout.addWidget(self.table)
        
        # ====== Pagination ======
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
            self.search_input.setPlaceholderText("ပြေစာအမှတ်ဖြင့် ရှာရန်...")
            self.btn_export.setText("📊 Excel ထုတ်မည်")
            self.btn_today.setText("ယနေ့")
            self.btn_week.setText("ဤတစ်ပတ်")
            self.btn_month.setText("ဤတစ်လ")
            self.btn_3months.setText("၃ လ")
            self.btn_6months.setText("၆ လ")
            self.btn_year.setText("ဤတစ်နှစ်")
            headers = ["ID", "ပြေစာအမှတ်", "ရက်စွဲ", "စုစုပေါင်း", "လျှော့စျေး", "အသားတင်"]
        else:
            self.search_input.setPlaceholderText("Search by invoice no...")
            self.btn_export.setText("📊 Export Excel")
            self.btn_today.setText("Today")
            self.btn_week.setText("This Week")
            self.btn_month.setText("This Month")
            self.btn_3months.setText("3 Months")
            self.btn_6months.setText("6 Months")
            self.btn_year.setText("This Year")
            headers = ["ID", "Invoice No", "Date", "Total", "Discount", "Net Total"]
        self.table.setHorizontalHeaderLabels(headers)
        self.load_discounted_receipts()
    
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
    
    def get_date_range(self):
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        return from_date, to_date
    
    def on_page_changed(self, page: int, page_size: int):
        self.load_discounted_receipts(page, page_size)
    
    def reset_and_load(self):
        self.pagination.set_current_page(1)
        self.load_discounted_receipts()
    
    def load_discounted_receipts(self, page=1, page_size=50):
        """
        Load ONLY receipts that have discount_amount > 0.
        """
        symbol = get_currency_symbol()
        search_text = self.search_input.text().strip()
        from_date, to_date = self.get_date_range()
        
        conn = connect_db()
        cursor = conn.cursor()
        like = f'%{search_text}%'
        
        # ✅ Only show receipts with discount
        if search_text:
            cursor.execute("""
                SELECT COUNT(*) FROM sales
                WHERE status = 'completed'
                  AND discount_amount > 0
                  AND date(created_at) BETWEEN ? AND ?
                  AND invoice_no LIKE ?
            """, (from_date, to_date, like))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM sales
                WHERE status = 'completed'
                  AND discount_amount > 0
                  AND date(created_at) BETWEEN ? AND ?
            """, (from_date, to_date))
        total_items = cursor.fetchone()[0]
        self.pagination.set_total_items(total_items, emit_signal=False)
        
        offset = (page - 1) * page_size
        
        # ✅ Main query - only discounted receipts
        if search_text:
            cursor.execute("""
                SELECT id, invoice_no, created_at, total, discount_amount,
                       (total - discount_amount) as net_total
                FROM sales
                WHERE status = 'completed'
                  AND discount_amount > 0
                  AND date(created_at) BETWEEN ? AND ?
                  AND invoice_no LIKE ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (from_date, to_date, like, page_size, offset))
        else:
            cursor.execute("""
                SELECT id, invoice_no, created_at, total, discount_amount,
                       (total - discount_amount) as net_total
                FROM sales
                WHERE status = 'completed'
                  AND discount_amount > 0
                  AND date(created_at) BETWEEN ? AND ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (from_date, to_date, page_size, offset))
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(0)
        for row_data in rows:
            sale_id, invoice_no, created_at, total, discount_amount, net_total = row_data
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(sale_id)))
            self.table.setItem(row, 1, QTableWidgetItem(invoice_no))
            self.table.setItem(row, 2, QTableWidgetItem(str(created_at)[:16]))
            self.table.setItem(row, 3, QTableWidgetItem(format_money(total, symbol)))
            
            # Discount column - normal text color
            discount_item = QTableWidgetItem(format_money(discount_amount, symbol))
            self.table.setItem(row, 4, discount_item)
            
            # Net Total column - normal text color
            net_item = QTableWidgetItem(format_money(net_total, symbol))
            self.table.setItem(row, 5, net_item)
    
    # ============================================================
    # ✅ DOUBLE CLICK HANDLER - Show Receipt Detail
    # ============================================================
    def show_receipt_detail(self, row, column):
        """Handle double click on table row - show receipt detail dialog."""
        id_item = self.table.item(row, 0)
        if id_item:
            try:
                sale_id = int(id_item.text())
                from ui.receipt_detail_dialog import ReceiptDetailDialog
                dialog = ReceiptDetailDialog(sale_id)
                dialog.exec()
            except ValueError as e:
                QMessageBox.warning(self, "Error", f"Invalid sale ID: {e}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open receipt details: {e}")
    
    def load_discounts(self):
        """Alias for load_discounted_receipts (called from parent)"""
        self.load_discounted_receipts()
    
    def export_to_excel(self):
        """Export discounted receipts to Excel"""
        QMessageBox.information(self, "Export", "Export function will be implemented")
    
    def showEvent(self, event):
        self.load_discounted_receipts()
        super().showEvent(event)