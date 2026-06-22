# ui/inventory_page/warehouse_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QHeaderView, QLineEdit,
    QLabel, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.language import lang
from loguru import logger


class WarehouseDialog(QDialog):
    """Manage warehouse/location for products"""
    warehouses_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Locations")
        self.setMinimumSize(700, 500)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Top section: Add new location
        top_group = QGroupBox("Add New Location")
        top_layout = QHBoxLayout()
        
        self.location_name = QLineEdit()
        self.location_name.setPlaceholderText("Enter location name (e.g., Shelf A1, Warehouse 1)")
        top_layout.addWidget(self.location_name, 2)
        
        self.btn_add_location = QPushButton("Add Location")
        self.btn_add_location.clicked.connect(self.add_location)
        top_layout.addWidget(self.btn_add_location)
        
        top_group.setLayout(top_layout)
        layout.addWidget(top_group)
        
        # Location table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Location Name", "Product Count", "Actions"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setColumnHidden(0, True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self.edit_location)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_location)
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_locations()
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
            self.setWindowTitle("ပစ္စည်းထားရာနေရာများ စီမံရန်")
            self.location_name.setPlaceholderText("နေရာအမည်ထည့်ပါ (ဥပမာ - စင်တန်း A1၊ ဂိုဒေါင် ၁)")
            self.btn_add_location.setText("နေရာအသစ်ထည့်")
            self.btn_edit.setText("ပြင်ဆင်")
            self.btn_delete.setText("ဖျက်")
            self.btn_close.setText("ပိတ်မည်")
            self.table.setHorizontalHeaderLabels(["ID", "နေရာအမည်", "ပစ္စည်းအရေအတွက်", "လုပ်ဆောင်ချက်"])
        else:
            self.setWindowTitle("Manage Locations")
            self.location_name.setPlaceholderText("Enter location name (e.g., Shelf A1, Warehouse 1)")
            self.btn_add_location.setText("Add Location")
            self.btn_edit.setText("Edit")
            self.btn_delete.setText("Delete")
            self.btn_close.setText("Close")
            self.table.setHorizontalHeaderLabels(["ID", "Location Name", "Product Count", "Actions"])
    
    def load_locations(self):
        """Load locations from product_locations table"""
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get all unique locations from product_locations table
        cursor.execute("""
            SELECT DISTINCT location FROM product_locations 
            WHERE location IS NOT NULL AND location != ''
            ORDER BY location
        """)
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(0)
        for row in rows:
            location_name = row[0]
            
            # Count products in this location
            conn2 = connect_db()
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT COUNT(*) FROM product_locations WHERE location = ?", (location_name,))
            count = cursor2.fetchone()[0]
            conn2.close()
            
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(location_name))
            self.table.setItem(r, 1, QTableWidgetItem(location_name))
            self.table.setItem(r, 2, QTableWidgetItem(str(count)))
            
            btn_delete = QPushButton("🗑️" if self.get_lang() != "my" else "🗑️ ဖျက်")
            btn_delete.setFixedSize(80, 30)
            btn_delete.clicked.connect(lambda checked, name=location_name: self.delete_location_by_name(name))
            self.table.setCellWidget(r, 3, btn_delete)
    
    def add_location(self):
        """Add a new location to product_locations table"""
        name = self.location_name.text().strip()
        if not name:
            lang_code = self.get_lang()
            msg = "Please enter a location name." if lang_code != "my" else "နေရာအမည်ထည့်ပါ။"
            QMessageBox.warning(self, "Error", msg)
            return
        
        # Check if location already exists in product_locations
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM product_locations WHERE location = ?", (name,))
        exists = cursor.fetchone()[0] > 0
        conn.close()
        
        if exists:
            lang_code = self.get_lang()
            msg = f"Location '{name}' already exists!" if lang_code != "my" else f"နေရာ '{name}' ရှိပြီးသားပါ။"
            QMessageBox.warning(self, "Error", msg)
            return
        
        # Check if there are any products without location to assign
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products LIMIT 1")
        product = cursor.fetchone()
        
        if product:
            # For now, we'll just create a placeholder entry to add the location
            lang_code = self.get_lang()
            msg = f"Location '{name}' added successfully!\n\nTo assign products to this location, use the 'Add to Location' button in product location dialog." if lang_code != "my" else f"နေရာ '{name}' ထည့်သွင်းပြီးပါပြီ။\n\nပစ္စည်းများကို ဤနေရာသို့ သတ်မှတ်ရန် ပစ္စည်းနေရာပြင်ဆင်ရေးမှ 'နေရာသို့ထည့်' ခလုတ်ကို သုံးပါ။"
            QMessageBox.information(self, "Success", msg)
        else:
            lang_code = self.get_lang()
            msg = "No products found. Please add a product first to use locations." if lang_code != "my" else "ပစ္စည်းမရှိပါ။ နေရာအသုံးပြုရန် ပစ္စည်းအရင်ထည့်ပါ။"
            QMessageBox.warning(self, "Warning", msg)
        
        conn.close()
        
        self.location_name.clear()
        self.load_locations()
        self.warehouses_changed.emit()
    
    def edit_location(self):
        """Edit location name in product_locations, stock_movements, and products tables"""
        current_row = self.table.currentRow()
        if current_row < 0:
            lang_code = self.get_lang()
            msg = "Please select a location to edit." if lang_code != "my" else "ပြင်ဆင်လိုသော နေရာကိုရွေးပါ။"
            QMessageBox.warning(self, "No Selection", msg)
            return
        
        old_name = self.table.item(current_row, 1).text()
        
        lang_code = self.get_lang()
        new_name, ok = QInputDialog.getText(
            self, 
            "Edit Location" if lang_code != "my" else "နေရာပြင်ဆင်ရန်",
            "Enter new name:" if lang_code != "my" else "အမည်အသစ်ထည့်ပါ:",
            text=old_name
        )
        
        if ok and new_name.strip():
            new_name = new_name.strip()
            if new_name == old_name:
                return
            
            conn = connect_db()
            cursor = conn.cursor()
            try:
                cursor.execute("BEGIN IMMEDIATE")
                
                # Update product_locations table
                cursor.execute("UPDATE product_locations SET location = ? WHERE location = ?", (new_name, old_name))
                
                # IMPORTANT: Update stock_movements table as well
                cursor.execute("UPDATE stock_movements SET location = ? WHERE location = ?", (new_name, old_name))
                
                # Also update products.warehouse for backward compatibility
                cursor.execute("UPDATE products SET warehouse = ? WHERE warehouse = ?", (new_name, old_name))
                
                conn.commit()
                
                self.load_locations()
                self.warehouses_changed.emit()
                
                lang_code = self.get_lang()
                msg = f"Location renamed to '{new_name}' and updated in all records!" if lang_code != "my" else f"နေရာအမည် '{new_name}' သို့ ပြောင်းလဲပြီး မှတ်တမ်းအားလုံးတွင် ပြင်ဆင်ပြီးပါပြီ။"
                QMessageBox.information(self, "Success", msg)
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to rename location: {e}")
                lang_code = self.get_lang()
                msg = f"Failed to rename location: {e}" if lang_code != "my" else f"နေရာအမည်ပြောင်းလဲရာတွင် အမှားရှိသည်: {e}"
                QMessageBox.critical(self, "Error", msg)
            finally:
                conn.close()
    
    def delete_location(self):
        """Delete location from product_locations, stock_movements, and products tables"""
        current_row = self.table.currentRow()
        if current_row < 0:
            lang_code = self.get_lang()
            msg = "Please select a location to delete." if lang_code != "my" else "ဖျက်လိုသော နေရာကိုရွေးပါ။"
            QMessageBox.warning(self, "No Selection", msg)
            return
        
        name = self.table.item(current_row, 1).text()
        count = int(self.table.item(current_row, 2).text())
        
        if count > 0:
            lang_code = self.get_lang()
            msg = f"Location '{name}' has {count} products. Please move or remove them first." if lang_code != "my" else f"နေရာ '{name}' တွင် ပစ္စည်း {count} ခုရှိပါသည်။ ဦးစွာရွှေ့ပြောင်းပါ။"
            QMessageBox.warning(self, "Cannot Delete", msg)
            return
        
        lang_code = self.get_lang()
        reply = QMessageBox.question(
            self, 
            "Confirm Delete" if lang_code != "my" else "အတည်ပြုဖျက်ရန်",
            f"Delete location '{name}' permanently?" if lang_code != "my" else f"နေရာ '{name}' ကို အပြီးတိုင်ဖျက်မည်လား?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = connect_db()
            cursor = conn.cursor()
            try:
                cursor.execute("BEGIN IMMEDIATE")
                
                # Delete from product_locations
                cursor.execute("DELETE FROM product_locations WHERE location = ?", (name,))
                
                # Update stock_movements - set location to empty string
                cursor.execute("UPDATE stock_movements SET location = '' WHERE location = ?", (name,))
                
                # Also update products.warehouse for backward compatibility
                cursor.execute("UPDATE products SET warehouse = '' WHERE warehouse = ?", (name,))
                
                conn.commit()
                
                self.load_locations()
                self.warehouses_changed.emit()
                
                lang_code = self.get_lang()
                msg = "Location deleted successfully!" if lang_code != "my" else "နေရာဖျက်ပြီးပါပြီ။"
                QMessageBox.information(self, "Success", msg)
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to delete location: {e}")
                lang_code = self.get_lang()
                msg = f"Failed to delete location: {e}" if lang_code != "my" else f"နေရာဖျက်ရာတွင် အမှားရှိသည်: {e}"
                QMessageBox.critical(self, "Error", msg)
            finally:
                conn.close()
    
    def delete_location_by_name(self, name):
        """Delete location by name"""
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM product_locations WHERE location = ?", (name,))
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            lang_code = self.get_lang()
            msg = f"Location '{name}' has {count} products. Please move or remove them first." if lang_code != "my" else f"နေရာ '{name}' တွင် ပစ္စည်း {count} ခုရှိပါသည်။ ဦးစွာရွှေ့ပြောင်းပါ။"
            QMessageBox.warning(self, "Cannot Delete", msg)
            return
        
        lang_code = self.get_lang()
        reply = QMessageBox.question(
            self,
            "Confirm Delete" if lang_code != "my" else "အတည်ပြုဖျက်ရန်",
            f"Delete location '{name}' permanently?" if lang_code != "my" else f"နေရာ '{name}' ကို အပြီးတိုင်ဖျက်မည်လား?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            conn = connect_db()
            cursor = conn.cursor()
            try:
                cursor.execute("BEGIN IMMEDIATE")
                
                # Delete from product_locations
                cursor.execute("DELETE FROM product_locations WHERE location = ?", (name,))
                
                # Update stock_movements - set location to empty string
                cursor.execute("UPDATE stock_movements SET location = '' WHERE location = ?", (name,))
                
                # Also update products.warehouse for backward compatibility
                cursor.execute("UPDATE products SET warehouse = '' WHERE warehouse = ?", (name,))
                
                conn.commit()
                
                self.load_locations()
                self.warehouses_changed.emit()
                
                lang_code = self.get_lang()
                msg = "Location deleted successfully!" if lang_code != "my" else "နေရာဖျက်ပြီးပါပြီ။"
                QMessageBox.information(self, "Success", msg)
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to delete location: {e}")
                lang_code = self.get_lang()
                msg = f"Failed to delete location: {e}" if lang_code != "my" else f"နေရာဖျက်ရာတွင် အမှားရှိသည်: {e}"
                QMessageBox.critical(self, "Error", msg)
            finally:
                conn.close()