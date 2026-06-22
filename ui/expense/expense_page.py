# ui/expense/expense_page.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from utils.language import lang
from ui.expense.expense_cards import ExpenseCards
from ui.expense.expense_filters import ExpenseFilters
from ui.expense.expense_table import ExpenseTable
from ui.expense.expense_export import ExpenseExport
from ui.expense_dialog import ExpenseDialog
from ui.expense_categories_dialog import ExpenseCategoriesDialog
from ui.expense_budget_dialog import ExpenseBudgetDialog
from ui.expense_notification_dialog import ExpenseNotificationDialog
from ui.expense_comparison_dialog import ExpenseComparisonDialog
from loguru import logger
from PyQt6.QtWidgets import QTableWidgetItem


class ExpensePage(QWidget):
    def __init__(self, user_role=None, parent=None):
        super().__init__(parent)
        self.user_role = user_role
        
        lang.language_changed.connect(self.on_language_changed)
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Cards
        self.cards = ExpenseCards(self)
        layout.addWidget(self.cards)
        
        # Date buttons
        self.setup_date_buttons(layout)
        
        # Filters
        self.filters = ExpenseFilters(self)
        self.filters.filter_changed.connect(self.on_filter_changed)
        layout.addWidget(self.filters)
        
        # Action buttons
        self.setup_action_buttons(layout)
        
        # Table
        self.table = ExpenseTable(self)
        self.table.expense_selected.connect(self.on_expense_selected)
        self.table.expense_double_clicked.connect(self.on_expense_double_clicked)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def setup_date_buttons(self, layout):
        date_layout = QHBoxLayout()
        date_layout.setSpacing(10)
        
        self.btn_today = QPushButton("Today")
        self.btn_this_week = QPushButton("This Week")
        self.btn_this_month = QPushButton("This Month")
        self.btn_last_month = QPushButton("Last Month")
        self.btn_this_year = QPushButton("This Year")
        
        self.btn_today.clicked.connect(lambda: self.set_date_range("today"))
        self.btn_this_week.clicked.connect(lambda: self.set_date_range("week"))
        self.btn_this_month.clicked.connect(lambda: self.set_date_range("month"))
        self.btn_last_month.clicked.connect(lambda: self.set_date_range("last_month"))
        self.btn_this_year.clicked.connect(lambda: self.set_date_range("year"))
        
        date_layout.addWidget(self.btn_today)
        date_layout.addWidget(self.btn_this_week)
        date_layout.addWidget(self.btn_this_month)
        date_layout.addWidget(self.btn_last_month)
        date_layout.addWidget(self.btn_this_year)
        date_layout.addStretch()
        
        layout.addLayout(date_layout)
    
    def setup_action_buttons(self, layout):
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add Expense")
        self.btn_edit = QPushButton("Edit")
        self.btn_delete = QPushButton("Delete")
        self.btn_categories = QPushButton("Manage Categories")
        self.btn_budget = QPushButton("Budget Settings")
        self.btn_notifications = QPushButton("🔔 Notifications")
        self.btn_compare = QPushButton("📊 Compare")
        self.btn_export_excel = QPushButton("📊 Export Excel")
        self.btn_export_category = QPushButton("📁 Export Category")
        self.btn_export_monthly = QPushButton("📅 Export Monthly")
        
        self.btn_add.clicked.connect(self.add_expense)
        self.btn_edit.clicked.connect(self.edit_expense)
        self.btn_delete.clicked.connect(self.delete_expense)
        self.btn_categories.clicked.connect(self.manage_categories)
        self.btn_budget.clicked.connect(self.open_budget_dialog)
        self.btn_notifications.clicked.connect(self.open_notification_settings)
        self.btn_compare.clicked.connect(self.open_comparison_dialog)
        self.btn_export_excel.clicked.connect(self.export_to_excel)
        self.btn_export_category.clicked.connect(self.export_category)
        self.btn_export_monthly.clicked.connect(self.export_monthly)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_categories)
        btn_layout.addWidget(self.btn_budget)
        btn_layout.addWidget(self.btn_notifications)
        btn_layout.addWidget(self.btn_compare)
        btn_layout.addWidget(self.btn_export_excel)
        btn_layout.addWidget(self.btn_export_category)
        btn_layout.addWidget(self.btn_export_monthly)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def load_initial_data(self):
        self.filters.load_categories()
        self.load_expenses()
        self.cards.update_totals()
        self.apply_card_style()
    
    def load_expenses(self, page=1, page_size=50):
        search_text = self.filters.get_search_text()
        category = self.filters.get_category()
        from_date, to_date = self.filters.get_date_range()
        symbol = get_currency_symbol()
        
        conn = connect_db()
        cursor = conn.cursor()
        
        base_query = "FROM expenses WHERE expense_date BETWEEN ? AND ?"
        params = [from_date, to_date]
        
        if search_text:
            base_query += " AND (LOWER(description) LIKE ? OR LOWER(reference_no) LIKE ?)"
            like = f'%{search_text}%'
            params.extend([like, like])
        
        if category != "All Categories":
            base_query += " AND category = ?"
            params.append(category)
        
        count_query = f"SELECT COUNT(*){base_query}"
        cursor.execute(count_query, params)
        total_items = cursor.fetchone()[0]
        self.table.pagination.set_total_items(total_items, emit_signal=False)
        
        offset = (page - 1) * page_size
        data_query = f"""
            SELECT id, expense_no, expense_date, category, description, 
                   amount, payment_method, reference_no, notes
            {base_query}
            ORDER BY expense_date DESC LIMIT ? OFFSET ?
        """
        cursor.execute(data_query, params + [page_size, offset])
        rows = cursor.fetchall()
        
        # Calculate total amount for current page
        total_amount = sum(row[5] for row in rows) if rows else 0
        
        self.table.table.setRowCount(0)  # Clear table first
        
        for row_idx, row_data in enumerate(rows):
            exp_id, exp_no, exp_date, cat, desc, amount, method, ref_no, notes = row_data
            self.table.table.insertRow(row_idx)
            self.table.table.setItem(row_idx, 0, QTableWidgetItem(str(exp_id)))
            self.table.table.setItem(row_idx, 1, QTableWidgetItem(exp_no or ""))
            self.table.table.setItem(row_idx, 2, QTableWidgetItem(exp_date or ""))
            self.table.table.setItem(row_idx, 3, QTableWidgetItem(cat or ""))
            self.table.table.setItem(row_idx, 4, QTableWidgetItem(desc or ""))
            
            amount_item = QTableWidgetItem(format_money(amount, symbol))
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.table.setItem(row_idx, 5, amount_item)
            
            self.table.table.setItem(row_idx, 6, QTableWidgetItem(method or ""))
            self.table.table.setItem(row_idx, 7, QTableWidgetItem(ref_no or ""))
            self.table.table.setItem(row_idx, 8, QTableWidgetItem(notes or ""))
            
            cursor.execute("SELECT COUNT(*) FROM expense_attachments WHERE expense_id = ?", (exp_id,))
            att_count = cursor.fetchone()[0]
            attachments_item = QTableWidgetItem(f"📎 {att_count}" if att_count > 0 else "")
            attachments_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.table.setItem(row_idx, 9, attachments_item)
        
        # Add summary row with total
        self.table.set_total_amount(total_amount)
        self.table.add_summary_row(len(rows), symbol)
        
        conn.close()
        self.cards.update_totals()
    
    def on_filter_changed(self):
        self.table.current_page = 1
        self.load_expenses()
    
    def on_expense_selected(self, expense_id):
        self.table.selected_expense_id = expense_id
    
    def on_expense_double_clicked(self, expense_id, expense_no):
        from ui.expense_attachment_dialog import ExpenseAttachmentDialog
        dialog = ExpenseAttachmentDialog(expense_id, expense_no, self)
        dialog.exec()
    
    def set_date_range(self, range_type):
        today = QDate.currentDate()
        
        if range_type == "today":
            self.filters.from_date.setDate(today)
            self.filters.to_date.setDate(today)
        elif range_type == "week":
            start = today.addDays(-(today.dayOfWeek() - 1))
            end = start.addDays(6)
            self.filters.from_date.setDate(start)
            self.filters.to_date.setDate(end)
        elif range_type == "month":
            start = QDate(today.year(), today.month(), 1)
            self.filters.from_date.setDate(start)
            self.filters.to_date.setDate(today)
        elif range_type == "last_month":
            first_day_this = QDate(today.year(), today.month(), 1)
            last_day_last = first_day_this.addDays(-1)
            first_day_last = QDate(last_day_last.year(), last_day_last.month(), 1)
            self.filters.from_date.setDate(first_day_last)
            self.filters.to_date.setDate(last_day_last)
        elif range_type == "year":
            start = QDate(today.year(), 1, 1)
            self.filters.from_date.setDate(start)
            self.filters.to_date.setDate(today)
        
        self.on_filter_changed()
    
    def add_expense(self):
        dialog = ExpenseDialog(parent=self)
        if dialog.exec():
            self.load_expenses()
            self.filters.load_categories()
            self.cards.update_totals()
    
    def edit_expense(self):
        expense_id = self.table.get_selected_id()
        if not expense_id:
            msg = "Please select an expense to edit."
            QMessageBox.warning(self, "No Selection", msg)
            return
        dialog = ExpenseDialog(expense_id, self)
        if dialog.exec():
            self.load_expenses()
            self.cards.update_totals()
    
    def delete_expense(self):
        expense_id = self.table.get_selected_id()
        if not expense_id:
            msg = "Please select an expense to delete."
            QMessageBox.warning(self, "No Selection", msg)
            return
        
        reply = QMessageBox.question(self, "Confirm Delete", "Delete this expense permanently?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = connect_db()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM expense_attachments WHERE expense_id = ?", (expense_id,))
                cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
                conn.commit()
                self.table.clear_selection()
                self.load_expenses()
                self.cards.update_totals()
                QMessageBox.information(self, "Deleted", "Expense deleted successfully.")
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Error", f"Could not delete: {e}")
            finally:
                conn.close()
    
    def manage_categories(self):
        dialog = ExpenseCategoriesDialog(self)
        dialog.exec()
        self.filters.load_categories()
    
    def open_budget_dialog(self):
        dialog = ExpenseBudgetDialog(self)
        dialog.exec()
    
    def open_notification_settings(self):
        dialog = ExpenseNotificationDialog(self)
        dialog.exec()
    
    def open_comparison_dialog(self):
        dialog = ExpenseComparisonDialog(self)
        dialog.exec()
    
    def export_to_excel(self):
        from_date, to_date = self.filters.get_date_range()
        category = self.filters.get_category()
        search_text = self.filters.get_search_text()
        ExpenseExport.export_expense_report(self, from_date, to_date, category, search_text)
    
    def export_category(self):
        from_date, to_date = self.filters.get_date_range()
        ExpenseExport.export_category_report(self, from_date, to_date)
    
    def export_monthly(self):
        from_date, to_date = self.filters.get_date_range()
        ExpenseExport.export_monthly_report(self, from_date, to_date)
    
    def apply_card_style(self):
        theme = self.get_current_theme()
        self.cards.apply_style(theme)
    
    def get_current_theme(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='theme'")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "Light"
        except:
            return "Light"
    
    def on_language_changed(self, lang_code):
        self.retranslateUi()
        self.cards.retranslateUi(lang_code)
        self.filters.retranslateUi(lang_code)
        self.table.retranslateUi(lang_code)
        self.load_expenses()
        self.cards.update_totals()
    
    def retranslateUi(self):
        lang_code = lang.get_current()
        
        if lang_code == "my":
            self.btn_today.setText("ယနေ့")
            self.btn_this_week.setText("ဤတစ်ပတ်")
            self.btn_this_month.setText("ဤလ")
            self.btn_last_month.setText("ပြီးခဲ့သည့်လ")
            self.btn_this_year.setText("ဤနှစ်")
            self.btn_add.setText("အသုံးစရိတ်အသစ်")
            self.btn_edit.setText("ပြင်ဆင်")
            self.btn_delete.setText("ဖျက်")
            self.btn_categories.setText("အမျိုးအစားများ")
            self.btn_budget.setText("ဘတ်ဂျက်သတ်မှတ်ချက်များ")
            self.btn_notifications.setText("🔔 သတိပေးချက်များ")
            self.btn_compare.setText("📊 နှိုင်းယှဉ်မည်")
            self.btn_export_excel.setText("📊 Excel ထုတ်မည်")
            self.btn_export_category.setText("📁 အမျိုးအစားအလိုက်")
            self.btn_export_monthly.setText("📅 လစဉ် Excel")
        else:
            self.btn_today.setText("Today")
            self.btn_this_week.setText("This Week")
            self.btn_this_month.setText("This Month")
            self.btn_last_month.setText("Last Month")
            self.btn_this_year.setText("This Year")
            self.btn_add.setText("Add Expense")
            self.btn_edit.setText("Edit")
            self.btn_delete.setText("Delete")
            self.btn_categories.setText("Manage Categories")
            self.btn_budget.setText("Budget Settings")
            self.btn_notifications.setText("🔔 Notifications")
            self.btn_compare.setText("📊 Compare")
            self.btn_export_excel.setText("📊 Export Excel")
            self.btn_export_category.setText("📁 Export Category")
            self.btn_export_monthly.setText("📅 Export Monthly")
        
        self.cards.retranslateUi(lang_code)
        self.filters.retranslateUi(lang_code)
        self.table.retranslateUi(lang_code)
    
    def showEvent(self, event):
        self.load_expenses()
        self.cards.update_totals()
        self.apply_card_style()
        super().showEvent(event)