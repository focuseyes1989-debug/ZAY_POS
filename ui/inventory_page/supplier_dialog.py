from PyQt6.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QComboBox, QDialogButtonBox
from models.database import connect_db


class SupplierDialog(QDialog):
    def __init__(self, supplier_id=None, supplier_data=None, parent=None):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.setWindowTitle("Supplier Information")
        self.resize(400, 500)
        layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.contact_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.company_edit = QLineEdit()
        self.tax_edit = QLineEdit()
        self.website_edit = QLineEdit()
        self.payment_terms = QComboBox()
        self.payment_terms.addItems(["Cash", "Credit 7 Days", "Credit 15 Days", "Credit 30 Days"])
        self.bank_edit = QLineEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive"])
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.labels = {
            "name": QLabel("Supplier Name:"),
            "contact": QLabel("Contact Person:"),
            "phone": QLabel("Phone:"),
            "email": QLabel("Email:"),
            "address": QLabel("Address:"),
            "company": QLabel("Company Name:"),
            "tax": QLabel("Tax Number:"),
            "website": QLabel("Website:"),
            "payment": QLabel("Payment Terms:"),
            "bank": QLabel("Bank Account:"),
            "status": QLabel("Status:")
        }
        self.btn_box = buttons

        layout.addRow(self.labels["name"], self.name_edit)
        layout.addRow(self.labels["contact"], self.contact_edit)
        layout.addRow(self.labels["phone"], self.phone_edit)
        layout.addRow(self.labels["email"], self.email_edit)
        layout.addRow(self.labels["address"], self.address_edit)
        layout.addRow(self.labels["company"], self.company_edit)
        layout.addRow(self.labels["tax"], self.tax_edit)
        layout.addRow(self.labels["website"], self.website_edit)
        layout.addRow(self.labels["payment"], self.payment_terms)
        layout.addRow(self.labels["bank"], self.bank_edit)
        layout.addRow(self.labels["status"], self.status_combo)
        layout.addRow(buttons)

        self.setLayout(layout)

        if supplier_data:
            self.name_edit.setText(supplier_data.get("name", ""))
            self.contact_edit.setText(supplier_data.get("contact_person", ""))
            self.phone_edit.setText(supplier_data.get("phone", ""))
            self.email_edit.setText(supplier_data.get("email", ""))
            self.address_edit.setText(supplier_data.get("address", ""))
            self.company_edit.setText(supplier_data.get("company_name", ""))
            self.tax_edit.setText(supplier_data.get("tax_number", ""))
            self.website_edit.setText(supplier_data.get("website", ""))
            idx = self.payment_terms.findText(supplier_data.get("payment_terms", "Cash"))
            if idx >= 0:
                self.payment_terms.setCurrentIndex(idx)
            self.bank_edit.setText(supplier_data.get("bank_account", ""))
            idx2 = self.status_combo.findText(supplier_data.get("status", "Active"))
            if idx2 >= 0:
                self.status_combo.setCurrentIndex(idx2)

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
            self.setWindowTitle("ပေးသွင်းသူအချက်အလက်" if self.supplier_id is None else "ပေးသွင်းသူပြင်ဆင်ရန်")
            translations = {
                "name": "ပေးသွင်းသူအမည်:",
                "contact": "ဆက်သွယ်ရမည့်သူ:",
                "phone": "ဖုန်း:",
                "email": "အီးမေး:",
                "address": "လိပ်စာ:",
                "company": "ကုမ္ပဏီအမည်:",
                "tax": "အခွန်အမှတ်:",
                "website": "ဝက်ဘ်ဆိုက်:",
                "payment": "ငွေပေးချေမှုအခြေအနေ:",
                "bank": "ဘဏ်အကောင့်:",
                "status": "အခြေအနေ:"
            }
            for key, text in translations.items():
                self.labels[key].setText(text)
            self.payment_terms.setItemText(0, "ငွေသား")
            self.payment_terms.setItemText(1, "ရက် ၇ အတွင်းငွေချေး")
            self.payment_terms.setItemText(2, "ရက် ၁၅ အတွင်းငွေချေး")
            self.payment_terms.setItemText(3, "ရက် ၃၀ အတွင်းငွေချေး")
            self.status_combo.setItemText(0, "သက်ဝင်")
            self.status_combo.setItemText(1, "မသက်ဝင်")
            self.btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("အိုကေ")
            self.btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("မလုပ်တော့")
        else:
            self.setWindowTitle("Supplier Information" if self.supplier_id is None else "Edit Supplier")
            for key, label in self.labels.items():
                label.setText(key.replace("_", " ").title() + ":")
            self.payment_terms.setItemText(0, "Cash")
            self.payment_terms.setItemText(1, "Credit 7 Days")
            self.payment_terms.setItemText(2, "Credit 15 Days")
            self.payment_terms.setItemText(3, "Credit 30 Days")
            self.status_combo.setItemText(0, "Active")
            self.status_combo.setItemText(1, "Inactive")
            self.btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("OK")
            self.btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "contact_person": self.contact_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "company_name": self.company_edit.text().strip(),
            "tax_number": self.tax_edit.text().strip(),
            "website": self.website_edit.text().strip(),
            "payment_terms": self.payment_terms.currentText(),
            "bank_account": self.bank_edit.text().strip(),
            "status": self.status_combo.currentText()
        }