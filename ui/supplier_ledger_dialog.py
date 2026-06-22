from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QComboBox,
    QDateEdit, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QColor
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from utils.language import lang
from ui.widgets.pagination_widget import PaginationWidget


class SupplierLedgerDialog(QDialog):
    def __init__(self, supplier_id=None, supplier_name=None, parent=None):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.all_entries = []  # Store all entries for pagination
        self.setWindowTitle(f"Supplier Ledger - {supplier_name}" if supplier_name else "Supplier Ledger")
        self.setMinimumSize(1000, 650)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()

        # Filter section
        filter_group = QGroupBox()
        filter_layout = QHBoxLayout()

        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.from_date)

        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.to_date)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_ledger)
        filter_layout.addWidget(self.btn_refresh)

        # Add payment button in filter row
        self.btn_payment = QPushButton("Make Payment")
        self.btn_payment.clicked.connect(self.make_payment)
        filter_layout.addWidget(self.btn_payment)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Summary section
        summary_group = QGroupBox()
        summary_layout = QHBoxLayout()
        self.total_purchases_label = QLabel("Total Purchases: 0")
        self.total_paid_label = QLabel("Total Paid: 0")
        self.balance_label = QLabel("Balance: 0")
        summary_layout.addWidget(self.total_purchases_label)
        summary_layout.addWidget(self.total_paid_label)
        summary_layout.addWidget(self.balance_label)
        summary_layout.addStretch()
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Ledger table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Date", "Reference", "Type", "Debit (Purchase)", "Credit (Payment)", "Balance", "Notes"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Pagination
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)
        layout.addWidget(self.pagination)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_print = QPushButton("Print Report")
        self.btn_print.clicked.connect(self.print_report)
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_print)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.load_ledger()
        self.retranslateUi()

    def get_lang(self):
        return lang.get_current()

    def retranslateUi(self):
        lang_code = self.get_lang()
        if lang_code == "my":
            self.setWindowTitle(f"ပေးသွင်းသူစာရင်း - {self.supplier_name}" if self.supplier_name else "ပေးသွင်းသူစာရင်း")
            self.total_purchases_label.setText("စုစုပေါင်းဝယ်ယူမှု: 0")
            self.total_paid_label.setText("စုစုပေါင်းပေးချေမှု: 0")
            self.balance_label.setText("ကျန်ငွေ: 0")
            self.btn_print.setText("အစီရင်ခံစာထုတ်မည်")
            self.btn_close.setText("ပိတ်မည်")
            self.btn_refresh.setText("ပြန်လည်")
            self.btn_payment.setText("ငွေပေးချေမည်")
            self.table.setHorizontalHeaderLabels([
                "ရက်စွဲ", "ကိုးကားအမှတ်", "အမျိုးအစား",
                "ဝယ်ယူမှု (အကြွေး)", "ငွေပေးချေမှု (အသွေး)", "ကျန်ငွေ", "မှတ်ချက်"
            ])
        else:
            self.setWindowTitle(f"Supplier Ledger - {self.supplier_name}" if self.supplier_name else "Supplier Ledger")
            self.total_purchases_label.setText("Total Purchases: 0")
            self.total_paid_label.setText("Total Paid: 0")
            self.balance_label.setText("Balance: 0")
            self.btn_print.setText("Print Report")
            self.btn_close.setText("Close")
            self.btn_refresh.setText("Refresh")
            self.btn_payment.setText("Make Payment")
            self.table.setHorizontalHeaderLabels([
                "Date", "Reference", "Type",
                "Debit (Purchase)", "Credit (Payment)", "Balance", "Notes"
            ])

    def on_page_changed(self, page: int, page_size: int):
        """Handle page change - display current page of entries"""
        self.display_entries(page, page_size)

    def display_entries(self, page=1, page_size=50):
        """Display entries for current page"""
        if not self.all_entries:
            self.table.setRowCount(0)
            return
        
        start = (page - 1) * page_size
        end = start + page_size
        page_entries = self.all_entries[start:end]
        
        symbol = get_currency_symbol()
        self.table.setRowCount(0)
        
        # Calculate running balance up to this point
        running_balance = 0
        # Calculate balance before this page
        for entry in self.all_entries[:start]:
            running_balance += entry['debit'] - entry['credit']
        
        for entry in page_entries:
            running_balance += entry['debit'] - entry['credit']
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(entry['date']))
            self.table.setItem(row, 1, QTableWidgetItem(entry['reference']))
            
            type_item = QTableWidgetItem(entry['type'])
            if entry['type'] == 'Purchase Order':
                type_item.setForeground(QColor(52, 152, 219))  # Light Blue
            else:
                type_item.setForeground(QColor(46, 204, 113))  # Light Green
            self.table.setItem(row, 2, type_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(format_money(entry['debit'], symbol)))
            self.table.setItem(row, 4, QTableWidgetItem(format_money(entry['credit'], symbol)))
            
            balance_item = QTableWidgetItem(format_money(running_balance, symbol))
            if running_balance > 0:
                balance_item.setForeground(QColor(231, 76, 60))  # Light Red
                balance_item.setBackground(QColor(255, 240, 240))
            elif running_balance < 0:
                balance_item.setForeground(QColor(46, 204, 113))  # Light Green
                balance_item.setBackground(QColor(240, 255, 240))
            else:
                balance_item.setForeground(QColor(128, 128, 128))  # Gray
            self.table.setItem(row, 5, balance_item)
            
            self.table.setItem(row, 6, QTableWidgetItem(entry['notes']))

    def load_ledger(self):
        """Load all ledger entries and setup pagination"""
        if not self.supplier_id:
            return

        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")

        conn = connect_db()
        cursor = conn.cursor()

        # Get all supplier payments/transactions (both purchases and payments)
        cursor.execute("""
            SELECT 
                sp.payment_date as trans_date,
                sp.reference_no,
                CASE 
                    WHEN sp.payment_type = 'Purchase' THEN 'Purchase Order'
                    WHEN sp.payment_type IN ('Paid', 'Cash', 'Bank Transfer', 'Cheque', 'Mobile Money') THEN 'Payment'
                    ELSE sp.payment_type
                END as trans_type,
                CASE WHEN sp.payment_type = 'Purchase' THEN sp.amount ELSE 0 END as debit,
                CASE WHEN sp.payment_type != 'Purchase' THEN sp.amount ELSE 0 END as credit,
                sp.notes,
                sp.payment_type as original_type
            FROM supplier_payments sp
            WHERE sp.supplier_id = ? AND date(sp.payment_date) BETWEEN ? AND ?
            ORDER BY sp.payment_date
        """, (self.supplier_id, from_date, to_date))
        
        rows = cursor.fetchall()
        
        # If no data in supplier_payments, check purchase_orders table for legacy data
        if not rows:
            cursor.execute("""
                SELECT 
                    po.order_date,
                    po.po_no,
                    'Purchase Order' as trans_type,
                    po.total_amount as debit,
                    0 as credit,
                    po.notes,
                    po.payment_status
                FROM purchase_orders po
                WHERE po.supplier_id = ? AND date(po.order_date) BETWEEN ? AND ?
                ORDER BY po.order_date
            """, (self.supplier_id, from_date, to_date))
            purchase_rows = cursor.fetchall()
            
            for row in purchase_rows:
                order_date, po_no, trans_type, debit, credit, notes, payment_status = row
                rows.append((order_date, po_no, trans_type, debit, credit, notes, payment_status))
        
        conn.close()

        # Calculate totals
        total_purchases = 0
        total_payments = 0
        entries = []

        for row in rows:
            if len(row) >= 7:
                trans_date, ref_no, trans_type, debit, credit, notes, original_type = row[:7]
            else:
                continue
                
            total_purchases += debit if debit else 0
            total_payments += credit if credit else 0
            entries.append({
                'date': trans_date,
                'reference': ref_no or "",
                'type': trans_type,
                'debit': debit if debit else 0,
                'credit': credit if credit else 0,
                'notes': notes or "",
                'original_type': original_type
            })

        # Sort entries by date
        entries.sort(key=lambda x: x['date'])
        
        # Store all entries for pagination
        self.all_entries = entries
        
        # Setup pagination
        total_items = len(entries)
        self.pagination.set_total_items(total_items, emit_signal=False)
        
        # Display first page
        self.display_entries(1, self.pagination._page_size)

        # Update summary labels
        balance = total_purchases - total_payments
        symbol = get_currency_symbol()
        lang_code = self.get_lang()
        
        if lang_code == "my":
            self.total_purchases_label.setText(f"စုစုပေါင်းဝယ်ယူမှု: {format_money(total_purchases, symbol)}")
            self.total_paid_label.setText(f"စုစုပေါင်းပေးချေမှု: {format_money(total_payments, symbol)}")
            self.balance_label.setText(f"ကျန်ငွေ: {format_money(balance, symbol)}")
            if balance > 0:
                self.balance_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            elif balance < 0:
                self.balance_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
            else:
                self.balance_label.setStyleSheet("color: #333;")
        else:
            self.total_purchases_label.setText(f"Total Purchases: {format_money(total_purchases, symbol)}")
            self.total_paid_label.setText(f"Total Paid: {format_money(total_payments, symbol)}")
            self.balance_label.setText(f"Balance: {format_money(balance, symbol)}")
            if balance > 0:
                self.balance_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            elif balance < 0:
                self.balance_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
            else:
                self.balance_label.setStyleSheet("color: #333;")

    def make_payment(self):
        """Open payment dialog for this supplier"""
        from ui.supplier_payment_dialog import SupplierPaymentDialog
        
        # Get current balance
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN payment_type = 'Purchase' THEN amount ELSE 0 END), 0) as total_purchases,
                COALESCE(SUM(CASE WHEN payment_type != 'Purchase' THEN amount ELSE 0 END), 0) as total_payments
            FROM supplier_payments
            WHERE supplier_id = ?
        """, (self.supplier_id,))
        row = cursor.fetchone()
        
        # If no data in supplier_payments, get from purchase_orders
        if not row or (row[0] == 0 and row[1] == 0):
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) as total_purchases
                FROM purchase_orders
                WHERE supplier_id = ?
            """, (self.supplier_id,))
            po_row = cursor.fetchone()
            total_purchases = po_row[0] if po_row else 0
            total_payments = 0
        else:
            total_purchases = row[0] if row else 0
            total_payments = row[1] if row else 0
        
        conn.close()
        
        current_balance = total_purchases - total_payments
        
        dialog = SupplierPaymentDialog(self.supplier_id, self.supplier_name, current_balance, self)
        if dialog.exec():
            self.load_ledger()  # Refresh ledger after payment

    def print_report(self):
        """Print all entries (not just current page)"""
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter, QFont, QFontMetrics, QPageLayout, QPageSize
        from PyQt6.QtWidgets import QFileDialog

        if not self.all_entries:
            QMessageBox.warning(self, "No Data", "No ledger entries to print.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report", f"supplier_ledger_{self.supplier_name}.pdf", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)

        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Error", "Could not start PDF generation.")
            return

        font = QFont("Arial", 9)
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        headers = ["Date", "Reference", "Type", "Debit", "Credit", "Balance", "Notes"]
        col_widths = [100, 120, 100, 100, 100, 100, 180]
        
        y = 30
        x = 20
        row_height = fm.height() + 6
        symbol = get_currency_symbol()

        # Title
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(20, y, f"Supplier Ledger - {self.supplier_name}")
        y += 30
        
        # Date range
        date_font = QFont("Arial", 10)
        painter.setFont(date_font)
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        painter.drawText(20, y, f"Period: {from_date} to {to_date}")
        y += 25

        # Headers
        painter.setFont(font)
        for i, header in enumerate(headers):
            painter.drawText(x, y, col_widths[i], row_height, Qt.AlignmentFlag.AlignLeft, header)
            x += col_widths[i]
        
        y += row_height
        x = 20

        # Print all entries with running balance
        running_balance = 0
        for entry in self.all_entries:
            if y + row_height > printer.height() - 50:
                printer.newPage()
                y = 30
                # Re-print headers
                for i, header in enumerate(headers):
                    painter.drawText(x, y, col_widths[i], row_height, Qt.AlignmentFlag.AlignLeft, header)
                    x += col_widths[i]
                y += row_height
                x = 20

            running_balance += entry['debit'] - entry['credit']
            
            painter.drawText(x, y, col_widths[0], row_height, Qt.AlignmentFlag.AlignLeft, entry['date'])
            painter.drawText(x + col_widths[0], y, col_widths[1], row_height, Qt.AlignmentFlag.AlignLeft, entry['reference'])
            painter.drawText(x + col_widths[0] + col_widths[1], y, col_widths[2], row_height, Qt.AlignmentFlag.AlignLeft, entry['type'])
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2], y, col_widths[3], row_height, Qt.AlignmentFlag.AlignLeft, format_money(entry['debit'], symbol))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], y, col_widths[4], row_height, Qt.AlignmentFlag.AlignLeft, format_money(entry['credit'], symbol))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4], y, col_widths[5], row_height, Qt.AlignmentFlag.AlignLeft, format_money(running_balance, symbol))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4] + col_widths[5], y, col_widths[6], row_height, Qt.AlignmentFlag.AlignLeft, entry['notes'])
            
            y += row_height
            x = 20

        painter.end()
        QMessageBox.information(self, "Export Complete", f"PDF saved to:\n{file_path}")