from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDoubleSpinBox, QPushButton, QMessageBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money


class ExpenseBudgetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Budget Settings")
        self.setMinimumSize(1100, 700)  # Increased from 900x600
        self.resize(1200, 750)  # Default size
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)  # Add more padding

        # ========== MONTH/YEAR SELECTION ==========
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(15)
        selection_layout.addWidget(QLabel("Select Month/Year:"))

        self.month_combo = QComboBox()
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        self.month_combo.addItems(months)
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
        self.month_combo.setMinimumWidth(150)
        selection_layout.addWidget(self.month_combo)

        self.year_spin = QDoubleSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setDecimals(0)
        self.year_spin.setValue(QDate.currentDate().year())
        self.year_spin.setFixedWidth(100)  # Increased from 80 to 100
        self.year_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        selection_layout.addWidget(self.year_spin)

        self.btn_load = QPushButton("Load")
        self.btn_load.setStyleSheet("background-color: #5865f2; color: white; padding: 6px 20px;")
        self.btn_load.clicked.connect(self.load_budgets)
        selection_layout.addWidget(self.btn_load)

        selection_layout.addStretch()
        layout.addLayout(selection_layout)

        # ========== SUMMARY CARDS ==========
        card_layout = QHBoxLayout()
        card_layout.setSpacing(15)
        
        # Get current theme for dynamic styling
        self.current_theme = self.get_theme()
        
        # Total Budget Card
        self.total_card, self.total_title_label, self.total_amount_label = self.create_summary_card("Total Budget", "0")
        card_layout.addWidget(self.total_card, 1)
        
        # Total Actual Card
        self.actual_card, self.actual_title_label, self.actual_amount_label = self.create_summary_card("Total Actual", "0")
        card_layout.addWidget(self.actual_card, 1)
        
        # Remaining Card
        self.remaining_card, self.remaining_title_label, self.remaining_amount_label = self.create_summary_card("Remaining", "0")
        card_layout.addWidget(self.remaining_card, 1)
        
        # Used Percentage Card
        self.used_card, self.used_title_label, self.used_percent_label = self.create_summary_card("Overall Used", "0%")
        card_layout.addWidget(self.used_card, 1)
        
        layout.addLayout(card_layout)

        # ========== BUDGET TABLE ==========
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Category", "Budget", "Actual", "Used %", "Remaining", "Status", "Notes"
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
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(55)
        layout.addWidget(self.table)

        # ========== BUTTONS ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        self.btn_save = QPushButton("Save Budgets")
        self.btn_save.clicked.connect(self.save_budgets)
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_close)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.apply_card_style()
        self.load_budgets()
        self.retranslateUi()

    def create_summary_card(self, title, value):
        card = QFrame()
        card.setObjectName("dashboardCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return card, title_label, value_label

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
        """Use the same object-name driven style as dashboard cards."""
        for widget in [
            self.total_card, self.actual_card, self.remaining_card, self.used_card,
            self.total_title_label, self.actual_title_label, self.remaining_title_label, self.used_title_label,
            self.total_amount_label, self.actual_amount_label, self.remaining_amount_label, self.used_percent_label,
        ]:
            widget.setStyleSheet("")

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
            self.setWindowTitle("ဘတ်ဂျက်သတ်မှတ်ချက်များ")
            self.total_title_label.setText("စုစုပေါင်းဘတ်ဂျက်")
            self.actual_title_label.setText("စုစုပေါင်းအသုံးစရိတ်")
            self.remaining_title_label.setText("ကျန်ငွေ")
            self.used_title_label.setText("အသုံးပြုမှုနှုန်း")
            self.btn_save.setText("သိမ်းဆည်းမည်")
            self.btn_close.setText("ပိတ်မည်")
            self.btn_load.setText("ဖွင့်မည်")
            self.table.setHorizontalHeaderLabels([
                "အမျိုးအစား", "ဘတ်ဂျက်", "အသုံးစရိတ်", 
                "အသုံးပြုမှု", "ကျန်ငွေ", "အခြေအနေ", "မှတ်ချက်"
            ])
            # Update month names to Myanmar
            months = ["ဇန်နဝါရီ", "ဖေဖော်ဝါရီ", "မတ်", "ဧပြီ", "မေ", "ဇွန်", 
                      "ဇူလိုင်", "ဩဂုတ်", "စက်တင်ဘာ", "အောက်တိုဘာ", "နိုဝင်ဘာ", "ဒီဇင်ဘာ"]
            self.month_combo.blockSignals(True)
            self.month_combo.clear()
            self.month_combo.addItems(months)
            self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
            self.month_combo.blockSignals(False)
        else:
            self.setWindowTitle("Budget Settings")
            self.total_title_label.setText("Total Budget")
            self.actual_title_label.setText("Total Actual")
            self.remaining_title_label.setText("Remaining")
            self.used_title_label.setText("Overall Used")
            self.btn_save.setText("Save Budgets")
            self.btn_close.setText("Close")
            self.btn_load.setText("Load")
            self.table.setHorizontalHeaderLabels([
                "Category", "Budget", "Actual", 
                "Used %", "Remaining", "Status", "Notes"
            ])
            # Reset month names to English
            months = ["January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"]
            self.month_combo.blockSignals(True)
            self.month_combo.clear()
            self.month_combo.addItems(months)
            self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
            self.month_combo.blockSignals(False)
        
        self.apply_card_style()

    def load_budgets(self):
        month = self.month_combo.currentIndex() + 1
        year = int(self.year_spin.value())
        symbol = get_currency_symbol()

        conn = connect_db()
        cursor = conn.cursor()

        # Get all expense categories
        cursor.execute("SELECT id, name FROM expense_categories ORDER BY name")
        categories = cursor.fetchall()

        # Get budgets for selected month/year
        cursor.execute("""
            SELECT category, budget_amount, notes 
            FROM expense_budgets 
            WHERE month = ? AND year = ?
        """, (month, year))
        budgets = {row[0]: {"amount": row[1], "notes": row[2] or ""} for row in cursor.fetchall()}

        # Get actual expenses for selected month/year
        month_start = f"{year}-{month:02d}-01"
        if month == 12:
            month_end = f"{year+1}-01-01"
        else:
            month_end = f"{year}-{month+1:02d}-01"
        
        cursor.execute("""
            SELECT category, COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE expense_date >= ? AND expense_date < ?
            GROUP BY category
        """, (month_start, month_end))
        actuals = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()

        self.table.setRowCount(0)
        total_budget = 0
        total_actual = 0

        for cat_id, cat_name in categories:
            budget = budgets.get(cat_name, {}).get("amount", 0)
            actual = actuals.get(cat_name, 0)
            total_budget += budget
            total_actual += actual
            
            used_percent = (actual / budget * 100) if budget > 0 else 0
            remaining = budget - actual
            notes = budgets.get(cat_name, {}).get("notes", "")
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Category (read-only)
            cat_item = QTableWidgetItem(cat_name)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, cat_item)
            
            # Budget amount (editable)
            budget_spin = QDoubleSpinBox()
            budget_spin.setRange(0, 999999999)
            budget_spin.setDecimals(0)
            budget_spin.setPrefix(f"{symbol} ")
            budget_spin.setValue(budget)
            budget_spin.setMinimumWidth(120)
            budget_spin.valueChanged.connect(self.update_summary)
            self.table.setCellWidget(row, 1, budget_spin)
            
            # Actual amount (read-only)
            actual_item = QTableWidgetItem(format_money(actual, symbol))
            actual_item.setFlags(actual_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if actual > budget and budget > 0:
                actual_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 2, actual_item)
            
            # Used percentage
            used_text = f"{used_percent:.1f}%"
            percent_item = QTableWidgetItem(used_text)
            percent_item.setFlags(percent_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if used_percent >= 100:
                percent_item.setForeground(Qt.GlobalColor.red)
            elif used_percent >= 80:
                percent_item.setForeground(Qt.GlobalColor.darkYellow)
            elif used_percent > 0:
                percent_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 3, percent_item)
            
            # Remaining amount
            remaining_item = QTableWidgetItem(format_money(remaining, symbol))
            remaining_item.setFlags(remaining_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if remaining < 0:
                remaining_item.setForeground(Qt.GlobalColor.red)
            elif remaining > 0:
                remaining_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 4, remaining_item)
            
            # Status
            if budget == 0:
                status_text = "No Budget"
                status_color = Qt.GlobalColor.gray
            elif actual >= budget:
                status_text = "⚠️ Exceeded"
                status_color = Qt.GlobalColor.red
            elif actual >= budget * 0.8:
                status_text = "⚠️ Warning"
                status_color = Qt.GlobalColor.darkYellow
            else:
                status_text = "✓ OK"
                status_color = Qt.GlobalColor.darkGreen
            
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_color)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, status_item)
            
            # Notes
            notes_item = QTableWidgetItem(notes)
            self.table.setItem(row, 6, notes_item)
            
            # Set row height
            self.table.setRowHeight(row, 55)
        
        # Update summary cards
        self.total_amount_label.setText(format_money(total_budget, symbol))
        self.actual_amount_label.setText(format_money(total_actual, symbol))
        remaining_total = total_budget - total_actual
        self.remaining_amount_label.setText(format_money(remaining_total, symbol))
        
        overall_percent = (total_actual / total_budget * 100) if total_budget > 0 else 0
        self.used_percent_label.setText(f"{overall_percent:.1f}%")
        
        self.remaining_amount_label.setStyleSheet("")
        self.used_percent_label.setStyleSheet("")

    def update_summary(self):
        """Update summary when budget values change"""
        total_budget = 0
        for row in range(self.table.rowCount()):
            budget_widget = self.table.cellWidget(row, 1)
            if budget_widget:
                total_budget += budget_widget.value()
        
        total_actual = 0
        symbol = get_currency_symbol()
        for row in range(self.table.rowCount()):
            actual_item = self.table.item(row, 2)
            if actual_item:
                text = actual_item.text().replace(symbol, "").replace(",", "")
                try:
                    total_actual += float(text)
                except:
                    pass
        
        self.total_amount_label.setText(format_money(total_budget, symbol))
        self.actual_amount_label.setText(format_money(total_actual, symbol))
        remaining = total_budget - total_actual
        self.remaining_amount_label.setText(format_money(remaining, symbol))
        
        overall_percent = (total_actual / total_budget * 100) if total_budget > 0 else 0
        self.used_percent_label.setText(f"{overall_percent:.1f}%")
        
        self.remaining_amount_label.setStyleSheet("")
        self.used_percent_label.setStyleSheet("")
        
        # Update individual row statuses
        for row in range(self.table.rowCount()):
            budget_widget = self.table.cellWidget(row, 1)
            budget = budget_widget.value() if budget_widget else 0
            
            actual_item = self.table.item(row, 2)
            actual_text = actual_item.text().replace(symbol, "").replace(",", "") if actual_item else "0"
            try:
                actual = float(actual_text)
            except:
                actual = 0
            
            used_percent = (actual / budget * 100) if budget > 0 else 0
            remaining_row = budget - actual
            
            # Update used percentage
            percent_item = self.table.item(row, 3)
            if percent_item:
                percent_item.setText(f"{used_percent:.1f}%")
                if used_percent >= 100:
                    percent_item.setForeground(Qt.GlobalColor.red)
                elif used_percent >= 80:
                    percent_item.setForeground(Qt.GlobalColor.darkYellow)
                else:
                    percent_item.setForeground(Qt.GlobalColor.darkGreen)
            
            # Update remaining amount
            remaining_item = self.table.item(row, 4)
            if remaining_item:
                remaining_item.setText(format_money(remaining_row, symbol))
                if remaining_row < 0:
                    remaining_item.setForeground(Qt.GlobalColor.red)
                else:
                    remaining_item.setForeground(Qt.GlobalColor.darkGreen)
            
            # Update status
            status_item = self.table.item(row, 5)
            if status_item:
                if budget == 0:
                    status_item.setText("No Budget")
                    status_item.setForeground(Qt.GlobalColor.gray)
                elif actual >= budget:
                    status_item.setText("⚠️ Exceeded")
                    status_item.setForeground(Qt.GlobalColor.red)
                elif actual >= budget * 0.8:
                    status_item.setText("⚠️ Warning")
                    status_item.setForeground(Qt.GlobalColor.darkYellow)
                else:
                    status_item.setText("✓ OK")
                    status_item.setForeground(Qt.GlobalColor.darkGreen)

    def save_budgets(self):
        month = self.month_combo.currentIndex() + 1
        year = int(self.year_spin.value())

        conn = connect_db()
        cursor = conn.cursor()
        
        try:
            for row in range(self.table.rowCount()):
                category = self.table.item(row, 0).text()
                budget_widget = self.table.cellWidget(row, 1)
                budget = budget_widget.value() if budget_widget else 0
                notes_item = self.table.item(row, 6)
                notes = notes_item.text() if notes_item else ""
                
                cursor.execute("""
                    INSERT INTO expense_budgets (category, month, year, budget_amount, notes)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(category, month, year) 
                    DO UPDATE SET budget_amount = excluded.budget_amount, notes = excluded.notes, updated_at = CURRENT_TIMESTAMP
                """, (category, month, year, budget, notes))
            
            conn.commit()
            lang = self.get_lang()
            msg = "Budgets saved successfully!" if lang != "my" else "ဘတ်ဂျက်များ သိမ်းဆည်းပြီးပါပြီ။"
            QMessageBox.information(self, "Success", msg)
            self.load_budgets()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save budgets: {e}")
        finally:
            conn.close()

    def showEvent(self, event):
        """Update card style when dialog becomes visible"""
        self.apply_card_style()
        super().showEvent(event)
