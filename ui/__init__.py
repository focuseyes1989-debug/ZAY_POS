# ui/__init__.py
"""
UI package for ZAY POS application.
"""

from ui.customer_page.customer_display import CustomerDisplayWindow
from ui.receipt_dialog import ReceiptDialog
from ui.receipt_detail_dialog import ReceiptDetailDialog

__all__ = [
    'CustomerDisplayWindow',
    'ReceiptDialog',
    'ReceiptDetailDialog',
]