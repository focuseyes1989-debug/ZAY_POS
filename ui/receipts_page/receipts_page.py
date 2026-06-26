# ui/receipts_page/receipts_page.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget
)
from PyQt6.QtCore import Qt
from ui.receipts_page.receipts_tab import ReceiptsTab
from ui.receipts_page.refund_tab import RefundTab
from ui.receipts_page.discount_tab import DiscountTab
from ui.receipts_page.credit_tab import CreditTab  # ✅ Added
from utils.permissions import PermissionManager, Permission
from utils.language import lang


class ReceiptsPage(QWidget):
    def __init__(self, user_id=None, user_role=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.user_role = user_role
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                padding: 10px 20px;
                font-weight: bold;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
            QTabBar::tab:hover:!selected {
                background-color: palette(midlight);
            }
        """)
        
        # Create tabs
        self.receipts_tab = ReceiptsTab(user_id, user_role, self)
        self.refund_tab = RefundTab(user_id, user_role, self)
        self.discount_tab = DiscountTab(user_id, user_role, self)
        self.credit_tab = CreditTab(user_id, user_role, self)  # ✅ Added
        
        # Add tabs
        self.tab_widget.addTab(self.receipts_tab, "📋 Receipts")
        self.tab_widget.addTab(self.refund_tab, "↩️ Refunded")
        self.tab_widget.addTab(self.discount_tab, "🏷️ Discounted")
        self.tab_widget.addTab(self.credit_tab, "💳 Credit")  # ✅ Added
        
        # Apply permissions
        self.apply_permissions()
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
        # Language support
        lang.language_changed.connect(self.retranslateUi)
        self.retranslateUi()
    
    def apply_permissions(self):
        """Apply permissions to tabs based on user role"""
        if self.user_id:
            # Refund tab
            if not PermissionManager.user_has_permission(self.user_id, Permission.REFUND_RECEIPT):
                index = self.tab_widget.indexOf(self.refund_tab)
                if index >= 0:
                    self.tab_widget.setTabEnabled(index, False)
                    self.tab_widget.setTabToolTip(index, "You don't have permission to refund receipts")
            
            # Discount tab
            if not PermissionManager.user_has_permission(self.user_id, Permission.EDIT_SETTINGS):
                index = self.tab_widget.indexOf(self.discount_tab)
                if index >= 0:
                    self.tab_widget.setTabEnabled(index, False)
                    self.tab_widget.setTabToolTip(index, "You don't have permission to manage discounts")
            
            # Credit tab
            if not PermissionManager.user_has_permission(self.user_id, Permission.VIEW_CREDIT):
                index = self.tab_widget.indexOf(self.credit_tab)
                if index >= 0:
                    self.tab_widget.setTabEnabled(index, False)
                    self.tab_widget.setTabToolTip(index, "You don't have permission to view credit receipts")
    
    def retranslateUi(self):
        """Update UI text when language changes"""
        lang_code = lang.get_current()
        if lang_code == "my":
            self.tab_widget.setTabText(0, "📋 ပြေစာများ")
            self.tab_widget.setTabText(1, "↩️ ပြန်အမ်းပြီး")
            self.tab_widget.setTabText(2, "🏷️ လျှော့စျေး")
            self.tab_widget.setTabText(3, "💳 အကြွေး")  # ✅ Added
        else:
            self.tab_widget.setTabText(0, "📋 Receipts")
            self.tab_widget.setTabText(1, "↩️ Refunded")
            self.tab_widget.setTabText(2, "🏷️ Discounted")
            self.tab_widget.setTabText(3, "💳 Credit")  # ✅ Added
    
    def refresh_all(self):
        """Refresh all tabs"""
        self.receipts_tab.load_sales()
        self.refund_tab.load_refunded_sales()
        self.discount_tab.load_discounts()
        self.credit_tab.load_credit_receipts()  # ✅ Added
    
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        self.refresh_all()