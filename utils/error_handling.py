# utils/error_handler.py (improved version)
from PyQt6.QtWidgets import QMessageBox, QTextEdit, QVBoxLayout, QDialog, QPushButton
from PyQt6.QtCore import Qt
from loguru import logger
import traceback
import sys


class ErrorDialog(QDialog):
    def __init__(self, error_type, error_message, error_details, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Error - {error_type}")
        self.setMinimumSize(600, 400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Error icon and message
        msg_label = QLabel(f"<b>{error_type}</b><br>{error_message}")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # Details text area
        details_text = QTextEdit()
        details_text.setPlainText(error_details)
        details_text.setReadOnly(True)
        layout.addWidget(details_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_copy = QPushButton("Copy to Clipboard")
        btn_copy.clicked.connect(lambda: self.copy_to_clipboard(error_details))
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_copy)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def copy_to_clipboard(self, text):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)


def show_error_dialog(error_type, error_message, error_details, parent=None):
    dialog = ErrorDialog(error_type, error_message, error_details, parent)
    dialog.exec()


def handle_exception(exc_type, exc_value, exc_traceback):
    """Enhanced global exception handler"""
    error_details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical("Unhandled exception")
    
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app and not app.startingUp():
        show_error_dialog(
            "Unexpected Error",
            str(exc_value),
            error_details
        )
    sys.__excepthook__(exc_type, exc_value, exc_traceback)