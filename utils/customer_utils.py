# utils/customer_utils.py
from models.database import DBContext

def load_customers():
    """Return list of (id, name, points) for all customers."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, points FROM customers ORDER BY name")
        return cursor.fetchall()