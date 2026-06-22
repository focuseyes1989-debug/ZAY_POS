# ui/main_window/main_window_actions.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from models.database import connect_db
from ui.reports.reports_dialog import ReportsDialog
from ui.profit_report_dialog import ProfitReportDialog
from ui.outstanding_report_dialog import OutstandingReportDialog
from ui.auto_backup_dialog import AutoBackupDialog
from ui.role_management_dialog import RoleManagementDialog
from ui.activity_log_page import ActivityLogPage
from ui.themes import apply_theme
from utils.translations import tr
from utils.activity_logger import log_activity
from loguru import logger
import os


class MainWindowActions:
    """Handle action methods for MainWindow"""
    
    # ========== THEME ACTIONS ==========
    def save_theme_to_db(self, theme_name):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'theme'", (theme_name,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save theme: {e}")

    def apply_theme(self, theme_name):
        logger.info(f"Switching theme to: {theme_name}")
        app = QApplication.instance()
        if app:
            from ui.themes import apply_theme as apply_theme_style
            apply_theme_style(app, theme_name)
        if not self.follow_system_theme:
            self.save_theme_to_db(theme_name)

    def set_theme_menu_enabled(self, enabled):
        if hasattr(self, 'dark_theme_action'):
            self.dark_theme_action.setEnabled(enabled)
        if hasattr(self, 'light_theme_action'):
            self.light_theme_action.setEnabled(enabled)
    
    # ========== REPORT ACTIONS ==========
    def open_sales_report(self):
        dialog = ReportsDialog(self)
        dialog.set_default_tab(0)
        dialog.exec()

    def open_expense_report(self):
        dialog = ReportsDialog(self)
        dialog.set_default_tab(1)
        dialog.exec()

    def open_profit_loss_report(self):
        from ui.profit_loss_report_dialog import ProfitLossReportDialog
        dialog = ProfitLossReportDialog(self)
        dialog.exec()

    def open_profit_report(self):
        dialog = ProfitReportDialog(self)
        dialog.exec()

    def open_financial_summary(self):
        dialog = ReportsDialog(self)
        dialog.set_default_tab(3)
        dialog.exec()

    # ========== CREDIT ACTIONS ==========
    def open_outstanding_report(self):
        dialog = OutstandingReportDialog(self)
        dialog.exec()

    # ========== BACKUP ACTIONS ==========
    def open_auto_backup(self):
        dialog = AutoBackupDialog(self.auto_backup_manager, self)
        dialog.exec()

    # ========== ROLE MANAGEMENT ==========
    def open_role_management(self):
        dialog = RoleManagementDialog(self)
        dialog.exec()

    # ========== USER ACTIONS ==========
    def logout(self):
        logger.info(f"User {self.current_user['username']} logging out")
        log_activity(self.current_user["id"], self.current_user["username"], "Logout", "User logged out")
        self.logout_triggered = True
        self.logout_signal.emit()
        self.close()

    def exit_app(self):
        logger.info("Application exit requested")
        self.logout_triggered = False
        self.close()

    def show_activity_log(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("activity_log"))
        dialog.resize(1000, 600)
        layout = QVBoxLayout()
        layout.addWidget(ActivityLogPage())
        dialog.setLayout(layout)
        dialog.exec()

    # ========== SETTINGS ACTIONS ==========
    def refresh_general_settings(self):
        if hasattr(self, 'sales_page'):
            if hasattr(self.sales_page, 'load_settings'):
                self.sales_page.load_settings()
            if hasattr(self.sales_page, 'load_loyalty_settings'):
                self.sales_page.load_loyalty_settings()
            if hasattr(self.sales_page, 'load_payment_types'):
                self.sales_page.load_payment_types()
            if hasattr(self.sales_page, 'update_totals'):
                self.sales_page.update_totals()
            logger.info("General settings refreshed in SalesPage")

    def refresh_currency(self):
        if hasattr(self, 'sales_page'):
            if hasattr(self.sales_page, 'cart_widget') and hasattr(self.sales_page.cart_widget, 'refresh_table'):
                self.sales_page.cart_widget.refresh_table()
            elif hasattr(self.sales_page, 'load_cart'):
                self.sales_page.load_cart()
            if hasattr(self.sales_page, 'totals_widget') and hasattr(self.sales_page.totals_widget, 'update_totals'):
                self.sales_page.totals_widget.update_totals()
            elif hasattr(self.sales_page, 'update_totals'):
                self.sales_page.update_totals()
            logger.info("Currency refreshed in SalesPage")

    def refresh_shop_info(self):
        """Refresh shop logo and title"""
        self.update_shop_logo()
        self.update_shop_title()
        logger.info("Shop info refreshed")

    def update_shop_logo(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='shop_logo'")
            row = cursor.fetchone()
            conn.close()
            logo_path = row[0] if row else ""
            if logo_path and os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.logo_label.setPixmap(pixmap)
                    self.logo_label.setVisible(True)
                else:
                    self.logo_label.setVisible(False)
            else:
                self.logo_label.setVisible(False)
        except Exception as e:
            logger.error(f"Failed to load shop logo: {e}")
            self.logo_label.setVisible(False)

    def update_shop_title(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='shop_name'")
            row = cursor.fetchone()
            conn.close()
            shop_name = row[0] if row and row[0] else "ZAY POS"
        except Exception as e:
            logger.error(f"Failed to load shop name: {e}")
            shop_name = "ZAY POS"
        self.title_label.setText(shop_name)