# ui/settings/receipt_setting.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QFileDialog, QTextEdit, QCheckBox, QScrollArea, QFrame,
    QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from models.database import connect_db
from utils.language import lang
import os
import shutil


class ReceiptSettingWidget(QWidget):
    receipt_settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_receipt_settings()

    def setup_ui(self):
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # ========== BUSINESS INFORMATION GROUP ==========
        business_group = QGroupBox()
        business_layout = QFormLayout()
        business_layout.setVerticalSpacing(15)

        # Shop Name
        self.shop_name_label = QLabel()
        self.shop_name_edit = QLineEdit()
        self.shop_name_edit.setPlaceholderText("Enter your shop name")
        business_layout.addRow(self.shop_name_label, self.shop_name_edit)

        # Shop Phone
        self.shop_phone_label = QLabel()
        self.shop_phone_edit = QLineEdit()
        self.shop_phone_edit.setPlaceholderText("e.g., 09-123456789")
        business_layout.addRow(self.shop_phone_label, self.shop_phone_edit)

        # Shop Address
        self.shop_address_label = QLabel()
        self.shop_address_edit = QTextEdit()
        self.shop_address_edit.setMaximumHeight(60)
        self.shop_address_edit.setPlaceholderText("Enter your shop address")
        business_layout.addRow(self.shop_address_label, self.shop_address_edit)

        business_group.setLayout(business_layout)
        content_layout.addWidget(business_group)

        # ========== LOGO GROUP ==========
        logo_group = QGroupBox()
        logo_layout = QVBoxLayout()
        
        # Logo preview
        self.logo_preview_label = QLabel("Logo Preview")
        self.logo_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview = QLabel()
        self.logo_preview.setFixedHeight(100)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet("border: 1px solid #ced4da; border-radius: 4px; background-color: #f8f9fa;")
        logo_layout.addWidget(self.logo_preview_label)
        logo_layout.addWidget(self.logo_preview)
        
        # Logo path and browse button
        logo_row = QHBoxLayout()
        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setReadOnly(True)
        self.logo_path_edit.setPlaceholderText("No logo selected")
        logo_row.addWidget(self.logo_path_edit)
        self.btn_browse_logo = QPushButton("Browse")
        self.btn_browse_logo.clicked.connect(self.select_shop_logo)
        logo_row.addWidget(self.btn_browse_logo)
        logo_layout.addLayout(logo_row)
        
        logo_group.setLayout(logo_layout)
        content_layout.addWidget(logo_group)

        # ========== RECEIPT HEADER/FOOTER GROUP ==========
        receipt_group = QGroupBox()
        receipt_layout = QFormLayout()
        receipt_layout.setVerticalSpacing(12)

        # Receipt Header
        self.header_label = QLabel()
        self.receipt_header = QTextEdit()
        self.receipt_header.setMaximumHeight(80)
        self.receipt_header.setPlaceholderText("Header message (e.g., Thank you for shopping!)")
        receipt_layout.addRow(self.header_label, self.receipt_header)

        # Footer Message
        self.footer_label = QLabel()
        self.receipt_footer = QTextEdit()
        self.receipt_footer.setMaximumHeight(80)
        self.receipt_footer.setPlaceholderText("Footer message (e.g., Visit us again!)")
        receipt_layout.addRow(self.footer_label, self.receipt_footer)

        # Show customer name on receipt
        self.show_customer_check = QCheckBox()
        receipt_layout.addRow("", self.show_customer_check)

        receipt_group.setLayout(receipt_layout)
        content_layout.addWidget(receipt_group)

        # Save button
        self.btn_save = QPushButton()
        self.btn_save.clicked.connect(self.save_settings)
        content_layout.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignCenter)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def retranslateUi(self):
        if lang.get_current() == "my":
            self.shop_name_label.setText("ဆိုင်အမည်:")
            self.shop_phone_label.setText("ဖုန်းနံပါတ်:")
            self.shop_address_label.setText("လိပ်စာ:")
            self.logo_preview_label.setText("ဆိုင်အမှတ်တံဆိပ် အကြိုကြည့်ရန်")
            self.btn_browse_logo.setText("ပုံရွေးရန်")
            self.header_label.setText("ပြေစာအပေါ်ပိုင်း:")
            self.footer_label.setText("ပြေစာအောက်ပိုင်း:")
            self.show_customer_check.setText("ပြေစာတွင်ဝယ်ယူသူအမည်ပြရန်")
            self.btn_save.setText("သိမ်းဆည်းမည်")
        else:
            self.shop_name_label.setText("Shop Name:")
            self.shop_phone_label.setText("Phone Number:")
            self.shop_address_label.setText("Address:")
            self.logo_preview_label.setText("Logo Preview")
            self.btn_browse_logo.setText("Browse")
            self.header_label.setText("Receipt Header:")
            self.footer_label.setText("Receipt Footer:")
            self.show_customer_check.setText("Show Customer Name on Receipt")
            self.btn_save.setText("Save Receipt Settings")

    def load_receipt_settings(self):
        conn = connect_db()
        cursor = conn.cursor()
        
        # Load shop info
        cursor.execute("SELECT value FROM settings WHERE key='shop_name'")
        row = cursor.fetchone()
        self.shop_name_edit.setText(row[0] if row else "")
        
        cursor.execute("SELECT value FROM settings WHERE key='shop_phone'")
        row = cursor.fetchone()
        self.shop_phone_edit.setText(row[0] if row else "")
        
        cursor.execute("SELECT value FROM settings WHERE key='shop_address'")
        row = cursor.fetchone()
        self.shop_address_edit.setPlainText(row[0] if row else "")
        
        # Load logo
        cursor.execute("SELECT value FROM settings WHERE key='shop_logo'")
        row = cursor.fetchone()
        logo_path = row[0] if row else ""
        self.logo_path_edit.setText(logo_path)
        if logo_path and os.path.exists(logo_path):
            self.update_logo_preview(logo_path)
        
        # Load receipt settings
        cursor.execute("SELECT value FROM settings WHERE key='receipt_header'")
        row = cursor.fetchone()
        self.receipt_header.setPlainText(row[0] if row else "")
        
        cursor.execute("SELECT value FROM settings WHERE key='receipt_footer'")
        row = cursor.fetchone()
        self.receipt_footer.setPlainText(row[0] if row else "")
        
        cursor.execute("SELECT value FROM settings WHERE key='show_customer_name'")
        row = cursor.fetchone()
        self.show_customer_check.setChecked(row[0] == '1' if row else True)
        
        conn.close()

    def save_settings(self):
        conn = connect_db()
        cursor = conn.cursor()
        
        # Save business info
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("shop_name", self.shop_name_edit.text()))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("shop_phone", self.shop_phone_edit.text()))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("shop_address", self.shop_address_edit.toPlainText()))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("shop_logo", self.logo_path_edit.text()))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("receipt_header", self.receipt_header.toPlainText()))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("receipt_footer", self.receipt_footer.toPlainText()))
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("show_customer_name", '1' if self.show_customer_check.isChecked() else '0'))
        
        conn.commit()
        conn.close()
        
        msg = "ပြေစာသတ်မှတ်ချက်များ သိမ်းဆည်းပြီးပါပြီ။" if lang.get_current() == "my" else "Receipt settings saved."
        QMessageBox.information(self, "Saved", msg)
        
        # Emit signal to notify that receipt settings have changed
        self.receipt_settings_changed.emit()

    def select_shop_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            # Create logos directory if not exists
            logo_dir = os.path.join(os.path.dirname(os.path.abspath("database/pos.db")), "logos")
            os.makedirs(logo_dir, exist_ok=True)
            
            # Copy logo to logos directory
            ext = os.path.splitext(file_path)[1]
            dest_path = os.path.join(logo_dir, f"shop_logo{ext}")
            try:
                shutil.copyfile(file_path, dest_path)
                self.logo_path_edit.setText(dest_path)
                self.update_logo_preview(dest_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save logo: {e}")

    def update_logo_preview(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_preview.setPixmap(scaled)
        else:
            self.logo_preview.setText("Preview not available")