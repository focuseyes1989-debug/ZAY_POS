# ui/sales_page/cart_widget.py
import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QSpinBox,
    QPushButton, QLabel, QMessageBox, QHeaderView, QInputDialog, QApplication, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal
from utils.currency import get_currency_symbol, format_money
from models.database import connect_db
from loguru import logger

CART_BACKUP_FILE = "temp/cart_backup.json"

def save_cart_to_file(cart):
    try:
        os.makedirs("temp", exist_ok=True)
        with open(CART_BACKUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(cart, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save cart backup: {e}")

def load_cart_from_file():
    try:
        if os.path.exists(CART_BACKUP_FILE):
            with open(CART_BACKUP_FILE, 'r', encoding='utf-8') as f:
                cart = json.load(f)
                valid_cart = []
                for item in cart:
                    if all(k in item for k in ('id', 'name', 'price', 'qty', 'is_service')):
                        item['qty'] = max(1, int(item['qty']))
                        valid_cart.append(item)
                return valid_cart
    except Exception as e:
        logger.error(f"Failed to load cart backup: {e}")
    return []

def delete_cart_backup():
    try:
        if os.path.exists(CART_BACKUP_FILE):
            os.remove(CART_BACKUP_FILE)
    except Exception as e:
        logger.error(f"Failed to delete cart backup: {e}")


class CartWidget(QWidget):
    cart_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cart = []
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label = QLabel("Shopping Cart")
        layout.addWidget(self.label)
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Added Location column
        self.table.setWordWrap(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(45)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(5, 100)
        layout.addWidget(self.table)

    def add_product(self, product_id, name, price, stock_available):
        """Add a regular product (non-service)."""
        for item in self.cart:
            if item["id"] == product_id and not item.get("is_service", False):
                new_qty = item["qty"] + 1
                if new_qty > stock_available:
                    QMessageBox.warning(self, "Stock Insufficient", f"Only {stock_available} left.")
                    return
                item["qty"] = new_qty
                self.refresh_table()
                return
        if stock_available < 1:
            QMessageBox.warning(self, "Out of Stock", f"{name} is out of stock.")
            return
        
        # Get location for this product (FIFO)
        location = self.get_best_location(product_id)
        
        self.cart.append({
            "id": product_id, 
            "name": name, 
            "price": price, 
            "qty": 1, 
            "is_service": False,
            "location": location  # Store location in cart
        })
        self.refresh_table()

    def add_service(self, product_id, name, manual_price):
        """Add a service product (no stock check)."""
        for item in self.cart:
            if item["id"] == product_id and item.get("is_service", False):
                item["qty"] += 1
                self.refresh_table()
                return
        self.cart.append({
            "id": product_id, 
            "name": name, 
            "price": manual_price, 
            "qty": 1, 
            "is_service": True,
            "location": None
        })
        self.refresh_table()

    def get_best_location(self, product_id):
        """FIFO: Get the location with earliest expiry date for this product"""
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get locations with stock > 0, ordered by expiry date (earliest first)
        cursor.execute("""
            SELECT location, quantity, expire_date 
            FROM product_locations 
            WHERE product_id = ? AND quantity > 0
            ORDER BY expire_date ASC, last_updated ASC
        """, (product_id,))
        
        locations = cursor.fetchall()
        conn.close()
        
        if locations:
            # Return the first location (earliest expiry)
            return locations[0][0]
        return None

    def add_product_by_barcode(self, keyword):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, stock, sold_by FROM products WHERE barcode=? OR sku=? OR name LIKE ?",
                       (keyword, keyword, f'%{keyword}%'))
        product = cursor.fetchone()
        conn.close()
        if not product:
            QApplication.beep()
            QMessageBox.warning(self, "Not Found", "Product Not Found")
            return
        pid, name, price, stock, sold_by = product
        price = float(price) if price else 0.0
        if sold_by and sold_by.lower() == "service":
            manual_price, ok = QInputDialog.getDouble(
                self, "Service Price", f"Enter price for {name}:",
                value=0.0, min=0.0, max=1000000.0, decimals=2
            )
            if ok:
                self.add_service(pid, name, manual_price)
        else:
            # Non‑service product: check stock
            if stock <= 0:
                QMessageBox.warning(self, "Out of Stock", f"{name} is out of stock.")
                return
            self.add_product(pid, name, price, stock)

    def refresh_table(self):
        symbol = get_currency_symbol()
        self.table.setRowCount(0)
        for row, item in enumerate(self.cart):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item["name"]))
            
            qty_spin = QSpinBox()
            qty_spin.setValue(item["qty"])
            qty_spin.valueChanged.connect(lambda val, r=row: self.update_qty(r, val))
            self.table.setCellWidget(row, 1, qty_spin)
            
            self.table.setItem(row, 2, QTableWidgetItem(format_money(item['price'], symbol)))
            total = item["price"] * item["qty"]
            self.table.setItem(row, 3, QTableWidgetItem(format_money(total, symbol)))
            
            # Location column
            location_display = item.get("location", "-") if not item.get("is_service", False) else "N/A"
            self.table.setItem(row, 4, QTableWidgetItem(str(location_display)))
            
            btn_remove = QPushButton("Remove")
            btn_remove.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn_remove.clicked.connect(lambda _, r=row: self.remove_item(r))
            self.table.setCellWidget(row, 5, btn_remove)
            
        self.cart_changed.emit()
        save_cart_to_file(self.cart)

    def update_qty(self, row, value):
        if value <= 0:
            self.remove_item(row)
        else:
            self.cart[row]["qty"] = value
            self.refresh_table()

    def remove_item(self, row):
        del self.cart[row]
        self.refresh_table()

    def clear(self):
        self.cart.clear()
        self.refresh_table()
        delete_cart_backup()

    def get_cart(self):
        return self.cart

    def compute_subtotal(self):
        return sum(item["price"] * item["qty"] for item in self.cart)

    def retranslateUi(self):
        from utils.language import lang
        if lang.get_current() == "my":
            self.label.setText("ဈေးခြင်း")
            self.table.setHorizontalHeaderLabels(["ပစ္စည်း", "အရေအတွက်", "စျေးနှုန်း", "စုစုပေါင်း", "နေရာ", "ဖျက်မည်"])
        else:
            self.label.setText("Shopping Cart")
            self.table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Total", "Location", "Remove"])