from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QComboBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPushButton,
    QMessageBox, QDialogButtonBox, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from datetime import datetime


class SupplierPaymentDialog(QDialog):
    def __init__(self, supplier_id, supplier_name, current_balance=0, parent=None):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.current_balance = current_balance
        self.setWindowTitle(f"Record Payment - {supplier_name}")
        self.setMinimumWidth(500)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Balance info
        info_group = QGroupBox()
        info_layout = QHBoxLayout()
        symbol = get_currency_symbol()
        self.balance_label = QLabel()
        self.balance_label.setText(f"Current Balance: {format_money(current_balance, symbol)}")
        if current_balance > 0:
            self.balance_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        elif current_balance < 0:
            self.balance_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.balance_label.setStyleSheet("color: #333;")
        info_layout.addWidget(self.balance_label)
        info_layout.addStretch()
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Payment form
        form_group = QGroupBox("Payment Details")
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(12)

        # Payment amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, current_balance if current_balance > 0 else 10000000)
        self.amount_spin.setDecimals(0)
        self.amount_spin.setSuffix(f" {symbol}")
        self.amount_spin.setMaximum(current_balance if current_balance > 0 else 10000000)
        form_layout.addRow(QLabel("Payment Amount:"), self.amount_spin)

        # Payment date
        self.payment_date = QDateEdit()
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDate(QDate.currentDate())
        form_layout.addRow(QLabel("Payment Date:"), self.payment_date)

        # Reference number
        self.reference_no = QLineEdit()
        self.reference_no.setPlaceholderText("Optional - e.g., Bank Ref, Cheque No")
        form_layout.addRow(QLabel("Reference No:"), self.reference_no)

        # Payment type
        self.payment_type = QComboBox()
        self.payment_type.addItems(["Cash", "Bank Transfer", "Cheque", "Mobile Money"])
        form_layout.addRow(QLabel("Payment Method:"), self.payment_type)

        # Purchase order selection (optional)
        self.po_combo = QComboBox()
        self.po_combo.addItem("-- General Payment (not linked to specific PO) --", None)
        self.load_unpaid_purchase_orders()
        form_layout.addRow(QLabel("Apply to PO:"), self.po_combo)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Optional notes about this payment")
        form_layout.addRow(QLabel("Notes:"), self.notes)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Record Payment")
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 20px;")
        self.btn_save.clicked.connect(self.save_payment)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.retranslateUi()

    def load_unpaid_purchase_orders(self):
        """Load unpaid or partially paid purchase orders for this supplier"""
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, po_no, total_amount, payment_status
            FROM purchase_orders
            WHERE supplier_id = ? AND payment_status IN ('Unpaid', 'Partial')
            ORDER BY order_date DESC
        """, (self.supplier_id,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            po_id, po_no, amount, status = row
            self.po_combo.addItem(f"{po_no} - {format_money(amount)} ({status})", po_id)

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
            self.setWindowTitle(f"ငွေပေးချေမှု မှတ်တမ်းတင်ရန် - {self.supplier_name}")
            self.balance_label.setText(f"လက်ကျန်ကြွေးငွေ: {format_money(self.current_balance)}")
            self.amount_spin.setSuffix(" ကျပ်")
        else:
            self.setWindowTitle(f"Record Payment - {self.supplier_name}")
            self.balance_label.setText(f"Current Balance: {format_money(self.current_balance)}")

    def save_payment(self):
        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid payment amount.")
            return

        payment_date = self.payment_date.date().toString("yyyy-MM-dd")
        ref_no = self.reference_no.text().strip() or f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payment_type = self.payment_type.currentText()
        notes = self.notes.toPlainText()
        po_id = self.po_combo.currentData()

        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")

            # Insert payment record
            cursor.execute("""
                INSERT INTO supplier_payments 
                (supplier_id, amount, payment_date, reference_no, payment_type, notes, purchase_order_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.supplier_id, amount, payment_date, ref_no, payment_type, notes, po_id))

            # Update purchase order payment status if linked to a PO
            if po_id:
                cursor.execute("""
                    SELECT total_amount, payment_status, COALESCE((
                        SELECT SUM(amount) FROM supplier_payments 
                        WHERE purchase_order_id = ? AND payment_type != 'Purchase'
                    ), 0) as total_paid
                    FROM purchase_orders WHERE id = ?
                """, (po_id, po_id))
                po = cursor.fetchone()
                if po:
                    total_amount, current_status, total_paid = po
                    new_total_paid = total_paid + amount
                    
                    if new_total_paid >= total_amount:
                        new_status = "Paid"
                    elif new_total_paid > 0:
                        new_status = "Partial"
                    else:
                        new_status = current_status
                    
                    cursor.execute("""
                        UPDATE purchase_orders 
                        SET payment_status = ? 
                        WHERE id = ?
                    """, (new_status, po_id))

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
