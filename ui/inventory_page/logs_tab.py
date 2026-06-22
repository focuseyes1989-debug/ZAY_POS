from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from models.database import connect_db
from ui.widgets.pagination_widget import PaginationWidget
from datetime import datetime
import csv


class LogsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.btn_export_pdf = QPushButton("Export PDF")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        self.btn_export_excel = QPushButton("Export Excel")
        self.btn_export_excel.clicked.connect(self.export_excel)
        
        # New export button for stock movement
        self.btn_export_movement = QPushButton("📊 Export Stock Movement")
        self.btn_export_movement.clicked.connect(self.export_stock_movement)
        
        btn_layout.addWidget(self.btn_export_pdf)
        btn_layout.addWidget(self.btn_export_excel)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_export_movement)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)
        layout.addWidget(self.pagination)

        self.setLayout(layout)

    def get_lang(self):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='language'")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "en"
        except:
            return "en"

    def on_page_changed(self, page: int, page_size: int):
        self.load_data(page, page_size)

    def refresh(self):
        self.load_data()

    def load_data(self, page=1, page_size=50):
        lang = self.get_lang()
        if lang == "my":
            headers = [
                "မှတ်တမ်း ID", "ပစ္စည်းအမည်", "ပေးသွင်းသူ", "လုပ်ဆောင်ချက်", "မပြောင်းမီပမာဏ",
                "ပြောင်းပြီးပမာဏ", "ပြောင်းလဲပမာဏ", "ကိုးကားအမှတ်", "အသုံးပြုသူ", "ရက်စွဲနှင့်အချိန်", "မှတ်ချက်"
            ]
        else:
            headers = [
                "Log ID", "Product Name", "Supplier", "Action Type", "Quantity Before",
                "Quantity After", "Changed Qty", "Reference No", "User", "Date Time", "Notes"
            ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setColumnHidden(0, True)

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stock_movements")
        total_items = cursor.fetchone()[0]
        self.pagination.set_total_items(total_items, emit_signal=False)

        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT sm.id, p.name, sup.name, sm.type, sm.old_stock, sm.new_stock, 
                   sm.quantity, sm.reference, sm.created_by, sm.created_at, sm.notes
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
            LEFT JOIN suppliers sup ON sm.supplier_id = sup.id
            ORDER BY sm.created_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value is not None else "")
                self.table.setItem(row_idx, col_idx, item)

    def get_all_movement_data(self):
        """Get all stock movement data for export"""
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sm.id, p.name, sup.name, sm.type, sm.old_stock, sm.new_stock, 
                   sm.quantity, sm.reference, sm.created_by, sm.created_at, sm.notes,
                   sm.reason
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
            LEFT JOIN suppliers sup ON sm.supplier_id = sup.id
            ORDER BY sm.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def export_stock_movement(self):
        """Export stock movement report to CSV"""
        lang = self.get_lang()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Stock Movement" if lang != "my" else "စတော့လှုပ်ရှားမှုမှတ်တမ်း ထုတ်ရန်", 
            f"stock_movement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            "CSV Files (*.csv)"
        )
        if not file_path:
            return
        
        try:
            rows = self.get_all_movement_data()
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(["=" * 90])
                writer.writerow(["STOCK MOVEMENT REPORT"] if lang != "my" else ["စတော့လှုပ်ရှားမှု အစီရင်ခံစာ"])
                writer.writerow(["=" * 90])
                writer.writerow([])
                writer.writerow(["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(["Total Movements:", len(rows)])
                writer.writerow([])
                
                # Column Headers
                if lang == "my":
                    writer.writerow(["ပစ္စည်းအမည်", "ပေးသွင်းသူ", "လုပ်ဆောင်ချက်", "မပြောင်းမီပမာဏ",
                                   "ပြောင်းပြီးပမာဏ", "ပြောင်းလဲပမာဏ", "ကိုးကားအမှတ်", 
                                   "အသုံးပြုသူ", "ရက်စွဲနှင့်အချိန်", "အကြောင်းပြချက်", "မှတ်ချက်"])
                else:
                    writer.writerow(["Product Name", "Supplier", "Action Type", "Quantity Before",
                                   "Quantity After", "Changed Qty", "Reference No", 
                                   "User", "Date Time", "Reason", "Notes"])
                writer.writerow(["-" * 90])
                
                stock_in_count = 0
                stock_out_count = 0
                adjustment_count = 0
                
                for row in rows:
                    pid, name, supplier, action, old_stock, new_stock, qty, ref_no, user, created_at, notes, reason = row
                    
                    writer.writerow([
                        name or "",
                        supplier or "",
                        action or "",
                        old_stock if old_stock is not None else "",
                        new_stock if new_stock is not None else "",
                        qty if qty is not None else "",
                        ref_no or "",
                        user or "",
                        created_at[:19] if created_at else "",
                        reason or "",
                        notes or ""
                    ])
                    
                    if action == "in":
                        stock_in_count += 1
                    elif action == "out":
                        stock_out_count += 1
                    else:
                        adjustment_count += 1
                
                writer.writerow([])
                writer.writerow(["=" * 90])
                writer.writerow(["SUMMARY"])
                writer.writerow(["-" * 50])
                writer.writerow(["Stock In Movements:", stock_in_count])
                writer.writerow(["Stock Out Movements:", stock_out_count])
                writer.writerow(["Adjustments:", adjustment_count])
                writer.writerow(["Total Movements:", len(rows)])
                writer.writerow(["=" * 90])
                writer.writerow(["End of Report"])
            
            msg = f"Stock movement report exported successfully to:\n{file_path}" if lang != "my" else f"စတော့လှုပ်ရှားမှုမှတ်တမ်း အောင်မြင်စွာ ထုတ်ယူပြီးပါပြီ:\n{file_path}"
            QMessageBox.information(self, "Export Complete", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")

    def get_all_data(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sm.id, p.name, sup.name, sm.type, sm.old_stock, sm.new_stock, 
                   sm.quantity, sm.reference, sm.created_by, sm.created_at, sm.notes
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
            LEFT JOIN suppliers sup ON sm.supplier_id = sup.id
            ORDER BY sm.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def export_pdf(self):
        # Keep existing PDF export method
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter, QFont, QFontMetrics, QPageLayout, QPageSize
        rows = self.get_all_data()
        if not rows:
            QMessageBox.information(self, "No Data", "No stock movement records to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", "stock_movement_report.pdf", "PDF Files (*.pdf)")
        if not file_path:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Error", "Could not start PDF generation.")
            return
        font = QFont("Arial", 8)
        painter.setFont(font)
        fm = QFontMetrics(font)
        headers = ["ID", "Product", "Supplier", "Type", "Old Stock", "New Stock", "Qty Changed", "Reference", "User", "Date Time", "Notes"]
        col_widths = [40, 120, 100, 80, 80, 80, 80, 100, 100, 140, 150]
        y = 20
        x = 20
        row_height = fm.height() + 6
        for i, header in enumerate(headers):
            painter.drawText(x, y, col_widths[i], row_height, Qt.AlignmentFlag.AlignLeft, header)
            x += col_widths[i]
        y += row_height
        x = 20
        for row in rows:
            if y + row_height > printer.height() - 50:
                printer.newPage()
                y = 20
            painter.drawText(x, y, col_widths[0], row_height, Qt.AlignmentFlag.AlignLeft, str(row[0]))
            painter.drawText(x + col_widths[0], y, col_widths[1], row_height, Qt.AlignmentFlag.AlignLeft, str(row[1] or ""))
            painter.drawText(x + col_widths[0] + col_widths[1], y, col_widths[2], row_height, Qt.AlignmentFlag.AlignLeft, str(row[2] or ""))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2], y, col_widths[3], row_height, Qt.AlignmentFlag.AlignLeft, str(row[3] or ""))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], y, col_widths[4], row_height, Qt.AlignmentFlag.AlignLeft, str(row[4] or ""))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4], y, col_widths[5], row_height, Qt.AlignmentFlag.AlignLeft, str(row[5] or ""))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4] + col_widths[5], y, col_widths[6], row_height, Qt.AlignmentFlag.AlignLeft, str(row[6] or ""))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4] + col_widths[5] + col_widths[6], y, col_widths[7], row_height, Qt.AlignmentFlag.AlignLeft, str(row[7] or ""))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4] + col_widths[5] + col_widths[6] + col_widths[7], y, col_widths[8], row_height, Qt.AlignmentFlag.AlignLeft, str(row[8] or ""))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4] + col_widths[5] + col_widths[6] + col_widths[7] + col_widths[8], y, col_widths[9], row_height, Qt.AlignmentFlag.AlignLeft, str(row[9] or ""))
            painter.drawText(x + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4] + col_widths[5] + col_widths[6] + col_widths[7] + col_widths[8] + col_widths[9], y, col_widths[10], row_height, Qt.AlignmentFlag.AlignLeft, str(row[10] or ""))
            y += row_height
            x = 20
        painter.end()
        QMessageBox.information(self, "Export Complete", f"PDF saved to:\n{file_path}")

    def export_excel(self):
        # Keep existing Excel/CSV export method
        rows = self.get_all_data()
        if not rows:
            QMessageBox.information(self, "No Data", "No stock movement records to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel Report", "stock_movement_report.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Product", "Supplier", "Type", "Old Stock", "New Stock", "Qty Changed", "Reference", "User", "Date Time", "Notes"])
                for row in rows:
                    writer.writerow([str(r) for r in row])
            QMessageBox.information(self, "Export Complete", f"CSV saved to:\n{file_path}\n\nYou can open this file in Excel.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")