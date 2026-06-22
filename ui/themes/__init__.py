# ui/themes/__init__.py
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui.themes.dark_theme import DARK_THEME
from ui.themes.light_theme import LIGHT_THEME
from ui.themes.light_gray_theme import LIGHT_GRAY_THEME
from ui.themes.ubuntu_theme import UBUNTU_THEME
from ui.themes.ubuntu_dark_theme import UBUNTU_DARK_THEME
from ui.themes.windows_xp_theme import WINDOWS_XP_THEME
from ui.themes.pyqt6_dark_theme import PYQT6_DARK_THEME
from ui.themes.pyqt6_light_theme import PYQT6_LIGHT_THEME

THEMES = {
    "Dark": DARK_THEME,
    "Light": LIGHT_THEME,
    "Light Gray": LIGHT_GRAY_THEME,
    "Ubuntu": UBUNTU_THEME,
    "Ubuntu Dark": UBUNTU_DARK_THEME,
    "Windows XP": WINDOWS_XP_THEME,
    "PyQt6 Dark": PYQT6_DARK_THEME,
    "PyQt6 Light": PYQT6_LIGHT_THEME
}

def get_scaled_font_size(base_size=9):
    """Get font size scaled based on screen DPI"""
    try:
        screen = QApplication.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            scale = dpi / 96.0
            return int(base_size * scale)
    except:
        pass
    return base_size

def apply_font():
    """Apply scaled font to the application"""
    app = QApplication.instance()
    if app:
        font_size = get_scaled_font_size(9)
        font = QFont("Segoe UI", font_size)
        app.setFont(font)
        return font
    return None

def apply_theme(app, theme_name):
    """Apply the selected theme to the QApplication."""
    apply_font()
    if theme_name in THEMES:
        app.setStyleSheet(THEMES[theme_name])

def apply_discord_theme(app):
    apply_theme(app, "Dark")

def apply_dark_gray_touch_theme(app):
    apply_theme(app, "Dark")