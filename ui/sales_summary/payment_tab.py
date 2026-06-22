# ui/sales_summary/payment_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QFont
from models.database import connect_db
from utils.currency import format_money, get_currency_symbol


class PaymentTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load(self, from_date, to_date, lang_code):
        symbol = get_currency_symbol()
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(payment_type, 'Other') as payment_type,
                   COUNT(*) as transaction_count,
                   COALESCE(SUM(total), 0) as total_amount
            FROM sales
            WHERE status = 'completed' AND date(created_at) BETWEEN ? AND ?
            GROUP BY payment_type
            ORDER BY payment_type
        """, (from_date, to_date))
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(0)
        total_count = 0
        total_amount = 0.0
        
        for ptype, count, amount in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(ptype))
            self.table.setItem(r, 1, QTableWidgetItem(str(count)))
            self.table.setItem(r, 2, QTableWidgetItem(format_money(amount, symbol)))
            total_count += count
            total_amount += amount
        
        # Total row
        r = self.table.rowCount()
        self.table.insertRow(r)
        font = self.table.font()
        font.setBold(True)
        total_item = QTableWidgetItem("TOTAL")
        total_item.setFont(font)
        self.table.setItem(r, 0, total_item)
        item = QTableWidgetItem(str(total_count))
        item.setFont(font)
        self.table.setItem(r, 1, item)
        item = QTableWidgetItem(format_money(total_amount, symbol))
        item.setFont(font)
        self.table.setItem(r, 2, item)
        
        if lang_code == "my":
            self.table.setHorizontalHeaderLabels([
                "ငွေပေးချေမှုအမျိုးအစား", "ငွေပေးချေမှုအရေအတွက်", "ငွေပေးချေမှုပမာဏ"
            ])
        else:
            self.table.setHorizontalHeaderLabels([
                "Payment Type", "Transaction Count", "Amount"
            ])