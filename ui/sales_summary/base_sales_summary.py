# ui/sales_summary/base_sales_summary.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QPushButton,
    QFileDialog, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QDate
from models.database import connect_db
from utils.currency import format_money, get_currency_symbol
from utils.language import lang
from utils.excel_exporter import ExcelExporter
from datetime import datetime
import csv


class BaseSalesSummary(QWidget):
    """Base class for sales summary page with common functionality"""
    
    def __init__(self):
        super().__init__()
        self.items_data = []
        self.categories_data = []
        
    def get_date_range(self):
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        return from_date, to_date

    def get_currency_symbol(self):
        return get_currency_symbol()

    def get_lang(self):
        return lang.get_current()

    def set_today_range(self):
        today = QDate.currentDate()
        self.from_date.setDate(today)
        self.to_date.setDate(today)
        self.load_all_tabs()

    def set_this_week_range(self):
        today = QDate.currentDate()
        start_of_week = today.addDays(-(today.dayOfWeek() - 1))
        end_of_week = start_of_week.addDays(6)
        self.from_date.setDate(start_of_week)
        self.to_date.setDate(end_of_week)
        self.load_all_tabs()

    def set_this_month_range(self):
        today = QDate.currentDate()
        start_of_month = QDate(today.year(), today.month(), 1)
        end_of_month = QDate(today.year(), today.month(), today.daysInMonth())
        self.from_date.setDate(start_of_month)
        self.to_date.setDate(end_of_month)
        self.load_all_tabs()

    def set_last_month_range(self):
        today = QDate.currentDate()
        first_day_this_month = QDate(today.year(), today.month(), 1)
        last_day_last_month = first_day_this_month.addDays(-1)
        first_day_last_month = QDate(last_day_last_month.year(), last_day_last_month.month(), 1)
        self.from_date.setDate(first_day_last_month)
        self.to_date.setDate(last_day_last_month)
        self.load_all_tabs()

    def set_this_year_range(self):
        today = QDate.currentDate()
        start_of_year = QDate(today.year(), 1, 1)
        end_of_year = QDate(today.year(), 12, 31)
        self.from_date.setDate(start_of_year)
        self.to_date.setDate(end_of_year)
        self.load_all_tabs()

    def load_all_tabs(self):
        """Load all tabs - to be overridden"""
        pass

    def retranslateUi(self):
        """Retranslate UI - to be overridden"""
        pass