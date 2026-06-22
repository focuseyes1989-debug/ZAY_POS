from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QInputDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QColor, QImageReader
from utils.currency import get_currency_symbol, format_money
from models.database import connect_db
from ui.widgets.pagination_widget import PaginationWidget
from ui.product_detail_dialog import ProductDetailDialog
from utils.paths import app_path
import functools
import os


def resolve_image_path(image_path: str):
    if not image_path:
        return ""
    if os.path.isabs(image_path):
        return image_path
    return app_path(image_path)


@functools.lru_cache(maxsize=200)
def load_thumbnail(image_path: str, size: int = 50):
    """Load product thumbnail with caching"""
    if not image_path:
        return None
    
    resolved_path = resolve_image_path(image_path)
    if not resolved_path or not os.path.exists(resolved_path):
        return None
    
    # Use optimized thumbnail from image_optimizer
    from utils.image_optimizer import ImageOptimizer
    thumb_path = ImageOptimizer.get_thumbnail_path(resolved_path, (size, size))
    
    if thumb_path and os.path.exists(thumb_path):
        pixmap = QPixmap(thumb_path)
        if not pixmap.isNull():
            return pixmap
    
    # Fallback: original method
    reader = QImageReader(resolved_path)
    reader.setScaledSize(QSize(size, size))
    image = reader.read()
    if not image.isNull():
        return QPixmap.fromImage(image)
    return None


class ProductTable(QWidget):
    product_selected = pyqtSignal(int, str, float, int)
    service_selected = pyqtSignal(int, str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = 1
        self.rows_per_page = 50
        self.current_rows = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(8)  # ID, Image, Name, Barcode, Price, Stock, Sold By, Status
        self.table.setColumnHidden(0, True)  # Hide ID column
        self.table.setWordWrap(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.cellClicked.connect(self.on_row_clicked)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)  # Double click handler
        self.table.verticalHeader().setDefaultSectionSize(60)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Image
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Barcode
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Price
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Stock
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Sold By
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  # Status

        # Set column width for image
        self.table.setColumnWidth(1, 70)

        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)

        layout.addWidget(self.table)
        layout.addWidget(self.pagination)
        self.setLayout(layout)

    def on_cell_double_clicked(self, row, column):
        """Handle double click on product row - show product detail dialog"""
        id_item = self.table.item(row, 0)
        if id_item:
            try:
                product_id = int(id_item.text())
                dialog = ProductDetailDialog(product_id)
                dialog.exec()
            except ValueError:
                pass

    def on_page_changed(self, page: int, page_size: int):
        self.current_page = page
        self.rows_per_page = page_size
        parent = self.parent()
        if parent and hasattr(parent, 'apply_filter'):
            parent.current_page = page
            parent.items_per_page = page_size
            parent.apply_filter()

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

    def populate_table(self, rows):
        symbol = get_currency_symbol()
        self.table.setRowCount(0)
        self.current_rows = rows
        for row_data in rows:
            if len(row_data) >= 7:
                # row_data: id, name, price, stock, low_stock, sold_by, image
                prod_id, name, price, stock, low_stock, sold_by, image_path = row_data[:7]
            else:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Column 0: ID (hidden)
            self.table.setItem(row, 0, QTableWidgetItem(str(prod_id)))

            # Column 1: Image thumbnail
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

            # Column 2: Name
            self.table.setItem(row, 2, QTableWidgetItem(name))
            
            # Column 3: Barcode
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT barcode FROM products WHERE id=?", (prod_id,))
            barcode_data = cursor.fetchone()
            conn.close()
            barcode = barcode_data[0] if barcode_data and barcode_data[0] else ""
            self.table.setItem(row, 3, QTableWidgetItem(barcode))
            
            # Column 4: Price
            if sold_by and sold_by.lower() == "service":
                price_display = "Service"
            else:
                price_display = format_money(price, symbol)
            self.table.setItem(row, 4, QTableWidgetItem(price_display))

            # Column 5: Stock
            if sold_by and sold_by.lower() == "service":
                stock_item = QTableWidgetItem("N/A")
            else:
                stock_val = stock if stock is not None else 0
                stock_item = QTableWidgetItem(str(stock_val))
                if stock_val == 0:
                    stock_item.setForeground(QColor(231, 76, 60))
                elif stock_val <= (low_stock if low_stock else 0):
                    stock_item.setForeground(QColor(230, 126, 34))
            self.table.setItem(row, 5, stock_item)
            
            # Column 6: Sold By
            sold_by_display = sold_by if sold_by else "Each"
            self.table.setItem(row, 6, QTableWidgetItem(sold_by_display))

            # Column 7: Status
            if sold_by and sold_by.lower() == "service":
                status_text = "Service"
                status_color = QColor(52, 152, 219)
            else:
                stock_val = stock if stock is not None else 0
                low_val = low_stock if low_stock else 0
                if stock_val == 0:
                    status_text = "Out of Stock"
                    status_color = QColor(231, 76, 60)
                elif stock_val <= low_val:
                    status_text = "Low Stock"
                    status_color = QColor(230, 126, 34)
                else:
                    status_text = "In Stock"
                    status_color = QColor(46, 204, 113)
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_color)
            self.table.setItem(row, 7, status_item)

    def get_selected_product_id(self):
        selected = self.table.currentRow()
        if selected >= 0:
            id_item = self.table.item(selected, 0)
            if id_item:
                return int(id_item.text())
        return None

    def get_current_rows(self):
        return self.current_rows

    def set_pagination_total(self, total):
        self.pagination.set_total_items(total, emit_signal=False)

    def get_pagination(self):
        return self.pagination

    def retranslateUi(self):
        from utils.language import lang
        if lang.get_current() == "my":
            headers = ["ID", "ပုံ", "ပစ္စည်းအမည်", "ဘားကုဒ်", "စျေးနှုန်း", "ကျန်", "ရောင်းပုံစံ", "အခြေအနေ"]
        else:
            headers = ["ID", "Image", "Name", "Barcode", "Price", "Stock", "Sold By", "Status"]
        self.table.setHorizontalHeaderLabels(headers)
