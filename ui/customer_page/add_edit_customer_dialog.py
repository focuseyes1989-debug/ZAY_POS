# ui/customer_page/add_edit_customer_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox, QTextEdit,
    QDialogButtonBox, QLabel
)
from PyQt6.QtGui import QIcon
from utils.currency import get_currency_symbol


class AddEditCustomerDialog(QDialog):
    def __init__(self, customer_data=None, language="en", parent=None):
        super().__init__(parent)
        self.customer_data = customer_data
        self.language = language
        self.setMinimumWidth(450)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))

        layout = QFormLayout()
        
        self.lbl_name = QLabel()
        self.name_edit = QLineEdit()
        self.lbl_phone = QLabel()
        self.phone_edit = QLineEdit()
        self.lbl_email = QLabel()
        self.email_edit = QLineEdit()
        self.lbl_address = QLabel()
        self.address_edit = QLineEdit()
        self.lbl_credit_limit = QLabel()
        self.credit_limit_edit = QDoubleSpinBox()
        self.credit_limit_edit.setRange(0, 999999999)
        self.credit_limit_edit.setDecimals(0)
        symbol = get_currency_symbol()
        self.credit_limit_edit.setPrefix(f"{symbol} ")
        self.lbl_remarks = QLabel()
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(80)

        layout.addRow(self.lbl_name, self.name_edit)
        layout.addRow(self.lbl_phone, self.phone_edit)
        layout.addRow(self.lbl_email, self.email_edit)
        layout.addRow(self.lbl_address, self.address_edit)
        layout.addRow(self.lbl_credit_limit, self.credit_limit_edit)
        layout.addRow(self.lbl_remarks, self.remarks_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

        self.setLayout(layout)

        if customer_data:
            self.name_edit.setText(customer_data.get("name", ""))
            self.phone_edit.setText(customer_data.get("phone", ""))
            self.email_edit.setText(customer_data.get("email", ""))
            self.address_edit.setText(customer_data.get("address", ""))
            self.credit_limit_edit.setValue(customer_data.get("credit_limit", 0))
            self.remarks_edit.setPlainText(customer_data.get("remarks", ""))

        self.retranslateUi()

    def retranslateUi(self):
        if self.language == "my":
            self.setWindowTitle("ဝယ်ယူသူပြင်ဆင်ရန်" if self.customer_data else "ဝယ်ယူသူအသစ်")
            self.lbl_name.setText("အမည်:")
            self.lbl_phone.setText("ဖုန်း:")
            self.lbl_email.setText("အီးမေး:")
            self.lbl_address.setText("လိပ်စာ:")
            self.lbl_credit_limit.setText("ခရက်ဒစ်ကန့်သတ်ချက်:")
            self.lbl_remarks.setText("မှတ်ချက်:")
            ok_btn = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
            cancel_btn = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
            if ok_btn:
                ok_btn.setText("သိမ်းမည်")
            if cancel_btn:
                cancel_btn.setText("မလုပ်တော့")
        else:
            self.setWindowTitle("Edit Customer" if self.customer_data else "Add Customer")
            self.lbl_name.setText("Name:")
            self.lbl_phone.setText("Phone:")
            self.lbl_email.setText("Email:")
            self.lbl_address.setText("Address:")
            self.lbl_credit_limit.setText("Credit Limit:")
            self.lbl_remarks.setText("Remarks:")
            ok_btn = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
            cancel_btn = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
            if ok_btn:
                ok_btn.setText("OK")
            if cancel_btn:
                cancel_btn.setText("Cancel")

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "credit_limit": self.credit_limit_edit.value(),
            "remarks": self.remarks_edit.toPlainText().strip()
        }