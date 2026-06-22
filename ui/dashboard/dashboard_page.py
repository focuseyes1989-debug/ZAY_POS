# ui/dashboard/dashboard_page.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt6.QtCore import Qt, QDate
from models.database import connect_db
from utils.currency import format_money
from utils.language import lang
from ui.dashboard.dashboard_cards import DashboardCards, BackupStatusCard
from ui.dashboard.dashboard_filters import DashboardFilters
from ui.dashboard.dashboard_export import DashboardExport
from ui.dashboard.dashboard_dialogs import DiscountedSalesDialog, RefundedSalesDialog
from ui.dashboard.dashboard_backup import DashboardBackupStatus


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        lang.language_changed.connect(self.retranslateUi)
        self.refresh_dashboard()
        self.retranslateUi()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Filters
        self.filters = DashboardFilters(self)
        self.filters.filter_changed.connect(self.refresh_dashboard)
        main_layout.addWidget(self.filters)
        
        # ========== KPI CARDS (5 cards in one row) ==========
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)
        
        # 1. Today's Sales Card
        self.today_sales_card = DashboardCards.create_card("Today's Sales", "0")
        self.today_sales_card.clicked = lambda: self.show_today_sales_detail()
        kpi_layout.addWidget(self.today_sales_card, 1)
        
        # 2. Today's Expense Card
        self.today_expense_card = DashboardCards.create_card("Today's Expense", "0")
        kpi_layout.addWidget(self.today_expense_card, 1)
        
        # 3. Today's Profit Card
        self.today_profit_card = DashboardCards.create_card("Today's Profit", "0")
        kpi_layout.addWidget(self.today_profit_card, 1)
        
        # 4. Outstanding Credit Card
        self.outstanding_card = DashboardCards.create_clickable_card("Outstanding Credit", "0")
        self.outstanding_card.clicked.connect(self.go_to_outstanding_report)
        kpi_layout.addWidget(self.outstanding_card, 1)
        
        # 5. Low Stock Count Card
        self.low_stock_card = DashboardCards.create_clickable_card("Low Stock Count", "0")
        self.low_stock_card.clicked.connect(self.go_to_low_stock_tab)
        kpi_layout.addWidget(self.low_stock_card, 1)
        
        main_layout.addLayout(kpi_layout)
        
        # ========== FINANCIAL SUMMARY CARDS (Optional - can be hidden) ==========
        # These are additional cards for detailed financial info
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(15)
        
        self.gross_sales_card = DashboardCards.create_card("Gross Sales", "0")
        summary_layout.addWidget(self.gross_sales_card, 1)
        
        self.net_sales_card = DashboardCards.create_card("Net Sales", "0")
        summary_layout.addWidget(self.net_sales_card, 1)
        
        self.gross_profit_card = DashboardCards.create_card("Gross Profit", "0")
        summary_layout.addWidget(self.gross_profit_card, 1)
        
        self.refunds_card = DashboardCards.create_card("Refunds", "0")
        summary_layout.addWidget(self.refunds_card, 1)
        
        self.discount_card = DashboardCards.create_card("Discount", "0")
        summary_layout.addWidget(self.discount_card, 1)
        
        main_layout.addLayout(summary_layout)
        
        # Backup status card
        backup_layout = QHBoxLayout()
        backup_layout.setSpacing(15)
        
        self.backup_card = BackupStatusCard.create(self)
        self.backup_card.mousePressEvent = self.open_backup_settings
        
        backup_layout.addWidget(self.backup_card, 1)
        backup_layout.addStretch()
        
        main_layout.addLayout(backup_layout)
        
        # Daily summary table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Gross Sales", "Net Sales", "Gross Profit", "Refunds", "Discount"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)
        
        self.setLayout(main_layout)
    
    def show_today_sales_detail(self):
        """Show today's sales detail dialog"""
        today = QDate.currentDate().toString("yyyy-MM-dd")
        from ui.receipts_page import ReceiptsPage
        # Create a simple dialog to show today's sales
        QMessageBox.information(self, "Today's Sales", f"Today's sales details will be shown here")
    
    def go_to_outstanding_report(self):
        """Go to outstanding credit report"""
        main_window = self.window()
        if hasattr(main_window, 'open_outstanding_report'):
            main_window.open_outstanding_report()
    
    def go_to_low_stock_tab(self):
        """Go to low stock tab in inventory"""
        main_window = self.window()
        if hasattr(main_window, 'inventory_page') and main_window.inventory_page:
            if hasattr(main_window, 'switch_to_page'):
                main_window.switch_to_page(3)
                if hasattr(main_window.inventory_page, 'tabs'):
                    main_window.inventory_page.tabs.setCurrentIndex(1)
    
    def update_kpi_cards(self):
        """Update KPI cards with today's data"""
        today = QDate.currentDate().toString("yyyy-MM-dd")
        symbol = self.filters.get_currency_symbol()
        lang_code = self.get_lang()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # 1. Today's Sales
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) FROM sales 
            WHERE status = 'completed' AND date(created_at) = ?
        """, (today,))
        today_sales = cursor.fetchone()[0]
        DashboardCards.update_card(self.today_sales_card, today_sales)
        
        # 2. Today's Expense
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses 
            WHERE expense_date = ?
        """, (today,))
        today_expense = cursor.fetchone()[0]
        DashboardCards.update_card(self.today_expense_card, today_expense)
        
        # 3. Today's Profit (Sales - Expense)
        today_profit = today_sales - today_expense
        profit_card = self.today_profit_card
        if hasattr(profit_card, 'value_label'):
            profit_card.value_label.setText(format_money(today_profit, symbol))
            if today_profit >= 0:
                profit_card.value_label.setStyleSheet("color: #2ecc71; font-size: 18pt; font-weight: bold;")
            else:
                profit_card.value_label.setStyleSheet("color: #e74c3c; font-size: 18pt; font-weight: bold;")
        
        # 4. Outstanding Credit (Total balance from credit_sales)
        cursor.execute("""
            SELECT COALESCE(SUM(balance_amount), 0) FROM credit_sales 
            WHERE status != 'paid' AND balance_amount > 0
        """)
        outstanding = cursor.fetchone()[0]
        outstanding_card = self.outstanding_card
        if hasattr(outstanding_card, 'value_label'):
            outstanding_card.value_label.setText(format_money(outstanding, symbol))
            if outstanding > 0:
                outstanding_card.value_label.setStyleSheet("color: #e74c3c; font-size: 18pt; font-weight: bold;")
        
        # 5. Low Stock Count
        cursor.execute("""
            SELECT COUNT(*) FROM products 
            WHERE (sold_by IS NULL OR sold_by != 'Service') 
              AND stock > 0 AND stock <= low_stock
        """)
        low_stock_count = cursor.fetchone()[0]
        low_stock_card = self.low_stock_card
        if hasattr(low_stock_card, 'value_label'):
            low_stock_card.value_label.setText(str(low_stock_count))
            if low_stock_count > 0:
                low_stock_card.value_label.setStyleSheet("color: #e67e22; font-size: 18pt; font-weight: bold;")
        
        conn.close()
    
    def update_financial_cards(self, from_date, to_date):
        """Update financial summary cards"""
        symbol = self.filters.get_currency_symbol()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Gross Sales
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE status='completed' AND date(created_at) BETWEEN ? AND ?", (from_date, to_date))
        gross_sales = cursor.fetchone()[0]
        
        # Refunds
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE status='refunded' AND date(created_at) BETWEEN ? AND ?", (from_date, to_date))
        refunds = cursor.fetchone()[0]
        
        net_sales = gross_sales - refunds
        
        # Discount
        cursor.execute("SELECT COALESCE(SUM(discount_amount), 0) FROM sales WHERE status='completed' AND date(created_at) BETWEEN ? AND ?", (from_date, to_date))
        discount_total = cursor.fetchone()[0]
        
        # COGS
        cursor.execute("""
            SELECT COALESCE(SUM(products.cost * sale_items.qty), 0)
            FROM sale_items
            JOIN products ON sale_items.product_name = products.name
            JOIN sales ON sale_items.sale_id = sales.id
            WHERE sales.status='completed' AND date(sales.created_at) BETWEEN ? AND ?
        """, (from_date, to_date))
        cogs = cursor.fetchone()[0]
        
        gross_profit = net_sales - cogs
        
        conn.close()
        
        DashboardCards.update_card(self.gross_sales_card, gross_sales)
        DashboardCards.update_card(self.net_sales_card, net_sales)
        DashboardCards.update_card(self.gross_profit_card, gross_profit)
        DashboardCards.update_card(self.refunds_card, refunds)
        DashboardCards.update_card(self.discount_card, discount_total)
    
    def refresh_dashboard(self):
        from_date, to_date = self.filters.get_date_range()
        
        # Update KPI cards (today's data)
        self.update_kpi_cards()
        
        # Update financial summary cards
        self.update_financial_cards(from_date, to_date)
        
        # Update backup status
        self.update_backup_status()
        
        # Daily summary table
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT date(created_at) as sale_date,
                   COALESCE(SUM(total), 0) as daily_gross,
                   COALESCE(SUM(CASE WHEN status='refunded' THEN total ELSE 0 END), 0) as daily_refunds,
                   COALESCE(SUM(CASE WHEN status='completed' THEN discount_amount ELSE 0 END), 0) as daily_discount
            FROM sales
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY date(created_at)
            ORDER BY sale_date DESC
        """, (from_date, to_date))
        rows = cursor.fetchall()
        
        self.table.setRowCount(0)
        for row in rows:
            sale_date, daily_gross, daily_refunds, daily_discount = row
            daily_net = daily_gross - daily_refunds
            cursor.execute("""
                SELECT COALESCE(SUM(products.cost * sale_items.qty), 0)
                FROM sale_items
                JOIN products ON sale_items.product_name = products.name
                JOIN sales ON sale_items.sale_id = sales.id
                WHERE date(sales.created_at) = ? AND sales.status='completed'
            """, (sale_date,))
            daily_cogs = cursor.fetchone()[0]
            daily_profit = daily_net - daily_cogs
            
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(sale_date))
            self.table.setItem(r, 1, QTableWidgetItem(format_money(daily_gross)))
            self.table.setItem(r, 2, QTableWidgetItem(format_money(daily_net)))
            self.table.setItem(r, 3, QTableWidgetItem(format_money(daily_profit)))
            self.table.setItem(r, 4, QTableWidgetItem(format_money(daily_refunds)))
            self.table.setItem(r, 5, QTableWidgetItem(format_money(daily_discount)))
        
        conn.close()
    
    def update_backup_status(self):
        main_window = self.window()
        if hasattr(main_window, 'auto_backup_manager'):
            DashboardBackupStatus.update_backup_status(self, main_window.auto_backup_manager)
    
    def open_backup_settings(self, event):
        main_window = self.window()
        if hasattr(main_window, 'open_auto_backup'):
            main_window.open_auto_backup()
    
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
        lang_code = self.get_lang()
        self.filters.retranslateUi(lang_code)
        
        # Update KPI card titles
        if lang_code == "my":
            self.today_sales_card.title_label.setText("ယနေ့ရောင်းအား")
            self.today_expense_card.title_label.setText("ယနေ့အသုံးစရိတ်")
            self.today_profit_card.title_label.setText("ယနေ့အမြတ်")
            self.outstanding_card.title_label.setText("ကျန်အကြွေး")
            self.low_stock_card.title_label.setText("စတော့နည်းနေသောပစ္စည်း")
            
            self.gross_sales_card.title_label.setText("စုစုပေါင်းရောင်းအား")
            self.net_sales_card.title_label.setText("အသားတင်ရောင်းအား")
            self.gross_profit_card.title_label.setText("အသားတင်အမြတ်")
            self.refunds_card.title_label.setText("ပြန်အမ်းငွေများ")
            self.discount_card.title_label.setText("လျှော့စျေး")
            self.backup_card.title_label.setText("Database Backup")
            
            headers = ["ရက်စွဲ", "စုစုပေါင်းရောင်းအား", "အသားတင်ရောင်းအား",
                       "အသားတင်အမြတ်", "ပြန်အမ်းငွေများ", "လျှော့စျေး"]
        else:
            self.today_sales_card.title_label.setText("Today's Sales")
            self.today_expense_card.title_label.setText("Today's Expense")
            self.today_profit_card.title_label.setText("Today's Profit")
            self.outstanding_card.title_label.setText("Outstanding Credit")
            self.low_stock_card.title_label.setText("Low Stock Count")
            
            self.gross_sales_card.title_label.setText("Gross Sales")
            self.net_sales_card.title_label.setText("Net Sales")
            self.gross_profit_card.title_label.setText("Gross Profit")
            self.refunds_card.title_label.setText("Refunds")
            self.discount_card.title_label.setText("Discount")
            self.backup_card.title_label.setText("Database Backup")
            
            headers = ["Date", "Gross Sales", "Net Sales", "Gross Profit", "Refunds", "Discount"]
        
        for col, text in enumerate(headers):
            self.table.setHorizontalHeaderItem(col, QTableWidgetItem(text))
        
        # Refresh to update colors
        self.update_kpi_cards()
    
    def showEvent(self, event):
        self.refresh_dashboard()
        super().showEvent(event)