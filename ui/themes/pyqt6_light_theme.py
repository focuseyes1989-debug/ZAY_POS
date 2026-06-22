# ui/themes/pyqt6_light_theme.py
PYQT6_LIGHT_THEME = """
/* ========== GLOBAL ========== */
* {
    font-family: "Segoe UI", "Noto Sans Myanmar", sans-serif;
    font-size: 9pt;
}

QWidget {
    background-color: #f0f0f0;
    color: #000000;
}

QMainWindow {
    background-color: #f0f0f0;
}

/* ========== MENU BAR ========== */
QMenuBar {
    background-color: #e0e0e0;
    color: #000000;
    padding: 2px 4px;
}
QMenuBar::item {
    background-color: transparent;
    padding: 4px 8px;
}
QMenuBar::item:selected {
    background-color: #d0d0d0;
}

/* ========== MENU POPUP ========== */
QMenu {
    background-color: #e0e0e0;
    border: 1px solid #c0c0c0;
    padding: 2px;
}
QMenu::item {
    background-color: transparent;
    padding: 4px 20px;
    color: #000000;
}
QMenu::item:selected {
    background-color: #d0d0d0;
}
QMenu::separator {
    height: 1px;
    background-color: #c0c0c0;
    margin: 2px 4px;
}

/* ========== DASHBOARD CARDS ========== */
#dashboardCard {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 8px;
}
#dashboardCard:hover {
    background-color: #f5f5f5;
}
#cardTitle {
    color: #6c6c6c;
    font-size: 9pt;
}
#cardValue {
    color: #000000;
    font-size: 16pt;
    font-weight: bold;
}

/* ========== NAVIGATOR BAR BUTTONS ========== */
#navBar QPushButton {
    background-color: transparent;
    color: #6c6c6c;
    border: none;
    padding: 6px 12px;
    min-width: 60px;
}
#navBar QPushButton:hover {
    background-color: #e0e0e0;
    color: #000000;
}
#navBar QPushButton:checked {
    background-color: #e0e0e0;
    color: #000000;
    border-bottom: 2px solid #6c6c6c;
}

/* ========== BUTTONS ========== */
QPushButton {
    background-color: #e0e0e0;
    color: #000000;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 4px 10px;
    min-width: 60px;
}
QPushButton:hover {
    background-color: #d0d0d0;
}
QPushButton:pressed {
    background-color: #c0c0c0;
}
QPushButton:checked {
    background-color: #d0d0d0;
    border: 1px solid #b0b0b0;
}

QTableWidget QPushButton, QDialog QPushButton {
    background-color: #e0e0e0;
    color: #000000;
    border: 1px solid #c0c0c0;
    border-radius: 3px;
    padding: 2px 6px;
}
QTableWidget QPushButton:hover, QDialog QPushButton:hover {
    background-color: #d0d0d0;
}

/* ========== TABLES ========== */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f5f5f5;
    selection-background-color: #d0d0d0;
    selection-color: #000000;
    gridline-color: #c0c0c0;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
}
QHeaderView::section {
    background-color: #e8e8e8;
    padding: 4px;
    border: none;
    font-weight: bold;
    color: #4a4a4a;
}
QTableWidget::item {
    padding: 4px;
}

/* ========== INPUT FIELDS ========== */
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 4px 6px;
    color: #000000;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #a0a0a0;
}
QLineEdit::placeholder {
    color: #8f8f8f;
}

/* ========== SPIN BOX ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 3px 18px 3px 6px;
    color: #000000;
    min-height: 24px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #e8e8e8;
    width: 16px;
    border: 1px solid #c0c0c0;
    border-radius: 2px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #d0d0d0;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid #4a4a4a;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #4a4a4a;
}

/* ========== COMBOBOX POPUP ========== */
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    selection-background-color: #d0d0d0;
    selection-color: #000000;
    color: #000000;
}
QComboBox::drop-down {
    border: none;
    width: 18px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #4a4a4a;
    margin-right: 4px;
}

/* ========== TABS ========== */
QTabWidget::pane {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #e8e8e8;
    padding: 6px 12px;
    margin-right: 2px;
    border: 1px solid #c0c0c0;
    border-bottom: none;
    color: #4a4a4a;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom: 1px solid #ffffff;
    color: #000000;
}
QTabBar::tab:hover:!selected {
    background-color: #d8d8d8;
}

/* ========== GROUP BOX ========== */
QGroupBox {
    font-weight: bold;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    background-color: #f0f0f0;
    color: #4a4a4a;
}

/* ========== LABELS ========== */
QLabel {
    background-color: transparent;
    color: #000000;
}

/* ========== STATUS BAR ========== */
QStatusBar {
    background-color: #e8e8e8;
    color: #4a4a4a;
    border-top: 1px solid #c0c0c0;
}

/* ========== SCROLL BARS ========== */
QScrollBar:vertical {
    background: #e8e8e8;
    width: 14px;
    border: 1px solid #c0c0c0;
}
QScrollBar::handle:vertical {
    background: #c0c0c0;
    border: 1px solid #b0b0b0;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #b0b0b0;
}
QScrollBar:horizontal {
    background: #e8e8e8;
    height: 14px;
    border: 1px solid #c0c0c0;
}
QScrollBar::handle:horizontal {
    background: #c0c0c0;
    border: 1px solid #b0b0b0;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #b0b0b0;
}

/* ========== DIALOGS ========== */
QDialog {
    background-color: #f0f0f0;
}
QMessageBox {
    background-color: #f0f0f0;
}
QMessageBox QLabel {
    color: #000000;
}
QMessageBox QPushButton {
    min-width: 60px;
    padding: 4px 10px;
}

/* ========== CHECKBOX & RADIO ========== */
QCheckBox, QRadioButton {
    spacing: 6px;
    color: #000000;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QCheckBox::indicator:unchecked {
    background-color: #ffffff;
    border: 1px solid #b0b0b0;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #ffffff;
    border: 1px solid #b0b0b0;
    border-radius: 3px;
}
QRadioButton::indicator:unchecked {
    background-color: #ffffff;
    border: 1px solid #b0b0b0;
    border-radius: 8px;
}
QRadioButton::indicator:checked {
    background-color: #ffffff;
    border: 1px solid #b0b0b0;
    border-radius: 8px;
}

/* ========== DATE EDIT CALENDAR ========== */
QDateEdit QCalendarWidget {
    background-color: #ffffff;
}
QCalendarWidget QTableView {
    background-color: #ffffff;
}
QCalendarWidget QHeaderView::section {
    background-color: #e8e8e8;
}
QCalendarWidget QToolButton {
    background-color: #e0e0e0;
    border: 1px solid #c0c0c0;
    border-radius: 3px;
    padding: 2px;
}

/* ========== TABLE WIDGET SPINBOX ========== */
QTableWidget QSpinBox {
    width: 60px;
    min-width: 60px;
    max-width: 60px;
}

/* ========== PRODUCT IMAGES IN TABLE ========== */
QTableWidget QLabel {
    max-width: 60px;
    max-height: 57px;
    min-width: 60px;
    min-height: 57px;
    border: none;
    background-color: transparent;
}
"""