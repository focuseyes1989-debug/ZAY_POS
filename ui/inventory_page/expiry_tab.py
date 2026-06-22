from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, QDate
from models.database import connect_db
from ui.widgets.pagination_widget import PaginationWidget
from datetime import date


class ExpiryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)
        layout.addWidget(self.pagination)

        self.setLayout(layout)

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

    def on_page_changed(self, page: int, page_size: int):
        self.load_data(page, page_size)

    def refresh(self):
        self.load_data()

    def load_data(self, page=1, page_size=50):
        lang = self.get_lang()
        if lang == "my":
            headers = [
                "ပစ္စည်းအမည်", "အသုတ်အမှတ်", "သက်တမ်းကုန်ရက်", "ကျန်ရက်များ",
                "အရေအတွက်", "ပေးသွင်းသူ", "အခြေအနေ"
            ]
        else:
            headers = [
                "Product Name", "Batch No", "Expiry Date", "Remaining Days",
                "Quantity", "Supplier", "Status"
            ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        today = date.today()
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM products 
            WHERE (sold_by IS NULL OR sold_by != 'Service')
              AND expire_date IS NOT NULL AND expire_date != ''
        """)
        total_items = cursor.fetchone()[0]
        self.pagination.set_total_items(total_items, emit_signal=False)

        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT p.name, p.batch_no, p.expire_date, p.stock,
                   s.name as supplier
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE (p.sold_by IS NULL OR p.sold_by != 'Service')
              AND p.expire_date IS NOT NULL AND p.expire_date != ''
            ORDER BY p.expire_date
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row in rows:
            name, batch, exp, qty, supplier = row
            try:
                exp_d = date.fromisoformat(exp)
                remaining = (exp_d - today).days
                if remaining < 0:
                    status = "Expired" if lang != "my" else "သက်တမ်းကုန်ပြီ"
                elif remaining <= 30:
                    status = "Near Expiry" if lang != "my" else "သက်တမ်းနီးပြီ"
                else:
                    status = "OK" if lang != "my" else "ကောင်းသည်"
            except:
                remaining = "?"
                status = "Invalid Date" if lang != "my" else "ရက်စွဲမမှန်ပါ"
            row_data = [name, batch or "", exp, remaining, qty, supplier or "", status]
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, val in enumerate(row_data):
                self.table.setItem(r, col, QTableWidgetItem(str(val)))