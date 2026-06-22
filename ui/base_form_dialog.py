import os
from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QCheckBox, QDialogButtonBox, QLabel
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon

class BaseFormDialog(QDialog):
    def __init__(self, title, fields, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.fields = fields
        self.inputs = {}
        self.data = data or {}
        self.layout = QFormLayout()
        self.create_fields()
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)
        self.setLayout(self.layout)
        self.setMinimumWidth(400)
        self.populate_from_data()

    def create_fields(self):
        for field in self.fields:
            name = field['name']
            label = field['label']
            ftype = field.get('type', 'line')
            if ftype == 'line':
                widget = QLineEdit()
            elif ftype == 'text':
                widget = QTextEdit()
                widget.setMaximumHeight(80)
            elif ftype == 'combo':
                widget = QComboBox()
                if 'items' in field:
                    widget.addItems(field['items'])
            elif ftype == 'spin':
                widget = QSpinBox()
                if 'range' in field:
                    widget.setRange(field['range'][0], field['range'][1])
            elif ftype == 'double':
                widget = QDoubleSpinBox()
                if 'range' in field:
                    widget.setRange(field['range'][0], field['range'][1])
                if 'decimals' in field:
                    widget.setDecimals(field['decimals'])
            elif ftype == 'date':
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                if 'default' in field:
                    widget.setDate(field['default'])
            elif ftype == 'checkbox':
                widget = QCheckBox()
            else:
                widget = QLineEdit()
            if field.get('readonly', False):
                widget.setReadOnly(True)
            self.inputs[name] = widget
            if ftype != 'checkbox':
                self.layout.addRow(QLabel(label), widget)
            else:
                self.layout.addRow(widget)

    def populate_from_data(self):
        for name, widget in self.inputs.items():
            if name in self.data:
                value = self.data[name]
                if value is None:
                    continue
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QTextEdit):
                    widget.setPlainText(str(value))
                elif isinstance(widget, QComboBox):
                    idx = widget.findText(str(value))
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(value))
                elif isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(value))
                elif isinstance(widget, QDateEdit):
                    if value:
                        widget.setDate(QDate.fromString(value, "yyyy-MM-dd"))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))

    def get_data(self):
        result = {}
        for name, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                result[name] = widget.text().strip()
            elif isinstance(widget, QTextEdit):
                result[name] = widget.toPlainText().strip()
            elif isinstance(widget, QComboBox):
                result[name] = widget.currentText()
            elif isinstance(widget, QSpinBox):
                result[name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                result[name] = widget.value()
            elif isinstance(widget, QDateEdit):
                result[name] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QCheckBox):
                result[name] = widget.isChecked()
            else:
                result[name] = widget.text()
        return result