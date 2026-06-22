# models/database/connection.py
"""
Database connection management with pooling.
"""

import sqlite3
import os
from loguru import logger
from models.database.pool import ConnectionPool, _pool

DB_NAME = "database/pos.db"

def connect_db():
    """
    Return a pooled connection (wrapped). The connection will automatically
    return to the pool when .close() is called or when garbage collected.
    """
    return _pool.get_connection()


def close_all_connections():
    """Close idle pooled database connections before replacing the database file."""
    _pool.close_all()


def release_connection(conn):
    """Explicitly return a connection to the pool (if not already closed)."""
    if hasattr(conn, 'close'):
        conn.close()


class DBContext:
    """Context manager for database connections. Usage: with DBContext() as conn:"""
    def __enter__(self):
        self.conn = connect_db()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()


def get_connection_with_health_check():
    """Get a healthy connection from the pool."""
    from models.database.pool import is_connection_healthy
    conn = connect_db()
    if not is_connection_healthy(conn):
        conn.close()
        # Remove dead connection from pool
        with _pool._lock:
            try:
                while not _pool._pool.empty():
                    dead_conn = _pool._pool.get_nowait()
                    if is_connection_healthy(dead_conn):
                        _pool._pool.put(dead_conn)
                        break
                    else:
                        try:
                            dead_conn.close()
                        except:
                            pass
            except:
                pass
        return connect_db()
    return conn