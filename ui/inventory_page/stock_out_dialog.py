# ui/inventory_page/stock_out_dialog.py
from PyQt6.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit, QPushButton, QMessageBox, QVBoxLayout, QInputDialog
from PyQt6.QtCore import QDate
from models.database import connect_db
from utils.currency import format_money
from datetime import datetime


class StockOutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stock Out")
        self.resize(500, 650)
        layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.stock_out_no = QLineEdit()
        self.stock_out_no.setReadOnly(True)
        self.stock_out_no.setText(f"SOUT-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search product by name, barcode or SKU...")
        self.product_search.textChanged.connect(self.filter_products)
        
        self.so_product = QComboBox()
        self.so_qty = QSpinBox()
        self.so_qty.setRange(1, 999999)
        self.so_reason = QComboBox()
        self.so_reason.addItems(["Sale", "Damage", "Transfer", "Other"])
        self.so_reference = QLineEdit()
        self.so_customer = QComboBox()
        self.so_issued_by = QLineEdit()
        self.so_date = QDateEdit()
        self.so_date.setCalendarPopup(True)
        self.so_date.setDate(QDate.currentDate())
        self.so_notes = QTextEdit()
        self.so_notes.setMaximumHeight(80)
        
        # Location ComboBox
        self.so_location = QComboBox()
        self.so_location.addItem("None", None)
        self.so_location.addItem("+ Add New Location", "__NEW__")
        self.load_locations()

        self.labels = {}
        for key in ["stock_out_no", "product", "qty", "reason", "reference",
                    "customer", "issued_by", "date", "location", "notes"]:
            self.labels[key] = QLabel(key.replace("_", " ").title() + ":")
        self.btn_save = QPushButton("Save Stock Out")

        self.form_layout.addRow(self.labels["stock_out_no"], self.stock_out_no)
        self.form_layout.addRow(QLabel("Search Product:"), self.product_search)
        self.form_layout.addRow(self.labels["product"], self.so_product)
        self.form_layout.addRow(self.labels["qty"], self.so_qty)
        self.form_layout.addRow(self.labels["reason"], self.so_reason)
        self.form_layout.addRow(self.labels["reference"], self.so_reference)
        self.form_layout.addRow(self.labels["customer"], self.so_customer)
        self.form_layout.addRow(self.labels["issued_by"], self.so_issued_by)
        self.form_layout.addRow(self.labels["date"], self.so_date)
        self.form_layout.addRow(self.labels["location"], self.so_location)
        self.form_layout.addRow(self.labels["notes"], self.so_notes)

        layout.addLayout(self.form_layout)
        layout.addWidget(self.btn_save)
        self.setLayout(layout)

        self.btn_save.clicked.connect(self.save)
        self.so_location.currentIndexChanged.connect(self.on_location_changed)
        self.load_dropdowns()
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
        
        self.so_location.blockSignals(True)
        
        # Clear and add default items
        self.so_location.clear()
        self.so_location.addItem("None", None)
        
        # Collect all unique locations
        locations_set = set()
        for (name,) in rows:
            locations_set.add(name)
        
        # Add locations to combobox
        for location in sorted(locations_set):
            self.so_location.addItem(location, location)
        
        # Add "Add New Location" option
        self.so_location.addItem("+ Add New Location", "__NEW__")
        
        self.so_location.blockSignals(False)
        conn.close()

    def on_location_changed(self, index):
        """Handle location combo box change"""
        if index < 0:
            return
            
        current_text = self.so_location.currentText()
        current_data = self.so_location.currentData()
        
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
                index = self.so_location.findText(new_location)
                if index >= 0:
                    self.so_location.setCurrentIndex(index)
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
                index = self.so_location.findText(new_location)
                if index >= 0:
                    self.so_location.setCurrentIndex(index)
                
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Warning", msg)
                # Reset to None
                self.so_location.setCurrentIndex(0)
        else:
            # If user cancels, reset to "None"
            self.so_location.setCurrentIndex(0)

    def retranslateUi(self):
        lang = self.get_lang()
        if lang == "my":
            self.setWindowTitle("စတော့ထွက်ရန်")
            translations = {
                "stock_out_no": "စတော့ထွက်အမှတ်:",
                "product": "ပစ္စည်း:",
                "qty": "အရေအတွက်:",
                "reason": "အကြောင်းပြချက်:",
                "reference": "ကိုးကားအမှတ်:",
                "customer": "ဝယ်ယူသူ:",
                "issued_by": "ထုတ်ပေးသူ:",
                "date": "ရက်စွဲ:",
                "location": "နေရာ:",
                "notes": "မှတ်ချက်:"
            }
            for key, text in translations.items():
                self.labels[key].setText(text)
            self.btn_save.setText("သိမ်းဆည်းမည်")
            self.so_reason.setItemText(0, "ရောင်းချခြင်း")
            self.so_reason.setItemText(1, "ပျက်စီးခြင်း")
            self.so_reason.setItemText(2, "လွှဲပြောင်းခြင်း")
            self.so_reason.setItemText(3, "အခြား")
            self.product_search.setPlaceholderText("ပစ္စည်းအမည် / ဘားကုဒ် / SKU ဖြင့်ရှာရန်...")
            
            # Update "Add New Location" text
            index = self.so_location.findData("__NEW__")
            if index >= 0:
                self.so_location.setItemText(index, "+ နေရာအသစ်ထည့်")
        else:
            self.setWindowTitle("Stock Out")
            for key, label in self.labels.items():
                label.setText(key.replace("_", " ").title() + ":")
            self.btn_save.setText("Save Stock Out")
            self.so_reason.setItemText(0, "Sale")
            self.so_reason.setItemText(1, "Damage")
            self.so_reason.setItemText(2, "Transfer")
            self.so_reason.setItemText(3, "Other")
            self.product_search.setPlaceholderText("Search product by name, barcode or SKU...")
            
            # Update "Add New Location" text
            index = self.so_location.findData("__NEW__")
            if index >= 0:
                self.so_location.setItemText(index, "+ Add New Location")

    def load_dropdowns(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, barcode, sku, sold_by FROM products ORDER BY name")
        self.all_products = cursor.fetchall()
        self.filter_products()
        cursor.execute("SELECT id, name FROM customers ORDER BY name")
        custs = cursor.fetchall()
        self.so_customer.clear()
        self.so_customer.addItem("None", None)
        for cid, name in custs:
            self.so_customer.addItem(name, cid)
        conn.close()

    def filter_products(self):
        search_text = self.product_search.text().strip().lower()
        self.so_product.clear()
        self.so_product.blockSignals(True)
        for pid, name, barcode, sku, sold_by in self.all_products:
            if (search_text in name.lower() or 
                (barcode and search_text in barcode.lower()) or 
                (sku and search_text in sku.lower())):
                display_text = f"{name} {'(Service)' if sold_by == 'Service' else ''}"
                self.so_product.addItem(display_text, pid)
        self.so_product.blockSignals(False)
        if self.so_product.count() > 0:
            self.so_product.setCurrentIndex(0)

    def save(self):
        product_id = self.so_product.currentData()
        if product_id is None:
            QMessageBox.warning(self, "Error", "Please select a valid product.")
            return
        
        qty = self.so_qty.value()
        reason = self.so_reason.currentText()
        ref_no = self.so_reference.text()
        issued_by = self.so_issued_by.text()
        notes = self.so_notes.toPlainText()
        location = self.so_location.currentData()
        lang = self.get_lang()
        
        if not issued_by:
            msg = "ထုတ်ပေးသူအမည် ထည့်ရန်လိုအပ်ပါသည်။" if lang == "my" else "Issued By is required"
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
            
            if old_stock < qty:
                msg = f"စတော့မလုံလောက်ပါ။ ကျန် {old_stock} သာရှိသည်။" if lang == "my" else f"Insufficient stock. Only {old_stock} available"
                QMessageBox.warning(self, "Error", msg)
                return
            
            new_stock = old_stock - qty
            cursor.execute("UPDATE products SET stock = ?, last_updated = CURRENT_TIMESTAMP WHERE id=?", (new_stock, product_id))
            
            # Update product_locations table
            if location:
                cursor.execute("""
                    UPDATE product_locations 
                    SET quantity = quantity - ?
                    WHERE product_id = ? AND location = ?
                """, (qty, product_id, location))
                
                # Check if quantity becomes 0, delete the location entry
                cursor.execute("SELECT quantity FROM product_locations WHERE product_id = ? AND location = ?", (product_id, location))
                remaining = cursor.fetchone()
                if remaining and remaining[0] <= 0:
                    cursor.execute("DELETE FROM product_locations WHERE product_id = ? AND location = ?", (product_id, location))
            
            # Record stock movement with location
            cursor.execute("""
                INSERT INTO stock_movements 
                (product_id, type, quantity, old_stock, new_stock, reason, reference, created_by, notes, location)
                VALUES (?, 'out', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (product_id, qty, old_stock, new_stock, reason, ref_no, issued_by, notes, location))
            
            conn.commit()
            msg = f"စတော့ထွက်ပြီးပါပြီ။ လက်ကျန်: {new_stock}" if lang == "my" else f"Stock Out recorded. New stock: {new_stock}"
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