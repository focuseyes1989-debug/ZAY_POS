# ui/dashboard/dashboard_page.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QMessageBox
from PyQt6.QtCore import Qt, QDate, QTimer
from models.database import connect_db
from utils.currency import format_money
from utils.language import lang
from ui.dashboard.dashboard_cards import DashboardCards, BackupStatusCard
from ui.dashboard.dashboard_filters import DashboardFilters
from ui.dashboard.dashboard_export import DashboardExport
from ui.dashboard.dashboard_dialogs import DiscountedSalesDialog, RefundedSalesDialog
from ui.dashboard.dashboard_backup import DashboardBackupStatus
from loguru import logger


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
        
        # ============================================================
        # ✅ ROW 1: TODAY CARDS (5 cards in one row)
        # ============================================================
        today_layout = QHBoxLayout()
        today_layout.setSpacing(15)
        
        # 1. Today's Sales Card
        self.today_sales_card = DashboardCards.create_card("Today's Sales", "0")
        self.today_sales_card.clicked = lambda: self.show_today_sales_detail()
        today_layout.addWidget(self.today_sales_card, 1)
        
        # 2. Today's Expense Card
        self.today_expense_card = DashboardCards.create_card("Today's Expense", "0")
        today_layout.addWidget(self.today_expense_card, 1)
        
        # 3. Today's Profit Card
        self.today_profit_card = DashboardCards.create_card("Today's Profit", "0")
        today_layout.addWidget(self.today_profit_card, 1)
        
        # 4. Today Refunds Card (Clickable - goes to Refunded Tab)
        self.today_refunds_card = DashboardCards.create_clickable_card("Today Refunds", "0")
        self.today_refunds_card.clicked.connect(self.go_to_refunded_tab)
        today_layout.addWidget(self.today_refunds_card, 1)
        
        # 5. Today Discount Card (Clickable - goes to Discounted Tab)
        self.today_discount_card = DashboardCards.create_clickable_card("Today Discount", "0")
        self.today_discount_card.clicked.connect(self.go_to_discounted_tab)
        today_layout.addWidget(self.today_discount_card, 1)
        
        main_layout.addLayout(today_layout)
        
        # ============================================================
        # ✅ ROW 2: OTHER CARDS (Outstanding Credit, Low Stock Count, etc.)
        # ============================================================
        other_layout = QHBoxLayout()
        other_layout.setSpacing(15)
        
        # 1. Outstanding Credit Card
        self.outstanding_card = DashboardCards.create_clickable_card("Outstanding Credit", "0")
        self.outstanding_card.clicked.connect(self.go_to_outstanding_report)
        other_layout.addWidget(self.outstanding_card, 1)
        
        # 2. Low Stock Count Card
        self.low_stock_card = DashboardCards.create_clickable_card("Low Stock Count", "0")
        self.low_stock_card.clicked.connect(self.go_to_low_stock_tab)
        other_layout.addWidget(self.low_stock_card, 1)
        
        # 3. Gross Sales Card
        self.gross_sales_card = DashboardCards.create_card("Gross Sales", "0")
        other_layout.addWidget(self.gross_sales_card, 1)
        
        # 4. Net Sales Card
        self.net_sales_card = DashboardCards.create_card("Net Sales", "0")
        other_layout.addWidget(self.net_sales_card, 1)
        
        # 5. Gross Profit Card
        self.gross_profit_card = DashboardCards.create_card("Gross Profit", "0")
        other_layout.addWidget(self.gross_profit_card, 1)
        
        main_layout.addLayout(other_layout)
        
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
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)
        
        self.setLayout(main_layout)
    
    # ============================================================
    # ✅ HELPER: Update card with consistent styling
    # ============================================================
    
    def _update_card_value(self, card, value, symbol=None, color=None):
        """Update card value with consistent styling"""
        if card and hasattr(card, 'value_label'):
            # Format value
            if symbol:
                formatted_value = format_money(value, symbol)
            elif isinstance(value, int):
                formatted_value = str(value)
            else:
                formatted_value = format_money(value)
            
            card.value_label.setText(formatted_value)
            
            # Apply color if specified, otherwise use default
            if color:
                card.value_label.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {color};")
            else:
                card.value_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: palette(windowText);")
    
    # ============================================================
    # ✅ NAVIGATION METHODS
    # ============================================================
    
    def go_to_refunded_tab(self):
        """Navigate to Refunded Tab in Receipts Page"""
        main_window = self.window()
        
        if hasattr(main_window, 'switch_to_page'):
            main_window.switch_to_page(4)  # Receipts page
        
        QTimer.singleShot(150, lambda: self._switch_to_refunded_tab(main_window))
    
    def _switch_to_refunded_tab(self, main_window):
        """Switch to refunded tab after receipts page loads"""
        try:
            if hasattr(main_window, 'receipts_page'):
                receipts_page = main_window.receipts_page
                if hasattr(receipts_page, 'tab_widget'):
                    receipts_page.tab_widget.setCurrentIndex(1)
                    if hasattr(receipts_page, 'refund_tab'):
                        receipts_page.refund_tab.load_refunded_sales()
                        logger.info("Refunded tab loaded")
        except Exception as e:
            logger.error(f"Error switching to refunded tab: {e}")

    def go_to_discounted_tab(self):
        """Navigate to Discounted Tab in Receipts Page"""
        main_window = self.window()
        
        if hasattr(main_window, 'switch_to_page'):
            main_window.switch_to_page(4)  # Receipts page
        
        QTimer.singleShot(150, lambda: self._switch_to_discounted_tab(main_window))
    
    def _switch_to_discounted_tab(self, main_window):
        """Switch to discounted tab after receipts page loads"""
        try:
            if hasattr(main_window, 'receipts_page'):
                receipts_page = main_window.receipts_page
                if hasattr(receipts_page, 'tab_widget'):
                    receipts_page.tab_widget.setCurrentIndex(2)
                    if hasattr(receipts_page, 'discount_tab'):
                        receipts_page.discount_tab.load_discounted_receipts()
                        logger.info("Discounted tab loaded")
        except Exception as e:
            logger.error(f"Error switching to discounted tab: {e}")
    
    def show_today_sales_detail(self):
        """Show today's sales detail dialog"""
        today = QDate.currentDate().toString("yyyy-MM-dd")
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
                main_window.switch_to_page(3)  # Inventory page
                if hasattr(main_window.inventory_page, 'tabs'):
                    main_window.inventory_page.tabs.setCurrentIndex(1)  # Low stock tab
    
    def on_table_double_click(self, row, column):
        """Handle double click on table row - show daily detail"""
        date_item = self.table.item(row, 0)
        if date_item:
            from_date = date_item.text()
            to_date = from_date
            QMessageBox.information(self, "Daily Detail", f"Details for {from_date}")
    
    def update_kpi_cards(self):
        """Update KPI cards with today's data - consistent styling"""
        today = QDate.currentDate().toString("yyyy-MM-dd")
        symbol = self.filters.get_currency_symbol()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # 1. Today's Sales - Green
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) FROM sales 
            WHERE status = 'completed' AND date(created_at) = ?
        """, (today,))
        today_sales = cursor.fetchone()[0]
        self._update_card_value(self.today_sales_card, today_sales, symbol, "#2ecc71")
        
        # 2. Today's Expense - Red
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses 
            WHERE expense_date = ?
        """, (today,))
        today_expense = cursor.fetchone()[0]
        self._update_card_value(self.today_expense_card, today_expense, symbol, "#e74c3c")
        
        # 3. Today's Profit - Green if positive, Red if negative
        today_profit = today_sales - today_expense
        profit_color = "#2ecc71" if today_profit >= 0 else "#e74c3c"
        self._update_card_value(self.today_profit_card, today_profit, symbol, profit_color)
        
        # 4. Today Refunds - Red if > 0, Green if 0
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) FROM sales 
            WHERE status = 'refunded' AND date(created_at) = ?
        """, (today,))
        today_refunds = cursor.fetchone()[0]
        refunds_color = "#e74c3c" if today_refunds > 0 else "#2ecc71"
        self._update_card_value(self.today_refunds_card, today_refunds, symbol, refunds_color)
        
        # 5. Today Discount - Orange if > 0, Green if 0
        cursor.execute("""
            SELECT COALESCE(SUM(discount_amount), 0) FROM sales 
            WHERE status = 'completed' AND discount_amount > 0 AND date(created_at) = ?
        """, (today,))
        today_discount = cursor.fetchone()[0]
        discount_color = "#e67e22" if today_discount > 0 else "#2ecc71"
        self._update_card_value(self.today_discount_card, today_discount, symbol, discount_color)
        
        conn.close()
    
    def update_financial_cards(self, from_date, to_date):
        """Update financial summary cards - consistent styling"""
        symbol = self.filters.get_currency_symbol()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # 1. Outstanding Credit - Red if > 0, Green if 0
        cursor.execute("""
            SELECT COALESCE(SUM(balance_amount), 0) FROM credit_sales 
            WHERE status != 'paid' AND balance_amount > 0
        """)
        outstanding = cursor.fetchone()[0]
        outstanding_color = "#e74c3c" if outstanding > 0 else "#2ecc71"
        self._update_card_value(self.outstanding_card, outstanding, symbol, outstanding_color)
        
        # 2. Low Stock Count - Orange if > 0, Green if 0
        cursor.execute("""
            SELECT COUNT(*) FROM products 
            WHERE (sold_by IS NULL OR sold_by != 'Service') 
              AND stock > 0 AND stock <= low_stock
        """)
        low_stock_count = cursor.fetchone()[0]
        # ✅ Stock count - no currency symbol, just number
        stock_color = "#e67e22" if low_stock_count > 0 else "#2ecc71"
        self._update_card_value(self.low_stock_card, low_stock_count, None, stock_color)
        
        # 3. Gross Sales - Blue
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE status='completed' AND date(created_at) BETWEEN ? AND ?", (from_date, to_date))
        gross_sales = cursor.fetchone()[0]
        self._update_card_value(self.gross_sales_card, gross_sales, symbol, "#3498db")
        
        # 4. Net Sales - Blue
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE status='refunded' AND date(created_at) BETWEEN ? AND ?", (from_date, to_date))
        refunds = cursor.fetchone()[0]
        net_sales = gross_sales - refunds
        self._update_card_value(self.net_sales_card, net_sales, symbol, "#3498db")
        
        # 5. Gross Profit - Green if positive, Red if negative
        cursor.execute("""
            SELECT COALESCE(SUM(products.cost * sale_items.qty), 0)
            FROM sale_items
            JOIN products ON sale_items.product_name = products.name
            JOIN sales ON sale_items.sale_id = sales.id
            WHERE sales.status='completed' AND date(sales.created_at) BETWEEN ? AND ?
        """, (from_date, to_date))
        cogs = cursor.fetchone()[0]
        gross_profit = net_sales - cogs
        profit_color = "#2ecc71" if gross_profit >= 0 else "#e74c3c"
        self._update_card_value(self.gross_profit_card, gross_profit, symbol, profit_color)
        
        conn.close()
    
    def refresh_dashboard(self):
        from_date, to_date = self.filters.get_date_range()
        
        # Update KPI cards (today's data)
        self.update_kpi_cards()
        
        # Update financial summary cards (period data)
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
        symbol = self.filters.get_currency_symbol()
        
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
            self.table.setItem(r, 1, QTableWidgetItem(format_money(daily_gross, symbol)))
            self.table.setItem(r, 2, QTableWidgetItem(format_money(daily_net, symbol)))
            self.table.setItem(r, 3, QTableWidgetItem(format_money(daily_profit, symbol)))
            self.table.setItem(r, 4, QTableWidgetItem(format_money(daily_refunds, symbol)))
            self.table.setItem(r, 5, QTableWidgetItem(format_money(daily_discount, symbol)))
        
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
        
        # ============================================================
        # ✅ UPDATE ALL CARD TITLES
        # ============================================================
        if lang_code == "my":
            # Row 1: Today Cards
            self.today_sales_card.title_label.setText("ယနေ့ရောင်းအား")
            self.today_expense_card.title_label.setText("ယနေ့အသုံးစရိတ်")
            self.today_profit_card.title_label.setText("ယနေ့အမြတ်")
            self.today_refunds_card.title_label.setText("ယနေ့ပြန်အမ်းငွေ")
            self.today_discount_card.title_label.setText("ယနေ့လျှော့စျေး")
            
            # Row 2: Other Cards
            self.outstanding_card.title_label.setText("ကျန်အကြွေး")
            self.low_stock_card.title_label.setText("စတော့နည်းနေသောပစ္စည်း")
            self.gross_sales_card.title_label.setText("စုစုပေါင်းရောင်းအား")
            self.net_sales_card.title_label.setText("အသားတင်ရောင်းအား")
            self.gross_profit_card.title_label.setText("အသားတင်အမြတ်")
            self.backup_card.title_label.setText("Database Backup")
            
            headers = ["ရက်စွဲ", "စုစုပေါင်းရောင်းအား", "အသားတင်ရောင်းအား",
                       "အသားတင်အမြတ်", "ပြန်အမ်းငွေများ", "လျှော့စျေး"]
        else:
            # Row 1: Today Cards
            self.today_sales_card.title_label.setText("Today's Sales")
            self.today_expense_card.title_label.setText("Today's Expense")
            self.today_profit_card.title_label.setText("Today's Profit")
            self.today_refunds_card.title_label.setText("Today Refunds")
            self.today_discount_card.title_label.setText("Today Discount")
            
            # Row 2: Other Cards
            self.outstanding_card.title_label.setText("Outstanding Credit")
            self.low_stock_card.title_label.setText("Low Stock Count")
            self.gross_sales_card.title_label.setText("Gross Sales")
            self.net_sales_card.title_label.setText("Net Sales")
            self.gross_profit_card.title_label.setText("Gross Profit")
            self.backup_card.title_label.setText("Database Backup")
            
            headers = ["Date", "Gross Sales", "Net Sales", "Gross Profit", "Refunds", "Discount"]
        
        for col, text in enumerate(headers):
            self.table.setHorizontalHeaderItem(col, QTableWidgetItem(text))
        
        # Refresh to update colors
        self.update_kpi_cards()
        self.update_financial_cards(
            self.filters.from_date.date().toString("yyyy-MM-dd"),
            self.filters.to_date.date().toString("yyyy-MM-dd")
        )
    
    def showEvent(self, event):
        self.refresh_dashboard()
        super().showEvent(event)