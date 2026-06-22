from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox, QLabel
from PyQt6.QtCore import pyqtSignal
from models.database import connect_db


class ProductFilters(QWidget):
    filter_changed = pyqtSignal()
    barcode_scanned = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name / barcode / SKU...")
        self.search_input.textChanged.connect(self._on_filter_changed)
        self.search_input.returnPressed.connect(self._on_barcode_scanned)
        self.search_input.setClearButtonEnabled(True)

        self.category_label = QLabel("Category:")
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.currentTextChanged.connect(self._on_filter_changed)

        layout.addWidget(self.search_input)
        layout.addWidget(self.category_label)
        layout.addWidget(self.category_combo)

    def _on_filter_changed(self):
        self.filter_changed.emit()

    def _on_barcode_scanned(self):
        keyword = self.search_input.text().strip()
        if keyword:
            self.barcode_scanned.emit(keyword)
        self.search_input.clear()
        self.search_input.setFocus()

    def get_search_text(self) -> str:
        return self.search_input.text().strip().lower()

    def get_category(self) -> str:
        return self.category_combo.currentText()

    def load_categories(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name")
        rows = cursor.fetchall()
        self.category_combo.blockSignals(True)
        current = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("All Categories")
        for (name,) in rows:
            self.category_combo.addItem(name)
        idx = self.category_combo.findText(current)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        else:
            self.category_combo.setCurrentIndex(0)
        self.category_combo.blockSignals(False)
        conn.close()

    def reset(self):
        """Reset search and category to default (all products)"""
        self.search_input.clear()
        self.category_combo.setCurrentIndex(0)

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def retranslateUi(self):
        from utils.language import lang
        if lang.get_current() == "my":
            self.search_input.setPlaceholderText("ပစ္စည်းအမည် / ဘားကုဒ် / SKU ဖြင့် ရှာရန်...")
            self.category_label.setText("အမျိုးအစား:")
            if self.category_combo.count() > 0:
                self.category_combo.setItemText(0, "အားလုံး")
        else:
            self.search_input.setPlaceholderText("Search by name / barcode / SKU...")
            self.category_label.setText("Category:")
            if self.category_combo.count() > 0:
                self.category_combo.setItemText(0, "All Categories")