from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QComboBox, QDateEdit, QTabWidget, QFrame,
    QFileDialog, QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QColor, QFont
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from datetime import datetime
import csv


class ProfitReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profit & Loss Report")
        self.setMinimumSize(1100, 750)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # ========== FILTER SECTION ==========
        filter_group = QGroupBox("Report Filters")
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)

        # Date range
        filter_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.from_date)

        filter_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.to_date)

        # Report type
        filter_layout.addWidget(QLabel("Report Type:"))
        self.report_type = QComboBox()
        self.report_type.addItems(["Monthly", "Quarterly", "Yearly", "Custom Period"])
        self.report_type.currentTextChanged.connect(self.on_report_type_changed)
        filter_layout.addWidget(self.report_type)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_report)
        filter_layout.addWidget(self.btn_refresh)

        self.btn_export = QPushButton("Export CSV")
        self.btn_export.clicked.connect(self.export_report)
        filter_layout.addWidget(self.btn_export)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # ========== SUMMARY CARDS ==========
        card_layout = QHBoxLayout()
        card_layout.setSpacing(15)

        # Sales Card
        self.sales_card = self.create_card("Total Sales", "0", "#3498db")
        card_layout.addWidget(self.sales_card, 1)

        # COGS Card
        self.cogs_card = self.create_card("Cost of Goods Sold", "0", "#e74c3c")
        card_layout.addWidget(self.cogs_card, 1)

        # Gross Profit Card
        self.gross_card = self.create_card("Gross Profit", "0", "#2ecc71")
        card_layout.addWidget(self.gross_card, 1)

        # Expenses Card
        self.expenses_card = self.create_card("Operating Expenses", "0", "#e67e22")
        card_layout.addWidget(self.expenses_card, 1)

        # Net Profit Card
        self.net_card = self.create_card("Net Profit", "0", "#9b59b6")
        card_layout.addWidget(self.net_card, 1)

        # Margin Card
        self.margin_card = self.create_card("Net Profit Margin", "0%", "#1abc9c")
        card_layout.addWidget(self.margin_card, 1)

        layout.addLayout(card_layout)

        # ========== TABS ==========
        self.tabs = QTabWidget()

        # Summary Tab
        self.summary_tab = self.create_summary_tab()
        self.tabs.addTab(self.summary_tab, "Summary")

        # Monthly Breakdown Tab
        self.monthly_tab = self.create_monthly_tab()
        self.tabs.addTab(self.monthly_tab, "Monthly Breakdown")

        # Category Analysis Tab
        self.category_tab = self.create_category_tab()
        self.tabs.addTab(self.category_tab, "Category Analysis")

        # Top Products Tab
        self.products_tab = self.create_products_tab()
        self.tabs.addTab(self.products_tab, "Top Products")

        layout.addWidget(self.tabs)

        # Close button
        btn_layout = QHBoxLayout()
        self.btn_close = QPushButton("Close")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #40444b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 25px;
            }
            QPushButton:hover {
                background-color: #5865f2;
            }
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.apply_card_style()
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

    def apply_card_style(self):
        theme = self.get_theme()
        if theme == "Dark":
            card_style = """
                QFrame#profitCard {
                    background-color: #2f3136;
                    border: 1px solid #40444b;
                    border-radius: 12px;
                    padding: 15px;
                }
                QFrame#profitCard:hover {
                    background-color: #383a40;
                    border: 1px solid #5865f2;
                }
            """
            title_style = "color: #b9bbbe; font-size: 10pt;"
            amount_style = "color: #ffffff; font-size: 18pt; font-weight: bold;"
        else:
            card_style = """
                QFrame#profitCard {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 12px;
                    padding: 15px;
                }
                QFrame#profitCard:hover {
                    background-color: #f8f9fa;
                    border: 1px solid #adb5bd;
                }
            """
            title_style = "color: #6c757d; font-size: 10pt;"
            amount_style = "color: #212529; font-size: 18pt; font-weight: bold;"

        for card in [self.sales_card, self.cogs_card, self.gross_card, 
                     self.expenses_card, self.net_card, self.margin_card]:
            card.setStyleSheet(card_style)
            for child in card.findChildren(QLabel):
                if "amount" in child.objectName() or "total" in child.objectName().lower():
                    child.setStyleSheet(amount_style)
                else:
                    child.setStyleSheet(title_style)

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
        amount_label.setStyleSheet(f"color: {color}; font-size: 18pt; font-weight: bold;")

        layout.addWidget(title_label)
        layout.addWidget(amount_label)
        return card

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
            self.tabs.setTabText(0, "အကျဉ်းချုပ်")
            self.tabs.setTabText(1, "လစဉ် ခွဲခြမ်းစိတ်ဖြာ")
            self.tabs.setTabText(2, "အမျိုးအစား အလိုက်")
            self.tabs.setTabText(3, "ထိပ်ဆုံးပစ္စည်းများ")
        else:
            self.setWindowTitle("Profit & Loss Report")
            self.btn_refresh.setText("Refresh")
            self.btn_export.setText("Export CSV")
            self.btn_close.setText("Close")
            self.tabs.setTabText(0, "Summary")
            self.tabs.setTabText(1, "Monthly Breakdown")
            self.tabs.setTabText(2, "Category Analysis")
            self.tabs.setTabText(3, "Top Products")

    def get_date_range(self):
        return (
            self.from_date.date().toString("yyyy-MM-dd"),
            self.to_date.date().toString("yyyy-MM-dd")
        )

    def on_report_type_changed(self):
        today = QDate.currentDate()
        report_type = self.report_type.currentText()
        
        if report_type == "Monthly":
            self.from_date.setDate(QDate(today.year(), today.month(), 1))
            self.to_date.setDate(today)
        elif report_type == "Quarterly":
            quarter = (today.month() - 1) // 3
            quarter_start = quarter * 3 + 1
            self.from_date.setDate(QDate(today.year(), quarter_start, 1))
            self.to_date.setDate(today)
        elif report_type == "Yearly":
            self.from_date.setDate(QDate(today.year(), 1, 1))
            self.to_date.setDate(today)
        self.load_report()

    def load_report(self):
        from_date, to_date = self.get_date_range()
        symbol = get_currency_symbol()

        conn = connect_db()
        cursor = conn.cursor()

        # Total Sales
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) FROM sales
            WHERE status = 'completed' AND date(created_at) BETWEEN ? AND ?
        """, (from_date, to_date))
        total_sales = cursor.fetchone()[0]

        # COGS
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

        # Expenses
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses
            WHERE expense_date BETWEEN ? AND ?
        """, (from_date, to_date))
        total_expenses = cursor.fetchone()[0]

        # Calculate profits
        gross_profit = total_sales - total_cogs
        net_profit = gross_profit - total_expenses
        net_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0

        # Update cards
        self.update_card_amount(self.sales_card, format_money(total_sales, symbol))
        self.update_card_amount(self.cogs_card, format_money(total_cogs, symbol))
        self.update_card_amount(self.gross_card, format_money(gross_profit, symbol))
        self.update_card_amount(self.expenses_card, format_money(total_expenses, symbol))
        self.update_card_amount(self.net_card, format_money(net_profit, symbol))
        self.update_card_amount(self.margin_card, f"{net_margin:.1f}%")

        # Color coding for net profit
        if net_profit >= 0:
            self.find_child_amount_label(self.net_card).setStyleSheet("color: #2ecc71; font-size: 18pt; font-weight: bold;")
        else:
            self.find_child_amount_label(self.net_card).setStyleSheet("color: #e74c3c; font-size: 18pt; font-weight: bold;")

        # Load tabs
        self.load_summary_tab(from_date, to_date)
        self.load_monthly_tab(from_date, to_date)
        self.load_category_tab(from_date, to_date)
        self.load_products_tab(from_date, to_date)

        conn.close()

    def update_card_amount(self, card, amount):
        for child in card.findChildren(QLabel):
            if child.objectName() == "amount_label":
                child.setText(amount)
                break

    def find_child_amount_label(self, card):
        for child in card.findChildren(QLabel):
            if child.objectName() == "amount_label":
                return child
        return None

    def create_summary_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Summary table
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(4)
        self.summary_table.setHorizontalHeaderLabels(["Metric", "Amount", "Percentage of Sales", "Trend"])
        self.summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.summary_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.summary_table)
        
        widget.setLayout(layout)
        return widget

    def load_summary_tab(self, from_date, to_date):
        symbol = get_currency_symbol()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Convert QDate to Python date for calculation
        from_qdate = QDate.fromString(from_date, "yyyy-MM-dd")
        to_qdate = QDate.fromString(to_date, "yyyy-MM-dd")
        
        # Calculate date range in days
        date_range = from_qdate.daysTo(to_qdate)
        
        # Previous period dates
        prev_from = from_qdate.addDays(-date_range - 1).toString("yyyy-MM-dd")
        prev_to = from_qdate.addDays(-1).toString("yyyy-MM-dd")
        
        # Current period data
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) FROM sales
            WHERE status = 'completed' AND date(created_at) BETWEEN ? AND ?
        """, (from_date, to_date))
        current_sales = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(products.cost * sale_items.qty), 0)
            FROM sale_items
            JOIN sales ON sale_items.sale_id = sales.id
            JOIN products ON sale_items.product_name = products.name
            WHERE sales.status = 'completed' AND date(sales.created_at) BETWEEN ? AND ?
        """, (from_date, to_date))
        current_cogs = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses
            WHERE expense_date BETWEEN ? AND ?
        """, (from_date, to_date))
        current_expenses = cursor.fetchone()[0]
        
        # Previous period data
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) FROM sales
            WHERE status = 'completed' AND date(created_at) BETWEEN ? AND ?
        """, (prev_from, prev_to))
        prev_sales = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(products.cost * sale_items.qty), 0)
            FROM sale_items
            JOIN sales ON sale_items.sale_id = sales.id
            JOIN products ON sale_items.product_name = products.name
            WHERE sales.status = 'completed' AND date(sales.created_at) BETWEEN ? AND ?
        """, (prev_from, prev_to))
        prev_cogs = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses
            WHERE expense_date BETWEEN ? AND ?
        """, (prev_from, prev_to))
        prev_expenses = cursor.fetchone()[0]
        
        conn.close()
        
        current_gross = current_sales - current_cogs
        current_net = current_gross - current_expenses
        
        prev_gross = prev_sales - prev_cogs
        prev_net = prev_gross - prev_expenses
        
        metrics = [
            ("Total Sales", current_sales, prev_sales, 100),
            ("Cost of Goods Sold", current_cogs, prev_cogs, (current_cogs/current_sales*100) if current_sales > 0 else 0),
            ("Gross Profit", current_gross, prev_gross, (current_gross/current_sales*100) if current_sales > 0 else 0),
            ("Operating Expenses", current_expenses, prev_expenses, (current_expenses/current_sales*100) if current_sales > 0 else 0),
            ("Net Profit", current_net, prev_net, (current_net/current_sales*100) if current_sales > 0 else 0),
        ]
        
        self.summary_table.setRowCount(len(metrics))
        for i, (name, current, prev, percent) in enumerate(metrics):
            self.summary_table.setItem(i, 0, QTableWidgetItem(name))
            self.summary_table.setItem(i, 1, QTableWidgetItem(format_money(current, symbol)))
            self.summary_table.setItem(i, 2, QTableWidgetItem(f"{percent:.1f}%"))
            
            # Trend indicator
            if prev > 0:
                change = ((current - prev) / prev) * 100
                if change > 0:
                    trend = f"↑ +{change:.1f}%"
                    trend_color = QColor(46, 204, 113)
                elif change < 0:
                    trend = f"↓ {change:.1f}%"
                    trend_color = QColor(231, 76, 60)
                else:
                    trend = "→ 0%"
                    trend_color = QColor(128, 128, 128)
            else:
                trend = "N/A"
                trend_color = QColor(128, 128, 128)
            
            trend_item = QTableWidgetItem(trend)
            trend_item.setForeground(trend_color)
            self.summary_table.setItem(i, 3, trend_item)

    def create_monthly_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(7)
        self.monthly_table.setHorizontalHeaderLabels(["Month", "Sales", "COGS", "Gross Profit", "Expenses", "Net Profit", "Margin %"])
        self.monthly_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.monthly_table.horizontalHeader()
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.monthly_table)
        
        widget.setLayout(layout)
        return widget

    def load_monthly_tab(self, from_date, to_date):
        symbol = get_currency_symbol()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', s.created_at) as month,
                COALESCE(SUM(s.total), 0) as sales,
                COALESCE(SUM(p.cost * si.qty), 0) as cogs,
                COALESCE(SUM(e.amount), 0) as expenses
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            LEFT JOIN products p ON si.product_name = p.name
            LEFT JOIN expenses e ON strftime('%Y-%m', e.expense_date) = strftime('%Y-%m', s.created_at)
            WHERE s.status = 'completed' 
              AND date(s.created_at) BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m', s.created_at)
            ORDER BY month
        """, (from_date, to_date))
        rows = cursor.fetchall()
        conn.close()
        
        self.monthly_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            month, sales, cogs, expenses = row
            gross = sales - cogs
            net = gross - expenses
            margin = (net / sales * 100) if sales > 0 else 0
            
            self.monthly_table.setItem(i, 0, QTableWidgetItem(month))
            self.monthly_table.setItem(i, 1, QTableWidgetItem(format_money(sales, symbol)))
            self.monthly_table.setItem(i, 2, QTableWidgetItem(format_money(cogs, symbol)))
            
            gross_item = QTableWidgetItem(format_money(gross, symbol))
            gross_item.setForeground(QColor(46, 204, 113) if gross >= 0 else QColor(231, 76, 60))
            self.monthly_table.setItem(i, 3, gross_item)
            
            self.monthly_table.setItem(i, 4, QTableWidgetItem(format_money(expenses, symbol)))
            
            net_item = QTableWidgetItem(format_money(net, symbol))
            net_item.setForeground(QColor(46, 204, 113) if net >= 0 else QColor(231, 76, 60))
            self.monthly_table.setItem(i, 5, net_item)
            
            margin_item = QTableWidgetItem(f"{margin:.1f}%")
            if margin >= 20:
                margin_item.setForeground(QColor(46, 204, 113))
            elif margin >= 10:
                margin_item.setForeground(QColor(241, 196, 15))
            elif margin >= 0:
                margin_item.setForeground(QColor(230, 126, 34))
            else:
                margin_item.setForeground(QColor(231, 76, 60))
            self.monthly_table.setItem(i, 6, margin_item)

    def create_category_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(5)
        self.category_table.setHorizontalHeaderLabels(["Category", "Sales", "COGS", "Gross Profit", "Margin %"])
        self.category_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.category_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.category_table)
        
        widget.setLayout(layout)
        return widget

    def load_category_tab(self, from_date, to_date):
        symbol = get_currency_symbol()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COALESCE(p.category, 'Uncategorized') as category,
                COALESCE(SUM(si.total), 0) as sales,
                COALESCE(SUM(p.cost * si.qty), 0) as cogs
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            LEFT JOIN products p ON si.product_name = p.name
            WHERE s.status = 'completed' AND date(s.created_at) BETWEEN ? AND ?
            GROUP BY p.category
            ORDER BY sales DESC
        """, (from_date, to_date))
        rows = cursor.fetchall()
        conn.close()
        
        self.category_table.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            category, sales, cogs = row
            gross = sales - cogs
            margin = (gross / sales * 100) if sales > 0 else 0
            
            self.category_table.setItem(i, 0, QTableWidgetItem(category or "Uncategorized"))
            self.category_table.setItem(i, 1, QTableWidgetItem(format_money(sales, symbol)))
            self.category_table.setItem(i, 2, QTableWidgetItem(format_money(cogs, symbol)))
            
            gross_item = QTableWidgetItem(format_money(gross, symbol))
            self.category_table.setItem(i, 3, gross_item)
            
            margin_item = QTableWidgetItem(f"{margin:.1f}%")
            if margin > 30:
                margin_item.setForeground(QColor(46, 204, 113))
            elif margin > 15:
                margin_item.setForeground(QColor(241, 196, 15))
            else:
                margin_item.setForeground(QColor(230, 126, 34))
            self.category_table.setItem(i, 4, margin_item)

    def create_products_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(["Product", "Quantity Sold", "Sales", "COGS", "Gross Profit", "Margin %"])
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.products_table)
        
        widget.setLayout(layout)
        return widget

    def load_products_tab(self, from_date, to_date):
        symbol = get_currency_symbol()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                si.product_name,
                COALESCE(SUM(si.qty), 0) as qty,
                COALESCE(SUM(si.total), 0) as sales,
                COALESCE(SUM(p.cost * si.qty), 0) as cogs
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            LEFT JOIN products p ON si.product_name = p.name
            WHERE s.status = 'completed' AND date(s.created_at) BETWEEN ? AND ?
            GROUP BY si.product_name
            ORDER BY sales DESC
            LIMIT 20
        """, (from_date, to_date))
        rows = cursor.fetchall()
        conn.close()
        
        self.products_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            product, qty, sales, cogs = row
            gross = sales - cogs
            margin = (gross / sales * 100) if sales > 0 else 0
            
            self.products_table.setItem(i, 0, QTableWidgetItem(product))
            self.products_table.setItem(i, 1, QTableWidgetItem(str(int(qty))))
            self.products_table.setItem(i, 2, QTableWidgetItem(format_money(sales, symbol)))
            self.products_table.setItem(i, 3, QTableWidgetItem(format_money(cogs, symbol)))
            
            gross_item = QTableWidgetItem(format_money(gross, symbol))
            if gross >= 0:
                gross_item.setForeground(QColor(46, 204, 113))
            else:
                gross_item.setForeground(QColor(231, 76, 60))
            self.products_table.setItem(i, 4, gross_item)
            
            margin_item = QTableWidgetItem(f"{margin:.1f}%")
            if margin > 30:
                margin_item.setForeground(QColor(46, 204, 113))
            elif margin > 15:
                margin_item.setForeground(QColor(241, 196, 15))
            else:
                margin_item.setForeground(QColor(230, 126, 34))
            self.products_table.setItem(i, 5, margin_item)

    def export_report(self):
        from_date, to_date = self.get_date_range()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Profit Report", f"profit_report_{from_date}_to_{to_date}.csv", "CSV Files (*.csv)"
        )
        if not file_path:
            return
        
        symbol = get_currency_symbol()
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', s.created_at) as month,
                COALESCE(SUM(s.total), 0) as sales,
                COALESCE(SUM(p.cost * si.qty), 0) as cogs,
                COALESCE(SUM(e.amount), 0) as expenses
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            LEFT JOIN products p ON si.product_name = p.name
            LEFT JOIN expenses e ON strftime('%Y-%m', e.expense_date) = strftime('%Y-%m', s.created_at)
            WHERE s.status = 'completed' 
              AND date(s.created_at) BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m', s.created_at)
            ORDER BY month
        """, (from_date, to_date))
        rows = cursor.fetchall()
        conn.close()
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Month", "Sales", "COGS", "Gross Profit", "Expenses", "Net Profit", "Margin %"])
                for row in rows:
                    month, sales, cogs, expenses = row
                    gross = sales - cogs
                    net = gross - expenses
                    margin = (net / sales * 100) if sales > 0 else 0
                    writer.writerow([month, sales, cogs, gross, expenses, net, f"{margin:.1f}%"])
            QMessageBox.information(self, "Success", f"Report exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")

    def showEvent(self, event):
        self.apply_card_style()
        super().showEvent(event)