# ui/sales_page/payment_widget.py
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox
from PyQt6.QtCore import pyqtSignal, Qt
from utils.currency import get_currency_symbol, format_money


class PaymentWidget(QGroupBox):
    payment_amount_changed = pyqtSignal(float)
    checkout_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Payment")
        self.payment_manual_override = False
        self._programmatic_update = False
        self._grand_total = 0.0
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Payment Type
        pt_layout = QHBoxLayout()
        self.payment_type_label = QLabel("Type:")
        pt_layout.addWidget(self.payment_type_label)
        self.payment_combo = QComboBox()
        pt_layout.addWidget(self.payment_combo)
        layout.addLayout(pt_layout)

        # Received Amount
        amt_layout = QHBoxLayout()
        self.amt_label = QLabel("Received:")
        amt_layout.addWidget(self.amt_label)
        self.payment_input = QDoubleSpinBox()
        self.payment_input.setRange(0, 1000000)
        self.payment_input.setDecimals(0)
        self.payment_input.setFixedHeight(25)
        self.payment_input.setKeyboardTracking(False)  # Reduce signals while typing
        self.payment_input.valueChanged.connect(self.on_payment_changed)
        amt_layout.addWidget(self.payment_input)
        layout.addLayout(amt_layout)

        # Change Display
        chg_layout = QHBoxLayout()
        self.change_label_title = QLabel("Change:")
        chg_layout.addWidget(self.change_label_title)
        self.change_label = QLabel("0")
        chg_layout.addWidget(self.change_label)
        chg_layout.addStretch()
        layout.addLayout(chg_layout)

    def on_payment_changed(self, value):
        """Called when payment value changes (user or programmatic)"""
        if self._programmatic_update:
            return
        
        # User is manually changing the value
        self.payment_manual_override = True
        self.payment_amount_changed.emit(value)
        self.update_change()

    def auto_set_payment(self, grand_total):
        """Auto-set payment to grand total (only if not manually overridden)"""
        self._grand_total = grand_total
        
        if not self.payment_manual_override:
            self._programmatic_update = True
            self.payment_input.blockSignals(True)
            try:
                self.payment_input.setValue(grand_total)
            finally:
                self.payment_input.blockSignals(False)
            self._programmatic_update = False
            self.update_change()

    def update_change(self):
        """Update change display based on current payment and grand total"""
        # Get current grand total from totals widget
        if hasattr(self.parent(), 'totals_widget'):
            grand_total = self.parent().totals_widget.get_current_grand_total()
        else:
            grand_total = self._grand_total
            
        payment = self.payment_input.value()
        change = payment - grand_total
        symbol = get_currency_symbol()
        
        if change >= 0:
            self.change_label.setText(format_money(change, symbol))
            self.change_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.change_label.setText(f"-{format_money(abs(change), symbol)}")
            self.change_label.setStyleSheet("color: red; font-weight: bold;")

    def load_payment_types(self, types):
        self.payment_combo.blockSignals(True)
        self.payment_combo.clear()
        for name in types:
            self.payment_combo.addItem(name)
        # Always set "Cash" as default
        cash_idx = self.payment_combo.findText("Cash")
        if cash_idx >= 0:
            self.payment_combo.setCurrentIndex(cash_idx)
        else:
            self.payment_combo.setCurrentIndex(0)
        self.payment_combo.blockSignals(False)

    def get_selected_payment_type(self):
        return self.payment_combo.currentText()

    def get_payment_amount(self):
        return self.payment_input.value()

    def reset_manual_override(self):
        """Reset manual override flag after checkout"""
        self.payment_manual_override = False

    def set_payment_amount(self, amount):
        """Force set payment amount (used after manual override reset)"""
        self._programmatic_update = True
        self.payment_input.blockSignals(True)
        try:
            self.payment_input.setValue(amount)
        finally:
            self.payment_input.blockSignals(False)
        self._programmatic_update = False
        self.update_change()
    
    def reset_to_default(self):
        """Reset payment widget to default state"""
        # Reset payment type to Cash
        cash_idx = self.payment_combo.findText("Cash")
        if cash_idx >= 0:
            self.payment_combo.setCurrentIndex(cash_idx)
        
        # Reset payment amount to 0
        self._programmatic_update = True
        self.payment_input.blockSignals(True)
        try:
            self.payment_input.setValue(0)
        finally:
            self.payment_input.blockSignals(False)
        self._programmatic_update = False
        
        # Reset manual override
        self.payment_manual_override = False
        self._grand_total = 0.0
        
        # Update change display
        self.update_change()

    def retranslateUi(self):
        from utils.language import lang
        if lang.get_current() == "my":
            self.setTitle("ငွေပေးချေမှု")
            self.payment_type_label.setText("အမျိုးအစား:")
            self.amt_label.setText("လက်ခံငွေ:")
            self.change_label_title.setText("ပြန်အမ်းငွေ:")
        else:
            self.setTitle("Payment")
            self.payment_type_label.setText("Type:")
            self.amt_label.setText("Received:")
            self.change_label_title.setText("Change:")