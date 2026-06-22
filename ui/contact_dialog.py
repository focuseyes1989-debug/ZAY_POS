from ui.base_form_dialog import BaseFormDialog

class BaseContactDialog(BaseFormDialog):
    def __init__(self, title, fields, data=None, parent=None):
        super().__init__(title, fields, parent, data)

class SupplierDialog(BaseContactDialog):
    def __init__(self, supplier_id=None, supplier_data=None, parent=None):
        self.supplier_id = supplier_id
        fields = [
            {'name': 'name', 'label': 'Supplier Name', 'type': 'line', 'required': True},
            {'name': 'contact_person', 'label': 'Contact Person', 'type': 'line'},
            {'name': 'phone', 'label': 'Phone', 'type': 'line'},
            {'name': 'email', 'label': 'Email', 'type': 'line'},
            {'name': 'address', 'label': 'Address', 'type': 'line'},
            {'name': 'company_name', 'label': 'Company Name', 'type': 'line'},
            {'name': 'tax_number', 'label': 'Tax Number', 'type': 'line'},
            {'name': 'website', 'label': 'Website', 'type': 'line'},
            {'name': 'payment_terms', 'label': 'Payment Terms', 'type': 'combo', 'items': ['Cash', 'Credit 7 Days', 'Credit 15 Days', 'Credit 30 Days']},
            {'name': 'bank_account', 'label': 'Bank Account', 'type': 'line'},
            {'name': 'status', 'label': 'Status', 'type': 'combo', 'items': ['Active', 'Inactive']},
        ]
        title = "Supplier Information" if supplier_id is None else "Edit Supplier"
        super().__init__(title, fields, supplier_data, parent)

class AddEditCustomerDialog(BaseContactDialog):
    def __init__(self, customer_data=None, language="en", parent=None):
        fields = [
            {'name': 'name', 'label': 'Name', 'type': 'line', 'required': True},
            {'name': 'phone', 'label': 'Phone', 'type': 'line'},
            {'name': 'email', 'label': 'Email', 'type': 'line'},
            {'name': 'address', 'label': 'Address', 'type': 'line'},
        ]
        title = "Edit Customer" if customer_data else "Add Customer"
        super().__init__(title, fields, customer_data, parent)
        self.language = language
        self.retranslateUi()

    def retranslateUi(self):
        if self.language == "my":
            # translate labels
            pass