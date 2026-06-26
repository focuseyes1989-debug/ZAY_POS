# ui/receipts_page/refund_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QLineEdit, QDateEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from utils.permissions import PermissionManager, Permission
from ui.receipt_detail_dialog import ReceiptDetailDialog
from ui.widgets.pagination_widget import PaginationWidget
from datetime import datetime


class RefundTab(QWidget):
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
        
        # Table (7 columns)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setColumnHidden(0, True)  # hide ID column
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # ✅ Double click to show receipt detail
        self.table.cellDoubleClicked.connect(self.show_receipt_detail)
        self.table.setAlternatingRowColors(True)
        
        header = self.table.horizontalHeader()
        for col in range(1, 7):
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
            headers = ["ID", "ပြေစာအမှတ်", "ရက်စွဲ", "စုစုပေါင်း", "ဝယ်ယူသူ", 
                      "ငွေပေးချေမှုအမျိုးအစား", "ပြန်အမ်းချိန်"]
        else:
            self.search_input.setPlaceholderText("Search by invoice no or customer...")
            self.btn_export.setText("📊 Export Excel")
            self.btn_today.setText("Today")
            self.btn_week.setText("This Week")
            self.btn_month.setText("This Month")
            self.btn_3months.setText("3 Months")
            self.btn_6months.setText("6 Months")
            self.btn_year.setText("This Year")
            headers = ["ID", "Invoice No", "Date", "Total", "Customer", 
                      "Payment Type", "Refunded At"]
        self.table.setHorizontalHeaderLabels(headers)
        self.load_refunded_sales()
    
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
        self.load_refunded_sales(page, page_size)
    
    def reset_and_load(self):
        self.pagination.set_current_page(1)
        self.load_refunded_sales()
    
    def get_date_range(self):
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        return from_date, to_date
    
    def load_refunded_sales(self, page=1, page_size=50):
        """
        Load ONLY refunded sales (status = 'refunded').
        """
        symbol = get_currency_symbol()
        search_text = self.search_input.text().strip()
        from_date, to_date = self.get_date_range()
        
        conn = connect_db()
        cursor = conn.cursor()
        like = f'%{search_text}%'
        
        # ✅ Only show refunded sales
        if search_text:
            cursor.execute("""
                SELECT COUNT(*) FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status = 'refunded'
                  AND date(s.created_at) BETWEEN ? AND ?
                  AND (s.invoice_no LIKE ? OR c.name LIKE ?)
            """, (from_date, to_date, like, like))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM sales s
                WHERE s.status = 'refunded'
                  AND date(s.created_at) BETWEEN ? AND ?
            """, (from_date, to_date))
        total_items = cursor.fetchone()[0]
        self.pagination.set_total_items(total_items, emit_signal=False)
        
        offset = (page - 1) * page_size
        
        # ✅ Main query - only refunded sales
        if search_text:
            cursor.execute("""
                SELECT s.id, s.invoice_no, s.created_at, s.total,
                       c.name, s.payment_type
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status = 'refunded'
                  AND date(s.created_at) BETWEEN ? AND ?
                  AND (s.invoice_no LIKE ? OR c.name LIKE ?)
                ORDER BY s.created_at DESC
                LIMIT ? OFFSET ?
            """, (from_date, to_date, like, like, page_size, offset))
        else:
            cursor.execute("""
                SELECT s.id, s.invoice_no, s.created_at, s.total,
                       c.name, s.payment_type
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.status = 'refunded'
                  AND date(s.created_at) BETWEEN ? AND ?
                ORDER BY s.created_at DESC
                LIMIT ? OFFSET ?
            """, (from_date, to_date, page_size, offset))
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(0)
        for row_data in rows:
            sale_id, invoice_no, created_at, total, customer_name, payment_type = row_data
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(sale_id)))
            self.table.setItem(row, 1, QTableWidgetItem(invoice_no))
            self.table.setItem(row, 2, QTableWidgetItem(str(created_at)[:16]))
            self.table.setItem(row, 3, QTableWidgetItem(format_money(total, symbol)))
            self.table.setItem(row, 4, QTableWidgetItem(customer_name if customer_name else "Walk-in"))
            self.table.setItem(row, 5, QTableWidgetItem(payment_type if payment_type else "-"))
            
            # ✅ Refunded At - normal text color
            refund_display = str(created_at)[:16] if created_at else "-"
            refund_item = QTableWidgetItem(refund_display)
            self.table.setItem(row, 6, refund_item)
    
    # ✅ Alias method for backward compatibility
    def load_refundable_sales(self, page=1, page_size=50):
        """Alias for load_refunded_sales."""
        self.load_refunded_sales(page, page_size)
    
    # ============================================================
    # ✅ DOUBLE CLICK HANDLER - Show Receipt Detail
    # ============================================================
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
    
    def export_to_excel(self):
        """Export refunded receipts to Excel"""
        QMessageBox.information(self, "Export", "Export function will be implemented")
    
    def refresh(self):
        """Refresh the tab data"""
        self.load_refunded_sales()
    
    def showEvent(self, event):
        self.load_refunded_sales()
        super().showEvent(event)