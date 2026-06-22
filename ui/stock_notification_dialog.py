# stock_notification_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFontMetrics
from models.database import connect_db
from utils.language import lang


class StockNotificationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stock Alerts")
        self.setMinimumSize(800, 400)
        self.setModal(False)

        layout = QVBoxLayout()
        self.label = QLabel()
        layout.addWidget(self.label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Product", "SKU", "Current Stock", "Low Stock Level", "Status", "Suggested Order"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column stretch modes for responsiveness
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable word wrap for product name column
        self.table.setWordWrap(True)
        
        # Set row height to adjust for wrapped text
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        
        layout.addWidget(self.table)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        self.load_data()
        
        # Connect resize event to adjust column width
        self.table.horizontalHeader().sectionResized.connect(self.on_column_resized)
        
        # Use timer to handle initial resize
        QTimer.singleShot(100, self.adjust_product_column)

    def adjust_product_column(self):
        """Adjust product column to show full product names"""
        header = self.table.horizontalHeader()
        
        # Get available width for product column
        total_width = self.table.viewport().width()
        fixed_width = 0
        
        # Calculate fixed columns width
        for col in range(1, self.table.columnCount()):
            if header.sectionResizeMode(col) == QHeaderView.ResizeMode.ResizeToContents:
                fixed_width += header.sectionSize(col)
            else:
                fixed_width += header.sectionSize(col)
        
        # Set product column to take remaining space
        product_width = total_width - fixed_width - 20  # Subtract padding
        if product_width > 100:  # Minimum width
            header.resizeSection(0, product_width)
        
        # Update row heights for wrapped text
        self.adjust_row_heights()

    def adjust_row_heights(self):
        """Adjust row heights based on content"""
        font_metrics = QFontMetrics(self.table.font())
        product_col_width = self.table.horizontalHeader().sectionSize(0) - 10  # Subtract padding
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                text = item.text()
                # Calculate required height for wrapped text
                lines = font_metrics.boundingRect(0, 0, product_col_width, 0, 
                                                   Qt.TextFlag.TextWordWrap, text)
                required_height = lines.height() + 20  # Add padding
                current_height = self.table.verticalHeader().sectionSize(row)
                if required_height > current_height:
                    self.table.verticalHeader().resizeSection(row, required_height)
                elif required_height < current_height and required_height > 20:
                    self.table.verticalHeader().resizeSection(row, required_height)

    def on_column_resized(self, index, old_size, new_size):
        """Handle column resize events"""
        if index == 0:  # Product column
            self.adjust_row_heights()

    def resizeEvent(self, event):
        """Handle dialog resize event"""
        super().resizeEvent(event)
        self.adjust_product_column()

    def showEvent(self, event):
        """Handle dialog show event"""
        super().showEvent(event)
        QTimer.singleShot(50, self.adjust_product_column)

    def load_data(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, sku, stock, low_stock, sold_by,
                   CASE 
                       WHEN stock = 0 THEN 'Out of Stock'
                       WHEN stock <= low_stock THEN 'Low Stock'
                       ELSE 'OK'
                   END as status,
                   (low_stock * 2) as suggested
            FROM products
            WHERE (sold_by IS NULL OR sold_by != 'Service')
              AND (stock = 0 OR stock <= low_stock)
            ORDER BY stock ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        
        lang_code = lang.get_current()
        
        for row_idx, row in enumerate(rows):
            name, sku, stock, low_stock, sold_by, status, suggested = row
            
            # Product name with word wrap
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 0, name_item)
            
            # SKU
            sku_item = QTableWidgetItem(sku or "")
            sku_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 1, sku_item)
            
            # Stock
            stock_item = QTableWidgetItem(str(stock))
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 2, stock_item)
            
            # Low Stock Level
            low_item = QTableWidgetItem(str(low_stock))
            low_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 3, low_item)
            
            # Status
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            
            # Color code status
            if status == "Out of Stock":
                status_item.setBackground(Qt.GlobalColor.red)
                status_item.setForeground(Qt.GlobalColor.white)
            elif status == "Low Stock":
                status_item.setBackground(Qt.GlobalColor.yellow)
                status_item.setForeground(Qt.GlobalColor.black)
            else:
                status_item.setBackground(Qt.GlobalColor.green)
                status_item.setForeground(Qt.GlobalColor.white)
            
            self.table.setItem(row_idx, 4, status_item)
            
            # Suggested Order
            suggested_item = QTableWidgetItem(str(suggested))
            suggested_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 5, suggested_item)

        # Set headers based on language
        if lang_code == "my":
            self.label.setText(f"စတော့သတိပေးချက် - ပစ္စည်း {len(rows)} မျိုး")
            self.table.setHorizontalHeaderLabels([
                "ပစ္စည်းအမည်", "SKU", "လက်ကျန်", 
                "သတိပေးပမာဏ", "အခြေအနေ", "ပြန်မှာသင့်ပမာဏ"
            ])
        else:
            self.label.setText(f"Stock Alerts – {len(rows)} product(s)")
            self.table.setHorizontalHeaderLabels([
                "Product", "SKU", "Current Stock", 
                "Low Stock Level", "Status", "Suggested Order"
            ])
        
        # Apply alternating row colors
        self.table.setAlternatingRowColors(True)
        
        # Adjust product column after loading data
        QTimer.singleShot(50, self.adjust_product_column)