# ui/reports/reports_dialog.py
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QTimer
from ui.reports.base_report_dialog import BaseReportDialog
from ui.reports.sales_report import SalesReportTab
from ui.reports.expense_report import ExpenseReportTab
from ui.reports.profit_loss_report import ProfitLossReportTab
from ui.reports.financial_summary import FinancialSummaryTab
from loguru import logger


class ReportsDialog(BaseReportDialog):
    def __init__(self, parent=None):
        self.current_tab = 0
        self._is_loading = False
        self._pending_refresh = False
        self._default_tab_index = 0
        super().__init__(parent)
        self.setWindowTitle("Reports")
        
        # Setup tabs after everything is initialized
        QTimer.singleShot(100, self._init_tabs)
    
    def _init_tabs(self):
        """Initialize tabs after dialog is shown"""
        from_date, to_date = self.get_date_range()
        self.set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        
        # Load all tabs in background
        self.sales_tab.refresh(from_date, to_date)
        self.expense_tab.refresh(from_date, to_date)
        self.pl_tab.refresh(from_date, to_date)
        self.summary_tab.refresh(from_date, to_date)
        
        # Hide progress after all tabs loaded
        QTimer.singleShot(500, self._check_all_loaded)
    
    def _check_all_loaded(self):
        """Check if all tabs are loaded"""
        if not self.progress_bar.isVisible():
            return
        
        loading = False
        for tab in [self.sales_tab, self.expense_tab, self.pl_tab, self.summary_tab]:
            if hasattr(tab, '_is_loading') and tab._is_loading:
                loading = True
                break
        
        if not loading:
            self.progress_bar.setVisible(False)
            self.set_buttons_enabled(True)
            
            if self._default_tab_index > 0:
                self.tabs.setCurrentIndex(self._default_tab_index)
        else:
            QTimer.singleShot(500, self._check_all_loaded)
    
    def setup_tabs(self):
        self.sales_tab = SalesReportTab(self)
        self.tabs.addTab(self.sales_tab, "Sales Report")
        
        self.expense_tab = ExpenseReportTab(self)
        self.tabs.addTab(self.expense_tab, "Expense Report")
        
        self.pl_tab = ProfitLossReportTab(self)
        self.tabs.addTab(self.pl_tab, "Profit & Loss")
        
        self.summary_tab = FinancialSummaryTab(self)
        self.tabs.addTab(self.summary_tab, "Financial Summary")
        
        self.tabs.currentChanged.connect(self.on_tab_changed_debounced)
    
    def set_default_tab(self, index):
        """Set default tab index"""
        self._default_tab_index = index
        if hasattr(self, 'tabs') and self.tabs.count() > index:
            self.tabs.setCurrentIndex(index)
    
    def on_tab_changed_debounced(self, index):
        """Handle tab change with debounce"""
        if self._is_loading:
            return
        
        self.current_tab = index
        QTimer.singleShot(50, self._refresh_current_tab_safe)
    
    def _refresh_current_tab_safe(self):
        """Refresh current tab safely"""
        if self._is_loading:
            return
        
        self._is_loading = True
        self._pending_refresh = False
        
        from_date, to_date = self.get_date_range()
        current_index = self.tabs.currentIndex()
        
        if current_index == 0:
            if self.sales_tab.table.rowCount() == 0:
                self.sales_tab.refresh(from_date, to_date)
            else:
                self._is_loading = False
                self.set_buttons_enabled(True)
        elif current_index == 1:
            if self.expense_tab.table.rowCount() == 0:
                self.expense_tab.refresh(from_date, to_date)
            else:
                self._is_loading = False
                self.set_buttons_enabled(True)
        elif current_index == 2:
            if self.pl_tab.table.rowCount() == 0:
                self.pl_tab.refresh(from_date, to_date)
            else:
                self._is_loading = False
                self.set_buttons_enabled(True)
        elif current_index == 3:
            if self.summary_tab.sales_category_table.rowCount() == 0:
                self.summary_tab.refresh(from_date, to_date)
            else:
                self._is_loading = False
                self.set_buttons_enabled(True)
    
    def refresh_current_tab(self):
        """Force refresh current tab"""
        if self._is_loading:
            self._pending_refresh = True
            return
        
        self.set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        
        from_date, to_date = self.get_date_range()
        current_index = self.tabs.currentIndex()
        
        self._is_loading = True
        
        if current_index == 0:
            self.sales_tab.refresh(from_date, to_date)
        elif current_index == 1:
            self.expense_tab.refresh(from_date, to_date)
        elif current_index == 2:
            self.pl_tab.refresh(from_date, to_date)
        elif current_index == 3:
            self.summary_tab.refresh(from_date, to_date)
    
    def export_current_report(self):
        from_date, to_date = self.get_date_range()
        current_index = self.tabs.currentIndex()
        
        if current_index == 0:
            self.sales_tab.export(from_date, to_date)
        elif current_index == 1:
            self.expense_tab.export(from_date, to_date)
        elif current_index == 2:
            self.pl_tab.export(from_date, to_date)
        elif current_index == 3:
            self.summary_tab.export(from_date, to_date)
    
    def on_refresh_complete(self):
        """Called when a tab finishes refreshing"""
        self._is_loading = False
        
        loading = False
        for tab in [self.sales_tab, self.expense_tab, self.pl_tab, self.summary_tab]:
            if hasattr(tab, '_is_loading') and tab._is_loading:
                loading = True
                break
        
        if not loading:
            self.progress_bar.setVisible(False)
            self.set_buttons_enabled(True)
            
            if self._pending_refresh:
                self._pending_refresh = False
                QTimer.singleShot(100, self.refresh_current_tab)
    
    def on_refresh_error(self, error_msg):
        logger.error(f"Report error: {error_msg}")
        QMessageBox.warning(self, "Error", f"Failed to load report: {error_msg}")
        self._is_loading = False
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
    
    def retranslateUi(self):
        lang = self.get_lang()
        if lang == "my":
            self.setWindowTitle("အစီရင်ခံစာများ")
            if self.tabs.count() > 0:
                self.tabs.setTabText(0, "ရောင်းအားအစီရင်ခံစာ")
                self.tabs.setTabText(1, "အသုံးစရိတ်အစီရင်ခံစာ")
                self.tabs.setTabText(2, "အမြတ်အစွန်းအစီရင်ခံစာ")
                self.tabs.setTabText(3, "ဘဏ္ဍာရေးအကျဉ်းချုပ်")
            self.btn_refresh.setText("ပြန်လည်")
            self.btn_export.setText("📊 Excel ထုတ်မည်")
            self.btn_close.setText("ပိတ်မည်")
        else:
            self.setWindowTitle("Reports")
            if self.tabs.count() > 0:
                self.tabs.setTabText(0, "Sales Report")
                self.tabs.setTabText(1, "Expense Report")
                self.tabs.setTabText(2, "Profit & Loss")
                self.tabs.setTabText(3, "Financial Summary")
            self.btn_refresh.setText("Refresh")
            self.btn_export.setText("📊 Export Excel")
            self.btn_close.setText("Close")
    
    def showEvent(self, event):
        self.apply_card_style()
        super().showEvent(event)