# ui/themes/windows_xp_theme.py
WINDOWS_XP_THEME = """
/* ========== GLOBAL ========== */
* {
    font-family: "Segoe UI", "Tahoma", "Arial", sans-serif;
    font-size: 9pt;
}

QWidget {
    background-color: #ffffff;
    color: #000000;
}

QMainWindow {
    background-color: #3a6ea5;
}

/* ========== MENU BAR (Classic XP Blue) ========== */
QMenuBar {
    background-color: #245edc;
    color: white;
    padding: 2px 4px;
    font-weight: bold;
}
QMenuBar::item {
    background-color: transparent;
    padding: 2px 8px;
    border-radius: 0px;
}
QMenuBar::item:selected {
    background-color: #316ac5;
    color: white;
}

/* ========== MENU POPUP ========== */
QMenu {
    background-color: #ece9d8;
    border: 1px solid #0a246a;
    padding: 2px;
}
QMenu::item {
    background-color: transparent;
    padding: 4px 20px;
    color: #000000;
}
QMenu::item:selected {
    background-color: #316ac5;
    color: white;
}
QMenu::separator {
    height: 1px;
    background-color: #a7a7a7;
    margin: 2px 4px;
}

/* ========== DASHBOARD CARDS ========== */
#dashboardCard {
    background-color: #d4d0c8;
    border: 2px solid #0a246a;
    border-radius: 0px;
    padding: 8px;
}
#dashboardCard:hover {
    background-color: #e0dcd4;
    border-color: #316ac5;
}
#cardTitle {
    color: #000000;
    font-size: 9pt;
    font-weight: bold;
}
#cardValue {
    color: #000000;
    font-size: 16pt;
    font-weight: bold;
}

/* ========== NAVIGATOR BAR BUTTONS ========== */
#navBar QPushButton {
    background-color: #d4d0c8;
    color: #000000;
    border: 2px solid #0a246a;
    border-radius: 0px;
    padding: 6px 14px;
    font-weight: bold;
    min-width: 60px;
}
#navBar QPushButton:hover {
    background-color: #e0dcd4;
    border-color: #316ac5;
}
#navBar QPushButton:checked {
    background-color: #316ac5;
    color: white;
    border-color: #0a246a;
}

/* ========== BUTTONS ========== */
QPushButton {
    background-color: #d4d0c8;
    color: #000000;
    border: 2px solid #0a246a;
    border-radius: 0px;
    padding: 4px 10px;
    font-weight: bold;
    min-width: 60px;
}
QPushButton:hover {
    background-color: #e0dcd4;
    border-color: #316ac5;
}
QPushButton:pressed {
    background-color: #316ac5;
    color: white;
}
QPushButton:checked {
    background-color: #316ac5;
    color: white;
    border-color: #0a246a;
}

QTableWidget QPushButton, QDialog QPushButton {
    background-color: #d4d0c8;
    color: #000000;
    border: 1px solid #0a246a;
    border-radius: 0px;
    padding: 2px 6px;
}
QTableWidget QPushButton:hover, QDialog QPushButton:hover {
    background-color: #e0dcd4;
    border-color: #316ac5;
}

/* ========== TABLES ========== */
QTableWidget {
    background-color: #ece9d8;
    alternate-background-color: #d4d0c8;
    selection-background-color: #316ac5;
    selection-color: white;
    gridline-color: #a7a7a7;
    border: 2px solid #0a246a;
    border-radius: 0px;
}
QHeaderView::section {
    background-color: #d4d0c8;
    padding: 4px;
    border: none;
    font-weight: bold;
    color: #000000;
}
QTableWidget::item {
    padding: 4px;
}

/* ========== INPUT FIELDS ========== */
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: #ece9d8;
    border: 2px solid #0a246a;
    border-radius: 0px;
    padding: 4px 6px;
    color: #000000;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #316ac5;
}
QLineEdit::placeholder {
    color: #888888;
}

/* ========== SPIN BOX ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #ece9d8;
    border: 2px solid #0a246a;
    border-radius: 0px;
    padding: 3px 18px 3px 6px;
    color: #000000;
    min-height: 24px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #d4d0c8;
    width: 16px;
    border: 1px solid #0a246a;
    border-radius: 0px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #e0dcd4;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid #000000;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #000000;
}

/* ========== COMBOBOX POPUP ========== */
QComboBox QAbstractItemView {
    background-color: #ece9d8;
    border: 2px solid #0a246a;
    border-radius: 0px;
    selection-background-color: #316ac5;
    selection-color: white;
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
    border-top: 4px solid #000000;
    margin-right: 4px;
}

/* ========== TABS ========== */
QTabWidget::pane {
    background-color: #ece9d8;
    border: 2px solid #0a246a;
    border-radius: 0px;
}
QTabBar::tab {
    background-color: #d4d0c8;
    padding: 6px 16px;
    margin-right: 2px;
    border: 2px solid #0a246a;
    border-bottom: none;
    color: #000000;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #ece9d8;
    border-bottom: 2px solid #ece9d8;
}
QTabBar::tab:hover:!selected {
    background-color: #e0dcd4;
}

/* ========== GROUP BOX ========== */
QGroupBox {
    font-weight: bold;
    border: 2px solid #0a246a;
    border-radius: 0px;
    margin-top: 8px;
    padding-top: 8px;
    background-color: #d4d0c8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    background-color: #d4d0c8;
    color: #000000;
}

/* ========== LABELS ========== */
QLabel {
    background-color: transparent;
    color: #000000;
}

/* ========== STATUS BAR ========== */
QStatusBar {
    background-color: #d4d0c8;
    color: #000000;
    border-top: 2px solid #0a246a;
}

/* ========== SCROLL BARS ========== */
QScrollBar:vertical {
    background: #d4d0c8;
    width: 16px;
    border: 1px solid #0a246a;
}
QScrollBar::handle:vertical {
    background: #ece9d8;
    border: 1px solid #0a246a;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #e0dcd4;
}
QScrollBar:horizontal {
    background: #d4d0c8;
    height: 16px;
    border: 1px solid #0a246a;
}
QScrollBar::handle:horizontal {
    background: #ece9d8;
    border: 1px solid #0a246a;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #e0dcd4;
}

/* ========== DIALOGS ========== */
QDialog {
    background-color: #3a6ea5;
}
QMessageBox {
    background-color: #3a6ea5;
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
    background-color: #ece9d8;
    border: 2px solid #0a246a;
    border-radius: 0px;
}
QCheckBox::indicator:checked {
    background-color: #316ac5;
    border: 2px solid #0a246a;
    border-radius: 0px;
}
QRadioButton::indicator:unchecked {
    background-color: #ece9d8;
    border: 2px solid #0a246a;
    border-radius: 8px;
}
QRadioButton::indicator:checked {
    background-color: #316ac5;
    border: 2px solid #0a246a;
    border-radius: 8px;
}

/* ========== DATE EDIT CALENDAR ========== */
QDateEdit QCalendarWidget {
    background-color: #ece9d8;
}
QCalendarWidget QTableView {
    background-color: #ece9d8;
}
QCalendarWidget QHeaderView::section {
    background-color: #d4d0c8;
}
QCalendarWidget QToolButton {
    background-color: #d4d0c8;
    border: 1px solid #0a246a;
    border-radius: 0px;
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