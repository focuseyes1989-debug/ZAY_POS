# ui/dashboard/dashboard_cards.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from utils.currency import format_money


class ClickableCard(QFrame):
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class DashboardCards:
    """Handle dashboard card creation and management"""
    
    @staticmethod
    def create_card(title, value_text):
        card = QFrame()
        card.setObjectName("dashboardCard")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label = QLabel(value_text)
        value_label.setObjectName("cardValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        card.title_label = title_label
        card.value_label = value_label
        return card

    @staticmethod
    def create_clickable_card(title, value_text):
        card = ClickableCard()
        card.setObjectName("dashboardCard")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label = QLabel(value_text)
        value_label.setObjectName("cardValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        card.title_label = title_label
        card.value_label = value_label
        return card

    @staticmethod
    def update_card(card, value, symbol=None):
        if card and hasattr(card, 'value_label'):
            if symbol:
                card.value_label.setText(format_money(value, symbol))
            else:
                card.value_label.setText(str(value) if isinstance(value, int) else format_money(value))
    
    @staticmethod
    def update_stock_card(card, value):
        if card and hasattr(card, 'value_label'):
            card.value_label.setText(str(value))


class BackupStatusCard:
    """Create backup status card for dashboard"""
    
    @staticmethod
    def create(parent):
        card = QFrame()
        card.setObjectName("dashboardCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        icon_label = QLabel("✅")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 24pt;")
        
        title_label = QLabel("Database Backup")
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        status_label = QLabel("Last Backup: Checking...")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("font-size: 10pt;")
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        
        # Store references
        card.icon_label = icon_label
        card.title_label = title_label
        card.status_label = status_label
        
        return card