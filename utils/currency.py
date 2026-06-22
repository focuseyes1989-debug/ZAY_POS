from models.database import connect_db

def get_currency_symbol():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='currency'")
    row = cursor.fetchone()
    conn.close()
    currency = row[0] if row else "Kyats (Ks)"
    if currency == "Dollar ($)":
        return "$"
    elif currency == "Baht (B)":
        return "B"
    else:
        return "Ks"

def format_money(value, symbol=None):
    """Return formatted money string without unnecessary trailing zeros."""
    if symbol is None:
        symbol = get_currency_symbol()
    try:
        amount = round(float(value), 2)
    except (TypeError, ValueError):
        amount = 0
    if amount == 0:
        amount = 0
    formatted = f"{amount:.2f}".rstrip("0").rstrip(".")
    return f"{symbol}{formatted}"
