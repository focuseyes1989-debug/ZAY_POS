# ui/inventory_page/adjustment_dialog.py
from PyQt6.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit, QPushButton, QMessageBox, QVBoxLayout, QInputDialog
from PyQt6.QtCore import QDate
from models.database import connect_db
from utils.currency import format_money
from datetime import datetime


class AdjustmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adjustment")
        self.resize(500, 700)
        layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.adj_no = QLineEdit()
        self.adj_no.setReadOnly(True)
        self.adj_no.setText(f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search product by name, barcode or SKU...")
        self.product_search.textChanged.connect(self.filter_products)
        
        self.adj_product = QComboBox()
        self.adj_old_qty = QLabel("0")
        self.adj_new_qty = QSpinBox()
        self.adj_new_qty.setRange(0, 999999)
        self.adj_new_qty.valueChanged.connect(self.update_diff)
        self.adj_diff = QLabel("0")
        self.adj_type = QComboBox()
        self.adj_type.addItems(["Add", "Remove"])
        self.adj_reason = QLineEdit()
        self.adj_reason.setPlaceholderText("Damage / Counting Error / Return")
        self.adj_staff = QLineEdit()
        self.adj_date = QDateEdit()
        self.adj_date.setCalendarPopup(True)
        self.adj_date.setDate(QDate.currentDate())
        self.adj_notes = QTextEdit()
        self.adj_notes.setMaximumHeight(80)
        
        # Location ComboBox
        self.adj_location = QComboBox()
        self.adj_location.addItem("None", None)
        self.adj_location.addItem("+ Add New Location", "__NEW__")
        self.load_locations()

        self.labels = {}
        for key in ["adj_no", "product", "old_qty", "new_qty", "diff",
                    "type", "reason", "staff", "date", "location", "notes"]:
            self.labels[key] = QLabel(key.replace("_", " ").title() + ":")
        self.btn_save = QPushButton("Apply Adjustment")

        self.form_layout.addRow(self.labels["adj_no"], self.adj_no)
        self.form_layout.addRow(QLabel("Search Product:"), self.product_search)
        self.form_layout.addRow(self.labels["product"], self.adj_product)
        self.form_layout.addRow(self.labels["old_qty"], self.adj_old_qty)
        self.form_layout.addRow(self.labels["new_qty"], self.adj_new_qty)
        self.form_layout.addRow(self.labels["diff"], self.adj_diff)
        self.form_layout.addRow(self.labels["type"], self.adj_type)
        self.form_layout.addRow(self.labels["reason"], self.adj_reason)
        self.form_layout.addRow(self.labels["staff"], self.adj_staff)
        self.form_layout.addRow(self.labels["date"], self.adj_date)
        self.form_layout.addRow(self.labels["location"], self.adj_location)
        self.form_layout.addRow(self.labels["notes"], self.adj_notes)

        layout.addLayout(self.form_layout)
        layout.addWidget(self.btn_save)
        self.setLayout(layout)

        self.btn_save.clicked.connect(self.save)
        self.adj_location.currentIndexChanged.connect(self.on_location_changed)
        self.load_product_combo()
        self.adj_product.currentIndexChanged.connect(self.load_old_stock)
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

    def load_locations(self):
        """Load locations from database"""
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get locations from product_locations table
        cursor.execute("SELECT DISTINCT location FROM product_locations WHERE location IS NOT NULL AND location != '' ORDER BY location")
        rows = cursor.fetchall()
        
        self.adj_location.blockSignals(True)
        
        # Clear and add default items
        self.adj_location.clear()
        self.adj_location.addItem("None", None)
        
        # Collect all unique locations
        locations_set = set()
        for (name,) in rows:
            locations_set.add(name)
        
        # Add locations to combobox
        for location in sorted(locations_set):
            self.adj_location.addItem(location, location)
        
        # Add "Add New Location" option
        self.adj_location.addItem("+ Add New Location", "__NEW__")
        
        self.adj_location.blockSignals(False)
        conn.close()

    def on_location_changed(self, index):
        """Handle location combo box change"""
        if index < 0:
            return
            
        current_text = self.adj_location.currentText()
        current_data = self.adj_location.currentData()
        
        # Check if user wants to add new location
        if current_data == "__NEW__" or current_text == "+ Add New Location":
            self.add_new_location()

    def add_new_location(self):
        """Add a new location to the system"""
        lang = self.get_lang()
        
        new_location, ok = QInputDialog.getText(
            self,
            "New Location" if lang != "my" else "နေရာအသစ်ထည့်ရန်",
            "Enter location name:" if lang != "my" else "နေရာအမည်ထည့်ပါ:"
        )
        
        if ok and new_location.strip():
            new_location = new_location.strip()
            
            conn = connect_db()
            cursor = conn.cursor()
            
            # Check if location already exists in product_locations
            cursor.execute("SELECT COUNT(*) FROM product_locations WHERE location = ?", (new_location,))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                conn.close()
                msg = f"Location '{new_location}' already exists!" if lang != "my" else f"နေရာ '{new_location}' ရှိပြီးသားပါ။"
                QMessageBox.warning(self, "Error", msg)
                # Refresh and select the existing location
                self.load_locations()
                index = self.adj_location.findText(new_location)
                if index >= 0:
                    self.adj_location.setCurrentIndex(index)
                return
            
            # Get the first product to associate with this location
            cursor.execute("SELECT id FROM products LIMIT 1")
            product = cursor.fetchone()
            
            if product:
                # Create a placeholder entry with 0 quantity
                cursor.execute("""
                    INSERT INTO product_locations (product_id, location, quantity)
                    VALUES (?, ?, 0)
                """, (product[0], new_location))
                conn.commit()
                
                msg = f"Location '{new_location}' added successfully!" if lang != "my" else f"နေရာ '{new_location}' ထည့်သွင်းပြီးပါပြီ။"
                success = True
            else:
                msg = "No products found. Please add a product first, then add locations." if lang != "my" else "ပစ္စည်းမရှိပါ။ ပစ္စည်းအရင်ထည့်ပြီးမှ နေရာအသစ်ထည့်ပါ။"
                success = False
            
            conn.close()
            
            if success:
                # Refresh locations and select the new one
                self.load_locations()
                index = self.adj_location.findText(new_location)
                if index >= 0:
                    self.adj_location.setCurrentIndex(index)
                
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Warning", msg)
                # Reset to None
                self.adj_location.setCurrentIndex(0)
        else:
            # If user cancels, reset to "None"
            self.adj_location.setCurrentIndex(0)

    def retranslateUi(self):
        lang = self.get_lang()
        if lang == "my":
            self.setWindowTitle("စတော့ပြင်ဆင်ချက်")
            translations = {
                "adj_no": "ပြင်ဆင်ချက်အမှတ်:",
                "product": "ပစ္စည်း:",
                "old_qty": "မူလပမာဏ:",
                "new_qty": "ပြင်ဆင်ပြီးပမာဏ:",
                "diff": "ပြောင်းလဲမှု:",
                "type": "ပြင်ဆင်မှုအမျိုးအစား:",
                "reason": "အကြောင်းပြချက်:",
                "staff": "ပြင်ဆင်သူ:",
                "date": "ရက်စွဲ:",
                "location": "နေရာ:",
                "notes": "မှတ်ချက်:"
            }
            for key, text in translations.items():
                self.labels[key].setText(text)
            self.btn_save.setText("ပြင်ဆင်မည်")
            self.adj_type.setItemText(0, "ပေါင်းထည့်")
            self.adj_type.setItemText(1, "ဖယ်ရှား")
            self.product_search.setPlaceholderText("ပစ္စည်းအမည် / ဘားကုဒ် / SKU ဖြင့်ရှာရန်...")
            
            # Update "Add New Location" text
            index = self.adj_location.findData("__NEW__")
            if index >= 0:
                self.adj_location.setItemText(index, "+ နေရာအသစ်ထည့်")
        else:
            self.setWindowTitle("Stock Adjustment")
            for key, label in self.labels.items():
                label.setText(key.replace("_", " ").title() + ":")
            self.btn_save.setText("Apply Adjustment")
            self.adj_type.setItemText(0, "Add")
            self.adj_type.setItemText(1, "Remove")
            self.product_search.setPlaceholderText("Search product by name, barcode or SKU...")
            
            # Update "Add New Location" text
            index = self.adj_location.findData("__NEW__")
            if index >= 0:
                self.adj_location.setItemText(index, "+ Add New Location")

    def load_product_combo(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, barcode, sku, sold_by FROM products ORDER BY name")
        self.all_products = cursor.fetchall()
        self.filter_products()
        conn.close()

    def filter_products(self):
        search_text = self.product_search.text().strip().lower()
        self.adj_product.clear()
        self.adj_product.blockSignals(True)
        for pid, name, barcode, sku, sold_by in self.all_products:
            if (search_text in name.lower() or 
                (barcode and search_text in barcode.lower()) or 
                (sku and search_text in sku.lower())):
                display_text = f"{name} {'(Service)' if sold_by == 'Service' else ''}"
                self.adj_product.addItem(display_text, pid)
        self.adj_product.blockSignals(False)
        if self.adj_product.count() > 0:
            self.adj_product.setCurrentIndex(0)

    def load_old_stock(self):
        pid = self.adj_product.currentData()
        if pid:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT stock, sold_by FROM products WHERE id=?", (pid,))
            stock, sold_by = cursor.fetchone()
            conn.close()
            if sold_by == "Service":
                QMessageBox.warning(self, "Warning", "Adjustment for Service products is not allowed (they have no stock).")
                self.adj_new_qty.setEnabled(False)
                self.adj_old_qty.setText("N/A")
                return
            else:
                self.adj_new_qty.setEnabled(True)
                self.adj_old_qty.setText(str(stock))
                self.adj_new_qty.setValue(stock)

    def update_diff(self):
        try:
            old = int(self.adj_old_qty.text())
        except:
            old = 0
        new = self.adj_new_qty.value()
        diff = new - old
        self.adj_diff.setText(str(diff))

    def save(self):
        product_id = self.adj_product.currentData()
        if product_id is None:
            QMessageBox.warning(self, "Error", "Please select a valid product.")
            return
        
        new_qty = self.adj_new_qty.value()
        reason = self.adj_reason.text()
        staff = self.adj_staff.text()
        notes = self.adj_notes.toPlainText()
        location = self.adj_location.currentData()
        lang = self.get_lang()
        
        if not reason or not staff:
            msg = "အကြောင်းပြချက်နှင့် ပြင်ဆင်သူအမည် ထည့်ရန်လိုအပ်ပါသည်။" if lang == "my" else "Reason and Adjusted By are required"
            QMessageBox.warning(self, "Error", msg)
            return
        
        # Check if location is valid
        if location == "__NEW__":
            msg = "Please select a valid location or add a new one first." if lang != "my" else "ကျေးဇူးပြု၍ နေရာတစ်ခုရွေးပါ သို့မဟုတ် အသစ်ထည့်ပါ။"
            QMessageBox.warning(self, "Error", msg)
            return

        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT stock, sold_by FROM products WHERE id=?", (product_id,))
            old_stock, sold_by = cursor.fetchone()
            if sold_by == "Service":
                QMessageBox.warning(self, "Error", "Cannot adjust stock for Service products.")
                return
            
            if old_stock == new_qty:
                QMessageBox.information(self, "Info", "No change" if lang != "my" else "ပြောင်းလဲမှုမရှိပါ")
                return
            
            # Update product stock
            cursor.execute("UPDATE products SET stock = ?, last_updated = CURRENT_TIMESTAMP WHERE id=?", (new_qty, product_id))
            
            # Update product_locations table
            if location:
                diff = new_qty - old_stock
                if diff > 0:
                    # Add stock to location
                    cursor.execute("""
                        INSERT INTO product_locations (product_id, location, quantity)
                        VALUES (?, ?, ?)
                        ON CONFLICT(product_id, location) 
                        DO UPDATE SET quantity = quantity + excluded.quantity
                    """, (product_id, location, diff))
                elif diff < 0:
                    # Remove stock from location
                    cursor.execute("""
                        UPDATE product_locations 
                        SET quantity = quantity + ?
                        WHERE product_id = ? AND location = ?
                    """, (diff, product_id, location))
                    
                    # Check if quantity becomes 0 or negative, delete the location entry
                    cursor.execute("SELECT quantity FROM product_locations WHERE product_id = ? AND location = ?", (product_id, location))
                    remaining = cursor.fetchone()
                    if remaining and remaining[0] <= 0:
                        cursor.execute("DELETE FROM product_locations WHERE product_id = ? AND location = ?", (product_id, location))
            
            # Record stock movement with location
            cursor.execute("""
                INSERT INTO stock_movements 
                (product_id, type, quantity, old_stock, new_stock, reason, created_by, notes, location)
                VALUES (?, 'adjustment', ?, ?, ?, ?, ?, ?, ?)
            """, (product_id, abs(new_qty - old_stock), old_stock, new_qty, reason, staff, notes, location))
            
            conn.commit()
            msg = f"စတော့ကို {old_stock} မှ {new_qty} သို့ ပြင်ဆင်ပြီးပါပြီ။" if lang == "my" else f"Stock adjusted from {old_stock} to {new_qty}"
            if location:
                msg += f" (Location: {location})" if lang == "my" else f" (Location: {location})"
            QMessageBox.information(self, "Success", msg)
            
            # Refresh stock alerts in main window
            main_window = self.window()
            if hasattr(main_window, 'check_stock_alerts'):
                main_window.check_stock_alerts()
            
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()