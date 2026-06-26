# ui/product_form_dialog.py
import os
import shutil
import uuid
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, 
    QDoubleSpinBox, QDateEdit, QTextEdit, QPushButton, 
    QDialogButtonBox, QLabel, QMessageBox, QFileDialog, QHBoxLayout, QWidget
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QIcon
from models.database import connect_db
from utils.language import lang
from utils.paths import app_path, app_relative_path, get_app_root
from loguru import logger


class ProductFormDialog(QDialog):
    def __init__(self, product_id=None, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.image_path = ""
        self.setWindowTitle("Add Product" if product_id is None else "Edit Product")
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setMinimumSize(550, 520)

        # Create form layout
        layout = QFormLayout()
        layout.setVerticalSpacing(12)
        layout.setHorizontalSpacing(20)

        # Fields
        self.name_input = QLineEdit()
        self.category_combo = QComboBox()
        
        # Barcode input with scanner support
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan barcode...")
        self.barcode_input.setClearButtonEnabled(True)
        self.barcode_input.returnPressed.connect(self.on_barcode_entered)
        # Install event filter to intercept Enter key
        self.barcode_input.installEventFilter(self)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.sold_by_combo = QComboBox()
        self.sold_by_combo.addItems(["Each", "Service"])
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 999999)
        self.price_input.setDecimals(0)
        
        # Low Stock Alert
        self.low_stock_input = QSpinBox()
        self.low_stock_input.setRange(0, 999999)
        self.low_stock_input.setToolTip("Stock ဘယ်လောက်ကျန်ရင် သတိပေးချက်ပြမလဲ သတ်မှတ်ပါ")
        
        # Image
        self.image_input = QLineEdit()
        self.image_input.setReadOnly(True)
        
        # Image browse button in a horizontal layout
        image_widget = QWidget()
        image_layout = QHBoxLayout(image_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(5)
        self.image_input.setMinimumWidth(200)
        self.btn_browse = QPushButton("Browse Image")
        self.btn_browse.clicked.connect(self.select_image)
        image_layout.addWidget(self.image_input)
        image_layout.addWidget(self.btn_browse)

        # Labels
        self.label_name = QLabel()
        self.label_category = QLabel()
        self.label_barcode = QLabel()
        self.label_description = QLabel()
        self.label_sold_by = QLabel()
        self.label_price = QLabel()
        self.label_low_stock = QLabel()
        self.label_image = QLabel()

        # Add rows
        layout.addRow(self.label_name, self.name_input)
        layout.addRow(self.label_category, self.category_combo)
        layout.addRow(self.label_barcode, self.barcode_input)
        layout.addRow(self.label_description, self.description_input)
        layout.addRow(self.label_sold_by, self.sold_by_combo)
        layout.addRow(self.label_price, self.price_input)
        layout.addRow(self.label_low_stock, self.low_stock_input)
        layout.addRow(self.label_image, image_widget)

        # Info label for cost/stock/expiry
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #5865f2; font-size: 9pt;")
        self.info_label.setWordWrap(True)
        layout.addRow(QLabel(""), self.info_label)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

        self.setLayout(layout)

        # Load data
        self.load_categories()
        if self.product_id:
            self.load_product_data()
        self.toggle_service_fields(self.sold_by_combo.currentText())
        self.sold_by_combo.currentTextChanged.connect(self.toggle_service_fields)

        # Language support
        lang.language_changed.connect(self.retranslateUi)
        self.retranslateUi()

    def eventFilter(self, obj, event):
        """Filter events for barcode input field to prevent Enter from moving focus"""
        if obj == self.barcode_input and event.type() == event.Type.KeyPress:
            # Allow Tab key to move focus normally
            if event.key() == Qt.Key.Key_Tab:
                return False
            
            # For Enter key, handle barcode and stay in field
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Don't let Enter move focus - we handle it manually
                return True
        
        return super().eventFilter(obj, event)

    def on_barcode_entered(self):
        """Handle barcode entry - stay in field after scanning"""
        barcode = self.barcode_input.text().strip()
        
        if barcode:
            # Check if barcode already exists (skip if editing same product)
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM products WHERE barcode = ? AND id != ?", 
                          (barcode, self.product_id if self.product_id else -1))
            existing = cursor.fetchone()
            conn.close()
            
            if existing:
                QMessageBox.warning(self, "Duplicate Barcode", 
                                   f"Barcode '{barcode}' already exists for product: {existing[1]}")
                self.barcode_input.selectAll()
                return
            
            # Keep focus on barcode field for next scan
            self.barcode_input.setFocus()
            self.barcode_input.selectAll()
            
            # Visual feedback - green border flash
            self.barcode_input.setStyleSheet("border: 2px solid #27ae60;")
            QTimer.singleShot(300, lambda: self.barcode_input.setStyleSheet(""))

    def keyPressEvent(self, event):
        """Override key press event for barcode scanner handling"""
        # If event is from barcode field and Enter is pressed, handle it
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.focusWidget() == self.barcode_input:
                # Handle barcode entry and stay in field
                self.on_barcode_entered()
                event.accept()
                return
        
        super().keyPressEvent(event)

    def load_categories(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name")
        rows = cursor.fetchall()
        self.category_combo.clear()
        for (name,) in rows:
            self.category_combo.addItem(name)
        conn.close()

    def load_product_data(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, category, barcode, description, sold_by, price,
                   low_stock, image
            FROM products WHERE id=?
        """, (self.product_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            self.name_input.setText(row[0])
            idx = self.category_combo.findText(row[1])
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            self.barcode_input.setText(row[2] or "")
            self.description_input.setPlainText(row[3])
            self.sold_by_combo.setCurrentText(row[4])
            self.price_input.setValue(float(row[5]))
            self.low_stock_input.setValue(int(row[6]) if row[6] else 0)
            self.image_path = row[7] or ""
            self.image_input.setText(row[7] or "")

    def toggle_service_fields(self, sold_by):
        is_service = (sold_by == "Service")
        self.price_input.setEnabled(not is_service)
        self.low_stock_input.setEnabled(not is_service)
        if is_service:
            self.price_input.setValue(0.0)
            self.low_stock_input.setValue(0)
            self.info_label.setText("Note: Cost, Stock and Expiry Date are managed in Inventory page via Stock In/Out.")
        else:
            self.info_label.setText("Note: Cost, Stock and Expiry Date will be set when you perform Stock In. Low Stock Alert is set here.")

    def select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Product Image", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            self.image_path = file_name
            self.image_input.setText(file_name)

    def get_project_root(self):
        return get_app_root()

    def get_product_images_dir(self):
        image_dir = app_path("database", "product_images")
        os.makedirs(image_dir, exist_ok=True)
        return image_dir

    def normalize_product_image_path(self, image_path):
        """
        Normalize and optimize product image.
        Stores relative path for portability.
        """
        if not image_path:
            return ""

        if not os.path.exists(image_path):
            return image_path

        # Optimize image (resize to 400x400, JPEG quality 80)
        from utils.image_optimizer import ImageOptimizer
        optimized_path = ImageOptimizer.optimize_image(
            image_path,
            output_size=(400, 400),
            quality=80,
            output_format='JPEG'
        )
        
        # ✅ Store as relative path for portability
        if optimized_path:
            # Get just the filename
            filename = os.path.basename(optimized_path)
            
            # Store as relative path (database/product_images/filename)
            # This ensures it works on any computer
            relative_path = os.path.join('database', 'product_images', filename)
            return relative_path
        
        return image_path

    def generate_sku(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products ORDER BY id DESC LIMIT 1")
        last = cursor.fetchone()
        conn.close()
        next_id = last[0] + 1 if last else 1
        return f"ITM-{next_id:05d}"

    def accept(self):
        is_service = (self.sold_by_combo.currentText() == "Service")
        
        # Default values
        default_cost = 0.0
        default_stock = 0
        default_expire_date = None
        low_stock = self.low_stock_input.value()
        image_path = self.normalize_product_image_path(self.image_path)
        
        # Validate barcode if entered
        barcode = self.barcode_input.text().strip()
        if barcode:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM products WHERE barcode = ? AND id != ?", 
                          (barcode, self.product_id if self.product_id else -1))
            existing = cursor.fetchone()
            conn.close()
            
            if existing:
                QMessageBox.warning(self, "Duplicate Barcode", 
                                   f"Barcode '{barcode}' already exists.")
                self.barcode_input.setFocus()
                self.barcode_input.selectAll()
                return
        
        conn = connect_db()
        cursor = conn.cursor()
        
        if self.product_id is None:
            sku = self.generate_sku()
            cursor.execute("""
                INSERT INTO products (name, category, description, sold_by, price, cost, sku,
                                      barcode, stock, low_stock, expire_date, image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.name_input.text(), self.category_combo.currentText(),
                  self.description_input.toPlainText(),
                  "Service" if is_service else "Each", self.price_input.value(),
                  default_cost, sku, barcode,
                  default_stock, low_stock,
                  default_expire_date, image_path))
            msg = "Product Saved Successfully"
        else:
            cursor.execute("""
                UPDATE products SET name=?, category=?, barcode=?, description=?, sold_by=?,
                price=?, low_stock=?, image=?
                WHERE id=?
            """, (self.name_input.text(), self.category_combo.currentText(),
                  barcode, self.description_input.toPlainText(),
                  "Service" if is_service else "Each", self.price_input.value(),
                  low_stock, image_path, self.product_id))
            msg = "Product Updated Successfully"
        
        conn.commit()
        conn.close()
        
        info_msg = "Product saved. Use Stock In from Inventory page to add cost, stock and expiry date."
        QMessageBox.information(self, "Success", f"{msg}\n\n{info_msg}")
        super().accept()

    def focus_barcode(self):
        """Focus on barcode field for scanning"""
        self.barcode_input.setFocus()
        self.barcode_input.selectAll()

    def showEvent(self, event):
        """Focus on barcode field when dialog shows"""
        super().showEvent(event)
        # Focus on barcode input after dialog is shown
        QTimer.singleShot(100, self.focus_barcode)

    def retranslateUi(self):
        lang_code = lang.get_current()
        if lang_code == "my":
            self.setWindowTitle("ပစ္စည်းအသစ်ထည့်ရန်" if self.product_id is None else "ပစ္စည်းပြင်ဆင်ရန်")
            self.label_name.setText("ပစ္စည်းအမည်:")
            self.label_category.setText("အမျိုးအစား:")
            self.label_barcode.setText("ဘားကုဒ်:")
            self.barcode_input.setPlaceholderText("ဘားကုဒ်ဖတ်ရန်...")
            self.label_description.setText("ဖော်ပြချက်:")
            self.label_sold_by.setText("ရောင်းပုံစံ:")
            self.label_price.setText("စျေးနှုန်း:")
            self.label_low_stock.setText("သတိပေးသိုလှောင်မှု:")
            self.label_image.setText("ပစ္စည်းပုံ:")
            self.btn_browse.setText("ပုံရွေးရန်")
            self.info_label.setText("မှတ်ချက် - ကုန်ကျစရိတ်၊ စတော့နှင့် သက်တမ်းကုန်ရက်တို့ကို Inventory စာမျက်နှာမှ Stock In ဖြင့် သတ်မှတ်ပါ။")
            self.low_stock_input.setToolTip("စတော့ဘယ်လောက်ကျန်ရင် သတိပေးချက်ပြမလဲ သတ်မှတ်ပါ")
            self.sold_by_combo.setItemText(0, "တစ်ခုချင်း")
            self.sold_by_combo.setItemText(1, "ဝန်ဆောင်မှု")
            ok_btn = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            cancel_btn = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
            if ok_btn:
                ok_btn.setText("သိမ်းမည်")
            if cancel_btn:
                cancel_btn.setText("မလုပ်တော့")
        else:
            self.setWindowTitle("Add Product" if self.product_id is None else "Edit Product")
            self.label_name.setText("Product Name:")
            self.label_category.setText("Category:")
            self.label_barcode.setText("Barcode:")
            self.barcode_input.setPlaceholderText("Scan barcode...")
            self.label_description.setText("Description:")
            self.label_sold_by.setText("Sold By:")
            self.label_price.setText("Price:")
            self.label_low_stock.setText("Low Stock Alert:")
            self.label_image.setText("Product Image:")
            self.btn_browse.setText("Browse Image")
            self.info_label.setText("Note: Cost, Stock and Expiry Date are managed in Inventory page via Stock In.")
            self.low_stock_input.setToolTip("Set the stock level at which you want to receive alerts")
            self.sold_by_combo.setItemText(0, "Each")
            self.sold_by_combo.setItemText(1, "Service")
            ok_btn = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            cancel_btn = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
            if ok_btn:
                ok_btn.setText("OK")
            if cancel_btn:
                cancel_btn.setText("Cancel")