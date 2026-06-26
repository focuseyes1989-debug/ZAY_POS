from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QDateEdit, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QColor
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money


class CustomerLedgerDialog(QDialog):
    def __init__(self, customer_id, customer_name, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.setWindowTitle(f"Ledger - {customer_name}")
        self.setMinimumSize(900, 600)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        info_group = QGroupBox("Customer Information")
        info_layout = QHBoxLayout()
        
        self.name_label = QLabel(f"<b>Customer:</b> {customer_name}")
        info_layout.addWidget(self.name_label)
        
        self.balance_label = QLabel("<b>Current Balance:</b> Loading...")
        info_layout.addWidget(self.balance_label)
        info_layout.addStretch()
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-3))
        filter_layout.addWidget(self.from_date)
        
        filter_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.to_date)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_ledger)
        filter_layout.addWidget(self.btn_refresh)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Reference", "Type", "Debit", "Credit", "Balance"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout()
        
        self.total_debit_label = QLabel("Total Debit: 0")
        self.total_credit_label = QLabel("Total Credit: 0")
        self.net_balance_label = QLabel("Net Balance: 0")
        summary_layout.addWidget(self.total_debit_label)
        summary_layout.addWidget(self.total_credit_label)
        summary_layout.addWidget(self.net_balance_label)
        summary_layout.addStretch()
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

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
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='language'")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "en"
        except:
            return "en"

    def retranslateUi(self):
        lang = self.get_lang()
        if lang == "my":
            self.setWindowTitle(f"စာရင်း - {self.customer_name}")
            self.btn_refresh.setText("ပြန်လည်")
            self.btn_print.setText("ပရင့်ထုတ်မည်")
            self.btn_close.setText("ပိတ်မည်")
            self.table.setHorizontalHeaderLabels(["ရက်စွဲ", "ကိုးကားအမှတ်", "အမျိုးအစား", "အကြွေး", "အသွေး", "ကျန်ငွေ"])

    def load_ledger(self):
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        symbol = get_currency_symbol()

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cs.sale_date, cs.invoice_no, 'Credit Sale' as type, cs.total_amount, 0 as credit
            FROM credit_sales cs
            WHERE cs.customer_id = ?
              AND cs.sale_date BETWEEN ? AND ?
              AND COALESCE(cs.status, '') != 'refunded'
            ORDER BY cs.sale_date
        """, (self.customer_id, from_date, to_date))
        sales = cursor.fetchall()

        cursor.execute("""
            SELECT cp.payment_date, cp.reference_no, 'Payment' as type, 0 as debit, cp.amount
            FROM credit_payments cp
            JOIN credit_sales cs ON cp.credit_sale_id = cs.id
            WHERE cp.customer_id = ?
              AND cp.payment_date BETWEEN ? AND ?
              AND COALESCE(cs.status, '') != 'refunded'
            ORDER BY cp.payment_date
        """, (self.customer_id, from_date, to_date))
        payments = cursor.fetchall()

        cursor.execute("SELECT current_balance FROM customers WHERE id = ?", (self.customer_id,))
        row = cursor.fetchone()
        current_balance = row[0] if row else 0
        conn.close()

        entries = []
        total_debit = 0
        total_credit = 0

        for sale in sales:
            date, ref, type, debit, credit = sale
            total_debit += debit
            entries.append({
                'date': date,
                'reference': ref,
                'type': type,
                'debit': debit,
                'credit': credit,
            })

        for payment in payments:
            date, ref, type, debit, credit = payment
            total_credit += credit
            entries.append({
                'date': date,
                'reference': ref or f"PAY-{date}",
                'type': type,
                'debit': debit,
                'credit': credit,
            })

        entries.sort(key=lambda x: x['date'])

        running_balance = 0
        self.table.setRowCount(0)

        for entry in entries:
            running_balance += entry['debit'] - entry['credit']
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(entry['date']))
            self.table.setItem(row, 1, QTableWidgetItem(entry['reference']))
            
            type_item = QTableWidgetItem(entry['type'])
            if entry['type'] == 'Credit Sale':
                type_item.setForeground(QColor(231, 76, 60))
            else:
                type_item.setForeground(QColor(46, 204, 113))
            self.table.setItem(row, 2, type_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(format_money(entry['debit'], symbol)))
            self.table.setItem(row, 4, QTableWidgetItem(format_money(entry['credit'], symbol)))
            
            balance_item = QTableWidgetItem(format_money(running_balance, symbol))
            if running_balance > 0:
                balance_item.setForeground(QColor(231, 76, 60))
            elif running_balance < 0:
                balance_item.setForeground(QColor(46, 204, 113))
            self.table.setItem(row, 5, balance_item)

        self.total_debit_label.setText(f"Total Debit: {format_money(total_debit, symbol)}")
        self.total_credit_label.setText(f"Total Credit: {format_money(total_credit, symbol)}")
        net_balance = total_debit - total_credit
        self.net_balance_label.setText(f"Net Balance: {format_money(net_balance, symbol)}")
        self.balance_label.setText(f"<b>Current Balance:</b> {format_money(current_balance, symbol)}")
        
        if current_balance > 0:
            self.balance_label.setStyleSheet("color: #e74c3c;")
        else:
            self.balance_label.setStyleSheet("color: #27ae60;")

    def print_report(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter, QFont, QFontMetrics, QPageLayout, QPageSize
        from PyQt6.QtWidgets import QFileDialog

        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No ledger entries to print.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report", f"customer_ledger_{self.customer_name}.pdf", "PDF Files (*.pdf)"
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
        
        headers = ["Date", "Reference", "Type", "Debit", "Credit", "Balance"]
        col_widths = [100, 120, 100, 100, 100, 100]
        
        y = 30
        x = 20
        row_height = fm.height() + 6

        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(20, y, f"Customer Ledger - {self.customer_name}")
        y += 30
        
        date_font = QFont("Arial", 10)
        painter.setFont(date_font)
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        painter.drawText(20, y, f"Period: {from_date} to {to_date}")
        y += 25

        painter.setFont(font)
        for i, header in enumerate(headers):
            painter.drawText(x, y, col_widths[i], row_height, Qt.AlignmentFlag.AlignLeft, header)
            x += col_widths[i]
        
        y += row_height
        x = 20

        for row in range(self.table.rowCount()):
            if y + row_height > printer.height() - 50:
                printer.newPage()
                y = 30
                for i, header in enumerate(headers):
                    painter.drawText(x, y, col_widths[i], row_height, Qt.AlignmentFlag.AlignLeft, header)
                    x += col_widths[i]
                y += row_height
                x = 20

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                text = item.text() if item else ""
                painter.drawText(x, y, col_widths[col], row_height, Qt.AlignmentFlag.AlignLeft, text)
                x += col_widths[col]
            y += row_height
            x = 20

        painter.end()
        QMessageBox.information(self, "Export Complete", f"PDF saved to:\n{file_path}")
