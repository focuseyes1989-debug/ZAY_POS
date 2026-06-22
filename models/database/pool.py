# models/database/pool.py
"""
Connection pool implementation with thread safety.
"""

import os
import sqlite3
import threading
import weakref
from queue import Queue, Empty
from loguru import logger

DB_NAME = "database/pos.db"
POOL_SIZE = 20  # Increased for better concurrency


class ConnectionPool:
    """Simple connection pool for SQLite with automatic return on close."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._pool = Queue(maxsize=POOL_SIZE)
                cls._instance._size = POOL_SIZE
                cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        """Create initial connections."""
        for _ in range(self._size):
            conn = self._create_connection()
            self._pool.put(conn)

    def _create_connection(self):
        """Create a new database connection with WAL mode and foreign keys enabled."""
        try:
            os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
            conn = sqlite3.connect(DB_NAME, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys = ON")
            conn.isolation_level = 'DEFERRED'
            logger.debug(f"New database connection created (pool)")
            return conn
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            raise

    def get_connection(self, timeout=5.0, max_retries=3):
        """Get a connection from the pool with retry logic."""
        retries = 0
        while retries < max_retries:
            try:
                conn = self._pool.get(timeout=timeout)
                # Check if connection is still alive
                try:
                    conn.execute("SELECT 1").fetchone()
                except (sqlite3.OperationalError, sqlite3.DatabaseError):
                    # Connection is dead, create new one
                    conn = self._create_connection()
                
                # Rollback any pending transaction to ensure clean state
                try:
                    conn.rollback()
                except:
                    pass
                
                # Wrap the connection so that when close() is called, it returns to pool
                return _PooledConnection(conn, self)
            except Empty:
                retries += 1
                if retries >= max_retries:
                    logger.warning(f"Database connection pool exhausted after {max_retries} retries – creating temporary unpooled connection")
                    # Fallback: create a temporary connection (not pooled, but still works)
                    return self._create_connection()
                logger.warning(f"Connection pool empty, retry {retries}/{max_retries}")
                import time
                time.sleep(0.5)
        
        return self._create_connection()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        if conn:
            try:
                conn.rollback()
                self._pool.put(conn)
            except Exception as e:
                logger.error(f"Failed to return connection to pool: {e}")
                try:
                    conn.close()
                except:
                    pass

    def close_all(self):
        """Close all connections in the pool (for app shutdown)."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except:
                pass


class _PooledConnection:
    """Wrapper that returns the connection to the pool when closed."""
    def __init__(self, conn, pool):
        self._conn = conn
        self._pool = pool
        self._finalizer = weakref.finalize(self, self._close_and_return)

    def _close_and_return(self):
        if self._conn:
            self._pool.return_connection(self._conn)
            self._conn = None

    def close(self):
        self._close_and_return()
        self._finalizer.detach()

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self._conn.__enter__()

    def __exit__(self, *args):
        self.close()


# Global pool instance - ဒီ line ကို ထည့်ပါ
_pool = ConnectionPool()


def get_pool_stats():
    """Get connection pool statistics."""
    with _pool._lock:
        return {
            "pool_size": _pool._pool.qsize(),
            "max_size": POOL_SIZE,
            "available": _pool._pool.qsize(),
            "usage_percentage": ((POOL_SIZE - _pool._pool.qsize()) / POOL_SIZE * 100) if POOL_SIZE > 0 else 0
        }


def is_connection_healthy(conn):
    """Check if a database connection is still alive."""
    try:
        conn.execute("SELECT 1").fetchone()
        return True
    except (sqlite3.OperationalError, sqlite3.DatabaseError, AttributeError):
        return False