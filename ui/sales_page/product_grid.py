# ui/sales_page/product_grid.py
import os
import functools
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox,
    QApplication, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QColor, QImageReader
from models.database import connect_db
from utils.currency import get_currency_symbol, format_money
from utils.paths import app_path
from ui.widgets.pagination_widget import PaginationWidget


def resolve_image_path(image_path: str):
    """Resolve image path to absolute path using app_path for relative paths."""
    if not image_path:
        return ""
    if os.path.isabs(image_path):
        return image_path
    return app_path(image_path)


@functools.lru_cache(maxsize=100)
def load_thumbnail(image_path: str, size: int = 50):
    """
    Load and cache product image thumbnail.
    Supports both relative and absolute paths.
    Will try multiple path resolutions if the image is not found.
    """
    if not image_path:
        return None
    
    # First attempt: resolve using app_path
    resolved_path = resolve_image_path(image_path)
    
    # If not found, try alternative resolutions
    if not resolved_path or not os.path.exists(resolved_path):
        # Try relative to current working directory
        if not os.path.isabs(image_path):
            alt_path = os.path.join(os.getcwd(), image_path)
            if os.path.exists(alt_path):
                resolved_path = alt_path
            else:
                # Try just the filename in product_images directory
                filename = os.path.basename(image_path)
                # Get the database directory
                db_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                alt_path2 = os.path.join(db_dir, 'database', 'product_images', filename)
                if os.path.exists(alt_path2):
                    resolved_path = alt_path2
                else:
                    # Try app_path again with just the filename
                    alt_path3 = app_path(os.path.join('database', 'product_images', filename))
                    if os.path.exists(alt_path3):
                        resolved_path = alt_path3
    
    # If still not found, return None
    if not resolved_path or not os.path.exists(resolved_path):
        return None
    
    # Load and scale the image
    reader = QImageReader(resolved_path)
    reader.setScaledSize(QSize(size, size))
    image = reader.read()
    if not image.isNull():
        return QPixmap.fromImage(image)
    return None


