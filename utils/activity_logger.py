# utils/activity_logger.py
from models.database import connect_db
from datetime import datetime
from loguru import logger

def log_activity(user_id, username, action, details=None, ip_address=None):
    """Insert an activity record into the database."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_activity_log (user_id, username, action, details, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, action, details, ip_address, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")