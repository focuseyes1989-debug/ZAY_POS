# receipt_detail_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money


class ReceiptDetailDialog(QDialog):
    def __init__(self, sale_id):
        super().__init__()
        self.sale_id = sale_id
        self.setWindowTitle("Receipt Details")
        self.setMinimumSize(700, 550)
        self.setModal(True)
        
        # Set window icon
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))

        main_layout = QVBoxLayout()

        # Load sale data
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.invoice_no, s.created_at, s.total, s.payment, s.change_amount,
                   c.name, s.payment_type
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE s.id = ?
        """, (sale_id,))
        sale = cursor.fetchone()

        if not sale:
            main_layout.addWidget(QLabel("Sale not found."))
            self.setLayout(main_layout)
            conn.close()
            return

        invoice_no, created_at, total, payment, change, customer_name, payment_type = sale
        symbol = get_currency_symbol()

        # Header info with larger font
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        header_font = QFont()
        header_font.setPointSize(12)
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

        # Fetch sale items
        cursor.execute("""
            SELECT product_name, qty, price, total
            FROM sale_items
            WHERE sale_id = ?
        """, (sale_id,))
        items = cursor.fetchall()
        conn.close()

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
        totals_layout.addWidget(self._create_label(f"Subtotal: {format_money(subtotal, symbol)}", totals_font))
        totals_layout.addWidget(self._create_label(f"Total: {format_money(total, symbol)}", totals_font))
        totals_layout.addWidget(self._create_label(f"Payment: {format_money(payment, symbol)}", totals_font))
        totals_layout.addWidget(self._create_label(f"Change: {format_money(change, symbol)}", totals_font))
        main_layout.addLayout(totals_layout)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.setFixedSize(100, 35)
        btn_close.clicked.connect(self.accept)
        main_layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

    def _create_label(self, text, font):
        label = QLabel(text)
        label.setFont(font)
        return label