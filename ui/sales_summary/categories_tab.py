# ui/sales_summary/categories_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from models.database import connect_db
from utils.currency import format_money, get_currency_symbol


class CategoriesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.full_data = []
        
        layout = QVBoxLayout()
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search category name...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #5865f2;
            }
        """)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        
        self.clear_btn = self._create_clear_button()
        search_layout.addWidget(self.clear_btn)
        
        layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def _create_clear_button(self):
        btn = QPushButton("✕ Clear")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn.clicked.connect(self.clear_search)
        return btn
    
    def clear_search(self):
        self.search_input.clear()
    
    def filter_table(self):
        search_text = self.search_input.text().lower().strip()
        
        if not search_text:
            self._display_data(self.full_data)
            return
        
        filtered = [row for row in self.full_data if search_text in row[0].lower()]
        self._display_data(filtered)
    
    def _display_data(self, rows):
        symbol = get_currency_symbol()
        lang_code = self.parent_page.get_lang() if self.parent_page else "en"
        
        self.table.setRowCount(0)
        for row_data in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row_data[0] if row_data[0] else "Uncategorized"))
            self.table.setItem(r, 1, QTableWidgetItem(str(row_data[1])))
            self.table.setItem(r, 2, QTableWidgetItem(format_money(row_data[2], symbol)))
            self.table.setItem(r, 3, QTableWidgetItem(format_money(row_data[3], symbol)))
            profit = row_data[2] - row_data[3]
            self.table.setItem(r, 4, QTableWidgetItem(format_money(profit, symbol)))
        
        if lang_code == "my":
            self.table.setHorizontalHeaderLabels([
                "အမျိုးအစား", "ရောင်းရသည့်အရေအတွက်", "စုစုပေါင်းရောင်းအား",
                "ကုန်ကျစရိတ်", "အသားတင်အမြတ်"
            ])
        else:
            self.table.setHorizontalHeaderLabels([
                "Category", "Items Sold", "Net Sales", "Cost of Goods", "Gross Profit"
            ])
    
    def load(self, from_date, to_date):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(products.category, 'Uncategorized') as category,
                   COALESCE(SUM(sale_items.qty), 0) as items_sold,
                   COALESCE(SUM(sale_items.total), 0) as net_sales,
                   COALESCE(SUM(products.cost * sale_items.qty), 0) as cogs
            FROM sale_items
            JOIN sales ON sale_items.sale_id = sales.id
            LEFT JOIN products ON sale_items.product_name = products.name
            WHERE sales.status = 'completed' AND date(sales.created_at) BETWEEN ? AND ?
            GROUP BY products.category
            ORDER BY net_sales DESC
        """, (from_date, to_date))
        rows = cursor.fetchall()
        conn.close()
        
        self.full_data = [list(row) for row in rows]
        
        if self.search_input.text().strip():
            self.filter_table()
        else:
            self._display_data(self.full_data)
    
    def retranslateUi(self):
        lang_code = self.parent_page.get_lang() if self.parent_page else "en"
        if lang_code == "my":
            self.search_input.setPlaceholderText("အမျိုးအစားရှာရန်...")
            self.clear_btn.setText("✕ ရှင်းမည်")
        else:
            self.search_input.setPlaceholderText("Search category name...")
            self.clear_btn.setText("✕ Clear")