from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QDateEdit, QTextEdit, QPushButton,
    QMessageBox, QComboBox, QGroupBox
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from datetime import datetime


class CreditSaleDialog(QDialog):
    def __init__(self, customer_id=None, customer_name=None, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.setWindowTitle(f"Credit Sale - {customer_name}" if customer_name else "Credit Sale")
        self.setMinimumWidth(500)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Customer info
        info_group = QGroupBox("Customer Information")
        info_layout = QFormLayout()
        self.customer_label = QLabel(customer_name if customer_name else "Select customer first")
        info_layout.addRow(QLabel("Customer:"), self.customer_label)
        
        # Credit limit and current balance
        self.credit_limit_label = QLabel("0")
        self.current_balance_label = QLabel("0")
        info_layout.addRow(QLabel("Credit Limit:"), self.credit_limit_label)
        info_layout.addRow(QLabel("Current Balance:"), self.current_balance_label)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Sale details
        sale_group = QGroupBox("Sale Details")
        sale_layout = QFormLayout()
        sale_layout.setVerticalSpacing(12)

        # Invoice No (auto-generated)
        self.invoice_no = QLineEdit()
        self.invoice_no.setReadOnly(True)
        self.invoice_no.setText(f"CR-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        sale_layout.addRow(QLabel("Invoice No:"), self.invoice_no)

        # Total Amount
        self.total_amount = QDoubleSpinBox()
        self.total_amount.setRange(0, 99999999)
        self.total_amount.setDecimals(0)
        symbol = get_currency_symbol()
        self.total_amount.setPrefix(f"{symbol} ")
        self.total_amount.valueChanged.connect(self.update_balance)
        sale_layout.addRow(QLabel("Total Amount:"), self.total_amount)

        # Paid Amount (Partial payment)
        self.paid_amount = QDoubleSpinBox()
        self.paid_amount.setRange(0, 99999999)
        self.paid_amount.setDecimals(0)
        self.paid_amount.setPrefix(f"{symbol} ")
        self.paid_amount.valueChanged.connect(self.update_balance)
        sale_layout.addRow(QLabel("Paid Today:"), self.paid_amount)

        # Balance Due
        self.balance_amount = QLabel("0")
        self.balance_amount.setStyleSheet("font-weight: bold; color: #e74c3c;")
        sale_layout.addRow(QLabel("Balance Due:"), self.balance_amount)

        # Sale Date
        self.sale_date = QDateEdit()
        self.sale_date.setCalendarPopup(True)
        self.sale_date.setDate(QDate.currentDate())
        sale_layout.addRow(QLabel("Sale Date:"), self.sale_date)

        # Due Date
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate().addDays(15))
        sale_layout.addRow(QLabel("Due Date:"), self.due_date)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        sale_layout.addRow(QLabel("Notes:"), self.notes)

        sale_group.setLayout(sale_layout)
        layout.addWidget(sale_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save Credit Sale")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #5865f2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #4752c4;
            }
        """)
        self.btn_save.clicked.connect(self.save_credit_sale)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #40444b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #5865f2;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_customer_info()
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
        symbol = get_currency_symbol()
        if lang == "my":
            self.setWindowTitle(f"အကြွေးရောင်းချမှု - {self.customer_name}" if self.customer_name else "အကြွေးရောင်းချမှု")
            self.btn_save.setText("သိမ်းဆည်းမည်")
            self.btn_cancel.setText("မလုပ်တော့")
        else:
            self.setWindowTitle(f"Credit Sale - {self.customer_name}" if self.customer_name else "Credit Sale")
            self.btn_save.setText("Save Credit Sale")
            self.btn_cancel.setText("Cancel")

    def load_customer_info(self):
        if not self.customer_id:
            return
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT credit_limit, current_balance FROM customers WHERE id = ?
        """, (self.customer_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            symbol = get_currency_symbol()
            self.credit_limit_label.setText(format_money(row[0] or 0, symbol))
            self.current_balance_label.setText(format_money(row[1] or 0, symbol))
            if (row[1] or 0) >= (row[0] or 0) and (row[0] or 0) > 0:
                self.current_balance_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def update_balance(self):
        total = self.total_amount.value()
        paid = self.paid_amount.value()
        balance = total - paid
        symbol = get_currency_symbol()
        self.balance_amount.setText(format_money(balance, symbol))
        
        if balance > 0:
            self.balance_amount.setStyleSheet("font-weight: bold; color: #e74c3c;")
        else:
            self.balance_amount.setStyleSheet("font-weight: bold; color: #27ae60;")

    def check_credit_limit(self, amount):
        if not self.customer_id:
            return True
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT credit_limit, current_balance FROM customers WHERE id = ?", (self.customer_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            credit_limit = row[0] or 0
            current_balance = row[1] or 0
            new_balance = current_balance + amount
            
            if credit_limit > 0 and new_balance > credit_limit:
                symbol = get_currency_symbol()
                lang = self.get_lang()
                msg = f"Credit limit exceeded!\n\nLimit: {format_money(credit_limit, symbol)}\nCurrent: {format_money(current_balance, symbol)}\nThis sale: {format_money(amount, symbol)}\nNew balance: {format_money(new_balance, symbol)}\n\nProceed anyway?" if lang != "my" else f"ခရက်ဒစ်ကန့်သတ်ချက် ကျော်လွန်နေသည်!\n\nကန့်သတ်ချက်: {format_money(credit_limit, symbol)}\nလက်ရှိကျန်: {format_money(current_balance, symbol)}\nဤရောင်းချမှု: {format_money(amount, symbol)}\nအသစ်ကျန်: {format_money(new_balance, symbol)}\n\nဆက်လုပ်မည်လား?"
                reply = QMessageBox.warning(self, "Credit Limit Warning", msg,
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                return reply == QMessageBox.StandardButton.Yes
        return True

    def save_credit_sale(self):
        total = self.total_amount.value()
        paid = self.paid_amount.value()
        
        if total <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid total amount.")
            return
        
        if not self.check_credit_limit(total - paid):
            return
        
        conn = connect_db()
        cursor = conn.cursor()
        try:
            invoice_no = self.invoice_no.text()
            sale_date = self.sale_date.date().toString("yyyy-MM-dd")
            due_date = self.due_date.date().toString("yyyy-MM-dd")
            balance = total - paid
            notes = self.notes.toPlainText()
            
            cursor.execute("""
                INSERT INTO credit_sales (invoice_no, customer_id, total_amount, paid_amount, 
                                         balance_amount, sale_date, due_date, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (invoice_no, self.customer_id, total, paid, balance, sale_date, due_date, 
                  'partial' if paid > 0 and balance > 0 else 'pending' if paid == 0 else 'paid', notes))
            
            credit_sale_id = cursor.lastrowid
            
            cursor.execute("""
                UPDATE customers SET current_balance = current_balance + ?
                WHERE id = ?
            """, (balance, self.customer_id))
            
            if paid > 0:
                cursor.execute("""
                    INSERT INTO credit_payments (credit_sale_id, customer_id, amount, payment_date)
                    VALUES (?, ?, ?, ?)
                """, (credit_sale_id, self.customer_id, paid, sale_date))
            
            conn.commit()
            
            lang = self.get_lang()
            msg = "Credit sale recorded successfully!" if lang != "my" else "အကြွေးရောင်းချမှု အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။"
            QMessageBox.information(self, "Success", msg)
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")
        finally:
            conn.close()
