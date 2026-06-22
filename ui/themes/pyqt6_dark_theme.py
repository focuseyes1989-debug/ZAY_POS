# ui/themes/pyqt6_dark_theme.py
PYQT6_DARK_THEME = """
/* ========== GLOBAL ========== */
* {
    font-family: "Segoe UI", "Noto Sans Myanmar", sans-serif;
    font-size: 9pt;
}

QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
}

QMainWindow {
    background-color: #2b2b2b;
}

/* ========== MENU BAR ========== */
QMenuBar {
    background-color: #3c3c3c;
    color: #ffffff;
    padding: 2px 4px;
}
QMenuBar::item {
    background-color: transparent;
    padding: 4px 8px;
}
QMenuBar::item:selected {
    background-color: #4a4a4a;
}

/* ========== MENU POPUP ========== */
QMenu {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    padding: 2px;
}
QMenu::item {
    background-color: transparent;
    padding: 4px 20px;
    color: #ffffff;
}
QMenu::item:selected {
    background-color: #4a4a4a;
}
QMenu::separator {
    height: 1px;
    background-color: #4a4a4a;
    margin: 2px 4px;
}

/* ========== DASHBOARD CARDS ========== */
#dashboardCard {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    padding: 8px;
}
#dashboardCard:hover {
    background-color: #4a4a4a;
}
#cardTitle {
    color: #8f8f8f;
    font-size: 9pt;
}
#cardValue {
    color: #ffffff;
    font-size: 16pt;
    font-weight: bold;
}

/* ========== NAVIGATOR BAR BUTTONS ========== */
#navBar QPushButton {
    background-color: transparent;
    color: #8f8f8f;
    border: none;
    padding: 6px 12px;
    min-width: 60px;
}
#navBar QPushButton:hover {
    background-color: #4a4a4a;
    color: #ffffff;
}
#navBar QPushButton:checked {
    background-color: #4a4a4a;
    color: #ffffff;
    border-bottom: 2px solid #8f8f8f;
}

/* ========== BUTTONS ========== */
QPushButton {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    padding: 4px 10px;
    min-width: 60px;
}
QPushButton:hover {
    background-color: #4a4a4a;
}
QPushButton:pressed {
    background-color: #5a5a5a;
}
QPushButton:checked {
    background-color: #4a4a4a;
    border: 1px solid #5a5a5a;
}

QTableWidget QPushButton, QDialog QPushButton {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #4a4a4a;
    border-radius: 3px;
    padding: 2px 6px;
}
QTableWidget QPushButton:hover, QDialog QPushButton:hover {
    background-color: #4a4a4a;
}

/* ========== TABLES ========== */
QTableWidget {
    background-color: #3c3c3c;
    alternate-background-color: #353535;
    selection-background-color: #4a4a4a;
    selection-color: #ffffff;
    gridline-color: #4a4a4a;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
}
QHeaderView::section {
    background-color: #353535;
    padding: 4px;
    border: none;
    font-weight: bold;
    color: #8f8f8f;
}
QTableWidget::item {
    padding: 4px;
}

/* ========== INPUT FIELDS ========== */
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    padding: 4px 6px;
    color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #5a5a5a;
}
QLineEdit::placeholder {
    color: #8f8f8f;
}

/* ========== SPIN BOX ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    padding: 3px 18px 3px 6px;
    color: #ffffff;
    min-height: 24px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #353535;
    width: 16px;
    border: 1px solid #4a4a4a;
    border-radius: 2px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #4a4a4a;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid #8f8f8f;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #8f8f8f;
}

/* ========== COMBOBOX POPUP ========== */
QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    selection-background-color: #4a4a4a;
    selection-color: #ffffff;
    color: #ffffff;
}
QComboBox::drop-down {
    border: none;
    width: 18px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #8f8f8f;
    margin-right: 4px;
}

/* ========== TABS ========== */
QTabWidget::pane {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #353535;
    padding: 6px 12px;
    margin-right: 2px;
    border: 1px solid #4a4a4a;
    border-bottom: none;
    color: #8f8f8f;
}
QTabBar::tab:selected {
    background-color: #3c3c3c;
    border-bottom: 1px solid #3c3c3c;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #4a4a4a;
}

/* ========== GROUP BOX ========== */
QGroupBox {
    font-weight: bold;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    background-color: #3c3c3c;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    background-color: #3c3c3c;
    color: #8f8f8f;
}

/* ========== LABELS ========== */
QLabel {
    background-color: transparent;
    color: #ffffff;
}

/* ========== STATUS BAR ========== */
QStatusBar {
    background-color: #353535;
    color: #8f8f8f;
    border-top: 1px solid #4a4a4a;
}

/* ========== SCROLL BARS ========== */
QScrollBar:vertical {
    background: #353535;
    width: 14px;
    border: 1px solid #4a4a4a;
}
QScrollBar::handle:vertical {
    background: #5a5a5a;
    border: 1px solid #4a4a4a;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #6a6a6a;
}
QScrollBar:horizontal {
    background: #353535;
    height: 14px;
    border: 1px solid #4a4a4a;
}
QScrollBar::handle:horizontal {
    background: #5a5a5a;
    border: 1px solid #4a4a4a;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #6a6a6a;
}

/* ========== DIALOGS ========== */
QDialog {
    background-color: #2b2b2b;
}
QMessageBox {
    background-color: #2b2b2b;
}
QMessageBox QLabel {
    color: #ffffff;
}
QMessageBox QPushButton {
    min-width: 60px;
    padding: 4px 10px;
}

/* ========== CHECKBOX & RADIO ========== */
QCheckBox, QRadioButton {
    spacing: 6px;
    color: #ffffff;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QCheckBox::indicator:unchecked {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 3px;
}
QRadioButton::indicator:unchecked {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 8px;
}
QRadioButton::indicator:checked {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
    border-radius: 8px;
}

/* ========== DATE EDIT CALENDAR ========== */
QDateEdit QCalendarWidget {
    background-color: #3c3c3c;
}
QCalendarWidget QTableView {
    background-color: #3c3c3c;
}
QCalendarWidget QHeaderView::section {
    background-color: #353535;
}
QCalendarWidget QToolButton {
    background-color: #3c3c3c;
    border: 1px solid #4a4a4a;
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