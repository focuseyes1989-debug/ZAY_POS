# ui/manage_categories_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QInputDialog
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal
from models.database import connect_db


class ManageCategoriesDialog(QDialog):
    categories_changed = pyqtSignal()  # Signal for category changes
    
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setWindowTitle("Manage Categories")
        self.resize(400, 500)
        self.all_categories = []

        layout = QVBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_categories)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add New")
        self.btn_edit = QPushButton("Edit")
        self.btn_delete = QPushButton("Delete")
        self.btn_add.clicked.connect(self.add_category)
        self.btn_edit.clicked.connect(self.edit_category)
        self.btn_delete.clicked.connect(self.delete_category)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.load_categories()
        self.retranslateUi()

    # ---------- Language support ----------
    def retranslateUi(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='language'")
            row = cursor.fetchone()
            lang = row[0] if row else "en"
            conn.close()
        except:
            lang = "en"

        if lang == "my":
            self.setWindowTitle("အမျိုးအစားများ စီမံရန်")
            self.search_input.setPlaceholderText("အမျိုးအစားရှာရန်...")
            self.btn_add.setText("အသစ်ထည့်")
            self.btn_edit.setText("ပြင်ဆင်")
            self.btn_delete.setText("ဖျက်")
        else:
            self.setWindowTitle("Manage Categories")
            self.search_input.setPlaceholderText("Search category...")
            self.btn_add.setText("Add New")
            self.btn_edit.setText("Edit")
            self.btn_delete.setText("Delete")

    def load_categories(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        self.all_categories = cursor.fetchall()
        conn.close()
        self.filter_categories()

    def filter_categories(self):
        search_text = self.search_input.text().strip().lower()
        self.list_widget.clear()
        for cat_id, name in self.all_categories:
            if search_text in name.lower():
                item = QListWidgetItem(name)
                item.setData(1, cat_id)
                self.list_widget.addItem(item)

    def get_current_category_id(self):
        current = self.list_widget.currentItem()
        if current:
            return current.data(1)
        return None

    def get_language(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='language'")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "en"
        except:
            return "en"

    def add_category(self):
        lang = self.get_language()
        if lang == "my":
            title = "အမျိုးအစားအသစ်"
            label = "အမည်ထည့်ပါ:"
            error_msg = "မထည့်နိုင်ပါ: {e}"
            success_msg = "အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။"
        else:
            title = "New Category"
            label = "Enter category name:"
            error_msg = "Cannot add: {e}"
            success_msg = "Category added successfully."

        name, ok = QInputDialog.getText(self, title, label)
        if ok and name.strip():
            conn = connect_db()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (name.strip(),))
                conn.commit()
                QMessageBox.information(self, "Success", success_msg)
                self.categories_changed.emit()  # Emit signal
            except Exception as e:
                QMessageBox.warning(self, "Error", error_msg.format(e=str(e)))
            finally:
                conn.close()
            self.load_categories()

    def edit_category(self):
        cat_id = self.get_current_category_id()
        if cat_id is None:
            lang = self.get_language()
            msg = "ကျေးဇူးပြု၍ ပြင်ဆင်လိုသော အမျိုးအစားကို ရွေးပါ။" if lang == "my" else "Please select a category to edit."
            QMessageBox.warning(self, "No Selection", msg)
            return

        current_name = ""
        for cid, name in self.all_categories:
            if cid == cat_id:
                current_name = name
                break

        lang = self.get_language()
        if lang == "my":
            title = "အမျိုးအစားပြင်ဆင်ရန်"
            label = "အမည်အသစ်:"
            error_msg = "မပြင်ဆင်နိုင်ပါ: {e}"
            success_msg = "အောင်မြင်စွာ ပြင်ဆင်ပြီးပါပြီ။"
        else:
            title = "Edit Category"
            label = "New name:"
            error_msg = "Cannot update: {e}"
            success_msg = "Category updated successfully."

        new_name, ok = QInputDialog.getText(self, title, label, text=current_name)
        if ok and new_name.strip():
            conn = connect_db()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE categories SET name=? WHERE id=?", (new_name.strip(), cat_id))
                conn.commit()
                QMessageBox.information(self, "Success", success_msg)
                self.categories_changed.emit()  # Emit signal
            except Exception as e:
                QMessageBox.warning(self, "Error", error_msg.format(e=str(e)))
            finally:
                conn.close()
            self.load_categories()

    def delete_category(self):
        cat_id = self.get_current_category_id()
        if cat_id is None:
            lang = self.get_language()
            msg = "ကျေးဇူးပြု၍ ဖျက်လိုသော အမျိုးအစားကို ရွေးပါ။" if lang == "my" else "Please select a category to delete."
            QMessageBox.warning(self, "No Selection", msg)
            return

        lang = self.get_language()
        if lang == "my":
            confirm_text = "ဤအမျိုးအစားကို ဖျက်မည်လား။\nဤအမျိုးအစားအောက်ရှိ ပစ္စည်းများကို မဖျက်ပါ။"
            title = "အတည်ပြုဖျက်ရန်"
            success_msg = "အောင်မြင်စွာ ဖျက်ပြီးပါပြီ။"
        else:
            confirm_text = "Delete this category? Products using it will not be deleted."
            title = "Confirm Delete"
            success_msg = "Category deleted successfully."

        reply = QMessageBox.question(self, title, confirm_text,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = connect_db()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM categories WHERE id=?", (cat_id,))
                conn.commit()
                QMessageBox.information(self, "Success", success_msg)
                self.categories_changed.emit()  # Emit signal
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Cannot delete: {e}")
            finally:
                conn.close()
            self.load_categories()