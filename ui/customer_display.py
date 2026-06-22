# ui/customer_display.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QScreen, QMouseEvent
from PyQt6.QtWidgets import QApplication
from utils.currency import get_currency_symbol, format_money
from utils.language import lang


class TitleBar(QWidget):
    """Custom title bar for the customer display window"""
    
    close_clicked = pyqtSignal()
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_maximized = False
        self.dragging = False
        self.drag_position = QPoint()
        
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: white;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 5px 10px;
                font-size: 14pt;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2a2a4e;
            }
            QPushButton#close_btn:hover {
                background-color: #e94560;
            }
            QPushButton#maximize_btn:hover {
                background-color: #2a2a4e;
            }
            QPushButton#minimize_btn:hover {
                background-color: #2a2a4e;
            }
            QLabel {
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding-left: 10px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)
        
        # Title
        self.title_label = QLabel("🛒 Customer Display")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Minimize button
        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setObjectName("minimize_btn")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.minimize_btn)
        
        # Maximize button
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setObjectName("maximize_btn")
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.maximize_btn)
        
        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
    
    def toggle_maximize(self):
        """Toggle maximize state"""
        self.is_maximized = not self.is_maximized
        self.maximize_btn.setText("□" if not self.is_maximized else "❐")
        self.maximize_clicked.emit()
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.dragging and not self.is_maximized:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
    
    def retranslateUi(self):
        """Update translations"""
        lang_code = lang.get_current()
        if lang_code == "my":
            self.title_label.setText("🛒 ဝယ်ယူသူမျက်နှာပြင်")
        else:
            self.title_label.setText("🛒 Customer Display")


