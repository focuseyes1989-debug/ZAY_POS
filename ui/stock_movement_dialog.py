from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QDate
from ui.base_form_dialog import BaseFormDialog
from models.database import connect_db
from utils.currency import format_money
from datetime import datetime

class BaseStockMovementDialog(BaseFormDialog):
    def __init__(self, title, fields, movement_type, parent=None):
        self.movement_type = movement_type  # 'in', 'out', 'adjust'
        super().__init__(title, fields, parent)
        self.all_products = []
        self.load_products()
        self.inputs['product'].currentIndexChanged.connect(self.on_product_selected)
        self.setup_extra()

    def load_products(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, barcode, sku, sold_by FROM products ORDER BY name")
        self.all_products = cursor.fetchall()
        conn.close()
        self.filter_products()

    def filter_products(self):
        search_text = self.inputs.get('search', None)
        if search_text:
            text = search_text.text().strip().lower()
        else:
            text = ""
        self.inputs['product'].clear()
        for pid, name, barcode, sku, sold_by in self.all_products:
            if (text in name.lower() or (barcode and text in barcode.lower()) or (sku and text in sku.lower())):
                display = f"{name} {'(Service)' if sold_by == 'Service' else ''}"
                self.inputs['product'].addItem(display, pid)
        if self.inputs['product'].count() > 0:
            self.inputs['product'].setCurrentIndex(0)

    def on_product_selected(self):
        pass  # override

    def setup_extra(self):
        pass

    def get_product_id(self):
        return self.inputs['product'].currentData()

    def validate(self):
        product_id = self.get_product_id()
        if product_id is None:
            QMessageBox.warning(self, "Error", "Please select a valid product.")
            return False
        return True

class StockInDialog(BaseStockMovementDialog):
    def __init__(self, parent=None):
        fields = [
            {'name': 'stock_in_no', 'label': 'Stock In No', 'type': 'line', 'readonly': True},
            {'name': 'search', 'label': 'Search Product', 'type': 'line'},
            {'name': 'product', 'label': 'Product', 'type': 'combo'},
            {'name': 'supplier', 'label': 'Supplier', 'type': 'combo'},
            {'name': 'po_no', 'label': 'PO No', 'type': 'line'},
            {'name': 'qty', 'label': 'Quantity', 'type': 'spin', 'range': (1, 999999)},
            {'name': 'unit_cost', 'label': 'Unit Cost', 'type': 'double', 'range': (0, 1000000), 'decimals': 2},
            {'name': 'total_cost', 'label': 'Total Cost', 'type': 'line', 'readonly': True},
            {'name': 'batch_no', 'label': 'Batch No', 'type': 'line'},
            {'name': 'expiry', 'label': 'Expiry Date', 'type': 'date', 'default': QDate.currentDate().addDays(30)},
            {'name': 'received_by', 'label': 'Received By', 'type': 'line', 'required': True},
            {'name': 'date', 'label': 'Date', 'type': 'date', 'default': QDate.currentDate()},
            {'name': 'notes', 'label': 'Notes', 'type': 'text'},
        ]
        super().__init__("Stock In", fields, 'in', parent)
        self.stock_in_no.setText(f"SIN-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.load_suppliers()
        self.inputs['unit_cost'].valueChanged.connect(self.update_total)
        self.inputs['qty'].valueChanged.connect(self.update_total)
        self.update_total()

    def load_suppliers(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM suppliers ORDER BY name")
        for sid, name in cursor.fetchall():
            self.inputs['supplier'].addItem(name, sid)
        conn.close()

    def filter_products(self):
        search_text = self.inputs['search'].text().strip().lower()
        self.inputs['product'].clear()
        for pid, name, barcode, sku, sold_by in self.all_products:
            if (search_text in name.lower() or (barcode and search_text in barcode.lower()) or (sku and search_text in sku.lower())):
                display = f"{name} {'(Service)' if sold_by == 'Service' else ''}"
                self.inputs['product'].addItem(display, pid)
        if self.inputs['product'].count() > 0:
            self.inputs['product'].setCurrentIndex(0)

    def update_total(self):
        qty = self.inputs['qty'].value()
        cost = self.inputs['unit_cost'].value()
        total = qty * cost
        self.inputs['total_cost'].setText(format_money(total))

    def accept(self):
        if not self.validate():
            return
        product_id = self.get_product_id()
        qty = self.inputs['qty'].value()
        unit_cost = self.inputs['unit_cost'].value()
        batch_no = self.inputs['batch_no'].text()
        expire = self.inputs['expiry'].date().toString("yyyy-MM-dd")
        received_by = self.inputs['received_by'].text()
        notes = self.inputs['notes'].toPlainText()
        if not received_by:
            QMessageBox.warning(self, "Error", "Received By is required")
            return
        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT stock, cost FROM products WHERE id=?", (product_id,))
            old_stock, old_cost = cursor.fetchone()
            new_stock = old_stock + qty
            cursor.execute("UPDATE products SET stock = ?, cost = ?, expire_date = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?",
                           (new_stock, unit_cost, expire, product_id))
            cursor.execute("INSERT INTO stock_movements (product_id, type, quantity, old_stock, new_stock, reason, reference, created_by, notes) VALUES (?, 'in', ?, ?, ?, ?, ?, ?, ?)",
                           (product_id, qty, old_stock, new_stock, f"Stock In via {self.inputs['stock_in_no'].text()}", self.inputs['po_no'].text(), received_by, notes))
            conn.commit()
            QMessageBox.information(self, "Success", f"Stock In recorded. New stock: {new_stock}")
            super().accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()