# models/database/__init__.py
"""
Database module with connection pooling and ORM-like functionality.
"""

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
    check_and_run_migrations,  # ✅ New: Auto-migration function
    get_app_version,           # ✅ New: Get app version
    set_app_version            # ✅ New: Set app version
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
    'check_and_run_migrations',  # ✅ New
    'get_app_version',           # ✅ New
    'set_app_version',           # ✅ New
    
    # Indexes
    'create_optimized_indexes', 'drop_optimized_indexes',
    'analyze_query_performance', 'create_suggested_indexes',
    'get_index_usage_stats',
    
    # Health
    'check_database_health',
    
    # Auto Maintenance
    'start_auto_maintenance', 'stop_auto_maintenance'
]