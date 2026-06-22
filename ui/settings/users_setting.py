# ui/users_setting.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox, QLabel
)
from PyQt6.QtCore import Qt
from models.database import connect_db
from utils.language import lang
from utils.permissions import PermissionManager, Permission
import hashlib
import os


class UserDialog(QDialog):
    def __init__(self, user_data=None, parent=None, current_user_id=None):
        super().__init__(parent)
        self.user_data = user_data
        self.current_user_id = current_user_id
        self.setMinimumWidth(350)
        layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.full_name_edit = QLineEdit()
        self.role_combo = QComboBox()
        self.load_roles()  # Load roles from database

        layout.addRow(QLabel("Username:"), self.username_edit)
        layout.addRow(QLabel("Password:"), self.password_edit)
        layout.addRow(QLabel("Confirm Password:"), self.confirm_edit)
        layout.addRow(QLabel("Full Name:"), self.full_name_edit)
        layout.addRow(QLabel("Role:"), self.role_combo)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

        self.setLayout(layout)

        if user_data:
            self.username_edit.setText(user_data.get("username", ""))
            self.full_name_edit.setText(user_data.get("full_name", ""))
            idx = self.role_combo.findText(user_data.get("role", "Cashier"))
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)

        self.retranslateUi()

    def load_roles(self):
        """Load roles from user_roles table"""
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM user_roles ORDER BY name")
            rows = cursor.fetchall()
            self.role_combo.clear()
            for (name,) in rows:
                self.role_combo.addItem(name)
            conn.close()
        except Exception as e:
            print(f"Error loading roles: {e}")
            # Fallback roles
            self.role_combo.addItems(["Admin", "Manager", "Cashier", "Viewer"])

    def retranslateUi(self):
        if lang.get_current() == "my":
            self.setWindowTitle("အသုံးပြုသူပြင်ဆင်ရန်" if self.user_data else "အသုံးပြုသူအသစ်")
            # Translate labels
            for i in range(self.layout().rowCount()):
                label_item = self.layout().itemAt(i, QFormLayout.ItemRole.LabelRole)
                if label_item and isinstance(label_item.widget(), QLabel):
                    text = label_item.widget().text()
                    if "Username:" in text:
                        label_item.widget().setText("အသုံးပြုသူအမည်:")
                    elif "Password:" in text:
                        label_item.widget().setText("စကားဝှက်:")
                    elif "Confirm Password:" in text:
                        label_item.widget().setText("စကားဝှက်အတည်ပြု:")
                    elif "Full Name:" in text:
                        label_item.widget().setText("အမည်အပြည့်:")
                    elif "Role:" in text:
                        label_item.widget().setText("အခန်းကဏ္ဍ:")
            ok_btn = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
            cancel_btn = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
            if ok_btn:
                ok_btn.setText("သိမ်းမည်")
            if cancel_btn:
                cancel_btn.setText("မလုပ်တော့")
        else:
            self.setWindowTitle("Edit User" if self.user_data else "Add User")
            # Reset labels to English
            for i in range(self.layout().rowCount()):
                label_item = self.layout().itemAt(i, QFormLayout.ItemRole.LabelRole)
                if label_item and isinstance(label_item.widget(), QLabel):
                    text = label_item.widget().text()
                    if "အသုံးပြုသူအမည်" in text:
                        label_item.widget().setText("Username:")
                    elif "စကားဝှက်" in text:
                        label_item.widget().setText("Password:")
                    elif "စကားဝှက်အတည်ပြု" in text:
                        label_item.widget().setText("Confirm Password:")
                    elif "အမည်အပြည့်" in text:
                        label_item.widget().setText("Full Name:")
                    elif "အခန်းကဏ္ဍ" in text:
                        label_item.widget().setText("Role:")
            ok_btn = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
            cancel_btn = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
            if ok_btn:
                ok_btn.setText("OK")
            if cancel_btn:
                cancel_btn.setText("Cancel")

    def get_data(self):
        return {
            "username": self.username_edit.text().strip(),
            "password": self.password_edit.text(),
            "full_name": self.full_name_edit.text().strip(),
            "role": self.role_combo.currentText()
        }


