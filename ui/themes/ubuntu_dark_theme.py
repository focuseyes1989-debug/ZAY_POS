# ui/themes/ubuntu_dark_theme.py
UBUNTU_DARK_THEME = """
/* ========== GLOBAL ========== */
* {
    font-family: "Segoe UI", "Noto Sans Myanmar", "Whitney", "Helvetica Neue", sans-serif;
    font-size: 10pt;
}

QWidget {
    background-color: #2c2c2c;
    color: #e0e0e0;
}

QMainWindow {
    background-color: #2c2c2c;
}

/* ========== MENU BAR (Ubuntu Orange) ========== */
QMenuBar {
    background-color: #e95420;
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
    background-color: #c34113;
}

/* ========== MENU POPUP ========== */
QMenu {
    background-color: #2f3136;
    border: 1px solid #202225;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    background-color: transparent;
    padding: 6px 24px;
    color: #dcddde;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #e95420;
    color: white;
}
QMenu::separator {
    height: 1px;
    background-color: #202225;
    margin: 4px 8px;
}

/* ========== DASHBOARD CARDS ========== */
#dashboardCard {
    background-color: #2f3136;
    border: 1px solid #40444b;
    border-radius: 12px;
    padding: 8px;
}
#dashboardCard:hover {
    background-color: #383a40;
    border: 1px solid #e95420;
}
#cardTitle {
    color: #b9bbbe;
    font-size: 10pt;
    font-weight: normal;
}
#cardValue {
    color: #ffffff;
    font-size: 18pt;
    font-weight: bold;
}

/* ========== NAVIGATOR BAR BUTTONS ========== */
#navBar QPushButton {
    background-color: transparent;
    color: #b9bbbe;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-width: 70px;
}
#navBar QPushButton:hover {
    background-color: #40444b;
    color: white;
}
#navBar QPushButton:checked {
    background-color: #40444b;
    color: white;
    border-bottom: 2px solid #e95420;
}

/* ========== BUTTONS (Ubuntu Orange) ========== */
QPushButton {
    background-color: #e95420;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: 500;
    min-width: 70px;
}
QPushButton:hover {
    background-color: #c34113;
}
QPushButton:pressed {
    background-color: #ac3a10;
}
QPushButton:checked {
    background-color: #c34113;
    border: 1px solid #f47c33;
}

QTableWidget QPushButton, QDialog QPushButton {
    background-color: #40444b;
    color: #e95420;
    border-radius: 3px;
    padding: 4px 8px;
}
QTableWidget QPushButton:hover, QDialog QPushButton:hover {
    background-color: #e95420;
    color: white;
}

/* ========== TABLES ========== */
QTableWidget {
    background-color: #2f3136;
    alternate-background-color: #36393f;
    selection-background-color: #40444b;
    selection-color: #ffffff;
    gridline-color: #202225;
    border: 1px solid #202225;
    border-radius: 6px;
}
QHeaderView::section {
    background-color: #202225;
    padding: 8px;
    border: none;
    font-weight: 600;
    color: #b9bbbe;
}
QTableWidget::item {
    padding: 6px;
}

/* ========== INPUT FIELDS (Transparent) ========== */
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: transparent;
    border: 1px solid #40444b;
    border-radius: 4px;
    padding: 5px 8px;
    color: #dcddde;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #e95420;
}
QLineEdit::placeholder {
    color: #888888;
}

/* ========== SPIN BOX (Transparent) ========== */
QSpinBox, QDoubleSpinBox {
    background-color: transparent;
    border: 1px solid #40444b;
    border-radius: 4px;
    padding: 5px 20px 5px 8px;
    color: #dcddde;
    min-height: 22px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #2f3136;
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
    background-color: #e95420;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-bottom: 5px solid #b9bbbe;
    margin: 0 auto;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #b9bbbe;
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
    background-color: #2f3136;
    border: 1px solid #202225;
    border-radius: 4px;
    selection-background-color: #e95420;
    selection-color: white;
    color: #dcddde;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #e95420;
    margin-right: 6px;
}

/* ========== TABS (Transparent Background) ========== */
QTabWidget::pane {
    background-color: #2f3136;
    border: 1px solid #202225;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: transparent;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    color: #b9bbbe;
}
QTabBar::tab:selected {
    background-color: #e95420;
    color: white;
}
QTabBar::tab:hover:!selected {
    background-color: #2f3136;
    color: #dcddde;
}

/* ========== GROUP BOX (Transparent Title) ========== */
QGroupBox {
    font-weight: 600;
    border: 1px solid #202225;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: #2f3136;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    background-color: transparent;
    color: #e95420;
}

/* ========== LABELS (Transparent) ========== */
QLabel {
    background-color: transparent;
    color: #dcddde;
}

/* ========== STATUS BAR ========== */
QStatusBar {
    background-color: #202225;
    color: #b9bbbe;
    border-top: 1px solid #2f3136;
}

/* ========== SCROLL BARS ========== */
QScrollBar:vertical {
    background: #2f3136;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #40444b;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #e95420;
}
QScrollBar:horizontal {
    background: #2f3136;
    height: 12px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: #40444b;
    border-radius: 6px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #e95420;
}

/* ========== DIALOGS ========== */
QDialog {
    background-color: #2f3136;
}
QMessageBox {
    background-color: #2f3136;
}
QMessageBox QLabel {
    color: #dcddde;
}
QMessageBox QPushButton {
    min-width: 70px;
    padding: 5px 12px;
}

/* ========== CHECKBOX & RADIO ========== */
QCheckBox, QRadioButton {
    spacing: 6px;
    color: #dcddde;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QCheckBox::indicator:unchecked {
    background-color: #40444b;
    border: 1px solid #202225;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #e95420;
    border: 1px solid #e95420;
    border-radius: 3px;
}
QRadioButton::indicator:unchecked {
    background-color: #40444b;
    border: 1px solid #202225;
    border-radius: 8px;
}
QRadioButton::indicator:checked {
    background-color: #e95420;
    border: 1px solid #e95420;
    border-radius: 8px;
}

/* ========== DATE EDIT CALENDAR ========== */
QDateEdit QCalendarWidget {
    background-color: #2f3136;
}
QCalendarWidget QTableView {
    background-color: #2f3136;
}
QCalendarWidget QHeaderView::section {
    background-color: #202225;
}
QCalendarWidget QToolButton {
    background-color: #40444b;
    border-radius: 3px;
    padding: 2px;
}

/* ========== RADIO BUTTON (Transparent Background) ========== */
QRadioButton {
    spacing: 6px;
    background-color: transparent;
    color: #dcddde;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QRadioButton::indicator:unchecked {
    background-color: #40444b;
    border: 1px solid #202225;
    border-radius: 8px;
}
QRadioButton::indicator:checked {
    background-color: #e95420;
    border: 1px solid #e95420;
    border-radius: 8px;
}

/* ========== GROUP BOX (Transparent Title) ========== */
QGroupBox {
    font-weight: 600;
    border: 1px solid #202225;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: #2f3136;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    background-color: transparent;
    color: #e95420;
}

/* ========== CHECKBOX (Transparent Background) ========== */
QCheckBox {
    spacing: 6px;
    background-color: transparent;
    color: #dcddde;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QCheckBox::indicator:unchecked {
    background-color: #40444b;
    border: 1px solid #202225;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #e95420;
    border: 1px solid #e95420;
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