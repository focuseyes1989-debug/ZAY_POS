# ui/inventory_page/product_location_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QHeaderView, QLineEdit,
    QLabel, QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.language import lang
from utils.currency import format_money


class ProductLocationDialog(QDialog):
    """Manage multiple locations for a single product"""
    locations_changed = pyqtSignal()
    
    def __init__(self, product_id, product_name, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.product_name = product_name
        self.setWindowTitle(f"Manage Locations - {product_name}")
        self.setMinimumSize(700, 450)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Info label
        info_label = QLabel(f"<b>Product:</b> {product_name}")
        info_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(info_label)
        
        # Location table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Location", "Quantity", "Batch No", "Expiry Date"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setColumnHidden(0, True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
        # Add location section
        add_group = QGroupBox("Add to Location")
        add_layout = QHBoxLayout()
        
        self.location_combo = QComboBox()
        self.location_combo.setMinimumWidth(150)
        self.load_locations()
        add_layout.addWidget(QLabel("Location:"))
        add_layout.addWidget(self.location_combo)
        
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 999999)
        self.qty_spin.setValue(1)
        add_layout.addWidget(QLabel("Qty:"))
        add_layout.addWidget(self.qty_spin)
        
        self.btn_add = QPushButton("Add to Location")
        self.btn_add.clicked.connect(self.add_to_location)
        add_layout.addWidget(self.btn_add)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self.edit_location)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_location)
        self.btn_move = QPushButton("Move Stock")
        self.btn_move.clicked.connect(self.move_stock)
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_move)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_product_locations()
        self.retranslateUi()
    
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
    
    def retranslateUi(self):
        lang_code = self.get_lang()
        if lang_code == "my":
            self.setWindowTitle(f"နေရာများ စီမံရန် - {self.product_name}")
            self.table.setHorizontalHeaderLabels(["ID", "နေရာ", "ပမာဏ", "အသုတ်အမှတ်", "သက်တမ်းကုန်ရက်"])
            self.btn_add.setText("နေရာသို့ထည့်")
            self.btn_edit.setText("ပြင်ဆင်")
            self.btn_delete.setText("ဖျက်")
            self.btn_move.setText("စတော့ရွှေ့ပြောင်း")
            self.btn_close.setText("ပိတ်မည်")
        else:
            self.setWindowTitle(f"Manage Locations - {self.product_name}")
            self.table.setHorizontalHeaderLabels(["ID", "Location", "Quantity", "Batch No", "Expiry Date"])
            self.btn_add.setText("Add to Location")
            self.btn_edit.setText("Edit")
            self.btn_delete.setText("Delete")
            self.btn_move.setText("Move Stock")
            self.btn_close.setText("Close")
    
    def load_locations(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT warehouse FROM products WHERE warehouse IS NOT NULL AND warehouse != '' ORDER BY warehouse")
        rows = cursor.fetchall()
        self.location_combo.clear()
        for (name,) in rows:
            self.location_combo.addItem(name, name)
        # Add option to create new location
        self.location_combo.addItem("+ New Location", None)
        conn.close()
    
    def load_product_locations(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, location, quantity, batch_no, expire_date
            FROM product_locations
            WHERE product_id = ?
            ORDER BY location
        """, (self.product_id,))
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(0)
        total_qty = 0
        
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r, 2, QTableWidgetItem(str(row[2])))
            self.table.setItem(r, 3, QTableWidgetItem(row[3] or ""))
            self.table.setItem(r, 4, QTableWidgetItem(row[4] or ""))
            total_qty += row[2]
        
        # Update total stock in products table
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (total_qty, self.product_id))
        conn.commit()
        conn.close()
        
        self.locations_changed.emit()
    
    def add_to_location(self):
        location = self.location_combo.currentData()
        qty = self.qty_spin.value()
        
        if qty <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid quantity.")
            return
        
        if location is None:
            # Create new location
            new_location, ok = QInputDialog.getText(
                self, 
                "New Location",
                "Enter location name:"
            )
            if ok and new_location.strip():
                location = new_location.strip()
            else:
                return
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Check if location already exists for this product
        cursor.execute(
            "SELECT id, quantity FROM product_locations WHERE product_id = ? AND location = ?",
            (self.product_id, location)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing location
            new_qty = existing[1] + qty
            cursor.execute(
                "UPDATE product_locations SET quantity = ? WHERE id = ?",
                (new_qty, existing[0])
            )
            msg = f"Updated {location}: {new_qty} units"
        else:
            # Insert new location
            cursor.execute("""
                INSERT INTO product_locations (product_id, location, quantity)
                VALUES (?, ?, ?)
            """, (self.product_id, location, qty))
            msg = f"Added {qty} units to {location}"
        
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "Success", msg)
        self.load_product_locations()
    
    def edit_location(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a location to edit.")
            return
        
        loc_id = int(self.table.item(current_row, 0).text())
        current_location = self.table.item(current_row, 1).text()
        current_qty = int(self.table.item(current_row, 2).text())
        current_batch = self.table.item(current_row, 3).text()
        current_expiry = self.table.item(current_row, 4).text()
        
        # Edit dialog
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QSpinBox, QDateEdit, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Location")
        dialog.setMinimumWidth(400)
        
        form_layout = QFormLayout()
        
        location_edit = QLineEdit(current_location)
        qty_edit = QSpinBox()
        qty_edit.setRange(0, 999999)
        qty_edit.setValue(current_qty)
        batch_edit = QLineEdit(current_batch)
        expiry_edit = QDateEdit()
        expiry_edit.setCalendarPopup(True)
        if current_expiry:
            from PyQt6.QtCore import QDate
            expiry_edit.setDate(QDate.fromString(current_expiry, "yyyy-MM-dd"))
        
        form_layout.addRow("Location:", location_edit)
        form_layout.addRow("Quantity:", qty_edit)
        form_layout.addRow("Batch No:", batch_edit)
        form_layout.addRow("Expiry Date:", expiry_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form_layout.addRow(buttons)
        
        dialog.setLayout(form_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_location = location_edit.text().strip()
            new_qty = qty_edit.value()
            new_batch = batch_edit.text().strip()
            new_expiry = expiry_edit.date().toString("yyyy-MM-dd") if expiry_edit.date() else ""
            
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE product_locations 
                SET location = ?, quantity = ?, batch_no = ?, expire_date = ?
                WHERE id = ?
            """, (new_location, new_qty, new_batch, new_expiry, loc_id))
            conn.commit()
            conn.close()
            
            self.load_product_locations()
    
    def delete_location(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a location to delete.")
            return
        
        loc_id = int(self.table.item(current_row, 0).text())
        location = self.table.item(current_row, 1).text()
        qty = int(self.table.item(current_row, 2).text())
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {qty} units from '{location}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM product_locations WHERE id = ?", (loc_id,))
            conn.commit()
            conn.close()
            self.load_product_locations()
    
    def move_stock(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a location to move from.")
            return
        
        from_location = self.table.item(current_row, 1).text()
        from_qty = int(self.table.item(current_row, 2).text())
        
        # Get target location
        locations = []
        for row in range(self.table.rowCount()):
            loc = self.table.item(row, 1).text()
            if loc != from_location:
                locations.append(loc)
        
        if not locations:
            QMessageBox.warning(self, "No Location", "No other locations available to move to.")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        to_location, ok = QInputDialog.getItem(
            self,
            "Move Stock",
            f"Move from '{from_location}' to:",
            locations,
            0,
            False
        )
        
        if not ok:
            return
        
        qty_to_move, ok = QInputDialog.getInt(
            self,
            "Move Stock",
            f"How many units to move from '{from_location}' to '{to_location}'?",
            min=1, max=from_qty, value=1
        )
        
        if not ok or qty_to_move <= 0:
            return
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # Update from location
        cursor.execute(
            "UPDATE product_locations SET quantity = quantity - ? WHERE product_id = ? AND location = ?",
            (qty_to_move, self.product_id, from_location)
        )
        
        # Update to location
        cursor.execute(
            "SELECT id FROM product_locations WHERE product_id = ? AND location = ?",
            (self.product_id, to_location)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE product_locations SET quantity = quantity + ? WHERE id = ?",
                (qty_to_move, existing[0])
            )
        else:
            cursor.execute("""
                INSERT INTO product_locations (product_id, location, quantity)
                VALUES (?, ?, ?)
            """, (self.product_id, to_location, qty_to_move))
        
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "Success", f"Moved {qty_to_move} units from {from_location} to {to_location}")
        self.load_product_locations()