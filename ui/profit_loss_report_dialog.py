from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QDateEdit, QFrame, QFileDialog, QWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QColor
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from datetime import datetime
import csv


class ProfitLossReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profit & Loss Report")
        self.setMinimumSize(900, 600)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Date range selection
        date_group = QGroupBox("Date Range")
        date_layout = QHBoxLayout()
        
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.from_date)
        
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.to_date)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_report)
        date_layout.addWidget(self.btn_refresh)
        
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.clicked.connect(self.export_report)
        date_layout.addWidget(self.btn_export)
        
        date_layout.addStretch()
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        # Summary Cards
        card_layout = QHBoxLayout()
        card_layout.setSpacing(15)

        # Sales Card
        self.sales_card = self.create_card("Total Sales", "0", "#3498db")
        card_layout.addWidget(self.sales_card, 1)

        # Expenses Card
        self.expenses_card = self.create_card("Total Expenses", "0", "#e74c3c")
        card_layout.addWidget(self.expenses_card, 1)

        # Profit Card
        self.profit_card = self.create_card("Net Profit", "0", "#2ecc71")
        card_layout.addWidget(self.profit_card, 1)

        # Margin Card
        self.margin_card = self.create_card("Profit Margin", "0%", "#9b59b6")
        card_layout.addWidget(self.margin_card, 1)

        layout.addLayout(card_layout)

        # Main Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Category", "Amount", "Percentage of Sales", "Status", "Trend"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        # Close button
        btn_layout = QHBoxLayout()
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_report()
        self.retranslateUi()

    def get_theme(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='theme'")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "Light"
        except:
            return "Light"

    def create_card(self, title, amount, color):
        card = QFrame()
        card.setObjectName("profitCard")
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        amount_label = QLabel(amount)
        amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        amount_label.setObjectName("amount_label")
        amount_label.setStyleSheet(f"color: {color}; font-size: 22pt; font-weight: bold;")

        layout.addWidget(title_label)
        layout.addWidget(amount_label)
        return card

    def update_card_amount(self, card, amount):
        for child in card.findChildren(QLabel):
            if child.objectName() == "amount_label":
                child.setText(amount)
                break

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
            self.setWindowTitle("အမြတ်အစွန်း အစီရင်ခံစာ")
            self.btn_refresh.setText("ပြန်လည်")
            self.btn_export.setText("CSV ထုတ်မည်")
            self.btn_close.setText("ပိတ်မည်")
            self.table.setHorizontalHeaderLabels([
                "အမျိုးအစား", "ပမာဏ", "ရောင်းအား၏ ရာခိုင်နှုန်း", 
                "အခြေအနေ", "လမ်းကြောင်း"
            ])
        else:
            self.setWindowTitle("Profit & Loss Report")
            self.btn_refresh.setText("Refresh")
            self.btn_export.setText("Export CSV")
            self.btn_close.setText("Close")
            self.table.setHorizontalHeaderLabels([
                "Category", "Amount", "Percentage of Sales", 
                "Status", "Trend"
            ])

    def load_report(self):
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        symbol = get_currency_symbol()

        conn = connect_db()
        cursor = conn.cursor()

        # Calculate Total Sales
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) FROM sales
            WHERE status = 'completed' AND date(created_at) BETWEEN ? AND ?
        """, (from_date, to_date))
        total_sales = cursor.fetchone()[0]

        # Calculate COGS (Cost of Goods Sold)
        cursor.execute("""
            SELECT COALESCE(SUM(products.cost * sale_items.qty), 0)
            FROM sale_items
            JOIN sales ON sale_items.sale_id = sales.id
            JOIN products ON sale_items.product_name = products.name
            WHERE sales.status = 'completed' 
              AND date(sales.created_at) BETWEEN ? AND ?
              AND (products.sold_by IS NULL OR products.sold_by != 'Service')
        """, (from_date, to_date))
        total_cogs = cursor.fetchone()[0]

        # Calculate Gross Profit
        gross_profit = total_sales - total_cogs

        # Calculate Total Expenses
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses
            WHERE expense_date BETWEEN ? AND ?
        """, (from_date, to_date))
        total_expenses = cursor.fetchone()[0]

        # Calculate Net Profit
        net_profit = gross_profit - total_expenses

        # Calculate Profit Margin
        profit_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0

        conn.close()

        # Update Cards
        self.update_card_amount(self.sales_card, format_money(total_sales, symbol))
        self.update_card_amount(self.expenses_card, format_money(total_expenses, symbol))
        
        # Color coding for profit
        if net_profit >= 0:
            self.update_card_amount(self.profit_card, format_money(net_profit, symbol))
            profit_color = "#2ecc71"
        else:
            self.update_card_amount(self.profit_card, f"-{format_money(abs(net_profit), symbol)}")
            profit_color = "#e74c3c"
        
        self.update_card_amount(self.margin_card, f"{profit_margin:.1f}%")
        
        # Set color for profit amount
        for child in self.profit_card.findChildren(QLabel):
            if child.objectName() == "amount_label":
                child.setStyleSheet(f"color: {profit_color}; font-size: 22pt; font-weight: bold;")
                break

        # Populate Table
        data = [
            ("Total Sales", total_sales, 100, "Income", "↑"),
            ("Cost of Goods Sold (COGS)", total_cogs, 
             (total_cogs / total_sales * 100) if total_sales > 0 else 0, "Expense", "↓"),
            ("Gross Profit", gross_profit, 
             (gross_profit / total_sales * 100) if total_sales > 0 else 0, 
             "Profit" if gross_profit >= 0 else "Loss",
             "↑" if gross_profit >= 0 else "↓"),
            ("Operating Expenses", total_expenses, 
             (total_expenses / total_sales * 100) if total_sales > 0 else 0, "Expense", "↓"),
            ("Net Profit", net_profit, 
             (net_profit / total_sales * 100) if total_sales > 0 else 0,
             "Profit" if net_profit >= 0 else "Loss",
             "↑" if net_profit >= 0 else "↓"),
        ]

        self.table.setRowCount(len(data))
        for i, (category, amount, percentage, status, trend) in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(category))
            self.table.setItem(i, 1, QTableWidgetItem(format_money(amount, symbol)))
            self.table.setItem(i, 2, QTableWidgetItem(f"{percentage:.1f}%"))
            
            status_item = QTableWidgetItem(status)
            if status == "Profit":
                status_item.setForeground(QColor(46, 204, 113))
            elif status == "Loss":
                status_item.setForeground(QColor(231, 76, 60))
            else:
                status_item.setForeground(QColor(52, 152, 219))
            self.table.setItem(i, 3, status_item)
            
            trend_item = QTableWidgetItem(trend)
            if trend == "↑":
                trend_item.setForeground(QColor(46, 204, 113))
            elif trend == "↓":
                trend_item.setForeground(QColor(231, 76, 60))
            self.table.setItem(i, 4, trend_item)

    def export_report(self):
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Profit & Loss Report", 
            f"profit_loss_{from_date}_to_{to_date}.csv", 
            "CSV Files (*.csv)"
        )
        if not file_path:
            return
        
        try:
            symbol = get_currency_symbol()
            lang = self.get_lang()
            
            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) FROM sales
                WHERE status = 'completed' AND date(created_at) BETWEEN ? AND ?
            """, (from_date, to_date))
            total_sales = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(products.cost * sale_items.qty), 0)
                FROM sale_items
                JOIN sales ON sale_items.sale_id = sales.id
                JOIN products ON sale_items.product_name = products.name
                WHERE sales.status = 'completed' AND date(sales.created_at) BETWEEN ? AND ?
            """, (from_date, to_date))
            total_cogs = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM expenses
                WHERE expense_date BETWEEN ? AND ?
            """, (from_date, to_date))
            total_expenses = cursor.fetchone()[0]
            
            conn.close()

            gross_profit = total_sales - total_cogs
            net_profit = gross_profit - total_expenses
            profit_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["=" * 60])
                writer.writerow(["PROFIT & LOSS REPORT"])
                writer.writerow(["=" * 60])
                writer.writerow([])
                writer.writerow(["Period:", f"{from_date} to {to_date}"])
                writer.writerow(["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow([])
                writer.writerow(["METRIC", "AMOUNT", "% OF SALES"])
                writer.writerow(["-" * 60])
                writer.writerow(["Total Sales", format_money(total_sales, symbol), "100%"])
                writer.writerow(["COGS", format_money(total_cogs, symbol), 
                               f"{(total_cogs/total_sales*100):.1f}%" if total_sales > 0 else "0%"])
                writer.writerow(["Gross Profit", format_money(gross_profit, symbol),
                               f"{(gross_profit/total_sales*100):.1f}%" if total_sales > 0 else "0%"])
                writer.writerow(["Operating Expenses", format_money(total_expenses, symbol),
                               f"{(total_expenses/total_sales*100):.1f}%" if total_sales > 0 else "0%"])
                writer.writerrow(["Net Profit", format_money(net_profit, symbol),
                               f"{profit_margin:.1f}%"])
                writer.writerow([])
                writer.writerow(["=" * 60])
                writer.writerow(["End of Report"])
            
            msg = f"Report exported successfully to:\n{file_path}" if lang != "my" else f"အစီရင်ခံစာ အောင်မြင်စွာ ထုတ်ယူပြီးပါပြီ:\n{file_path}"
            QMessageBox.information(self, "Export Complete", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")