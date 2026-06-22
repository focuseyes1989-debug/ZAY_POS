from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import pyqtSignal


class PaginationWidget(QWidget):
    page_changed = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total_items = 0
        self._current_page = 1
        self._page_size = 50
        self._total_pages = 1

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(QLabel("Rows per page:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["25", "50", "100", "200"])
        self.page_size_combo.setCurrentText(str(self._page_size))
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        layout.addWidget(self.page_size_combo)

        self.btn_prev = QPushButton("Previous")
        self.btn_prev.clicked.connect(self._prev_page)
        layout.addWidget(self.btn_prev)

        self.page_label = QLabel("Page 1 of 1")
        layout.addWidget(self.page_label)

        self.btn_next = QPushButton("Next")
        self.btn_next.clicked.connect(self._next_page)
        layout.addWidget(self.btn_next)
        layout.addStretch()
        self.setLayout(layout)

    def set_total_items(self, total_items: int, emit_signal: bool = True):
        """Set total number of items - must be integer"""
        # Convert to int if it's a string
        if isinstance(total_items, str):
            try:
                total_items = int(total_items)
            except ValueError:
                total_items = 0
        
        self._total_items = total_items
        old_pages = self._total_pages
        self._total_pages = max(1, (total_items + self._page_size - 1) // self._page_size)
        
        if self._current_page > self._total_pages:
            self._current_page = self._total_pages
        self._update_controls()
        
        if emit_signal and (old_pages != self._total_pages or self._current_page != self._current_page):
            self._emit_page_changed()

    def set_current_page(self, page: int, emit_signal: bool = True):
        if 1 <= page <= self._total_pages and page != self._current_page:
            self._current_page = page
            self._update_controls()
            if emit_signal:
                self._emit_page_changed()

    def set_page_size(self, size: int, emit_signal: bool = True):
        if size != self._page_size:
            self._page_size = size
            self._current_page = 1
            self._total_pages = max(1, (self._total_items + size - 1) // size)
            self._update_controls()
            if emit_signal:
                self._emit_page_changed()

    def _update_controls(self):
        self.btn_prev.setEnabled(self._current_page > 1)
        self.btn_next.setEnabled(self._current_page < self._total_pages)
        from utils.language import lang
        if lang.get_current() == "my":
            self.page_label.setText(f"စာမျက်နှာ {self._current_page} / {self._total_pages}")
        else:
            self.page_label.setText(f"Page {self._current_page} of {self._total_pages}")
        self.page_size_combo.blockSignals(True)
        self.page_size_combo.setCurrentText(str(self._page_size))
        self.page_size_combo.blockSignals(False)

    def _emit_page_changed(self):
        self.page_changed.emit(self._current_page, self._page_size)

    def _on_page_size_changed(self, value: str):
        self.set_page_size(int(value))

    def _prev_page(self):
        if self._current_page > 1:
            self.set_current_page(self._current_page - 1)

    def _next_page(self):
        if self._current_page < self._total_pages:
            self.set_current_page(self._current_page + 1)