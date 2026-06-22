# ui/themes/light_gray_theme.py
LIGHT_GRAY_THEME = """
/* ========== GLOBAL ========== */
* {
    font-family: "Segoe UI", "Noto Sans Myanmar", "Whitney", "Helvetica Neue", sans-serif;
    font-size: 10pt;
}

QWidget {
    background-color: #e8e8e8;
    color: #2c2f33;
}

QMainWindow {
    background-color: #dcdcdc;
}

/* ========== MENU BAR (Discord Purple) ========== */
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
QMenuBar::item:pressed {
    background-color: #3c45a3;
}

/* ========== MENU POPUP ========== */
QMenu {
    background-color: #f0f0f0;
    border: 1px solid #c0c0c0;
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
    background-color: #c0c0c0;
    margin: 4px 8px;
}

/* ========== DASHBOARD CARDS ========== */
#dashboardCard {
    background-color: #f5f5f5;
    border: 1px solid #c8c8c8;
    border-radius: 12px;
    padding: 8px;
}
#dashboardCard:hover {
    background-color: #ececec;
    border: 1px solid #a0a0a0;
}
#cardTitle {
    color: #555555;
    font-size: 10pt;
    font-weight: normal;
}
#cardValue {
    color: #2c3e50;
    font-size: 18pt;
    font-weight: bold;
}

/* ========== NAVIGATOR BAR BUTTONS ========== */
#navBar QPushButton {
    background-color: transparent;
    color: #4a4a4a;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-width: 70px;
}
#navBar QPushButton:hover {
    background-color: #d0d0d0;
    color: #2c2f33;
}
#navBar QPushButton:checked {
    background-color: #d0d0d0;
    color: #2c2f33;
    border-bottom: 2px solid #5865f2;
}

/* ========== BUTTONS (Discord Purple) ========== */
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
    background-color: #e0e0e0;
    color: #5865f2;
    border-radius: 3px;
    padding: 4px 8px;
}
QTableWidget QPushButton:hover, QDialog QPushButton:hover {
    background-color: #d0d0d0;
}

/* ========== TABLES ========== */
QTableWidget {
    background-color: #f5f5f5;
    alternate-background-color: #ececec;
    selection-background-color: #d9e5f2;
    selection-color: #2c3e50;
    gridline-color: #d0d0d0;
    border: 1px solid #c8c8c8;
    border-radius: 6px;
}
QHeaderView::section {
    background-color: #e0e0e0;
    padding: 8px;
    border: none;
    font-weight: 600;
    color: #444444;
}
QTableWidget::item {
    padding: 6px;
}

/* ========== INPUT FIELDS (Transparent) ========== */
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: transparent;
    border: 1px solid #b8b8b8;
    border-radius: 4px;
    padding: 5px 8px;
    color: #333333;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #5865f2;
}
QLineEdit::placeholder {
    color: #999999;
}

/* ========== SPIN BOX (Transparent) ========== */
QSpinBox, QDoubleSpinBox {
    background-color: transparent;
    border: 1px solid #b8b8b8;
    border-radius: 4px;
    padding: 5px 20px 5px 8px;
    min-height: 22px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #e8e8e8;
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
    border-bottom: 5px solid #666666;
    margin: 0 auto;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #666666;
    margin: 0 auto;
}

QSpinBox::up-button:hover::up-arrow, QDoubleSpinBox::up-button:hover::up-arrow {
    border-bottom-color: white;
}

QSpinBox::down-button:hover::down-arrow, QDoubleSpinBox::down-button:hover::down-arrow {
    border-top-color: white;
}

QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
    background-color: #4752c4;
}

/* ========== COMBOBOX POPUP ========== */
QComboBox QAbstractItemView {
    background-color: #fafafa;
    border: 1px solid #b8b8b8;
    border-radius: 4px;
    selection-background-color: #5865f2;
    selection-color: white;
    color: #333333;
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
    background-color: #f5f5f5;
    border: 1px solid #c8c8c8;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: transparent;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    color: #444444;
}
QTabBar::tab:selected {
    background-color: #5865f2;
    color: white;
}
QTabBar::tab:hover:!selected {
    background-color: #d0d0d0;
}

/* ========== GROUP BOX (Transparent Title) ========== */
QGroupBox {
    font-weight: 600;
    border: 1px solid #c8c8c8;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: #f5f5f5;
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
    background-color: #e0e0e0;
    color: #444444;
    border-top: 1px solid #c8c8c8;
}

/* ========== SCROLL BARS ========== */
QScrollBar:vertical {
    background: #e8e8e8;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #b8b8b8;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #5865f2;
}
QScrollBar:horizontal {
    background: #e8e8e8;
    height: 12px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: #b8b8b8;
    border-radius: 6px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #5865f2;
}

/* ========== DIALOGS ========== */
QDialog {
    background-color: #e8e8e8;
}
QMessageBox {
    background-color: #e8e8e8;
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
    background-color: #fafafa;
    border: 1px solid #999999;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #5865f2;
    border: 1px solid #5865f2;
    border-radius: 3px;
}
QRadioButton::indicator:unchecked {
    background-color: #fafafa;
    border: 1px solid #999999;
    border-radius: 8px;
}
QRadioButton::indicator:checked {
    background-color: #5865f2;
    border: 1px solid #5865f2;
    border-radius: 8px;
}

/* ========== DATE EDIT CALENDAR ========== */
QDateEdit QCalendarWidget {
    background-color: #fafafa;
}
QCalendarWidget QTableView {
    background-color: #fafafa;
}
QCalendarWidget QHeaderView::section {
    background-color: #e0e0e0;
}
QCalendarWidget QToolButton {
    background-color: #e0e0e0;
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
    background-color: #fafafa;
    border: 1px solid #999999;
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
    border: 1px solid #c8c8c8;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: #f5f5f5;
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
    background-color: #fafafa;
    border: 1px solid #999999;
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