class UsersSettingWidget(QWidget):
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.current_user_id = user_id  # ID of logged-in user
        self.selected_user_id = None
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setColumnHidden(0, True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.users_table.cellClicked.connect(self.select_user)
        layout.addWidget(self.users_table)

        btn_layout = QHBoxLayout()
        self.btn_add_user = QPushButton()
        self.btn_edit_user = QPushButton()
        self.btn_delete_user = QPushButton()
        self.btn_add_user.clicked.connect(self.add_user)
        self.btn_edit_user.clicked.connect(self.edit_user)
        self.btn_delete_user.clicked.connect(self.delete_user)
        btn_layout.addWidget(self.btn_add_user)
        btn_layout.addWidget(self.btn_edit_user)
        btn_layout.addWidget(self.btn_delete_user)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Apply permissions to buttons
        self.apply_permissions()

        lang.language_changed.connect(self.retranslateUi)
        self.retranslateUi()

    def apply_permissions(self):
        """Apply permissions to user management buttons"""
        if self.current_user_id:
            # Check if user has add user permission
            if not PermissionManager.user_has_permission(self.current_user_id, Permission.ADD_USER):
                self.btn_add_user.setEnabled(False)
                self.btn_add_user.setToolTip("You don't have permission to add users")
            
            # Check if user has edit user permission
            if not PermissionManager.user_has_permission(self.current_user_id, Permission.EDIT_USER):
                self.btn_edit_user.setEnabled(False)
                self.btn_edit_user.setToolTip("You don't have permission to edit users")
            
            # Check if user has delete user permission
            if not PermissionManager.user_has_permission(self.current_user_id, Permission.DELETE_USER):
                self.btn_delete_user.setEnabled(False)
                self.btn_delete_user.setToolTip("You don't have permission to delete users")

    def retranslateUi(self):
        if lang.get_current() == "my":
            self.users_table.setHorizontalHeaderLabels(["ID", "အသုံးပြုသူအမည်", "အမည်အပြည့်", "အခန်းကဏ္ဍ"])
            self.btn_add_user.setText("အသစ်ထည့်")
            self.btn_edit_user.setText("ပြင်ဆင်")
            self.btn_delete_user.setText("ဖျက်")
        else:
            self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Full Name", "Role"])
            self.btn_add_user.setText("Add User")
            self.btn_edit_user.setText("Edit")
            self.btn_delete_user.setText("Delete")

    def load_users(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, role FROM users ORDER BY username")
        rows = cursor.fetchall()
        conn.close()
        self.users_table.setRowCount(0)
        for row in rows:
            r = self.users_table.rowCount()
            self.users_table.insertRow(r)
            for col, val in enumerate(row):
                self.users_table.setItem(r, col, QTableWidgetItem(str(val)))
        self.selected_user_id = None

    def select_user(self, row, col):
        id_item = self.users_table.item(row, 0)
        if id_item:
            self.selected_user_id = int(id_item.text())

    def add_user(self):
        # Check permission again
        if self.current_user_id and not PermissionManager.user_has_permission(self.current_user_id, Permission.ADD_USER):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to add users.")
            return
            
        dialog = UserDialog(parent=self, current_user_id=self.current_user_id)
        if dialog.exec():
            data = dialog.get_data()
            if not data["username"]:
                QMessageBox.warning(self, "Error", "Username is required.")
                return
            if data["password"] != dialog.confirm_edit.text():
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return
            if not data["password"]:
                QMessageBox.warning(self, "Error", "Password is required.")
                return
            salt = os.urandom(32).hex()
            password_hash = hashlib.pbkdf2_hmac('sha256', data["password"].encode(), bytes.fromhex(salt), 100000).hex()
            conn = connect_db()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, full_name, role, salt, force_password_change, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data["username"], password_hash, data["full_name"], data["role"], salt, 0, 1))
                conn.commit()
                QMessageBox.information(self, "Success", "User added successfully.")
                self.load_users()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Error", f"Could not add user: {e}")
            finally:
                conn.close()

    def edit_user(self):
        # Check permission
        if self.current_user_id and not PermissionManager.user_has_permission(self.current_user_id, Permission.EDIT_USER):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to edit users.")
            return
            
        if not self.selected_user_id:
            QMessageBox.warning(self, "No Selection", "Please select a user first.")
            return
        
        # Prevent editing own role if not admin (optional)
        if self.selected_user_id == self.current_user_id:
            # Can edit own profile but with restrictions
            pass
            
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username, full_name, role, salt FROM users WHERE id=?", (self.selected_user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            QMessageBox.warning(self, "Error", "User not found.")
            return
        user_data = {"username": row[0], "full_name": row[1] or "", "role": row[2]}
        dialog = UserDialog(user_data, self, self.current_user_id)
        if dialog.exec():
            data = dialog.get_data()
            if not data["username"]:
                QMessageBox.warning(self, "Error", "Username is required.")
                return
            if data["password"] and data["password"] != dialog.confirm_edit.text():
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return
            conn = connect_db()
            cursor = conn.cursor()
            try:
                if data["password"]:
                    # Generate new salt and hash
                    salt = os.urandom(32).hex()
                    password_hash = hashlib.pbkdf2_hmac('sha256', data["password"].encode(), bytes.fromhex(salt), 100000).hex()
                    cursor.execute("""
                        UPDATE users 
                        SET username=?, password_hash=?, full_name=?, role=?, salt=?, force_password_change=0
                        WHERE id=?
                    """, (data["username"], password_hash, data["full_name"], data["role"], salt, self.selected_user_id))
                else:
                    cursor.execute("""
                        UPDATE users 
                        SET username=?, full_name=?, role=?
                        WHERE id=?
                    """, (data["username"], data["full_name"], data["role"], self.selected_user_id))
                conn.commit()
                QMessageBox.information(self, "Success", "User updated successfully.")
                self.load_users()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Error", f"Could not update user: {e}")
            finally:
                conn.close()

    def delete_user(self):
        # Check permission
        if self.current_user_id and not PermissionManager.user_has_permission(self.current_user_id, Permission.DELETE_USER):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to delete users.")
            return
            
        if not self.selected_user_id:
            QMessageBox.warning(self, "No Selection", "Please select a user first.")
            return
        
        # Cannot delete yourself
        if self.selected_user_id == self.current_user_id:
            QMessageBox.warning(self, "Cannot Delete", "You cannot delete your own account.")
            return
            
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id=?", (self.selected_user_id,))
        role = cursor.fetchone()
        if role and role[0] == "Admin":
            cursor.execute("SELECT COUNT(*) FROM users WHERE role='Admin'")
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                QMessageBox.warning(self, "Cannot Delete", "Cannot delete the only admin user.")
                conn.close()
                return
        conn.close()
        
        confirm = QMessageBox.question(self, "Confirm Delete", "Delete this user permanently?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id=?", (self.selected_user_id,))
            conn.commit()
            conn.close()
            self.load_users()
            QMessageBox.information(self, "Deleted", "User deleted.")