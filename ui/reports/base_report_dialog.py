# ui/reports/base_report_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QDateEdit, QMessageBox, QFileDialog, QProgressBar,
    QTabWidget, QWidget, QFrame, QTableWidget, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, QThread, QObject, pyqtSignal
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from datetime import datetime
from loguru import logger
import csv


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict)


class BaseReportWorker(QObject):
    """Base worker for report generation"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict)
    
    def __init__(self, from_date, to_date):
        super().__init__()
        self.from_date = from_date
        self.to_date = to_date
    
    def run(self):
        raise NotImplementedError("Subclasses must implement run()")


class BaseReportDialog(QDialog):
    """Base class for all report dialogs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)
        
        # Thread management
        self.threads = []
        self.workers = []
        
        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(15)
        
        # Date range
        self.create_date_range()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setStyleSheet("height: 20px;")
        self.main_layout.addWidget(self.progress_bar)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Content area
        self.setup_tabs()
        self.main_layout.addWidget(self.tabs)
        
        # Buttons
        self.create_buttons()
        
        self.setLayout(self.main_layout)
        self.apply_card_style()
        self.refresh_current_tab()
    
    def create_date_range(self):
        date_group = QGroupBox("Date Range")
        date_layout = QHBoxLayout()
        
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.from_date)
        
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.to_date)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_current_tab)
        date_layout.addWidget(self.btn_refresh)
        
        self.btn_export = QPushButton("📊 Export Excel")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.btn_export.clicked.connect(self.export_current_report)
        date_layout.addWidget(self.btn_export)
        
        date_layout.addStretch()
        date_group.setLayout(date_layout)
        self.main_layout.addWidget(date_group)
    
    def create_buttons(self):
        btn_layout = QHBoxLayout()
        self.btn_close = QPushButton("Close")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #40444b;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 25px;
            }
            QPushButton:hover {
                background-color: #5865f2;
            }
        """)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        self.main_layout.addLayout(btn_layout)
    
    def setup_tabs(self):
        """Override this method to add tabs"""
        pass
    
    def get_date_range(self):
        return (
            self.from_date.date().toString("yyyy-MM-dd"),
            self.to_date.date().toString("yyyy-MM-dd")
        )
    
    def get_theme(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='theme'")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "Light"
        except:
            return "Light"
    
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
    
    def get_currency_symbol(self):
        return get_currency_symbol()
    
    def apply_card_style(self):
        theme = self.get_theme()
        
        if theme == "Dark":
            card_style = """
                QFrame#reportCard {
                    background-color: #2f3136;
                    border: 1px solid #40444b;
                    border-radius: 12px;
                    padding: 15px;
                }
                QFrame#reportCard:hover {
                    background-color: #383a40;
                    border: 1px solid #5865f2;
                }
            """
            amount_style = "color: #ffffff; font-size: 22pt; font-weight: bold;"
            table_style = """
                QTableWidget {
                    background-color: #2f3136;
                    alternate-background-color: #36393f;
                    selection-background-color: #40444b;
                    selection-color: #ffffff;
                    gridline-color: #202225;
                    border: 1px solid #202225;
                    border-radius: 6px;
                }
                QHeaderView::section {
                    background-color: #202225;
                    padding: 8px;
                    border: none;
                    font-weight: 600;
                    color: #b9bbbe;
                }
            """
        else:
            card_style = """
                QFrame#reportCard {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 12px;
                    padding: 15px;
                }
                QFrame#reportCard:hover {
                    background-color: #f8f9fa;
                    border: 1px solid #adb5bd;
                }
            """
            amount_style = "color: #212529; font-size: 22pt; font-weight: bold;"
            table_style = """
                QTableWidget {
                    background-color: white;
                    alternate-background-color: #f8f9fa;
                    selection-background-color: #e3f2fd;
                    selection-color: #1976d2;
                    gridline-color: #dee2e6;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                }
                QHeaderView::section {
                    background-color: #f1f3f5;
                    padding: 8px;
                    border: none;
                    font-weight: 600;
                    color: #495057;
                }
            """
        
        for card in self.findChildren(QFrame, "reportCard"):
            card.setStyleSheet(card_style)
            for child in card.findChildren(QLabel):
                if "amount" in child.objectName() or "total" in child.objectName().lower():
                    child.setStyleSheet(amount_style)
        
        for table in self.findChildren(QTableWidget):
            table.setStyleSheet(table_style)
    
    def create_card(self, title, initial_text="Loading...", color="#3498db"):
        card = QFrame()
        card.setObjectName("reportCard")
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)
        
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 10pt; color: #6c757d;")
        
        amount = QLabel(initial_text)
        amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        amount.setObjectName("amount_label")
        amount.setStyleSheet(f"color: {color}; font-size: 22pt; font-weight: bold;")
        
        layout.addWidget(label)
        layout.addWidget(amount)
        card.amount_label = amount
        return card
    
    def update_card(self, card, amount, symbol=None):
        if symbol:
            card.amount_label.setText(format_money(amount, symbol))
        else:
            card.amount_label.setText(str(amount))
    
    def set_buttons_enabled(self, enabled):
        self.btn_refresh.setEnabled(enabled)
        self.btn_export.setEnabled(enabled)
        self.btn_close.setEnabled(enabled)
    
    def cleanup_threads(self):
        for thread in self.threads[:]:
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(2000)
            except (RuntimeError, AttributeError):
                pass
        self.threads.clear()
        self.workers.clear()
    
    def closeEvent(self, event):
        self.cleanup_threads()
        event.accept()
    
    def showEvent(self, event):
        self.apply_card_style()
        super().showEvent(event)
    
    def refresh_current_tab(self):
        raise NotImplementedError("Subclasses must implement refresh_current_tab()")
    
    def export_current_report(self):
        raise NotImplementedError("Subclasses must implement export_current_report()")