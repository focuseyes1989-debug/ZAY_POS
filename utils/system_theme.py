# utils/system_theme.py
from PyQt6.QtCore import QObject, pyqtSignal
import sys


class SystemThemeDetector(QObject):
    theme_changed = pyqtSignal(str)  # 'Dark' or 'Light'

    def __init__(self):
        super().__init__()
        self._current = self.get_system_theme()

    def get_system_theme(self):
        """Read the current Windows system theme (Light/Dark)."""
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return "Light" if value == 1 else "Dark"
            except:
                pass
        # For other OS, return Light as default
        return "Light"

    def refresh(self):
        """Manually check and emit if the system theme has changed."""
        new_theme = self.get_system_theme()
        if new_theme != self._current:
            self._current = new_theme
            self.theme_changed.emit(new_theme)


system_theme = SystemThemeDetector()