from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from utils.language import lang  # Add lang import
import csv


class OutstandingReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Outstanding Debts Report")
        self.setMinimumSize(800, 500)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Summary cards
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(15)

        self.total_card = QFrame()
        self.total_card.setObjectName("reportCard")
        self.total_card.setFrameStyle(QFrame.Shape.StyledPanel)
        
        self.total_label = QLabel("Total Outstanding")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_amount = QLabel("0")
        self.total_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        total_layout = QVBoxLayout(self.total_card)
        total_layout.setSpacing(5)
        total_layout.addWidget(self.total_label)
        total_layout.addWidget(self.total_amount)
        summary_layout.addWidget(self.total_card, 1)

        self.overdue_card = QFrame()
        self.overdue_card.setObjectName("reportCard")
        self.overdue_card.setFrameStyle(QFrame.Shape.StyledPanel)
        
        self.overdue_label = QLabel("Overdue Amount")
        self.overdue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overdue_amount = QLabel("0")
        self.overdue_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        overdue_layout = QVBoxLayout(self.overdue_card)
        overdue_layout.setSpacing(5)
        overdue_layout.addWidget(self.overdue_label)
        overdue_layout.addWidget(self.overdue_amount)
        summary_layout.addWidget(self.overdue_card, 1)

        self.customer_count_card = QFrame()
        self.customer_count_card.setObjectName("reportCard")
        self.customer_count_card.setFrameStyle(QFrame.Shape.StyledPanel)
        
        self.customer_count_label = QLabel("Customers with Debt")
        self.customer_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.customer_count_amount = QLabel("0")
        self.customer_count_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        count_layout = QVBoxLayout(self.customer_count_card)
        count_layout.setSpacing(5)
        count_layout.addWidget(self.customer_count_label)
        count_layout.addWidget(self.customer_count_amount)
        summary_layout.addWidget(self.customer_count_card, 1)

        layout.addLayout(summary_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Customer ID", "Customer Name", "Phone", "Current Balance", "Credit Limit", "Status"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setColumnHidden(0, True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.clicked.connect(self.export_report)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_report)
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.apply_card_style()
        self.load_report()
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
        theme = self.get_theme()
        
        if theme == "Dark":
            card_style = """
                QFrame#reportCard {
                    background-color: #2f3136;
                    border: 1px solid #40444b;
                    border-radius: 12px;
                    padding: 15px;
                }
                QFrame#reportCard:hover {
                    background-color: #383a40;
                    border: 1px solid #5865f2;
                }
            """
            title_style = "color: #b9bbbe; font-size: 11pt; font-weight: normal;"
            amount_style = "color: #ffffff; font-size: 22pt; font-weight: bold;"
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
                    color: #dcddde;
                }
            """
            button_style = """
                QPushButton {
                    background-color: #5865f2;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 15px;
                }
                QPushButton:hover {
                    background-color: #4752c4;
                }
                QPushButton#closeBtn {
                    background-color: #40444b;
                }
                QPushButton#closeBtn:hover {
                    background-color: #5865f2;
                }
            """
        else:
            card_style = """
                QFrame#reportCard {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 12px;
                    padding: 15px;
                }
                QFrame#reportCard:hover {
                    background-color: #f8f9fa;
                    border: 1px solid #adb5bd;
                }
            """
            title_style = "color: #6c757d; font-size: 11pt; font-weight: normal;"
            amount_style = "color: #212529; font-size: 22pt; font-weight: bold;"
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
                    color: #212529;
                }
            """
            button_style = """
                QPushButton {
                    background-color: #5865f2;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 15px;
                }
                QPushButton:hover {
                    background-color: #4752c4;
                }
                QPushButton#closeBtn {
                    background-color: #6c757d;
                }
                QPushButton#closeBtn:hover {
                    background-color: #5865f2;
                }
            """
        
        # Apply styles
        for card in [self.total_card, self.overdue_card, self.customer_count_card]:
            card.setStyleSheet(card_style)
        
        self.total_label.setStyleSheet(title_style)
        self.overdue_label.setStyleSheet(title_style)
        self.customer_count_label.setStyleSheet(title_style)
        
        self.total_amount.setStyleSheet(amount_style)
        self.overdue_amount.setStyleSheet(amount_style)
        self.customer_count_amount.setStyleSheet(amount_style)
        
        self.table.setStyleSheet(table_style)
        
        self.btn_export.setStyleSheet(button_style)
        self.btn_refresh.setStyleSheet(button_style)
        self.btn_close.setStyleSheet(button_style)
        self.btn_close.setObjectName("closeBtn")

    def get_lang(self):
        return lang.get_current()

    def retranslateUi(self):
        lang_code = self.get_lang()
        if lang_code == "my":
            self.setWindowTitle("အကြွေးကျန်စာရင်း အစီရင်ခံစာ")
            self.total_label.setText("စုစုပေါင်းအကြွေးကျန်")
            self.overdue_label.setText("သက်တမ်းလွန်အကြွေး")
            self.customer_count_label.setText("အကြွေးရှိသောဝယ်ယူသူများ")
            self.btn_export.setText("CSV ထုတ်မည်")
            self.btn_refresh.setText("ပြန်လည်")
            self.btn_close.setText("ပိတ်မည်")
            self.table.setHorizontalHeaderLabels(["ID", "အမည်", "ဖုန်း", "လက်ကျန်အကြွေး", "ခရက်ဒစ်ကန့်သတ်ချက်", "အခြေအနေ"])
        else:
            self.setWindowTitle("Outstanding Debts Report")
            self.total_label.setText("Total Outstanding")
            self.overdue_label.setText("Overdue Amount")
            self.customer_count_label.setText("Customers with Debt")
            self.btn_export.setText("Export CSV")
            self.btn_refresh.setText("Refresh")
            self.btn_close.setText("Close")
            self.table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Current Balance", "Credit Limit", "Status"])

    def load_report(self):
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, phone, current_balance, credit_limit
            FROM customers
            WHERE current_balance > 0
            ORDER BY current_balance DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        symbol = get_currency_symbol()
        lang_code = self.get_lang()
        total_outstanding = sum(row[3] for row in rows)
        
        self.total_amount.setText(format_money(total_outstanding, symbol))
        self.customer_count_amount.setText(str(len(rows)))
        
        # Set color for total amount
        if total_outstanding > 0:
            theme = self.get_theme()
            if theme == "Dark":
                self.total_amount.setStyleSheet("color: #e74c3c; font-size: 22pt; font-weight: bold;")
            else:
                self.total_amount.setStyleSheet("color: #dc3545; font-size: 22pt; font-weight: bold;")
        
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            cust_id, name, phone, balance, credit_limit = row
            
            self.table.setItem(i, 0, QTableWidgetItem(str(cust_id)))
            self.table.setItem(i, 1, QTableWidgetItem(name))
            self.table.setItem(i, 2, QTableWidgetItem(phone or "-"))
            
            balance_item = QTableWidgetItem(format_money(balance, symbol))
            if balance > 0:
                balance_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(i, 3, balance_item)
            
            self.table.setItem(i, 4, QTableWidgetItem(format_money(credit_limit or 0, symbol)))
            
            # Check for overdue invoices
            conn2 = connect_db()
            cursor2 = conn2.cursor()
            cursor2.execute("""
                SELECT COUNT(*) FROM credit_sales
                WHERE customer_id = ? AND due_date < date('now') AND balance_amount > 0
            """, (cust_id,))
            overdue_count = cursor2.fetchone()[0]
            conn2.close()
            
            if overdue_count > 0:
                status = "⚠️ Overdue" if lang_code != "my" else "⚠️ သက်တမ်းလွန်"
                status_color = Qt.GlobalColor.red
            else:
                status = "✓ Current" if lang_code != "my" else "✓ လက်ရှိ"
                status_color = Qt.GlobalColor.darkGreen
            
            status_item = QTableWidgetItem(status)
            status_item.setForeground(status_color)
            self.table.setItem(i, 5, status_item)
        
        # Calculate total overdue amount
        conn3 = connect_db()
        cursor3 = conn3.cursor()
        cursor3.execute("""
            SELECT COALESCE(SUM(balance_amount), 0) FROM credit_sales
            WHERE due_date < date('now') AND balance_amount > 0
        """)
        overdue_total = cursor3.fetchone()[0]
        conn3.close()
        
        self.overdue_amount.setText(format_money(overdue_total, symbol))
        if overdue_total > 0:
            theme = self.get_theme()
            if theme == "Dark":
                self.overdue_amount.setStyleSheet("color: #e74c3c; font-size: 22pt; font-weight: bold;")
            else:
                self.overdue_amount.setStyleSheet("color: #dc3545; font-size: 22pt; font-weight: bold;")

    def export_report(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Outstanding Report", "outstanding_report.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, phone, current_balance, credit_limit
            FROM customers
            WHERE current_balance > 0
            ORDER BY current_balance DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Customer Name", "Phone", "Current Balance", "Credit Limit"])
                for row in rows:
                    writer.writerow([row[0], row[1] or "", row[2], row[3] or 0])
            QMessageBox.information(self, "Success", f"Report exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")

    def showEvent(self, event):
        """Re-apply card style when dialog becomes visible"""
        self.apply_card_style()
        super().showEvent(event)