class CustomerDisplayWindow(QWidget):
    """Customer display window showing cart items and totals"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_maximized = False
        
        # Remove default title bar and set window flags
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.FramelessWindowHint
        )
        
        self.setMinimumSize(600, 400)
        
        # Set dark theme for customer display
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #16213e;
                color: #ffffff;
                gridline-color: #2a3a5e;
                border: none;
                font-size: 14pt;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #0f3460;
            }
            QHeaderView::section {
                background-color: #0f3460;
                color: #ffffff;
                padding: 8px;
                border: none;
                font-size: 14pt;
                font-weight: bold;
            }
            QLabel {
                color: #ffffff;
                font-size: 16pt;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Custom title bar
        self.title_bar = TitleBar(self)
        self.title_bar.close_clicked.connect(self.close_display)
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self.toggle_maximize)
        layout.addWidget(self.title_bar)
        
        # Content area
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
            }
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 20, 30, 30)

        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("🛒 Your Cart")
        self.title_label.setStyleSheet("font-size: 28pt; font-weight: bold; color: #e94560;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.customer_name_label = QLabel("")
        self.customer_name_label.setStyleSheet("font-size: 16pt; color: #4ecdc4;")
        header_layout.addWidget(self.customer_name_label)
        
        content_layout.addLayout(header_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #2a3a5e; max-height: 2px;")
        content_layout.addWidget(separator)

        # Cart Table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels(["Item", "Qty", "Price", "Total"])
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cart_table.setShowGrid(True)
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #1e2a4a;
            }
        """)
        
        header = self.cart_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Set row height
        self.cart_table.verticalHeader().setDefaultSectionSize(50)
        
        content_layout.addWidget(self.cart_table)

        # Totals
        totals_layout = QHBoxLayout()
        totals_layout.setSpacing(30)
        
        self.subtotal_label = QLabel("Subtotal: 0")
        self.subtotal_label.setStyleSheet("font-size: 18pt; color: #a8a8b8;")
        totals_layout.addWidget(self.subtotal_label)
        
        self.discount_label = QLabel("Discount: 0")
        self.discount_label.setStyleSheet("font-size: 18pt; color: #f9ca24;")
        totals_layout.addWidget(self.discount_label)
        
        totals_layout.addStretch()
        
        self.grand_total_label = QLabel("Grand Total: 0")
        self.grand_total_label.setStyleSheet("font-size: 28pt; font-weight: bold; color: #4ecdc4;")
        totals_layout.addWidget(self.grand_total_label)
        
        content_layout.addLayout(totals_layout)
        
        layout.addWidget(content_widget)
        self.setLayout(layout)
        
        # Set initial size and position
        self.set_default_geometry()
        
        # Set timer to auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(500)  # Refresh every 500ms
        
        # Retranslate
        self.retranslateUi()

    def set_default_geometry(self):
        """Set default window geometry"""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            width = int(geometry.width() * 0.6)
            height = int(geometry.height() * 0.6)
            x = (geometry.width() - width) // 2
            y = (geometry.height() - height) // 2
            self.setGeometry(x, y, width, height)

    def toggle_maximize(self):
        """Toggle maximize state"""
        self.is_maximized = not self.is_maximized
        if self.is_maximized:
            self.showMaximized()
        else:
            self.showNormal()
            self.set_default_geometry()

    def close_display(self):
        """Close the customer display window"""
        self.refresh_timer.stop()
        self.close()
        # Notify parent that display is closed
        if self.parent_window and hasattr(self.parent_window, 'customer_display_closed'):
            self.parent_window.customer_display_closed()

    def refresh_display(self):
        """Refresh the display with current cart data"""
        if not self.parent_window:
            return
        
        # Get cart from parent
        if hasattr(self.parent_window, 'cart_widget'):
            cart_items = self.parent_window.cart_widget.get_cart()
            self.update_display(cart_items)

    def update_display(self, cart_items):
        """Update the display with cart items"""
        symbol = get_currency_symbol()
        
        self.cart_table.setRowCount(0)
        
        subtotal = 0
        for item in cart_items:
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            
            name = item.get('name', '')
            qty = item.get('qty', 0)
            price = item.get('price', 0)
            total = price * qty
            
            self.cart_table.setItem(row, 0, QTableWidgetItem(name))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.cart_table.setItem(row, 2, QTableWidgetItem(format_money(price, symbol)))
            self.cart_table.setItem(row, 3, QTableWidgetItem(format_money(total, symbol)))
            
            subtotal += total
        
        # Update subtotal
        self.subtotal_label.setText(f"Subtotal: {format_money(subtotal, symbol)}")
        
        # Get discount and grand total from parent
        if hasattr(self.parent_window, 'totals_widget'):
            reg_discount = self.parent_window.totals_widget.compute_regular_discount(subtotal)
            points_discount = self.parent_window.totals_widget.compute_points_discount(subtotal)
            total_discount = reg_discount + points_discount
            after_discount = subtotal - total_discount
            
            # Calculate tax
            tax = 0
            if hasattr(self.parent_window, 'tax_enabled') and self.parent_window.tax_enabled:
                if hasattr(self.parent_window, 'tax_rate'):
                    tax = after_discount * (self.parent_window.tax_rate / 100.0)
            
            grand_total = after_discount + tax
            
            self.discount_label.setText(f"Discount: {format_money(total_discount, symbol)}")
            self.grand_total_label.setText(f"Grand Total: {format_money(grand_total, symbol)}")
            
            # Color grand total based on amount
            if grand_total > 0:
                self.grand_total_label.setStyleSheet("font-size: 28pt; font-weight: bold; color: #4ecdc4;")
            else:
                self.grand_total_label.setStyleSheet("font-size: 28pt; font-weight: bold; color: #a8a8b8;")
        
        # Update customer name if available
        if hasattr(self.parent_window, 'checkout_handler'):
            customer_id = self.parent_window.checkout_handler.selected_customer_id
            if customer_id:
                from models.database import connect_db
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM customers WHERE id = ?", (customer_id,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    self.customer_name_label.setText(f"👤 {row[0]}")
                else:
                    self.customer_name_label.setText("")
            else:
                self.customer_name_label.setText("")

    def showEvent(self, event):
        """When window is shown, position it on secondary monitor if available"""
        super().showEvent(event)
        self.move_to_secondary_monitor()

    def move_to_secondary_monitor(self):
        """Move window to secondary monitor if available"""
        app = QApplication.instance()
        screens = app.screens()
        
        if len(screens) > 1 and not self.is_maximized:
            # Move to secondary monitor (index 1)
            screen = screens[1]
            geometry = screen.geometry()
            width = int(geometry.width() * 0.6)
            height = int(geometry.height() * 0.6)
            x = geometry.x() + (geometry.width() - width) // 2
            y = geometry.y() + (geometry.height() - height) // 2
            self.setGeometry(x, y, width, height)

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.close_display()
        elif event.key() == Qt.Key.Key_F11:
            self.toggle_maximize()
        super().keyPressEvent(event)

    def retranslateUi(self):
        """Update translations"""
        lang_code = lang.get_current()
        if lang_code == "my":
            self.title_label.setText("🛒 ဈေးခြင်း")
            self.cart_table.setHorizontalHeaderLabels(["ပစ္စည်း", "အရေအတွက်", "စျေးနှုန်း", "စုစုပေါင်း"])
            self.subtotal_label.setText(f"ကြားဖြတ်စုစုပေါင်း: 0")
            self.discount_label.setText(f"လျှော့စျေး: 0")
            self.grand_total_label.setText(f"စုစုပေါင်း: 0")
        else:
            self.title_label.setText("🛒 Your Cart")
            self.cart_table.setHorizontalHeaderLabels(["Item", "Qty", "Price", "Total"])
            self.subtotal_label.setText(f"Subtotal: 0")
            self.discount_label.setText(f"Discount: 0")
            self.grand_total_label.setText(f"Grand Total: 0")
        
        # Update title bar
        if hasattr(self, 'title_bar'):
            self.title_bar.retranslateUi()