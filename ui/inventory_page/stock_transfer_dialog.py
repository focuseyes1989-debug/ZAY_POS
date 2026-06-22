# ui/inventory_page/stock_transfer_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QComboBox, QSpinBox, QPushButton, QMessageBox,
    QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt
from models.database import connect_db
from utils.currency import format_money
from datetime import datetime
from loguru import logger


class StockTransferDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stock Transfer")
        self.resize(500, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Transfer Info
        info_group = QGroupBox("Transfer Information")
        form_layout = QFormLayout()
        
        self.transfer_no = QLineEdit()
        self.transfer_no.setReadOnly(True)
        self.transfer_no.setText(f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        form_layout.addRow("Transfer No:", self.transfer_no)
        
        # Product search
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search product by name, barcode or SKU...")
        self.product_search.textChanged.connect(self.filter_products)
        form_layout.addRow("Search:", self.product_search)
        
        self.product_combo = QComboBox()
        form_layout.addRow("Product:", self.product_combo)
        
        # From Location
        self.from_location = QComboBox()
        self.from_location.addItem("Select Location...", None)
        self.from_location.currentIndexChanged.connect(self.on_from_location_changed)
        form_layout.addRow("From Location:", self.from_location)
        
        # Available stock display
        self.available_stock_label = QLabel("Available: 0")
        form_layout.addRow("", self.available_stock_label)
        
        # To Location
        self.to_location = QComboBox()
        self.to_location.addItem("Select Location...", None)
        form_layout.addRow("To Location:", self.to_location)
        
        # Quantity
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 999999)
        self.qty_spin.setValue(1)
        form_layout.addRow("Quantity:", self.qty_spin)
        
        # Reason
        self.reason_edit = QLineEdit()
        self.reason_edit.setPlaceholderText("Reason for transfer (e.g., Restocking, Consolidation)")
        form_layout.addRow("Reason:", self.reason_edit)
        
        # Transfer Date
        self.date_edit = QLineEdit()
        self.date_edit.setText(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.date_edit.setReadOnly(True)
        form_layout.addRow("Date:", self.date_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        form_layout.addRow("Notes:", self.notes_edit)
        
        info_group.setLayout(form_layout)
        layout.addWidget(info_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_transfer = QPushButton("Transfer Stock")
        self.btn_transfer.clicked.connect(self.transfer_stock)
        self.btn_transfer.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px;")
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_transfer)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Load data after UI is fully created
        self.load_locations()
        self.load_products()
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
        lang = self.get_lang()
        if lang == "my":
            self.setWindowTitle("စတော့လွှဲပြောင်းခြင်း")
            self.transfer_no.setText(f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            self.product_search.setPlaceholderText("ပစ္စည်းအမည် / ဘားကုဒ် / SKU ဖြင့်ရှာရန်...")
            self.btn_transfer.setText("စတော့လွှဲမည်")
            self.btn_cancel.setText("မလုပ်တော့")
        else:
            self.setWindowTitle("Stock Transfer")
            self.btn_transfer.setText("Transfer Stock")
            self.btn_cancel.setText("Cancel")
    
    def load_locations(self):
        """Load locations from product_locations table"""
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT location FROM product_locations 
            WHERE location IS NOT NULL AND location != '' 
            ORDER BY location
        """)
        rows = cursor.fetchall()
        
        # Clear both combo boxes
        self.from_location.blockSignals(True)
        self.to_location.blockSignals(True)
        
        self.from_location.clear()
        self.from_location.addItem("Select Location...", None)
        
        self.to_location.clear()
        self.to_location.addItem("Select Location...", None)
        
        for (name,) in rows:
            self.from_location.addItem(name, name)
            self.to_location.addItem(name, name)
        
        self.from_location.blockSignals(False)
        self.to_location.blockSignals(False)
        conn.close()
    
    def load_products(self):
        """Load products into combo box"""
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, barcode, sku, sold_by 
            FROM products 
            WHERE (sold_by IS NULL OR sold_by != 'Service')
            ORDER BY name
        """)
        self.all_products = cursor.fetchall()
        self.filter_products()
        conn.close()
    
    def filter_products(self):
        """Filter products based on search text"""
        search_text = self.product_search.text().strip().lower()
        self.product_combo.clear()
        self.product_combo.blockSignals(True)
        
        for pid, name, barcode, sku, sold_by in self.all_products:
            if (search_text in name.lower() or 
                (barcode and search_text in barcode.lower()) or 
                (sku and search_text in sku.lower())):
                display_text = f"{name}"
                self.product_combo.addItem(display_text, pid)
        
        self.product_combo.blockSignals(False)
        if self.product_combo.count() > 0:
            self.product_combo.setCurrentIndex(0)
        
        # Update available stock
        self.update_available_stock()
    
    def on_from_location_changed(self):
        """Update available stock when from location changes"""
        self.update_available_stock()
    
    def update_available_stock(self):
        """Update available stock label based on selected product and location"""
        product_id = self.product_combo.currentData()
        from_loc = self.from_location.currentData()
        
        if not product_id or not from_loc or from_loc == "Select Location...":
            self.available_stock_label.setText("Available: 0")
            self.qty_spin.setMaximum(1)
            return
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT quantity FROM product_locations 
            WHERE product_id = ? AND location = ?
        """, (product_id, from_loc))
        
        row = cursor.fetchone()
        conn.close()
        
        qty = row[0] if row else 0
        self.available_stock_label.setText(f"Available: {qty}")
        
        # Update max quantity
        self.qty_spin.setMaximum(qty if qty > 0 else 1)
    
    def transfer_stock(self):
        """Perform stock transfer"""
        product_id = self.product_combo.currentData()
        from_loc = self.from_location.currentData()
        to_loc = self.to_location.currentData()
        qty = self.qty_spin.value()
        reason = self.reason_edit.text().strip()
        notes = self.notes_edit.toPlainText().strip()
        lang = self.get_lang()
        
        # Validations
        if not product_id:
            msg = "Please select a product." if lang != "my" else "ပစ္စည်းတစ်ခုရွေးပါ။"
            QMessageBox.warning(self, "Error", msg)
            return
        
        if not from_loc or from_loc == "Select Location...":
            msg = "Please select 'From' location." if lang != "my" else "'မှ' နေရာကိုရွေးပါ။"
            QMessageBox.warning(self, "Error", msg)
            return
        
        if not to_loc or to_loc == "Select Location...":
            msg = "Please select 'To' location." if lang != "my" else "'သို့' နေရာကိုရွေးပါ။"
            QMessageBox.warning(self, "Error", msg)
            return
        
        if from_loc == to_loc:
            msg = "From and To locations cannot be the same!" if lang != "my" else "'မှ' နှင့် 'သို့' နေရာများ တူမနိုင်ပါ။"
            QMessageBox.warning(self, "Error", msg)
            return
        
        if qty <= 0:
            msg = "Quantity must be greater than 0." if lang != "my" else "အရေအတွက်သည် ၀ ထက်ကြီးရပါမည်။"
            QMessageBox.warning(self, "Error", msg)
            return
        
        # Check available stock
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT quantity FROM product_locations 
            WHERE product_id = ? AND location = ?
        """, (product_id, from_loc))
        row = cursor.fetchone()
        available = row[0] if row else 0
        
        if qty > available:
            msg = f"Insufficient stock. Available: {available}" if lang != "my" else f"စတော့မလုံလောက်ပါ။ ကျန်: {available}"
            QMessageBox.warning(self, "Error", msg)
            conn.close()
            return
        
        # Perform transfer
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            # Get current total stock for product
            cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
            total_stock = cursor.fetchone()[0]
            
            # 1. Remove from source location
            cursor.execute("""
                UPDATE product_locations 
                SET quantity = quantity - ?
                WHERE product_id = ? AND location = ?
            """, (qty, product_id, from_loc))
            
            # Check if source location becomes 0, delete it
            cursor.execute("""
                SELECT quantity FROM product_locations 
                WHERE product_id = ? AND location = ?
            """, (product_id, from_loc))
            remaining = cursor.fetchone()
            if remaining and remaining[0] <= 0:
                cursor.execute("""
                    DELETE FROM product_locations 
                    WHERE product_id = ? AND location = ?
                """, (product_id, from_loc))
            
            # 2. Add to destination location
            cursor.execute("""
                INSERT INTO product_locations (product_id, location, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(product_id, location) 
                DO UPDATE SET quantity = quantity + excluded.quantity
            """, (product_id, to_loc, qty))
            
            # 3. Update total stock in products table
            cursor.execute("""
                UPDATE products 
                SET stock = (
                    SELECT COALESCE(SUM(quantity), 0) 
                    FROM product_locations 
                    WHERE product_id = ?
                ), last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (product_id, product_id))
            
            # Get new total stock
            cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
            new_total_stock = cursor.fetchone()[0]
            
            # 4. Record stock movement for FROM location (Stock Out)
            cursor.execute("""
                INSERT INTO stock_movements 
                (product_id, type, quantity, old_stock, new_stock, 
                 reason, reference, created_by, notes, location)
                VALUES (?, 'out', ?, ?, ?, 
                        ?, ?, ?, ?, ?)
            """, (
                product_id, 
                qty, 
                total_stock,
                new_total_stock,
                f"Transfer to {to_loc}: {reason}" if lang != "my" else f"{to_loc} သို့လွှဲ: {reason}",
                self.transfer_no.text(),
                "System",
                notes or reason,
                from_loc
            ))
            
            # 5. Record stock movement for TO location (Stock In)
            cursor.execute("""
                INSERT INTO stock_movements 
                (product_id, type, quantity, old_stock, new_stock, 
                 reason, reference, created_by, notes, location)
                VALUES (?, 'in', ?, ?, ?, 
                        ?, ?, ?, ?, ?)
            """, (
                product_id, 
                qty, 
                total_stock,
                new_total_stock,
                f"Transfer from {from_loc}: {reason}" if lang != "my" else f"{from_loc} မှလွှဲ: {reason}",
                self.transfer_no.text(),
                "System",
                notes or reason,
                to_loc
            ))
            
            conn.commit()
            
            # Get product name for success message
            cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
            product_name = cursor.fetchone()[0]
            
            msg = f"Successfully transferred {qty} units of '{product_name}' from {from_loc} to {to_loc}!" if lang != "my" else f"'{product_name}' ပစ္စည်း {qty} ခုကို {from_loc} မှ {to_loc} သို့ အောင်မြင်စွာ လွှဲပြောင်းပြီးပါပြီ။"
            QMessageBox.information(self, "Success", msg)
            
            # Refresh stock alerts in main window
            main_window = self.window()
            if hasattr(main_window, 'check_stock_alerts'):
                main_window.check_stock_alerts()
            
            self.accept()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Stock transfer failed: {e}")
            msg = f"Transfer failed: {e}" if lang != "my" else f"လွှဲပြောင်းမှု မအောင်မြင်ပါ: {e}"
            QMessageBox.critical(self, "Error", msg)
        finally:
            conn.close()