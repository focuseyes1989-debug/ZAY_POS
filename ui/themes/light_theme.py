# ui/themes/light_theme.py
LIGHT_THEME = """
/* ========== GLOBAL ========== */
* {
    font-family: "Segoe UI", "Noto Sans Myanmar", "Whitney", "Helvetica Neue", sans-serif;
    font-size: 10pt;
}

QWidget {
    background-color: #ffffff;
    color: #2c2f33;
}

QMainWindow {
    background-color: #f8f9fa;
}

/* ========== MENU BAR ========== */
QMenuBar {
    background-color: #5865f2;
    color: white;
    padding: 4px 8px;
    font-weight: 500;
}
QMenuBar::item {
    background-color: transparent;
    padding: 4px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #4752c4;
}

/* ========== MENU POPUP ========== */
QMenu {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    background-color: transparent;
    padding: 6px 24px;
    color: #2c2f33;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #5865f2;
    color: white;
}
QMenu::separator {
    height: 1px;
    background-color: #dee2e6;
    margin: 4px 8px;
}

/* ========== DASHBOARD CARDS ========== */
#dashboardCard {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 8px;
}
#dashboardCard:hover {
    background-color: #f8f9fa;
}
#cardTitle {
    color: #6c757d;
    font-size: 10pt;
    font-weight: normal;
}
#cardValue {
    color: #212529;
    font-size: 18pt;
    font-weight: bold;
}

/* ========== NAVIGATOR BAR BUTTONS ========== */
#navBar QPushButton {
    background-color: transparent;
    color: #495057;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-width: 70px;
}
#navBar QPushButton:hover {
    background-color: #e9ecef;
    color: #212529;
}
#navBar QPushButton:checked {
    background-color: #e9ecef;
    color: #212529;
    border-bottom: 2px solid #5865f2;
}

/* ========== BUTTONS ========== */
QPushButton {
    background-color: #5865f2;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: 500;
    min-width: 70px;
}
QPushButton:hover {
    background-color: #4752c4;
}
QPushButton:pressed {
    background-color: #3c45a3;
}
QPushButton:checked {
    background-color: #4752c4;
    border: 1px solid #7983f5;
}

QTableWidget QPushButton, QDialog QPushButton {
    background-color: #e9ecef;
    color: #5865f2;
    border-radius: 3px;
    padding: 4px 8px;
}
QTableWidget QPushButton:hover, QDialog QPushButton:hover {
    background-color: #dee2e6;
}

/* ========== TABLES ========== */
QTableWidget {
    background-color: white;
    alternate-background-color: #f8f9fa;
    selection-background-color: #e3f2fd;
    selection-color: #1976d2;
    gridline-color: #dee2e6;
    border: 1px solid #dee2e6;
    border-radius: 6px;
}
QHeaderView::section {
    background-color: #f1f3f5;
    padding: 8px;
    border: none;
    font-weight: 600;
    color: #495057;
}
QTableWidget::item {
    padding: 6px;
}

/* ========== INPUT FIELDS (Transparent) ========== */
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: transparent;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 5px 8px;
    color: #495057;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #5865f2;
}
QLineEdit::placeholder {
    color: #adb5bd;
}

/* ========== SPIN BOX (Transparent) ========== */
QSpinBox, QDoubleSpinBox {
    background-color: transparent;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 5px 20px 5px 8px;
    min-height: 22px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #f1f3f5;
    width: 20px;
    border: none;
    border-radius: 2px;
    margin: 1px;
    subcontrol-origin: border;
}

QSpinBox::up-button {
    subcontrol-position: top right;
    top: 1px;
    right: 1px;
}

QSpinBox::down-button {
    subcontrol-position: bottom right;
    bottom: 1px;
    right: 1px;
}

QDoubleSpinBox::up-button {
    subcontrol-position: top right;
    top: 1px;
    right: 1px;
}

QDoubleSpinBox::down-button {
    subcontrol-position: bottom right;
    bottom: 1px;
    right: 1px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #5865f2;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 5px solid #6c757d;
    margin: 0 auto;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #6c757d;
    margin: 0 auto;
}

QSpinBox::up-button:hover::up-arrow, QDoubleSpinBox::up-button:hover::up-arrow {
    border-bottom-color: white;
}

QSpinBox::down-button:hover::down-arrow, QDoubleSpinBox::down-button:hover::down-arrow {
    border-top-color: white;
}

/* ========== COMBOBOX POPUP ========== */
QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #ced4da;
    border-radius: 4px;
    selection-background-color: #5865f2;
    selection-color: white;
    color: #495057;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #5865f2;
    margin-right: 6px;
}

/* ========== TABS (Transparent Background) ========== */
QTabWidget::pane {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: transparent;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    color: #495057;
}
QTabBar::tab:selected {
    background-color: #5865f2;
    color: white;
}
QTabBar::tab:hover:!selected {
    background-color: #dee2e6;
}

/* ========== GROUP BOX (Transparent Title) ========== */
QGroupBox {
    font-weight: 600;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: white;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    background-color: transparent;
    color: #5865f2;
}

/* ========== LABELS (Transparent) ========== */
QLabel {
    background-color: transparent;
    color: #2c2f33;
}

/* ========== STATUS BAR ========== */
QStatusBar {
    background-color: #e9ecef;
    color: #495057;
    border-top: 1px solid #dee2e6;
}

/* ========== SCROLL BARS ========== */
QScrollBar:vertical {
    background: #f1f3f5;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #adb5bd;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #5865f2;
}
QScrollBar:horizontal {
    background: #f1f3f5;
    height: 12px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: #adb5bd;
    border-radius: 6px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #5865f2;
}

/* ========== DIALOGS ========== */
QDialog {
    background-color: white;
}
QMessageBox {
    background-color: white;
}
QMessageBox QLabel {
    color: #2c2f33;
}
QMessageBox QPushButton {
    min-width: 70px;
    padding: 5px 12px;
}

/* ========== CHECKBOX & RADIO ========== */
QCheckBox, QRadioButton {
    spacing: 6px;
    color: #2c2f33;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QCheckBox::indicator:unchecked {
    background-color: white;
    border: 1px solid #adb5bd;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #5865f2;
    border: 1px solid #5865f2;
    border-radius: 3px;
}
QRadioButton::indicator:unchecked {
    background-color: white;
    border: 1px solid #adb5bd;
    border-radius: 8px;
}
QRadioButton::indicator:checked {
    background-color: #5865f2;
    border: 1px solid #5865f2;
    border-radius: 8px;
}

/* ========== DATE EDIT CALENDAR ========== */
QDateEdit QCalendarWidget {
    background-color: white;
}
QCalendarWidget QTableView {
    background-color: white;
}
QCalendarWidget QHeaderView::section {
    background-color: #f1f3f5;
}
QCalendarWidget QToolButton {
    background-color: #e9ecef;
    border-radius: 3px;
    padding: 2px;
}

/* ========== RADIO BUTTON (Transparent Background) ========== */
QRadioButton {
    spacing: 6px;
    background-color: transparent;
    color: #2c2f33;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QRadioButton::indicator:unchecked {
    background-color: white;
    border: 1px solid #adb5bd;
    border-radius: 8px;
}
QRadioButton::indicator:checked {
    background-color: #5865f2;
    border: 1px solid #5865f2;
    border-radius: 8px;
}

/* ========== GROUP BOX (Transparent Title) ========== */
QGroupBox {
    font-weight: 600;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: white;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    background-color: transparent;
    color: #5865f2;
}

/* ========== CHECKBOX (Transparent Background) ========== */
QCheckBox {
    spacing: 6px;
    background-color: transparent;
    color: #2c2f33;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QCheckBox::indicator:unchecked {
    background-color: white;
    border: 1px solid #adb5bd;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #5865f2;
    border: 1px solid #5865f2;
    border-radius: 3px;
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