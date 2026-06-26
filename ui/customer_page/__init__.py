# ui/customer_page/__init__.py
from ui.customer_page.customers_page import CustomersPage
from ui.customer_page.customer_display import CustomerDisplayWindow
from ui.customer_page.customer_ledger_dialog import CustomerLedgerDialog
from ui.customer_page.credit_sale_dialog import CreditSaleDialog
from ui.customer_page.credit_payment_dialog import CreditPaymentDialog
from ui.customer_page.outstanding_report_dialog import OutstandingReportDialog
from ui.customer_page.add_edit_customer_dialog import AddEditCustomerDialog

__all__ = [
    'CustomersPage',
    'CustomerDisplayWindow',
    'CustomerLedgerDialog',
    'CreditSaleDialog',
    'CreditPaymentDialog',
    'OutstandingReportDialog',
    'AddEditCustomerDialog',
]