# models/database/__init__.py
"""
Database module with connection pooling and ORM-like functionality.
"""

import sqlite3
import os
from typing import Optional, List, Tuple, Any

# Connection
from models.database.connection import connect_db, DBContext, release_connection, close_all_connections
from models.database.pool import ConnectionPool, get_pool_stats

# Queries
from models.database.queries import (
    get_products, get_product, add_product, update_product, delete_product,
    get_sales, get_sale, add_sale, update_sale, delete_sale, get_sale_items,
    get_customers, get_customer, add_customer, update_customer, delete_customer,
    get_expenses, get_expense, add_expense, update_expense, delete_expense,
    get_settings, update_setting, get_setting
)

# Tables
from models.database.tables import create_tables, ensure_schema

# Maintenance
from models.database.maintenance import (
    optimize_database, vacuum_database, get_database_stats,
    rebuild_indexes, backup_database, expire_old_points, 
    expire_points_for_customer, check_and_recover
)

# Migrations
from models.database.migrations import (
    run_migrations, 
    rollback_to_version, 
    get_migration_status, 
    fix_missing_columns,
    check_and_run_migrations,
    get_app_version,
    set_app_version
)

# Indexes
from models.database.indexes import (
    create_optimized_indexes,
    drop_optimized_indexes,
    analyze_query_performance,
    create_suggested_indexes,
    get_index_usage_stats
)

# Health
from models.database.health import check_database_health

# Auto Maintenance
from models.database.auto_maintenance import (
    start_auto_maintenance,
    stop_auto_maintenance
)


# ============================================================================
# 🔥 ADDED: DatabaseManager class for backward compatibility
# ============================================================================

class DatabaseManager:
    """
    Database manager for application.
    Provides a unified interface for database operations.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        from models.database.connection import connect_db
        return connect_db(self.db_path)
    
    def release_connection(self, conn: sqlite3.Connection):
        """
        Release a database connection.
        
        Args:
            conn: Database connection to release
        """
        from models.database.connection import release_connection
        release_connection(conn)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Tuple]:
        """
        Execute a query and return results.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List[Tuple]: Query results
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.commit()
            return result
        finally:
            self.release_connection(conn)
    
    def execute_one(self, query: str, params: tuple = ()) -> Optional[Tuple]:
        """
        Execute a query and return one result.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Optional[Tuple]: Single query result
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.commit()
            return result
        finally:
            self.release_connection(conn)
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an update query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            int: Last row id
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            self.release_connection(conn)
    
    def execute_many(self, query: str, params_list: list) -> int:
        """
        Execute a query with multiple parameters.
        
        Args:
            query: SQL query
            params_list: List of parameter tuples
            
        Returns:
            int: Number of affected rows
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        finally:
            self.release_connection(conn)
    
    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script.
        
        Args:
            script: SQL script
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executescript(script)
            conn.commit()
        finally:
            self.release_connection(conn)
    
    def get_table_names(self) -> List[str]:
        """
        Get all table names.
        
        Returns:
            List[str]: List of table names
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in cursor.fetchall()]
        finally:
            self.release_connection(conn)
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_name: Table name to check
            
        Returns:
            bool: True if table exists
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cursor.fetchone() is not None
        finally:
            self.release_connection(conn)
    
    def get_table_info(self, table_name: str) -> List[Tuple]:
        """
        Get table column information.
        
        Args:
            table_name: Table name
            
        Returns:
            List[Tuple]: Table information
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            return cursor.fetchall()
        finally:
            self.release_connection(conn)
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Backup the database.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if backup successful
        """
        import shutil
        try:
            # Ensure backup directory exists
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
    
    def vacuum(self) -> None:
        """Optimize database with VACUUM."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            conn.commit()
        finally:
            self.release_connection(conn)
    
    def close(self) -> None:
        """Close all database connections."""
        from models.database.connection import close_all_connections
        close_all_connections()
    
    def get_db_size(self) -> int:
        """
        Get database file size.
        
        Returns:
            int: Size in bytes
        """
        if os.path.exists(self.db_path):
            return os.path.getsize(self.db_path)
        return 0


# Backward compatibility
def get_current_schema_version():
    """Get current database schema version (backward compatibility)."""
    status = get_migration_status()
    return status['current_version'] if status else "0.0.0"


__all__ = [
    # Connection
    'connect_db', 'DBContext', 'release_connection', 'close_all_connections',
    'ConnectionPool', 'get_pool_stats',
    
    # Queries
    'get_products', 'get_product', 'add_product', 'update_product', 'delete_product',
    'get_sales', 'get_sale', 'add_sale', 'update_sale', 'delete_sale', 'get_sale_items',
    'get_customers', 'get_customer', 'add_customer', 'update_customer', 'delete_customer',
    'get_expenses', 'get_expense', 'add_expense', 'update_expense', 'delete_expense',
    'get_settings', 'update_setting', 'get_setting',
    
    # Tables
    'create_tables', 'ensure_schema',
    
    # Maintenance
    'optimize_database', 'vacuum_database', 'get_database_stats',
    'rebuild_indexes', 'backup_database',
    'expire_old_points', 'expire_points_for_customer', 'check_and_recover',
    
    # Migrations
    'run_migrations', 'rollback_to_version', 'get_migration_status', 
    'fix_missing_columns', 'get_current_schema_version',
    'check_and_run_migrations',
    'get_app_version',
    'set_app_version',
    
    # Indexes
    'create_optimized_indexes', 'drop_optimized_indexes',
    'analyze_query_performance', 'create_suggested_indexes',
    'get_index_usage_stats',
    
    # Health
    'check_database_health',
    
    # Auto Maintenance
    'start_auto_maintenance', 'stop_auto_maintenance',
    
    # 🔥 Added
    'DatabaseManager',
]