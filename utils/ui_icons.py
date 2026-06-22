import re

from PyQt6.QtWidgets import QPushButton, QTabWidget


_INSTALLED = False
_ORIGINAL_BUTTON_INIT = None
_ORIGINAL_BUTTON_SET_TEXT = None
_ORIGINAL_TAB_ADD = None
_ORIGINAL_TAB_INSERT = None
_ORIGINAL_TAB_SET_TEXT = None

_LEADING_ICON_RE = re.compile(r"^\s*[\U0001F300-\U0001FAFF\u2600-\u27BF]+(?:\ufe0f)?\s+")

_ICON_RULES = [
    ("💵", ("cashdrawer", "cash drawer", "cash", "ငွေသား")),
    ("💳", ("payment", "pay", "paid", "ငွေပေး", "ပေးချေ")),
    ("🧾", ("receipt", "invoice", "print receipt", "ပြေစာ")),
    ("🖨️", ("print", "ပရင့်")),
    ("🛒", ("sales", "sale", "checkout", "cart", "ဈေးခြင်း", "ရောင်း", "ငွေရှင်း")),
    ("📊", ("dashboard", "summary", "report", "chart", "compare", "excel", "export", "စာရင်းထုတ်", "အစီရင်ခံ", "နှိုင်းယှဉ်")),
    ("📦", ("product", "item", "stock", "inventory", "ပစ္စည်း", "စတော့", "ကုန်")),
    ("📥", ("stock in", "import", "restore", "တင်", "restore", "ပြန်လည်")),
    ("📤", ("stock out", "backup", "upload", "ထုတ်", "backup")),
    ("🔄", ("refresh", "transfer", "change", "ပြန်လည်", "လွှဲပြောင်း")),
    ("➕", ("add", "create", "new", "အသစ်", "ထည့်")),
    ("✏️", ("edit", "adjust", "update", "ပြင်")),
    ("🗑️", ("delete", "remove", "clear", "reset", "ဖျက်", "ရှင်း")),
    ("💾", ("save", "ok", "confirm", "apply", "သိမ်း", "အတည်ပြု")),
    ("❌", ("cancel", "close", "exit", "logout", "ပိတ်", "မလုပ်တော့")),
    ("🔍", ("search", "view", "details", "ကြည့်")),
    ("👥", ("customer", "users", "role", "supplier", "ဝယ်ယူသူ", "အသုံးပြုသူ", "အခန်းကဏ္ဍ", "ရောင်းချသူ")),
    ("🏷️", ("category", "barcode", "tag", "အမျိုးအစား", "ဘားကုဒ်")),
    ("📁", ("folder", "file", "attachment", "ဖိုင်", "ဖိုင်တွဲ")),
    ("🖼️", ("image", "logo", "browse", "ပုံ", "အမှတ်တံဆိပ်")),
    ("⚙️", ("settings", "setting", "regional", "general", "သတ်မှတ်", "ပြင်ဆင်ချက်")),
    ("🔔", ("notification", "alert", "warning", "သတိပေး")),
    ("📅", ("today", "week", "month", "year", "date", "expiry", "ယနေ့", "တစ်ပတ်", "လ", "နှစ်", "ရက်")),
    ("📍", ("location", "warehouse", "address", "နေရာ", "လိပ်စာ")),
    ("🔐", ("login", "password", "permission", "ဝင်", "စကားဝှက်", "ခွင့်")),
    ("💰", ("expense", "budget", "profit", "cost", "price", "total", "အသုံးစရိတ်", "ဘတ်ဂျက်", "အမြတ်", "စျေး")),
]


def _has_icon(text):
    stripped = text.strip()
    if not stripped:
        return True
    if _LEADING_ICON_RE.match(stripped):
        return True
    return stripped[0] in {"✓", "✕", "□", "❐", "─", "+", "-"}


def icon_for_text(text):
    lowered = text.lower()
    for icon, keywords in _ICON_RULES:
        if any(keyword in lowered for keyword in keywords):
            return icon
    return ""


def with_ui_icon(text):
    if not isinstance(text, str) or _has_icon(text):
        return text
    icon = icon_for_text(text)
    return f"{icon} {text}" if icon else text


def install_ui_icons():
    global _INSTALLED
    global _ORIGINAL_BUTTON_INIT, _ORIGINAL_BUTTON_SET_TEXT
    global _ORIGINAL_TAB_ADD, _ORIGINAL_TAB_INSERT, _ORIGINAL_TAB_SET_TEXT

    if _INSTALLED:
        return

    _ORIGINAL_BUTTON_INIT = QPushButton.__init__
    _ORIGINAL_BUTTON_SET_TEXT = QPushButton.setText
    _ORIGINAL_TAB_ADD = QTabWidget.addTab
    _ORIGINAL_TAB_INSERT = QTabWidget.insertTab
    _ORIGINAL_TAB_SET_TEXT = QTabWidget.setTabText

    def button_init(self, *args, **kwargs):
        _ORIGINAL_BUTTON_INIT(self, *args, **kwargs)
        current_text = self.text()
        if current_text:
            _ORIGINAL_BUTTON_SET_TEXT(self, with_ui_icon(current_text))

    def button_set_text(self, text):
        _ORIGINAL_BUTTON_SET_TEXT(self, with_ui_icon(text))

    def tab_add(self, widget, *args):
        if args and isinstance(args[-1], str):
            args = (*args[:-1], with_ui_icon(args[-1]))
        return _ORIGINAL_TAB_ADD(self, widget, *args)

    def tab_insert(self, index, widget, *args):
        if args and isinstance(args[-1], str):
            args = (*args[:-1], with_ui_icon(args[-1]))
        return _ORIGINAL_TAB_INSERT(self, index, widget, *args)

    def tab_set_text(self, index, text):
        _ORIGINAL_TAB_SET_TEXT(self, index, with_ui_icon(text))

    QPushButton.__init__ = button_init
    QPushButton.setText = button_set_text
    QTabWidget.addTab = tab_add
    QTabWidget.insertTab = tab_insert
    QTabWidget.setTabText = tab_set_text
    _INSTALLED = True
