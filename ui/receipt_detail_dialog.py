# ui/receipt_detail_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money


class ReceiptDetailDialog(QDialog):
    def __init__(self, sale_id, is_credit=False):
        super().__init__()
        self.sale_id = sale_id
        self.is_credit = is_credit
        self.setWindowTitle("Receipt Details")
        self.setMinimumSize(700, 550)
        self.setModal(True)
        
        # Set window icon
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))

        main_layout = QVBoxLayout()

        # Load sale data based on type
        if is_credit:
            sale, items = self._load_credit_sale_data()
        else:
            sale, items = self._load_sale_data()

        if not sale:
            main_layout.addWidget(QLabel("Sale not found."))
            self.setLayout(main_layout)
            return

        symbol = get_currency_symbol()

        # Header info with larger font
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        header_font = QFont()
        header_font.setPointSize(12)
        
        if is_credit:
            # Credit sale data structure
            # invoice_no, sale_date, total_amount, paid_amount, change_amount, 
            # customer_name, payment_type, balance_amount, status, due_date
            invoice_no, sale_date, total_amount, paid_amount, change_amount, customer_name, payment_type, balance_amount, status, due_date = sale
            
            info_layout.addWidget(self._create_label(f"Invoice No: {invoice_no}", header_font))
            info_layout.addWidget(self._create_label(f"Date: {sale_date}", header_font))
            info_layout.addWidget(self._create_label(f"Payment Type: {payment_type if payment_type else 'Credit'}", header_font))
            info_layout.addWidget(self._create_label(f"Due Date: {due_date if due_date else 'N/A'}", header_font))
            
            # Status with color
            status_label = self._create_label(f"Status: {status}", header_font)
            if status == "paid":
                status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            elif status == "overdue" or (due_date and balance_amount > 0 and QDate.fromString(due_date, "yyyy-MM-dd") < QDate.currentDate()):
                status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                if status != "overdue":
                    status_label.setText(f"Status: Overdue")
            elif status == "pending" or status == "partial":
                status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            info_layout.addWidget(status_label)
            
            info_layout.addWidget(self._create_label(f"Balance: {format_money(balance_amount, symbol)}", header_font))
            if customer_name:
                info_layout.addWidget(self._create_label(f"Customer: {customer_name}", header_font))
            
            # ✅ Add Paid amount to header
            info_layout.addWidget(self._create_label(f"Paid: {format_money(paid_amount, symbol)}", header_font))
            
        else:
            # Regular sale data structure
            invoice_no, created_at, total, payment, change_amount, customer_name, payment_type = sale
            info_layout.addWidget(self._create_label(f"Invoice No: {invoice_no}", header_font))
            info_layout.addWidget(self._create_label(f"Date: {created_at}", header_font))
            info_layout.addWidget(self._create_label(f"Payment Type: {payment_type if payment_type else 'N/A'}", header_font))
            if customer_name:
                info_layout.addWidget(self._create_label(f"Customer: {customer_name}", header_font))
        
        main_layout.addWidget(info_frame)

        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Total"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set larger font for table
        table_font = QFont()
        table_font.setPointSize(11)
        self.items_table.setFont(table_font)
        self.items_table.verticalHeader().setDefaultSectionSize(30)

        # Populate items
        self.items_table.setRowCount(len(items))
        for row, (name, qty, price, total) in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(name))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.items_table.setItem(row, 2, QTableWidgetItem(format_money(price, symbol)))
            self.items_table.setItem(row, 3, QTableWidgetItem(format_money(total, symbol)))

        main_layout.addWidget(self.items_table)

        # Totals section
        subtotal = sum(item[3] for item in items)
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        totals_font = QFont()
        totals_font.setPointSize(12)
        totals_font.setBold(True)
        
        if is_credit:
            totals_layout.addWidget(self._create_label(f"Subtotal: {format_money(subtotal, symbol)}", totals_font))
            totals_layout.addWidget(self._create_label(f"Total: {format_money(total_amount, symbol)}", totals_font))
            totals_layout.addWidget(self._create_label(f"Paid: {format_money(paid_amount, symbol)}", totals_font))
            totals_layout.addWidget(self._create_label(f"Balance: {format_money(balance_amount, symbol)}", totals_font))
        else:
            totals_layout.addWidget(self._create_label(f"Subtotal: {format_money(subtotal, symbol)}", totals_font))
            totals_layout.addWidget(self._create_label(f"Total: {format_money(total, symbol)}", totals_font))
            totals_layout.addWidget(self._create_label(f"Payment: {format_money(payment, symbol)}", totals_font))
            totals_layout.addWidget(self._create_label(f"Change: {format_money(change_amount, symbol)}", totals_font))
        
        main_layout.addLayout(totals_layout)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.setFixedSize(100, 35)
        btn_close.clicked.connect(self.accept)
        main_layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

    def _load_sale_data(self):
        """Load regular sale data"""
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.invoice_no, s.created_at, s.total, s.payment, s.change_amount,
                   c.name, s.payment_type
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE s.id = ?
        """, (self.sale_id,))
        sale = cursor.fetchone()
        
        if not sale:
            conn.close()
            return None, []

        # Fetch sale items
        cursor.execute("""
            SELECT product_name, qty, price, total
            FROM sale_items
            WHERE sale_id = ?
        """, (self.sale_id,))
        items = cursor.fetchall()
        conn.close()
        
        return sale, items

    def _load_credit_sale_data(self):
        """Load credit sale data from credit_sales table"""
        conn = connect_db()
        cursor = conn.cursor()
        
        # ✅ Get credit sale directly from credit_sales table
        cursor.execute("""
            SELECT cs.invoice_no, cs.sale_date, cs.total_amount, cs.paid_amount,
                   0 as change_amount, c.name, 'Credit' as payment_type,
                   cs.balance_amount, cs.status, cs.due_date
            FROM credit_sales cs
            LEFT JOIN customers c ON cs.customer_id = c.id
            WHERE cs.id = ?
        """, (self.sale_id,))
        sale = cursor.fetchone()
        
        if not sale:
            conn.close()
            return None, []

        # Get items - try from sale_items via sale_id
        items = []
        
        # Check if there's a linked sale
        cursor.execute("SELECT sale_id FROM credit_sales WHERE id = ?", (self.sale_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            # Get items from sale_items using sale_id
            cursor.execute("""
                SELECT product_name, qty, price, total
                FROM sale_items
                WHERE sale_id = ?
            """, (result[0],))
            items = cursor.fetchall()
        
        # If no items found, try to get from credit_sale_items if exists
        if not items:
            try:
                cursor.execute("""
                    SELECT product_name, quantity, price, total
                    FROM credit_sale_items
                    WHERE credit_sale_id = ?
                """, (self.sale_id,))
                items = cursor.fetchall()
            except:
                pass
        
        # If still no items, create a placeholder
        if not items:
            # Get total amount and create a single item
            total_amount = sale[2] if sale else 0
            if total_amount > 0:
                items = [("Credit Sale Total", 1, total_amount, total_amount)]
        
        conn.close()
        return sale, items

    def _create_label(self, text, font):
        label = QLabel(text)
        label.setFont(font)
        return label