class ProductGrid(QWidget):
    product_selected = pyqtSignal(int, str, float, int)  # id, name, price, stock
    service_selected = pyqtSignal(int, str, float)      # id, name, price (no stock)
    barcode_scanned = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = 1
        self.rows_per_page = 50
        self.total_products = 0
        self.total_pages = 1

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name / barcode / SKU...")
        self.search_input.textChanged.connect(self.reset_and_filter)
        self.search_input.returnPressed.connect(self.scan_barcode)
        self.search_input.setClearButtonEnabled(True)
        self.category_label = QLabel("Category:")
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.currentTextChanged.connect(self.reset_and_filter)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.category_label)
        search_layout.addWidget(self.category_combo)
        layout.addLayout(search_layout)

        # Product table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setColumnHidden(0, True)
        self.table.setWordWrap(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.cellClicked.connect(self.on_row_clicked)
        self.table.verticalHeader().setDefaultSectionSize(60)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(1, 70)
        layout.addWidget(self.table)

        # Pagination widget
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)
        layout.addWidget(self.pagination)

        self.load_categories()
        self.load_products()

    def load_categories(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name")
        rows = cursor.fetchall()
        self.category_combo.blockSignals(True)
        current = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("All Categories")
        for (name,) in rows:
            self.category_combo.addItem(name)
        idx = self.category_combo.findText(current)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        else:
            self.category_combo.setCurrentIndex(0)
        self.category_combo.blockSignals(False)
        conn.close()

    def load_products(self, page=1, page_size=50):
        self.current_page = page
        self.rows_per_page = page_size
        search_text = self.search_input.text().strip().lower()
        selected_category = self.category_combo.currentText()
        use_category = selected_category != "All Categories"

        conn = connect_db()
        cursor = conn.cursor()

        count_params = []
        count_where = []
        if use_category:
            count_where.append("category = ?")
            count_params.append(selected_category)
        if search_text:
            like = f'%{search_text}%'
            count_where.append("(LOWER(name) LIKE ? OR LOWER(sku) LIKE ? OR LOWER(barcode) LIKE ?)")
            count_params.extend([like, like, like])

        count_sql = "SELECT COUNT(*) FROM products"
        if count_where:
            count_sql += " WHERE " + " AND ".join(count_where)
        cursor.execute(count_sql, count_params)
        total_items = cursor.fetchone()[0]
        self.pagination.set_total_items(total_items, emit_signal=False)

        offset = (page - 1) * page_size
        select_params = []
        where_clauses = []
        if use_category:
            where_clauses.append("category = ?")
            select_params.append(selected_category)
        if search_text:
            like = f'%{search_text}%'
            where_clauses.append("(LOWER(name) LIKE ? OR LOWER(sku) LIKE ? OR LOWER(barcode) LIKE ?)")
            select_params.extend([like, like, like])

        select_sql = """
            SELECT id, name, price, stock, low_stock, sold_by, image
            FROM products
        """
        if where_clauses:
            select_sql += " WHERE " + " AND ".join(where_clauses)
        select_sql += " ORDER BY name LIMIT ? OFFSET ?"
        cursor.execute(select_sql, select_params + [page_size, offset])
        rows = cursor.fetchall()
        conn.close()

        self.populate_table(rows)

    def on_page_changed(self, page: int, page_size: int):
        self.load_products(page, page_size)

    def reset_and_filter(self):
        self.pagination.set_current_page(1)
        self.load_products()

    def populate_table(self, rows):
        symbol = get_currency_symbol()
        self.table.setRowCount(0)
        for prod in rows:
            prod_id, name, price, stock, low_stock, sold_by, image_path = prod
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(prod_id)))

            # Thumbnail
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setScaledContents(True)
            image_label.setFixedSize(50, 50)
            thumb = load_thumbnail(image_path, 50)
            if thumb:
                image_label.setPixmap(thumb)
            else:
                image_label.setText("No img")
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(image_label)
            self.table.setCellWidget(row, 1, container)

            self.table.setItem(row, 2, QTableWidgetItem(name))
            if sold_by and sold_by.lower() == "service":
                price_display = "Service"
            else:
                price_display = format_money(price, symbol)
            self.table.setItem(row, 3, QTableWidgetItem(price_display))

            if sold_by and sold_by.lower() == "service":
                stock_item = QTableWidgetItem("N/A")
            else:
                stock_item = QTableWidgetItem(str(stock))
                if stock == 0:
                    stock_item.setForeground(QColor(231, 76, 60))
                elif stock <= low_stock:
                    stock_item.setForeground(QColor(230, 126, 34))
            self.table.setItem(row, 4, stock_item)

            if sold_by and sold_by.lower() == "service":
                status_text = "Service"
                status_color = QColor(52, 152, 219)
            else:
                if stock == 0:
                    status_text = "Out of Stock"
                    status_color = QColor(231, 76, 60)
                elif stock <= low_stock:
                    status_text = "Low Stock"
                    status_color = QColor(230, 126, 34)
                else:
                    status_text = "In Stock"
                    status_color = QColor(46, 204, 113)
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_color)
            self.table.setItem(row, 5, status_item)

    def on_row_clicked(self, row, column):
        id_item = self.table.item(row, 0)
        if not id_item:
            return
        try:
            prod_id = int(id_item.text())
        except:
            return
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, stock, sold_by FROM products WHERE id=?", (prod_id,))
        product = cursor.fetchone()
        conn.close()
        if product:
            name, price, stock, sold_by = product
            price = float(price) if price else 0.0
            if sold_by and sold_by.lower() == "service":
                manual_price, ok = QInputDialog.getDouble(
                    self, "Service Price", f"Enter price for {name}:",
                    value=0.0, min=0.0, max=1000000.0, decimals=2
                )
                if ok:
                    self.service_selected.emit(prod_id, name, manual_price)
            else:
                self.product_selected.emit(prod_id, name, price, stock)

    def scan_barcode(self):
        keyword = self.search_input.text().strip()
        if keyword:
            self.barcode_scanned.emit(keyword)
        self.search_input.clear()
        self.search_input.setFocus()

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def retranslateUi(self):
        from utils.language import lang
        if lang.get_current() == "my":
            self.search_input.setPlaceholderText("ပစ္စည်းအမည် / ဘားကုဒ် / SKU ဖြင့် ရှာရန်...")
            self.category_label.setText("အမျိုးအစား:")
            self.table.setHorizontalHeaderLabels(["ID", "ပုံ", "ပစ္စည်းအမည်", "စျေးနှုန်း", "ကျန်", "အခြေအနေ"])
        else:
            self.search_input.setPlaceholderText("Search by name / barcode / SKU...")
            self.category_label.setText("Category:")
            self.table.setHorizontalHeaderLabels(["ID", "Image", "Name", "Price", "Stock", "Status"])