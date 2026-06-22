# ui/inventory_page/stock_in_dialog.py
from PyQt6.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPushButton, QMessageBox, QVBoxLayout, QInputDialog
from PyQt6.QtCore import Qt, QDate, QTimer
from models.database import connect_db
from utils.currency import format_money
from datetime import datetime


class StockInDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stock In")
        self.resize(480, 700)
        layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.stock_in_no = QLineEdit()
        self.stock_in_no.setReadOnly(True)
        self.stock_in_no.setText(f"SIN-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        # Product search with barcode scanner support
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search product by name, barcode or SKU...")
        self.product_search.textChanged.connect(self.filter_products)
        self.product_search.returnPressed.connect(self.on_search_entered)
        self.product_search.installEventFilter(self)
        
        self.si_product = QComboBox()
        self.si_supplier = QComboBox()
        self.si_po_no = QLineEdit()
        self.si_qty = QSpinBox()
        self.si_qty.setRange(1, 999999)
        self.si_unit_cost = QDoubleSpinBox()
        self.si_unit_cost.setRange(0, 1000000)
        self.si_unit_cost.setDecimals(0)
        self.si_total_cost = QLabel("0")
        self.si_batch_no = QLineEdit()
        self.si_expiry = QDateEdit()
        self.si_expiry.setCalendarPopup(True)
        self.si_expiry.setDate(QDate.currentDate().addDays(30))
        self.si_received_by = QLineEdit()
        self.si_date = QDateEdit()
        self.si_date.setCalendarPopup(True)
        self.si_date.setDate(QDate.currentDate())
        self.si_notes = QTextEdit()
        self.si_notes.setMaximumHeight(80)
        
        # Location ComboBox
        self.si_location = QComboBox()
        self.si_location.addItem("None", None)
        self.si_location.addItem("+ Add New Location", "__NEW__")
        self.load_locations()
        
        # Payment Status
        self.si_payment_status = QComboBox()
        self.si_payment_status.addItems(["Paid", "Unpaid", "Partial"])

        self.labels = {}
        for key in ["stock_in_no", "product", "supplier", "po_no", "qty", "unit_cost",
                    "total_cost", "batch_no", "expiry", "received_by", "date", 
                    "location", "notes", "payment_status"]:
            self.labels[key] = QLabel(key.replace("_", " ").title() + ":")
        
        self.btn_save = QPushButton("Save Stock In")

        self.form_layout.addRow(self.labels["stock_in_no"], self.stock_in_no)
        self.form_layout.addRow(QLabel("Search Product:"), self.product_search)
        self.form_layout.addRow(self.labels["product"], self.si_product)
        self.form_layout.addRow(self.labels["supplier"], self.si_supplier)
        self.form_layout.addRow(self.labels["po_no"], self.si_po_no)
        self.form_layout.addRow(self.labels["qty"], self.si_qty)
        self.form_layout.addRow(self.labels["unit_cost"], self.si_unit_cost)
        self.form_layout.addRow(self.labels["total_cost"], self.si_total_cost)
        self.form_layout.addRow(self.labels["batch_no"], self.si_batch_no)
        self.form_layout.addRow(self.labels["expiry"], self.si_expiry)
        self.form_layout.addRow(self.labels["received_by"], self.si_received_by)
        self.form_layout.addRow(self.labels["date"], self.si_date)
        self.form_layout.addRow(self.labels["location"], self.si_location)
        self.form_layout.addRow(self.labels["payment_status"], self.si_payment_status)
        self.form_layout.addRow(self.labels["notes"], self.si_notes)

        layout.addLayout(self.form_layout)
        layout.addWidget(self.btn_save)
        self.setLayout(layout)

        self.si_unit_cost.valueChanged.connect(self.update_total)
        self.si_qty.valueChanged.connect(self.update_total)
        self.btn_save.clicked.connect(self.save)
        
        # Connect location combo box change event
        self.si_location.currentIndexChanged.connect(self.on_location_changed)

        self.all_products = []
        self.load_dropdowns()
        self.retranslateUi()
        
        # Focus on search field when dialog opens
        QTimer.singleShot(100, self.focus_search)

    def eventFilter(self, obj, event):
        """Filter events for search input field to prevent Enter from moving focus"""
        if obj == self.product_search and event.type() == event.Type.KeyPress:
            # Allow Tab key to move focus normally
            if event.key() == Qt.Key.Key_Tab:
                return False
            
            # For Enter key, handle search and stay in field
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Don't let Enter move focus - we handle it manually
                return True
        
        return super().eventFilter(obj, event)

    def on_search_entered(self):
        """Handle search entry - stay in field after scanning/searching"""
        search_text = self.product_search.text().strip()
        
        if search_text:
            # Check if there's an exact match with barcode or SKU
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name FROM products 
                WHERE barcode = ? OR sku = ? 
                LIMIT 1
            """, (search_text, search_text))
            product = cursor.fetchone()
            conn.close()
            
            if product:
                # Found exact match, select it in combobox
                pid, name = product
                for i in range(self.si_product.count()):
                    if self.si_product.itemData(i) == pid:
                        self.si_product.setCurrentIndex(i)
                        # Visual feedback - green border flash
                        self.product_search.setStyleSheet("border: 2px solid #27ae60;")
                        QTimer.singleShot(300, lambda: self.product_search.setStyleSheet(""))
                        return
            
            # Keep focus on search field for next scan
            self.product_search.setFocus()
            self.product_search.selectAll()

    def keyPressEvent(self, event):
        """Override key press event for search scanner handling"""
        # If event is from search field and Enter is pressed, handle it
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.focusWidget() == self.product_search:
                # Handle search entry and stay in field
                self.on_search_entered()
                event.accept()
                return
        
        super().keyPressEvent(event)

    def focus_search(self):
        """Focus on search field for scanning"""
        self.product_search.setFocus()
        self.product_search.selectAll()

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
        
        self.si_location.blockSignals(True)
        
        # Clear and add default items
        self.si_location.clear()
        self.si_location.addItem("None", None)
        
        # Collect all unique locations
        locations_set = set()
        for (name,) in rows:
            locations_set.add(name)
        
        # Add locations to combobox
        for location in sorted(locations_set):
            self.si_location.addItem(location, location)
        
        # Add "Add New Location" option
        self.si_location.addItem("+ Add New Location", "__NEW__")
        
        self.si_location.blockSignals(False)
        conn.close()

    def on_location_changed(self, index):
        """Handle location combo box change"""
        if index < 0:
            return
            
        current_text = self.si_location.currentText()
        current_data = self.si_location.currentData()
        
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
                index = self.si_location.findText(new_location)
                if index >= 0:
                    self.si_location.setCurrentIndex(index)
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
                index = self.si_location.findText(new_location)
                if index >= 0:
                    self.si_location.setCurrentIndex(index)
                
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Warning", msg)
                # Reset to None
                self.si_location.setCurrentIndex(0)
        else:
            # If user cancels, reset to "None"
            self.si_location.setCurrentIndex(0)

    def retranslateUi(self):
        lang = self.get_lang()
        if lang == "my":
            self.setWindowTitle("စတော့ဝင်ရန်")
            translations = {
                "stock_in_no": "စတော့ဝင်အမှတ်:",
                "product": "ပစ္စည်း:",
                "supplier": "ပေးသွင်းသူ:",
                "po_no": "ဝယ်ယူမှုအမှတ်:",
                "qty": "အရေအတွက်:",
                "unit_cost": "တစ်ခုချင်းကုန်ကျစရိတ်:",
                "total_cost": "စုစုပေါင်းကုန်ကျစရိတ်:",
                "batch_no": "အသုတ်အမှတ်:",
                "expiry": "သက်တမ်းကုန်ရက်:",
                "received_by": "လက်ခံသူ:",
                "date": "ရက်စွဲ:",
                "location": "နေရာ:",
                "notes": "မှတ်ချက်:",
                "payment_status": "ငွေပေးချေမှုအခြေအနေ:"
            }
            for key, text in translations.items():
                self.labels[key].setText(text)
            self.btn_save.setText("သိမ်းဆည်းမည်")
            self.product_search.setPlaceholderText("ပစ္စည်းအမည် / ဘားကုဒ် / SKU ဖြင့်ရှာရန်...")
            self.si_payment_status.setItemText(0, "ပေးပြီး")
            self.si_payment_status.setItemText(1, "မပေးရသေး")
            self.si_payment_status.setItemText(2, "တစ်ပိုင်းပေးပြီး")
            
            # Update "Add New Location" text
            index = self.si_location.findData("__NEW__")
            if index >= 0:
                self.si_location.setItemText(index, "+ နေရာအသစ်ထည့်")
        else:
            self.setWindowTitle("Stock In")
            for key, label in self.labels.items():
                label.setText(key.replace("_", " ").title() + ":")
            self.btn_save.setText("Save Stock In")
            self.product_search.setPlaceholderText("Search product by name, barcode or SKU...")
            self.si_payment_status.setItemText(0, "Paid")
            self.si_payment_status.setItemText(1, "Unpaid")
            self.si_payment_status.setItemText(2, "Partial")
            
            # Update "Add New Location" text
            index = self.si_location.findData("__NEW__")
            if index >= 0:
                self.si_location.setItemText(index, "+ Add New Location")

    def load_dropdowns(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, barcode, sku, sold_by FROM products ORDER BY name")
        self.all_products = cursor.fetchall()
        self.filter_products()
        
        # Load only ACTIVE suppliers for Stock In
        cursor.execute("SELECT id, name FROM suppliers WHERE status = 'Active' ORDER BY name")
        sups = cursor.fetchall()
        self.si_supplier.clear()
        self.si_supplier.addItem("None", None)
        for sid, name in sups:
            self.si_supplier.addItem(name, sid)
        conn.close()

    def filter_products(self):
        search_text = self.product_search.text().strip().lower()
        self.si_product.clear()
        self.si_product.blockSignals(True)
        for pid, name, barcode, sku, sold_by in self.all_products:
            if (search_text in name.lower() or 
                (barcode and search_text in barcode.lower()) or 
                (sku and search_text in sku.lower())):
                display_text = f"{name} {'(Service)' if sold_by == 'Service' else ''}"
                self.si_product.addItem(display_text, pid)
        self.si_product.blockSignals(False)
        if self.si_product.count() > 0:
            self.si_product.setCurrentIndex(0)

    def update_total(self):
        qty = self.si_qty.value()
        cost = self.si_unit_cost.value()
        total = qty * cost
        self.si_total_cost.setText(format_money(total))

    def save(self):
        product_id = self.si_product.currentData()
        if product_id is None:
            QMessageBox.warning(self, "Error", "Please select a valid product.")
            return
        
        qty = self.si_qty.value()
        unit_cost = self.si_unit_cost.value()
        batch_no = self.si_batch_no.text()
        expire = self.si_expiry.date().toString("yyyy-MM-dd")
        received_by = self.si_received_by.text()
        notes = self.si_notes.toPlainText()
        supplier_id = self.si_supplier.currentData()
        po_no_input = self.si_po_no.text().strip()
        payment_status = self.si_payment_status.currentText()
        location = self.si_location.currentData()
        lang = self.get_lang()
        
        if not received_by:
            msg = "လက်ခံသူအမည် ထည့်ရန်လိုအပ်ပါသည်။" if lang == "my" else "Received By is required"
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
            cursor.execute("BEGIN IMMEDIATE")

            # Get current product data
            cursor.execute("SELECT stock, cost, supplier_id FROM products WHERE id=?", (product_id,))
            old_stock, old_cost, old_supplier = cursor.fetchone()
            old_stock = old_stock if old_stock is not None else 0
            old_cost = old_cost if old_cost is not None else 0
            new_stock = old_stock + qty
            
            # Calculate new average cost
            if new_stock > 0:
                new_average_cost = ((old_stock * old_cost) + (qty * unit_cost)) / new_stock
            else:
                new_average_cost = unit_cost
            
            # Update product
            if old_supplier is None and supplier_id:
                cursor.execute("""
                    UPDATE products 
                    SET stock = ?, cost = ?, expire_date = ?, supplier_id = ?, 
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_stock, new_average_cost, expire, supplier_id, product_id))
            else:
                cursor.execute("""
                    UPDATE products 
                    SET stock = ?, cost = ?, expire_date = ?, 
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_stock, new_average_cost, expire, product_id))
            
            # Insert into product_locations table
            if location:
                cursor.execute("""
                    INSERT INTO product_locations (product_id, location, quantity, batch_no, expire_date)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(product_id, location) 
                    DO UPDATE SET quantity = quantity + excluded.quantity,
                                  batch_no = COALESCE(excluded.batch_no, batch_no),
                                  expire_date = COALESCE(excluded.expire_date, expire_date)
                """, (product_id, location, qty, batch_no, expire))
            
            # Record stock movement
            cursor.execute("""
                INSERT INTO stock_movements 
                (product_id, type, quantity, old_stock, new_stock, reason, reference, created_by, notes, supplier_id, location)
                VALUES (?, 'in', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (product_id, qty, old_stock, new_stock, f"Stock In via {self.stock_in_no.text()}", 
                  po_no_input, received_by, notes, supplier_id, location))
            
            # Create Purchase Order if supplier is selected
            if supplier_id and supplier_id != "None":
                if not po_no_input:
                    po_no_input = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                order_date = self.si_date.date().toString("yyyy-MM-dd")
                total_amount = qty * unit_cost
                cursor.execute("""
                    INSERT INTO purchase_orders 
                    (po_no, supplier_id, order_date, total_amount, status, payment_status, received_by, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (po_no_input, supplier_id, order_date, total_amount, 'completed', payment_status, received_by, notes))
                po_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO purchase_order_items 
                    (po_id, product_id, quantity, unit_price, total)
                    VALUES (?, ?, ?, ?, ?)
                """, (po_id, product_id, qty, unit_cost, total_amount))
                
                cursor.execute("""
                    INSERT INTO supplier_payments 
                    (supplier_id, amount, payment_date, reference_no, payment_type, notes, purchase_order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (supplier_id, total_amount, order_date, po_no_input, 'Purchase', notes, po_id))
                
                if payment_status == "Paid":
                    cursor.execute("""
                        INSERT INTO supplier_payments 
                        (supplier_id, amount, payment_date, reference_no, payment_type, notes, purchase_order_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (supplier_id, total_amount, order_date, po_no_input, 'Paid', f"Full payment for {po_no_input}", po_id))

            conn.commit()
            
            # Get updated stock info for the message
            if location:
                cursor.execute("SELECT quantity FROM product_locations WHERE product_id=? AND location=?", (product_id, location))
                location_qty = cursor.fetchone()
                loc_qty = location_qty[0] if location_qty else 0
                msg = f"စတော့ဝင်ပြီးပါပြီ။ နေရာ {location} တွင် လက်ကျန်: {loc_qty}" if lang == "my" else f"Stock In recorded. Location {location} now has: {loc_qty}"
            else:
                msg = f"စတော့ဝင်ပြီးပါပြီ။ စုစုပေါင်းလက်ကျန်: {new_stock}" if lang == "my" else f"Stock In recorded. Total stock: {new_stock}"
            
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
    
    def showEvent(self, event):
        """Focus on search field when dialog shows"""
        super().showEvent(event)
        QTimer.singleShot(100, self.focus_search)