from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QDateEdit, QTextEdit, QPushButton,
    QMessageBox, QComboBox, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from datetime import datetime


class CreditPaymentDialog(QDialog):
    def __init__(self, customer_id, customer_name, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.selected_credit_sale_id = None
        self.setWindowTitle(f"Payment Collection - {customer_name}")
        self.setMinimumSize(700, 550)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Customer info
        info_group = QGroupBox("Customer Information")
        info_layout = QFormLayout()
        self.customer_label = QLabel(customer_name)
        info_layout.addRow(QLabel("Customer:"), self.customer_label)
        
        self.current_balance_label = QLabel("Loading...")
        info_layout.addRow(QLabel("Current Balance:"), self.current_balance_label)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Outstanding Invoices
        invoice_group = QGroupBox("Outstanding Invoices")
        invoice_layout = QVBoxLayout()
        
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(5)
        self.invoice_table.setHorizontalHeaderLabels(["ID", "Invoice No", "Date", "Due Date", "Balance"])
        self.invoice_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoice_table.cellClicked.connect(self.select_invoice)
        self.invoice_table.setColumnHidden(0, True)
        header = self.invoice_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        invoice_layout.addWidget(self.invoice_table)
        invoice_group.setLayout(invoice_layout)
        layout.addWidget(invoice_group)

        # Payment details
        payment_group = QGroupBox("Payment Details")
        payment_layout = QFormLayout()
        payment_layout.setVerticalSpacing(12)

        # Amount
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 99999999)
        self.amount_input.setDecimals(0)
        symbol = get_currency_symbol()
        self.amount_input.setPrefix(f"{symbol} ")
        payment_layout.addRow(QLabel("Payment Amount:"), self.amount_input)

        # Payment Date
        self.payment_date = QDateEdit()
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDate(QDate.currentDate())
        payment_layout.addRow(QLabel("Payment Date:"), self.payment_date)

        # Payment Method
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "KBZPay", "WavePay", "Bank Transfer"])
        payment_layout.addRow(QLabel("Payment Method:"), self.payment_method)

        # Reference No
        self.reference_no = QLineEdit()
        self.reference_no.setPlaceholderText("Transaction reference (optional)")
        payment_layout.addRow(QLabel("Reference No:"), self.reference_no)

        # Note
        self.note = QTextEdit()
        self.note.setMaximumHeight(60)
        payment_layout.addRow(QLabel("Note:"), self.note)

        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_pay = QPushButton("Record Payment")
        self.btn_pay.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        self.btn_pay.clicked.connect(self.record_payment)
        self.btn_cancel = QPushButton("Close")
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
        btn_layout.addWidget(self.btn_pay)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_customer_info()
        self.load_outstanding_invoices()
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
            self.setWindowTitle(f"ငွေပေးချေမှု ကောက်ခံခြင်း - {self.customer_name}")
            self.btn_pay.setText("ငွေပေးချေမှု မှတ်တမ်းတင်ရန်")
            self.btn_cancel.setText("ပိတ်မည်")
        else:
            self.setWindowTitle(f"Payment Collection - {self.customer_name}")
            self.btn_pay.setText("Record Payment")
            self.btn_cancel.setText("Close")

    def load_customer_info(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT current_balance FROM customers WHERE id = ?", (self.customer_id,))
        row = cursor.fetchone()
        conn.close()
        
        symbol = get_currency_symbol()
        balance = row[0] if row else 0
        self.current_balance_label.setText(format_money(balance, symbol))
        self.amount_input.setMaximum(balance)

    def load_outstanding_invoices(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, invoice_no, sale_date, due_date, balance_amount
            FROM credit_sales
            WHERE customer_id = ? AND balance_amount > 0
            ORDER BY sale_date
        """, (self.customer_id,))
        rows = cursor.fetchall()
        conn.close()
        
        symbol = get_currency_symbol()
        self.invoice_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.invoice_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.invoice_table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.invoice_table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.invoice_table.setItem(i, 3, QTableWidgetItem(row[3] or ""))
            self.invoice_table.setItem(i, 4, QTableWidgetItem(format_money(row[4], symbol)))
            
            # Color code due date
            if row[3]:
                due_date = QDate.fromString(row[3], "yyyy-MM-dd")
                today = QDate.currentDate()
                if due_date < today:
                    self.invoice_table.item(i, 3).setForeground(Qt.GlobalColor.red)

    def select_invoice(self, row, col):
        id_item = self.invoice_table.item(row, 0)
        if id_item:
            self.selected_credit_sale_id = int(id_item.text())
            balance_item = self.invoice_table.item(row, 4)
            if balance_item:
                symbol = get_currency_symbol()
                balance_text = balance_item.text().replace(symbol, "").replace(",", "")
                try:
                    balance = float(balance_text)
                    self.amount_input.setMaximum(balance)
                    self.amount_input.setValue(balance)
                except:
                    pass

    def record_payment(self):
        amount = self.amount_input.value()
        if amount <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid payment amount.")
            return
        
        if self.selected_credit_sale_id:
            self.record_payment_to_invoice()
        else:
            self.record_general_payment()

    def record_payment_to_invoice(self):
        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT balance_amount FROM credit_sales WHERE id = ?", (self.selected_credit_sale_id,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.warning(self, "Error", "Invoice not found.")
                return
            
            current_balance = row[0]
            payment_amount = min(self.amount_input.value(), current_balance)
            
            new_balance = current_balance - payment_amount
            status = 'paid' if new_balance <= 0 else 'partial'
            
            cursor.execute("""
                UPDATE credit_sales 
                SET paid_amount = paid_amount + ?, balance_amount = ?, status = ?
                WHERE id = ?
            """, (payment_amount, new_balance, status, self.selected_credit_sale_id))
            
            payment_date = self.payment_date.date().toString("yyyy-MM-dd")
            payment_method = self.payment_method.currentText()
            reference_no = self.reference_no.text()
            note = self.note.toPlainText()
            
            cursor.execute("""
                INSERT INTO credit_payments (credit_sale_id, customer_id, amount, payment_date, payment_method, reference_no, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.selected_credit_sale_id, self.customer_id, payment_amount, payment_date, payment_method, reference_no, note))
            
            cursor.execute("""
                UPDATE customers SET current_balance = current_balance - ?
                WHERE id = ?
            """, (payment_amount, self.customer_id))
            
            conn.commit()
            
            lang = self.get_lang()
            msg = "Payment recorded successfully!" if lang != "my" else "ငွေပေးချေမှု အောင်မြင်စွာ မှတ်တမ်းတင်ပြီးပါပြီ။"
            QMessageBox.information(self, "Success", msg)
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to record payment: {e}")
        finally:
            conn.close()

    def record_general_payment(self):
        conn = connect_db()
        cursor = conn.cursor()
        try:
            payment_amount = self.amount_input.value()
            remaining = payment_amount
            
            cursor.execute("""
                SELECT id, balance_amount FROM credit_sales
                WHERE customer_id = ? AND balance_amount > 0
                ORDER BY sale_date
            """, (self.customer_id,))
            invoices = cursor.fetchall()
            
            payment_date = self.payment_date.date().toString("yyyy-MM-dd")
            payment_method = self.payment_method.currentText()
            reference_no = self.reference_no.text()
            note = self.note.toPlainText()
            
            for inv_id, balance in invoices:
                if remaining <= 0:
                    break
                
                pay_amount = min(remaining, balance)
                new_balance = balance - pay_amount
                status = 'paid' if new_balance <= 0 else 'partial'
                
                cursor.execute("""
                    UPDATE credit_sales 
                    SET paid_amount = paid_amount + ?, balance_amount = ?, status = ?
                    WHERE id = ?
                """, (pay_amount, new_balance, status, inv_id))
                
                cursor.execute("""
                    INSERT INTO credit_payments (credit_sale_id, customer_id, amount, payment_date, payment_method, reference_no, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (inv_id, self.customer_id, pay_amount, payment_date, payment_method, reference_no, note))
                
                remaining -= pay_amount
            
            cursor.execute("""
                UPDATE customers SET current_balance = current_balance - ?
                WHERE id = ?
            """, (payment_amount, self.customer_id))
            
            conn.commit()
            
            lang = self.get_lang()
            msg = "Payment recorded successfully!" if lang != "my" else "ငွေပေးချေမှု အောင်မြင်စွာ မှတ်တမ်းတင်ပြီးပါပြီ။"
            QMessageBox.information(self, "Success", msg)
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to record payment: {e}")
        finally:
            conn.close()
