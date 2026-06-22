from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
import hashlib
from models.database import connect_db
import os


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - ZAY POS")
        self.setWindowIcon(QIcon("assets/icons/zaypos.png"))
        self.setFixedSize(400, 300)
        self.setModal(True)
        self.user_info = None

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # ----- Logo and Title -----
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_label = QLabel()
        logo_path = "assets/icons/zaypos.png"
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)

        title_label = QLabel("ZAY POINT OF SALE LITE")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin-top: 5px;")
        logo_layout.addWidget(title_label)

        main_layout.addLayout(logo_layout)

        # ----- Form (Username / Password) -----
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")

        form_layout.addRow(QLabel("Username:"), self.username_edit)
        form_layout.addRow(QLabel("Password:"), self.password_edit)

        main_layout.addLayout(form_layout)

        # ----- Buttons -----
        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Login")
        self.btn_login.clicked.connect(self.attempt_login)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.username_edit.setFocus()

    def attempt_login(self):
        try:
            username = self.username_edit.text().strip()
            password = self.password_edit.text()

            if not username or not password:
                QMessageBox.warning(self, "Error", "Please enter both username and password.")
                return

            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password_hash, role, full_name, salt, force_password_change FROM users WHERE username=?", (username,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
                return

            user_id, db_username, stored_hash, role, full_name, salt, force_change = user

            # Verify password
            if salt:
                # Normal case: use stored salt
                input_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100000).hex()
                password_ok = (input_hash == stored_hash)
            else:
                # Old user without salt: verify using the old hardcoded salt
                input_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt_123', 100000).hex()
                password_ok = (input_hash == stored_hash)

            if not password_ok:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
                return

            # If password is correct but the user has no salt or force_change flag is set, ask to change password
            if salt is None or force_change == 1:
                reply = QMessageBox.question(
                    self,
                    "Password Expired",
                    "For security reasons, you must change your password.\nDo you want to change it now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    from ui.change_password_dialog import ChangePasswordDialog
                    dialog = ChangePasswordDialog(user_id, db_username, self, old_password=password)
                    if dialog.exec():
                        # After successful password change, login with new credentials
                        self.user_info = {
                            "id": user_id,
                            "username": db_username,
                            "role": role,
                            "full_name": full_name or db_username
                        }
                        self.accept()
                    return
                else:
                    QMessageBox.warning(self, "Login Failed", "You must change your password to continue.")
                    return

            # Normal login (secure user)
            self.user_info = {
                "id": user_id,
                "username": db_username,
                "role": role,
                "full_name": full_name or db_username
            }
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Login Error", f"An error occurred: {str(e)}")