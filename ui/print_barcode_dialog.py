from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QSizeF, QMarginsF
from PyQt6.QtGui import QPainter, QFont, QPixmap
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import barcode
from barcode.writer import ImageWriter
import tempfile
import os
from utils.translations import tr


class PrintBarcodeDialog(QDialog):
    def __init__(self, product_id, product_name, barcode_number, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.product_name = product_name
        self.barcode_number = barcode_number
        self.setWindowTitle(tr("print_barcode_title") + f" - {product_name}")
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout()

        # Info label
        info = QLabel(f"{tr('product')}: {product_name}\n{tr('barcode')}: {barcode_number}")
        layout.addWidget(info)

        # Quantity
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel(tr("quantity") + ":"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 100)
        self.qty_spin.setValue(1)
        qty_layout.addWidget(self.qty_spin)
        layout.addLayout(qty_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_preview = QPushButton(tr("preview"))
        self.btn_preview.clicked.connect(self.preview_barcode)
        self.btn_print = QPushButton(tr("print"))
        self.btn_print.clicked.connect(self.print_barcode)
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_print)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def generate_barcode_image(self, barcode_number):
        """Generate a Code128 barcode image as QPixmap."""
        try:
            # Use Code128 (supports any length, alphanumeric)
            bc = barcode.get('code128', barcode_number, writer=ImageWriter())
            # Write to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                bc.write(tmp.name)
                tmp_path = tmp.name
            pixmap = QPixmap(tmp_path)
            os.unlink(tmp_path)
            return pixmap
        except Exception as e:
            QMessageBox.warning(self, tr("error"), f"{tr('barcode_generate_error')}: {e}")
            return None

    def preview_barcode(self):
        pixmap = self.generate_barcode_image(self.barcode_number)
        if pixmap:
            dialog = QDialog(self)
            dialog.setWindowTitle(tr("preview"))
            layout = QVBoxLayout()
            label = QLabel()
            label.setPixmap(pixmap.scaled(400, 100, Qt.AspectRatioMode.KeepAspectRatio))
            layout.addWidget(label)
            btn_close = QPushButton(tr("close"))
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            dialog.setLayout(layout)
            dialog.exec()

    def print_barcode(self):
        quantity = self.qty_spin.value()
        pixmap = self.generate_barcode_image(self.barcode_number)
        if not pixmap:
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        # Label size: 50mm x 30mm (adjust as needed)
        try:
            label_width = 50  # mm
            label_height = 30  # mm
            page_size = QPageSize(QSizeF(label_width, label_height), QPageSize.Unit.Millimeter)
            layout = QPageLayout()
            layout.setPageSize(page_size)
            layout.setOrientation(QPageLayout.Orientation.Portrait)
            layout.setMargins(QMarginsF(2, 2, 2, 2))
            printer.setPageLayout(layout)
        except:
            pass

        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, tr("error"), tr("printer_error"))
            return

        page_rect = printer.pageRect()
        available_width = page_rect.width()
        available_height = page_rect.height()

        # Scale barcode
        barcode_width = available_width - 20
        barcode_height = int(barcode_width * pixmap.height() / pixmap.width())
        if barcode_height > available_height - 40:
            barcode_height = available_height - 40
            barcode_width = int(barcode_height * pixmap.width() / pixmap.height())

        font = QFont("Arial", 10)
        painter.setFont(font)
        fm = painter.fontMetrics()

        for i in range(quantity):
            if i > 0:
                printer.newPage()
            name_y = 10
            painter.drawText(10, name_y, self.product_name[:30])
            barcode_y = name_y + fm.height() + 5
            painter.drawPixmap(10, barcode_y, barcode_width, barcode_height, pixmap)
            num_y = barcode_y + barcode_height + 5
            painter.drawText(10, num_y, self.barcode_number)

        painter.end()
        QMessageBox.information(self, tr("print"), tr("barcode_print_success").format(quantity))