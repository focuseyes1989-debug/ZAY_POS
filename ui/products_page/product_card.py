# ui/products_page/product_card.py
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal, QDate
from utils.currency import get_currency_symbol, format_money
from models.database import connect_db
from loguru import logger


class ClickableCard(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class ProductCards(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = {}
        self.card_frames = {}
        self.setup_cards()

    def setup_cards(self):
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        card_definitions = [
            ("Total Cost", "total_cost"),
            ("Out of Stock", "out_stock"),
            ("Low Stock", "low_stock"),
            ("Expiring ≤7 Days", "expiring_soon"),
            ("Expired", "expired")
        ]

        for title, key in card_definitions:
            card = ClickableCard()
            card.setObjectName("dashboardCard")
            card_layout = QVBoxLayout()
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            value_label = QLabel("0")
            value_label.setObjectName("cardValue")
            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)
            card.setLayout(card_layout)
            card.title_label = title_label
            self.card_frames[key] = card
            self.cards[key] = value_label
            layout.addWidget(card, 1)
            card.clicked.connect(lambda k=key: self.on_card_clicked(k))

        self.setLayout(layout)

    def on_card_clicked(self, key):
        parent = self.parent()
        if parent and hasattr(parent, 'on_card_filter'):
            parent.on_card_filter(key)
        
        # If Total Cost card is clicked, show category cost dialog
        if key == "total_cost":
            from ui.products_page.category_cost_dialog import CategoryCostDialog
            dialog = CategoryCostDialog(parent)
            dialog.exec()

    def update_cards(self):
        symbol = get_currency_symbol()
        conn = connect_db()
        cursor = conn.cursor()

        try:
            # Debug: Show all products with cost and stock
            cursor.execute("SELECT id, name, cost, stock, sold_by FROM products")
            all_products = cursor.fetchall()
            logger.debug("=== All Products for Total Cost ===")
            total_cost_sum = 0
            for p in all_products:
                cost_val = p[2] if p[2] is not None else 0
                stock_val = p[3] if p[3] is not None else 0
                sold_by = p[4] if p[4] else "Each"
                if sold_by != "Service":
                    product_total = cost_val * stock_val
                    total_cost_sum += product_total
                    logger.debug(f"Product: {p[1]}, Cost: {cost_val}, Stock: {stock_val}, Total: {product_total}")
            
            logger.debug(f"Total Cost calculated: {total_cost_sum}")
            self.cards["total_cost"].setText(format_money(total_cost_sum, symbol))

            # Out of Stock
            cursor.execute("SELECT COUNT(*) FROM products WHERE (sold_by IS NULL OR sold_by != 'Service') AND COALESCE(stock, 0) = 0")
            self.cards["out_stock"].setText(str(cursor.fetchone()[0]))

            # Low Stock (stock > 0 and stock <= low_stock)
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE (sold_by IS NULL OR sold_by != 'Service') 
                  AND COALESCE(stock, 0) > 0 
                  AND COALESCE(stock, 0) <= COALESCE(low_stock, 0)
            """)
            self.cards["low_stock"].setText(str(cursor.fetchone()[0]))

            # Expiring Soon (7 days)
            today = QDate.currentDate()
            today_str = today.toString("yyyy-MM-dd")
            week_later_str = today.addDays(7).toString("yyyy-MM-dd")
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE expire_date IS NOT NULL 
                  AND expire_date >= ? AND expire_date <= ?
            """, (today_str, week_later_str))
            self.cards["expiring_soon"].setText(str(cursor.fetchone()[0]))

            # Expired
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE expire_date IS NOT NULL AND expire_date < ?
            """, (today_str,))
            self.cards["expired"].setText(str(cursor.fetchone()[0]))

        except Exception as e:
            logger.error(f"Error updating cards: {e}")
        finally:
            conn.close()

    def retranslateUi(self):
        translations = {
            "total_cost": ("စုစုပေါင်းကုန်ကျငွေ", "Total Cost"),
            "out_stock": ("ကုန်သွားပြီ", "Out of Stock"),
            "low_stock": ("စတော့နည်းနေပြီ", "Low Stock"),
            "expiring_soon": ("၇ ရက်အတွင်းသက်တမ်းကုန်မည်", "Expiring ≤7 Days"),
            "expired": ("သက်တမ်းကုန်သွားပြီ", "Expired")
        }
        from utils.language import lang
        lang_code = lang.get_current()
        for key, (my_text, en_text) in translations.items():
            if key in self.card_frames:
                self.card_frames[key].title_label.setText(my_text if lang_code == "my" else en_text)