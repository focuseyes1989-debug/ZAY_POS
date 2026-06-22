from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal
import json
import os

HISTORY_FILE = "temp/barcode_history.json"
MAX_HISTORY = 10


def load_barcode_history():
    try:
        os.makedirs("temp", exist_ok=True)
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []


def save_barcode_history(history):
    try:
        os.makedirs("temp", exist_ok=True)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history[:MAX_HISTORY], f)
    except:
        pass


class BarcodeHistoryWidget(QWidget):
    barcode_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.setLayout(self.layout)
        self.history = load_barcode_history()
        self.refresh_buttons()

    def add_barcode(self, barcode):
        if not barcode:
            return
        # Remove if already exists (to bring to front)
        if barcode in self.history:
            self.history.remove(barcode)
        self.history.insert(0, barcode)
        # Keep only max
        self.history = self.history[:MAX_HISTORY]
        save_barcode_history(self.history)
        self.refresh_buttons()

    def refresh_buttons(self):
        # Clear existing buttons
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        # Add label
        label = QLabel("Recent:")
        self.layout.addWidget(label)
        # Add buttons for each history item
        for barcode in self.history:
            btn = QPushButton(barcode)
            btn.setFixedHeight(25)
            btn.clicked.connect(lambda _, bc=barcode: self.barcode_selected.emit(bc))
            self.layout.addWidget(btn)
        self.layout.addStretch()

    def clear_history(self):
        self.history = []
        save_barcode_history([])
        self.refresh_buttons()