# utils/language.py
import sys
from PyQt6.QtCore import QObject, pyqtSignal
from models.database import connect_db

class LanguageManager(QObject):
    """Centralized language manager with signal support."""
    language_changed = pyqtSignal(str)
    _instance = None
    _current = "en"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_from_db()
        return cls._instance

    def _load_from_db(self):
        """Load language from database on first access."""
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key='language'")
            row = cursor.fetchone()
            conn.close()
            self._current = row[0] if row and row[0] in ('en', 'my') else "en"
        except Exception:
            self._current = "en"

    def get_current(self) -> str:
        return self._current

    def is_myanmar(self) -> bool:
        return self._current == "my"

    def tr(self, en_text: str, my_text: str) -> str:
        """Return the appropriate translation."""
        return my_text if self._current == "my" else en_text

    def set_language(self, lang_code: str):
        if lang_code not in ('en', 'my'):
            return
        self._current = lang_code
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'language'", (lang_code,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Failed to save language: {e}")
        self.language_changed.emit(lang_code)

# Singleton instance for easy import
lang = LanguageManager()