from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFrame, QComboBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QColor
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from datetime import datetime


class ExpenseComparisonDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Expense Comparison")
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # ========== COMPARISON TYPE SELECTION ==========
        type_group = QGroupBox("Comparison Type")
        type_layout = QHBoxLayout()

        self.comparison_type = QComboBox()
        self.comparison_type.addItems([
            "Current Month vs Last Month",
            "Current Month vs Same Month Last Year",
            "Custom Period Comparison"
        ])
        self.comparison_type.currentTextChanged.connect(self.on_comparison_type_changed)
        type_layout.addWidget(QLabel("Compare:"))
        type_layout.addWidget(self.comparison_type)
        type_layout.addStretch()

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # ========== CUSTOM PERIOD (initially hidden) ==========
        self.custom_group = QGroupBox("Custom Period")
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Period 1 (Current):"))
        self.period1_from = QDateEdit()
        self.period1_from.setCalendarPopup(True)
        self.period1_from.setDate(QDate.currentDate().addMonths(-1))
        custom_layout.addWidget(self.period1_from)
        custom_layout.addWidget(QLabel("to"))
        self.period1_to = QDateEdit()
        self.period1_to.setCalendarPopup(True)
        self.period1_to.setDate(QDate.currentDate())
        custom_layout.addWidget(self.period1_to)

        custom_layout.addSpacing(30)

        custom_layout.addWidget(QLabel("Period 2 (Previous):"))
        self.period2_from = QDateEdit()
        self.period2_from.setCalendarPopup(True)
        self.period2_from.setDate(QDate.currentDate().addMonths(-2))
        custom_layout.addWidget(self.period2_from)
        custom_layout.addWidget(QLabel("to"))
        self.period2_to = QDateEdit()
        self.period2_to.setCalendarPopup(True)
        self.period2_to.setDate(QDate.currentDate().addMonths(-1).addDays(-1))
        custom_layout.addWidget(self.period2_to)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_custom_comparison)
        custom_layout.addWidget(self.btn_refresh)
        custom_layout.addStretch()

        self.custom_group.setLayout(custom_layout)
        self.custom_group.setVisible(False)
        layout.addWidget(self.custom_group)

        # ========== SUMMARY CARDS (Dynamic Theme Support) ==========
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(15)

        # Get current theme
        self.current_theme = self.get_theme()

        # Current Period Card
        self.current_card = QFrame()
        self.current_card.setObjectName("dashboardCard")
        self.current_card.setFrameStyle(QFrame.Shape.StyledPanel)
        
        current_layout = QVBoxLayout(self.current_card)
        current_layout.setSpacing(5)
        
        self.current_title = QLabel("Current Period")
        self.current_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.current_amount = QLabel("0")
        self.current_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        current_layout.addWidget(self.current_title)
        current_layout.addWidget(self.current_amount)
        summary_layout.addWidget(self.current_card, 1)

        # Previous Period Card
        self.previous_card = QFrame()
        self.previous_card.setObjectName("dashboardCard")
        self.previous_card.setFrameStyle(QFrame.Shape.StyledPanel)
        
        previous_layout = QVBoxLayout(self.previous_card)
        previous_layout.setSpacing(5)
        
        self.previous_title = QLabel("Previous Period")
        self.previous_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.previous_amount = QLabel("0")
        self.previous_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        previous_layout.addWidget(self.previous_title)
        previous_layout.addWidget(self.previous_amount)
        summary_layout.addWidget(self.previous_card, 1)

        # Difference Card
        self.diff_card = QFrame()
        self.diff_card.setObjectName("dashboardCard")
        self.diff_card.setFrameStyle(QFrame.Shape.StyledPanel)
        
        diff_layout = QVBoxLayout(self.diff_card)
        diff_layout.setSpacing(5)
        
        self.diff_title = QLabel("Difference")
        self.diff_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.diff_amount = QLabel("0")
        self.diff_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.diff_percent = QLabel("(0%)")
        self.diff_percent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        diff_layout.addWidget(self.diff_title)
        diff_layout.addWidget(self.diff_amount)
        diff_layout.addWidget(self.diff_percent)
        summary_layout.addWidget(self.diff_card, 1)

        layout.addLayout(summary_layout)

        # ========== COMPARISON TABLE ==========
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Category", "Current Period", "Previous Period", 
            "Difference", "Change %", "Trend"
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        # ========== BEST/WORST CATEGORIES ==========
        best_worst_layout = QHBoxLayout()
        best_worst_layout.setSpacing(15)

        # Best Categories (Most decreased)
        best_group = QGroupBox("Biggest Decreases (Savings)")
        best_layout = QVBoxLayout()
        self.best_table = QTableWidget()
        self.best_table.setColumnCount(3)
        self.best_table.setHorizontalHeaderLabels(["Category", "Change", "Percentage"])
        self.best_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        best_layout.addWidget(self.best_table)
        best_group.setLayout(best_layout)
        best_worst_layout.addWidget(best_group, 1)

        # Worst Categories (Most increased)
        worst_group = QGroupBox("Biggest Increases (Spending)")
        worst_layout = QVBoxLayout()
        self.worst_table = QTableWidget()
        self.worst_table.setColumnCount(3)
        self.worst_table.setHorizontalHeaderLabels(["Category", "Change", "Percentage"])
        self.worst_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        worst_layout.addWidget(self.worst_table)
        worst_group.setLayout(worst_layout)
        best_worst_layout.addWidget(worst_group, 1)

        layout.addLayout(best_worst_layout)

        # ========== BUTTONS ==========
        btn_layout = QHBoxLayout()
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.apply_card_style()
        self.load_month_vs_last_month()
        self.retranslateUi()

    def get_theme(self):
        """Get current theme from settings"""
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
        """Apply dynamic styling based on current theme"""
        self.current_theme = self.get_theme()
        
        if self.current_theme == "Dark":
            # Dark theme styles
            card_style = """
                QFrame#dashboardCard {
                    background-color: #2f3136;
                    border: 1px solid #40444b;
                    border-radius: 12px;
                    padding: 15px;
                }
                QFrame#dashboardCard:hover {
                    background-color: #383a40;
                    border: 1px solid #5865f2;
                }
            """
            title_style = "color: #b9bbbe; font-size: 10pt; font-weight: normal;"
            amount_style = "color: #ffffff; font-size: 20pt; font-weight: bold;"
            table_style = """
                QTableWidget {
                    background-color: #2f3136;
                    alternate-background-color: #36393f;
                    selection-background-color: #40444b;
                    selection-color: #ffffff;
                    gridline-color: #202225;
                    border: 1px solid #202225;
                    border-radius: 6px;
                }
                QHeaderView::section {
                    background-color: #202225;
                    padding: 8px;
                    border: none;
                    font-weight: 600;
                    color: #b9bbbe;
                }
                QTableWidget::item {
                    padding: 6px;
                }
            """
            group_style = """
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #40444b;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px;
                    color: #b9bbbe;
                }
            """
            button_style = """
                QPushButton {
                    background-color: #5865f2;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 25px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #4752c4;
                }
            """
            combo_style = """
                QComboBox {
                    background-color: #40444b;
                    border: 1px solid #202225;
                    border-radius: 4px;
                    padding: 5px 8px;
                    color: #dcddde;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2f3136;
                    border: 1px solid #202225;
                    selection-background-color: #5865f2;
                    color: #dcddde;
                }
            """
            dateedit_style = """
                QDateEdit {
                    background-color: #40444b;
                    border: 1px solid #202225;
                    border-radius: 4px;
                    padding: 5px 8px;
                    color: #dcddde;
                }
            """
        else:
            # Light theme styles
            card_style = """
                QFrame#dashboardCard {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 12px;
                    padding: 15px;
                }
                QFrame#dashboardCard:hover {
                    background-color: #f8f9fa;
                    border: 1px solid #adb5bd;
                }
            """
            title_style = "color: #6c757d; font-size: 10pt; font-weight: normal;"
            amount_style = "color: #212529; font-size: 20pt; font-weight: bold;"
            table_style = """
                QTableWidget {
                    background-color: white;
                    alternate-background-color: #f8f9fa;
                    selection-background-color: #e3f2fd;
                    selection-color: #1976d2;
                    gridline-color: #dee2e6;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                }
                QHeaderView::section {
                    background-color: #f1f3f5;
                    padding: 8px;
                    border: none;
                    font-weight: 600;
                    color: #495057;
                }
                QTableWidget::item {
                    padding: 6px;
                }
            """
            group_style = """
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px;
                    color: #495057;
                }
            """
            button_style = """
                QPushButton {
                    background-color: #5865f2;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 25px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #4752c4;
                }
            """
            combo_style = """
                QComboBox {
                    background-color: white;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    padding: 5px 8px;
                    color: #495057;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    border: 1px solid #ced4da;
                    selection-background-color: #5865f2;
                    color: #495057;
                }
            """
            dateedit_style = """
                QDateEdit {
                    background-color: white;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    padding: 5px 8px;
                    color: #495057;
                }
            """
        
        # Apply styles
        self.current_card.setStyleSheet(card_style)
        self.previous_card.setStyleSheet(card_style)
        self.diff_card.setStyleSheet(card_style)
        
        self.current_title.setStyleSheet(title_style)
        self.previous_title.setStyleSheet(title_style)
        self.diff_title.setStyleSheet(title_style)
        
        self.current_amount.setStyleSheet(amount_style)
        self.previous_amount.setStyleSheet(amount_style)
        
        self.table.setStyleSheet(table_style)
        self.best_table.setStyleSheet(table_style)
        self.worst_table.setStyleSheet(table_style)
        
        self.custom_group.setStyleSheet(group_style)
        type_group = self.findChild(QGroupBox, "Comparison Type")
        if type_group:
            type_group.setStyleSheet(group_style)
        
        self.btn_close.setStyleSheet(button_style)
        self.btn_refresh.setStyleSheet(button_style)
        
        self.comparison_type.setStyleSheet(combo_style)
        
        self.period1_from.setStyleSheet(dateedit_style)
        self.period1_to.setStyleSheet(dateedit_style)
        self.period2_from.setStyleSheet(dateedit_style)
        self.period2_to.setStyleSheet(dateedit_style)

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
        symbol = get_currency_symbol()
        
        if lang == "my":
            self.setWindowTitle("အသုံးစရိတ် နှိုင်းယှဉ်ချက်")
            self.current_title.setText("လက်ရှိရကား")
            self.previous_title.setText("ယခင်ရကား")
            self.diff_title.setText("ကွာခြားချက်")
            self.btn_close.setText("ပိတ်မည်")
            self.btn_refresh.setText("ပြန်လည်")
            self.table.setHorizontalHeaderLabels([
                "အမျိုးအစား", "လက်ရှိရကား", "ယခင်ရကား",
                "ကွာခြားချက်", "ရာခိုင်နှုန်း", "လမ်းကြောင်း"
            ])
            self.best_table.setHorizontalHeaderLabels(["အမျိုးအစား", "ပြောင်းလဲမှု", "ရာခိုင်နှုန်း"])
            self.worst_table.setHorizontalHeaderLabels(["အမျိုးအစား", "ပြောင်းလဲမှု", "ရာခိုင်နှုန်း"])
        else:
            self.setWindowTitle("Expense Comparison")
            self.current_title.setText("Current Period")
            self.previous_title.setText("Previous Period")
            self.diff_title.setText("Difference")
            self.btn_close.setText("Close")
            self.btn_refresh.setText("Refresh")
            self.table.setHorizontalHeaderLabels([
                "Category", "Current Period", "Previous Period",
                "Difference", "Change %", "Trend"
            ])
            self.best_table.setHorizontalHeaderLabels(["Category", "Change", "Percentage"])
            self.worst_table.setHorizontalHeaderLabels(["Category", "Change", "Percentage"])
        
        # Re-apply card style when language changes (to ensure styles are correct)
        self.apply_card_style()

    def on_comparison_type_changed(self, text):
        if text == "Custom Period Comparison":
            self.custom_group.setVisible(True)
            self.load_custom_comparison()
        else:
            self.custom_group.setVisible(False)
            if text == "Current Month vs Last Month":
                self.load_month_vs_last_month()
            else:
                self.load_month_vs_last_year()

    def load_month_vs_last_month(self):
        """Load comparison between current month and last month"""
        today = QDate.currentDate()
        
        # Current month (this month)
        current_start = QDate(today.year(), today.month(), 1)
        current_end = QDate(today.year(), today.month(), today.daysInMonth())
        
        # Last month
        last_month_date = today.addMonths(-1)
        last_start = QDate(last_month_date.year(), last_month_date.month(), 1)
        last_end = QDate(last_month_date.year(), last_month_date.month(), last_month_date.daysInMonth())
        
        self.current_title.setText(f"{current_start.toString('MMM yyyy')}")
        self.previous_title.setText(f"{last_start.toString('MMM yyyy')}")
        
        self.load_comparison_data(
            current_start.toString("yyyy-MM-dd"),
            current_end.toString("yyyy-MM-dd"),
            last_start.toString("yyyy-MM-dd"),
            last_end.toString("yyyy-MM-dd")
        )

    def load_month_vs_last_year(self):
        """Load comparison between current month and same month last year"""
        today = QDate.currentDate()
        
        # Current month (this month this year)
        current_start = QDate(today.year(), today.month(), 1)
        current_end = QDate(today.year(), today.month(), today.daysInMonth())
        
        # Same month last year
        last_year_start = QDate(today.year() - 1, today.month(), 1)
        last_year_end = QDate(today.year() - 1, today.month(), last_year_start.daysInMonth())
        
        self.current_title.setText(f"{current_start.toString('MMM yyyy')}")
        self.previous_title.setText(f"{last_year_start.toString('MMM yyyy')}")
        
        self.load_comparison_data(
            current_start.toString("yyyy-MM-dd"),
            current_end.toString("yyyy-MM-dd"),
            last_year_start.toString("yyyy-MM-dd"),
            last_year_end.toString("yyyy-MM-dd")
        )

    def load_custom_comparison(self):
        """Load comparison with custom date ranges"""
        period1_from = self.period1_from.date().toString("yyyy-MM-dd")
        period1_to = self.period1_to.date().toString("yyyy-MM-dd")
        period2_from = self.period2_from.date().toString("yyyy-MM-dd")
        period2_to = self.period2_to.date().toString("yyyy-MM-dd")
        
        self.current_title.setText(f"{period1_from} to {period1_to}")
        self.previous_title.setText(f"{period2_from} to {period2_to}")
        
        self.load_comparison_data(period1_from, period1_to, period2_from, period2_to)

    def load_comparison_data(self, current_from, current_to, previous_from, previous_to):
        symbol = get_currency_symbol()

        conn = connect_db()
        cursor = conn.cursor()

        # Get current period expenses by category
        cursor.execute("""
            SELECT category, COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE expense_date BETWEEN ? AND ?
            GROUP BY category
        """, (current_from, current_to))
        current_data = {row[0]: row[1] for row in cursor.fetchall()}

        # Get previous period expenses by category
        cursor.execute("""
            SELECT category, COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE expense_date BETWEEN ? AND ?
            GROUP BY category
        """, (previous_from, previous_to))
        previous_data = {row[0]: row[1] for row in cursor.fetchall()}

        # Get all categories
        cursor.execute("SELECT name FROM expense_categories ORDER BY name")
        categories = cursor.fetchall()
        conn.close()

        # Calculate totals
        total_current = sum(current_data.values())
        total_previous = sum(previous_data.values())
        total_diff = total_current - total_previous
        total_percent = (total_diff / total_previous * 100) if total_previous > 0 else 0

        # Update summary cards
        self.current_amount.setText(format_money(total_current, symbol))
        self.previous_amount.setText(format_money(total_previous, symbol))
        
        diff_text = format_money(total_diff, symbol)
        self.diff_amount.setText(diff_text)
        self.diff_percent.setText(f"({total_percent:+.1f}%)")
        
        # Set colors for diff card based on theme
        if total_diff > 0:
            self.diff_amount.setStyleSheet("color: #e74c3c; font-size: 20pt; font-weight: bold;")
            self.diff_percent.setStyleSheet("color: #e74c3c; font-size: 10pt;")
        elif total_diff < 0:
            self.diff_amount.setStyleSheet("color: #2ecc71; font-size: 20pt; font-weight: bold;")
            self.diff_percent.setStyleSheet("color: #2ecc71; font-size: 10pt;")
        else:
            if self.current_theme == "Dark":
                self.diff_amount.setStyleSheet("color: #b9bbbe; font-size: 20pt; font-weight: bold;")
                self.diff_percent.setStyleSheet("color: #b9bbbe; font-size: 10pt;")
            else:
                self.diff_amount.setStyleSheet("color: #6c757d; font-size: 20pt; font-weight: bold;")
                self.diff_percent.setStyleSheet("color: #6c757d; font-size: 10pt;")

        # Populate main table
        self.table.setRowCount(0)
        comparisons = []

        for (cat_name,) in categories:
            current = current_data.get(cat_name, 0)
            previous = previous_data.get(cat_name, 0)
            diff = current - previous
            percent = (diff / previous * 100) if previous > 0 else (100 if current > 0 else 0)
            
            comparisons.append({
                'category': cat_name,
                'current': current,
                'previous': previous,
                'diff': diff,
                'percent': percent
            })
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(cat_name))
            self.table.setItem(row, 1, QTableWidgetItem(format_money(current, symbol)))
            self.table.setItem(row, 2, QTableWidgetItem(format_money(previous, symbol)))
            
            diff_item = QTableWidgetItem(format_money(diff, symbol))
            if diff > 0:
                diff_item.setForeground(QColor(231, 76, 60))  # Red
            elif diff < 0:
                diff_item.setForeground(QColor(46, 204, 113))  # Green
            self.table.setItem(row, 3, diff_item)
            
            percent_item = QTableWidgetItem(f"{percent:+.1f}%")
            if percent > 0:
                percent_item.setForeground(QColor(231, 76, 60))
            elif percent < 0:
                percent_item.setForeground(QColor(46, 204, 113))
            self.table.setItem(row, 4, percent_item)
            
            # Trend indicator
            if diff > 0:
                trend = "↑ Increased"
                trend_color = QColor(231, 76, 60)
            elif diff < 0:
                trend = "↓ Decreased"
                trend_color = QColor(46, 204, 113)
            else:
                trend = "→ No change"
                trend_color = QColor(128, 128, 128)
            
            trend_item = QTableWidgetItem(trend)
            trend_item.setForeground(trend_color)
            self.table.setItem(row, 5, trend_item)

        # Load best and worst categories
        self.load_best_worst_categories(comparisons)

    def load_best_worst_categories(self, comparisons):
        symbol = get_currency_symbol()
        
        # Best = most decreased (negative diff)
        best_categories = sorted(comparisons, key=lambda x: x['diff'])[:5]
        
        # Worst = most increased (positive diff)
        worst_categories = sorted(comparisons, key=lambda x: x['diff'], reverse=True)[:5]
        
        # Best table (Savings)
        self.best_table.setRowCount(0)
        for cat in best_categories:
            if cat['diff'] >= 0:
                continue
            row = self.best_table.rowCount()
            self.best_table.insertRow(row)
            self.best_table.setItem(row, 0, QTableWidgetItem(cat['category']))
            change_text = format_money(cat['diff'], symbol)
            self.best_table.setItem(row, 1, QTableWidgetItem(change_text))
            percent_text = f"{cat['percent']:+.1f}%"
            percent_item = QTableWidgetItem(percent_text)
            percent_item.setForeground(QColor(46, 204, 113))
            self.best_table.setItem(row, 2, percent_item)
        
        if self.best_table.rowCount() == 0:
            row = self.best_table.rowCount()
            self.best_table.insertRow(row)
            self.best_table.setItem(row, 0, QTableWidgetItem("No savings"))
            self.best_table.setItem(row, 1, QTableWidgetItem("0"))
            self.best_table.setItem(row, 2, QTableWidgetItem("0%"))
        
        # Worst table (Increased spending)
        self.worst_table.setRowCount(0)
        for cat in worst_categories:
            if cat['diff'] <= 0:
                continue
            row = self.worst_table.rowCount()
            self.worst_table.insertRow(row)
            self.worst_table.setItem(row, 0, QTableWidgetItem(cat['category']))
            change_text = format_money(cat['diff'], symbol)
            self.worst_table.setItem(row, 1, QTableWidgetItem(change_text))
            percent_text = f"{cat['percent']:+.1f}%"
            percent_item = QTableWidgetItem(percent_text)
            percent_item.setForeground(QColor(231, 76, 60))
            self.worst_table.setItem(row, 2, percent_item)
        
        if self.worst_table.rowCount() == 0:
            row = self.worst_table.rowCount()
            self.worst_table.insertRow(row)
            self.worst_table.setItem(row, 0, QTableWidgetItem("No increases"))
            self.worst_table.setItem(row, 1, QTableWidgetItem("0"))
            self.worst_table.setItem(row, 2, QTableWidgetItem("0%"))

    def showEvent(self, event):
        """Re-apply card style when dialog becomes visible (theme might have changed)"""
        self.apply_card_style()
        super().showEvent(event)