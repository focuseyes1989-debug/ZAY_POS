import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPixmap, QColor, QIcon
from models.database import connect_db
from utils.paths import app_path


class ProductDetailDialog(QDialog):
    def __init__(self, product_id):
        super().__init__()
        self.product_id = product_id
        self.setWindowTitle("Product Details")
        self.setMinimumSize(550, 750)
        self.setModal(True)
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))   # added icon

        # Store product data for later status update
        self.product_data = None

        # Property keys (English)
        self.property_keys = [
            "SKU", "Name", "Category", "Barcode",
            "Price", "Stock", "Low Stock Alert", "Expire Date", "Status"
        ]
        # Myanmar translations
        self.property_my = [
            "SKU", "ပစ္စည်းအမည်", "အမျိုးအစား", "ဘားကုဒ်",
            "စျေးနှုန်း", "ကျန်ရှိသိုလှောင်မှု", "သတိပေးသိုလှောင်မှု", "သက်တမ်းကုန်ရက်", "အခြေအနေ"
        ]

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # ----- Product Image -----
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(250)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #fafafa;")
        self.image_label.setText("Loading image...")
        main_layout.addWidget(self.image_label)

        # ----- Details Table -----
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Property", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dcdcdc;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

        self.table.setRowCount(len(self.property_keys))
        self.table_items = []  # store references to left column items for later translation
        for row, prop in enumerate(self.property_keys):
            item_prop = QTableWidgetItem(prop)
            font = item_prop.font()
            font.setBold(True)
            item_prop.setFont(font)
            self.table.setItem(row, 0, item_prop)
            self.table_items.append(item_prop)
            self.table.setItem(row, 1, QTableWidgetItem("-"))

        main_layout.addWidget(self.table)

        # ----- Close Button -----
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        main_layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

        # Load data and apply language
        self.load_product_data()
        self.retranslateUi()

    # ---------- Language support ----------
    def get_lang(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='language'")
            row = cursor.fetchone()
            lang = row[0] if row else "en"
            conn.close()
        except:
            lang = "en"
        return lang

    def retranslateUi(self):
        lang = self.get_lang()
        if lang == "my":
            # Myanmar (Burmese)
            self.setWindowTitle("ပစ္စည်းအသေးစိတ်")
            for row, text in enumerate(self.property_my):
                self.table_items[row].setText(text)
            self.table.setHorizontalHeaderLabels(["အကြောင်းအရာ", "တန်ဖိုး"])
            self.btn_close.setText("ပိတ်ရန်")
            # Update image placeholder texts
            current_img_text = self.image_label.text()
            if current_img_text == "Loading image...":
                self.image_label.setText("ပုံတင်နေသည်...")
            elif current_img_text == "Invalid image file":
                self.image_label.setText("ပုံဖိုင်မမှန်ပါ")
            elif current_img_text == "No image available":
                self.image_label.setText("ပုံမရှိပါ")
        else:
            # English
            self.setWindowTitle("Product Details")
            for row, text in enumerate(self.property_keys):
                self.table_items[row].setText(text)
            self.table.setHorizontalHeaderLabels(["Property", "Value"])
            self.btn_close.setText("Close")
            # Restore image placeholder texts
            current_img_text = self.image_label.text()
            if current_img_text == "ပုံတင်နေသည်...":
                self.image_label.setText("Loading image...")
            elif current_img_text == "ပုံဖိုင်မမှန်ပါ":
                self.image_label.setText("Invalid image file")
            elif current_img_text == "ပုံမရှိပါ":
                self.image_label.setText("No image available")

        # Refresh the status value (because it contains translated text)
        self.update_status_value()

    def update_status_value(self):
        """Re‑compute and update the status row using current language."""
        if not self.product_data:
            return
        sku, name, category, barcode, price, stock, low_stock, expire_date, image_path = self.product_data
        stock_val = int(stock) if stock is not None else 0
        low_val = int(low_stock) if low_stock is not None else 0
        today = QDate.currentDate()
        lang = self.get_lang()

        # Determine status text in current language
        if stock_val == 0:
            status_text = "Out of Stock" if lang != "my" else "ကုန်သွားပြီ"
            status_color = "red"
        elif stock_val <= low_val:
            status_text = "Low Stock" if lang != "my" else "စတော့နည်းနေပြီ"
            status_color = "orange"
        else:
            status_text = "In Stock" if lang != "my" else "ကျန်ရှိသည်"
            status_color = "green"

        if expire_date:
            try:
                expire_qdate = QDate.fromString(expire_date, "yyyy-MM-dd")
                if expire_qdate < today:
                    if lang == "my":
                        status_text += " | သက်တမ်းကုန်ပြီ"
                    else:
                        status_text += " | Expired"
                    status_color = "red"
                elif expire_qdate <= today.addDays(7):
                    if lang == "my":
                        status_text += " | သက်တမ်းနီးပြီ"
                    else:
                        status_text += " | Expiring Soon"
                    if status_color != "red":
                        status_color = "orange"
            except:
                pass

        # Create and style the status item
        status_item = QTableWidgetItem(status_text)
        if status_color == "red":
            status_item.setForeground(QColor(231, 76, 60))
            status_item.setBackground(QColor(255, 240, 240))
        elif status_color == "orange":
            status_item.setForeground(QColor(230, 126, 34))
            status_item.setBackground(QColor(255, 245, 235))
        else:
            status_item.setForeground(QColor(46, 204, 113))
            status_item.setBackground(QColor(240, 255, 240))
        status_item.setFont(self.table.font())
        self.table.setItem(self.property_keys.index("Status"), 1, status_item)

    def load_product_data(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sku, name, category, barcode, price, stock, low_stock,
                       expire_date, image
                FROM products WHERE id=?
            """, (self.product_id,))
            product = cursor.fetchone()
            conn.close()

            if not product:
                self.set_table_value("SKU", "Product not found")
                return

            self.product_data = product
            sku, name, category, barcode, price, stock, low_stock, expire_date, image_path = product

            stock_val = int(stock) if stock is not None else 0
            low_val = int(low_stock) if low_stock is not None else 0
            price_val = float(price) if price is not None else 0.0

            self.set_table_value("SKU", sku or "-")
            self.set_table_value("Name", name or "-")
            self.set_table_value("Category", category or "-")
            self.set_table_value("Barcode", barcode or "-")
            self.set_table_value("Price", f"{price_val:.2f}")
            self.set_table_value("Stock", str(stock_val))
            self.set_table_value("Low Stock Alert", str(low_val))
            self.set_table_value("Expire Date", expire_date or "None")

            # Load image
            self.load_image(image_path)
            # Status will be set in retranslateUi() -> update_status_value()
        except Exception as e:
            self.set_table_value("SKU", f"Error: {str(e)}")

    def set_table_value(self, property_name, value):
        try:
            row = self.property_keys.index(property_name)
            self.table.setItem(row, 1, QTableWidgetItem(value))
        except ValueError:
            pass

    def load_image(self, image_path):
        lang = self.get_lang()
        resolved_path = image_path
        if image_path and not os.path.isabs(image_path):
            resolved_path = app_path(image_path)

        if resolved_path and os.path.exists(resolved_path):
            pixmap = QPixmap(resolved_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.image_label.width() - 20,
                    self.image_label.height() - 20,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText("Invalid image file" if lang != "my" else "ပုံဖိုင်မမှန်ပါ")
        else:
            self.image_label.setText("No image available" if lang != "my" else "ပုံမရှိပါ")
