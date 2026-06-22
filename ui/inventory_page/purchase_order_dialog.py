from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QHeaderView
)
from PyQt6.QtCore import QDate
from models.database import connect_db
from utils.currency import format_money


class PurchaseOrderEditDialog(QDialog):
    def __init__(self, po_id, parent=None):
        super().__init__(parent)
        self.po_id = po_id
        self.setWindowTitle("Edit Purchase Order")
        self.setMinimumSize(700, 600)
        self.setModal(True)

        layout = QVBoxLayout()

        # Load PO data
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT po_no, supplier_id, order_date, total_amount, discount,
                   tax, payment_status, received_by, notes
            FROM purchase_orders WHERE id = ?
        """, (po_id,))
        po_data = cursor.fetchone()

        if not po_data:
            QMessageBox.warning(self, "Error", "Purchase order not found.")
            self.close()
            return

        po_no, supplier_id, order_date, total_amount, discount, tax, payment_status, received_by, notes = po_data

        # Form for header
        form_layout = QFormLayout()

        self.po_no_label = QLabel(po_no)
        form_layout.addRow("PO Number:", self.po_no_label)

        # Supplier combo
        self.supplier_combo = QComboBox()
        cursor.execute("SELECT id, name FROM suppliers ORDER BY name")
        suppliers = cursor.fetchall()
        self.supplier_map = {}
        for sid, name in suppliers:
            self.supplier_combo.addItem(name, sid)
            self.supplier_map[sid] = name
        idx = self.supplier_combo.findData(supplier_id)
        if idx >= 0:
            self.supplier_combo.setCurrentIndex(idx)
        form_layout.addRow("Supplier:", self.supplier_combo)

        # Order date
        self.order_date = QDateEdit()
        self.order_date.setCalendarPopup(True)
        self.order_date.setDate(QDate.fromString(order_date, "yyyy-MM-dd"))
        form_layout.addRow("Order Date:", self.order_date)

        # Discount
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 1000000)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setValue(discount if discount else 0.0)
        form_layout.addRow("Discount:", self.discount_spin)

        # Tax
        self.tax_spin = QDoubleSpinBox()
        self.tax_spin.setRange(0, 100)
        self.tax_spin.setDecimals(2)
        self.tax_spin.setSuffix(" %")
        self.tax_spin.setValue(tax if tax else 0.0)
        form_layout.addRow("Tax:", self.tax_spin)

        # Payment status
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Unpaid", "Paid", "Partial"])
        self.payment_combo.setCurrentText(payment_status if payment_status else "Unpaid")
        form_layout.addRow("Payment Status:", self.payment_combo)

        # Received by
        self.received_by = QLineEdit(received_by if received_by else "")
        form_layout.addRow("Received By:", self.received_by)

        # Notes
        self.notes = QTextEdit()
        self.notes.setPlainText(notes if notes else "")
        form_layout.addRow("Notes:", self.notes)

        layout.addLayout(form_layout)

        # Items table (read-only)
        items_label = QLabel("Order Items (read-only)")
        layout.addWidget(items_label)
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Product", "Quantity", "Unit Price", "Total"])
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.items_table)

        # Load items
        cursor.execute("""
            SELECT p.name, poi.quantity, poi.unit_price, poi.total
            FROM purchase_order_items poi
            JOIN products p ON poi.product_id = p.id
            WHERE poi.po_id = ?
        """, (po_id,))
        items = cursor.fetchall()
        self.items_table.setRowCount(len(items))
        for row, (name, qty, price, total) in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(name))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.items_table.setItem(row, 2, QTableWidgetItem(format_money(price)))
            self.items_table.setItem(row, 3, QTableWidgetItem(format_money(total)))

        conn.close()

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.clicked.connect(self.save_changes)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def save_changes(self):
        supplier_id = self.supplier_combo.currentData()
        order_date = self.order_date.date().toString("yyyy-MM-dd")
        discount = self.discount_spin.value()
        tax = self.tax_spin.value()
        payment_status = self.payment_combo.currentText()
        received_by = self.received_by.text()
        notes = self.notes.toPlainText()

        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE purchase_orders
                SET supplier_id = ?, order_date = ?, discount = ?, tax = ?,
                    payment_status = ?, received_by = ?, notes = ?
                WHERE id = ?
            """, (supplier_id, order_date, discount, tax, payment_status, received_by, notes, self.po_id))
            conn.commit()
            QMessageBox.information(self, "Success", "Purchase order updated successfully.")
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to update: {e}")
        finally:
            conn.close()