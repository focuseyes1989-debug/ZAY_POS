# models/database/indexes.py
"""
Database index management functions.
"""

from loguru import logger
from models.database.connection import DBContext


def create_optimized_indexes():
    """
    Create all optimized indexes for better query performance.
    
    Returns:
        Dict with creation results
    """
    indexes = [
        # Products table
        ("idx_products_category_price", 
         "CREATE INDEX IF NOT EXISTS idx_products_category_price ON products(category, price)"),
        ("idx_products_name_price", 
         "CREATE INDEX IF NOT EXISTS idx_products_name_price ON products(name, price)"),
        ("idx_products_stock_low", 
         "CREATE INDEX IF NOT EXISTS idx_products_stock_low ON products(stock, low_stock)"),
        
        # Sales table
        ("idx_sales_customer_date", 
         "CREATE INDEX IF NOT EXISTS idx_sales_customer_date ON sales(customer_id, created_at)"),
        ("idx_sales_status_date", 
         "CREATE INDEX IF NOT EXISTS idx_sales_status_date ON sales(status, created_at)"),
        ("idx_sales_payment_type", 
         "CREATE INDEX IF NOT EXISTS idx_sales_payment_type ON sales(payment_type)"),
        
        # Sales Items table
        ("idx_sale_items_product_sale", 
         "CREATE INDEX IF NOT EXISTS idx_sale_items_product_sale ON sale_items(product_name, sale_id)"),
        ("idx_sale_items_sale_product", 
         "CREATE INDEX IF NOT EXISTS idx_sale_items_sale_product ON sale_items(sale_id, product_name)"),
        
        # Customers table
        ("idx_customers_phone", 
         "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)"),
        ("idx_customers_email", 
         "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)"),
        ("idx_customers_points", 
         "CREATE INDEX IF NOT EXISTS idx_customers_points ON customers(points)"),
        
        # Stock Movements table
        ("idx_stock_movements_type_date", 
         "CREATE INDEX IF NOT EXISTS idx_stock_movements_type_date ON stock_movements(type, created_at)"),
        ("idx_stock_movements_product_date", 
         "CREATE INDEX IF NOT EXISTS idx_stock_movements_product_date ON stock_movements(product_id, created_at)"),
        
        # Expenses table
        ("idx_expenses_category_date", 
         "CREATE INDEX IF NOT EXISTS idx_expenses_category_date ON expenses(category, expense_date)"),
        ("idx_expenses_amount", 
         "CREATE INDEX IF NOT EXISTS idx_expenses_amount ON expenses(amount)"),
        
        # Credit Sales table
        ("idx_credit_sales_status_date", 
         "CREATE INDEX IF NOT EXISTS idx_credit_sales_status_date ON credit_sales(status, due_date)"),
        ("idx_credit_sales_customer_status", 
         "CREATE INDEX IF NOT EXISTS idx_credit_sales_customer_status ON credit_sales(customer_id, status)"),
        
        # Supplier Payments table
        ("idx_supplier_payments_date", 
         "CREATE INDEX IF NOT EXISTS idx_supplier_payments_date ON supplier_payments(payment_date DESC)"),
        ("idx_supplier_payments_type", 
         "CREATE INDEX IF NOT EXISTS idx_supplier_payments_type ON supplier_payments(payment_type)"),
        
        # Product Locations table
        ("idx_product_locations_quantity", 
         "CREATE INDEX IF NOT EXISTS idx_product_locations_quantity ON product_locations(quantity)"),
        ("idx_product_locations_expire", 
         "CREATE INDEX IF NOT EXISTS idx_product_locations_expire ON product_locations(expire_date)"),
        
        # User Activity Log indexes
        ("idx_activity_username", 
         "CREATE INDEX IF NOT EXISTS idx_activity_username ON user_activity_log(username)"),
        ("idx_activity_created", 
         "CREATE INDEX IF NOT EXISTS idx_activity_created ON user_activity_log(created_at DESC)"),
        
        # Customer Points Log indexes
        ("idx_points_log_customer_date", 
         "CREATE INDEX IF NOT EXISTS idx_points_log_customer_date ON customer_points_log(customer_id, created_at DESC)"),
        ("idx_points_log_type", 
         "CREATE INDEX IF NOT EXISTS idx_points_log_type ON customer_points_log(type)"),
        
        # Purchase Orders indexes
        ("idx_purchase_orders_supplier", 
         "CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)"),
        ("idx_purchase_orders_status", 
         "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)"),
        ("idx_purchase_orders_date", 
         "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date DESC)"),
        
        # Purchase Order Items indexes
        ("idx_po_items_product", 
         "CREATE INDEX IF NOT EXISTS idx_po_items_product ON purchase_order_items(product_id)"),
        ("idx_po_items_po", 
         "CREATE INDEX IF NOT EXISTS idx_po_items_po ON purchase_order_items(po_id)"),
    ]
    
    results = {
        'created': [],
        'failed': [],
        'skipped': []
    }
    
    with DBContext() as conn:
        cursor = conn.cursor()
        
        for name, sql in indexes:
            try:
                # Check if index already exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (name,))
                if cursor.fetchone():
                    results['skipped'].append(name)
                    continue
                
                cursor.execute(sql)
                results['created'].append(name)
                logger.debug(f"Created index: {name}")
            except Exception as e:
                results['failed'].append({'name': name, 'error': str(e)})
                logger.error(f"Failed to create index {name}: {e}")
        
        conn.commit()
    
    logger.info(f"Created {len(results['created'])} indexes, skipped {len(results['skipped'])} existing, failed {len(results['failed'])}")
    return results


def drop_optimized_indexes():
    """Drop all optimized indexes."""
    indexes = [
        'idx_products_category_price',
        'idx_products_name_price', 
        'idx_products_stock_low',
        'idx_sales_customer_date',
        'idx_sales_status_date',
        'idx_sales_payment_type',
        'idx_sale_items_product_sale',
        'idx_sale_items_sale_product',
        'idx_customers_phone',
        'idx_customers_email',
        'idx_customers_points',
        'idx_stock_movements_type_date',
        'idx_stock_movements_product_date',
        'idx_expenses_category_date',
        'idx_expenses_amount',
        'idx_credit_sales_status_date',
        'idx_credit_sales_customer_status',
        'idx_supplier_payments_date',
        'idx_supplier_payments_type',
        'idx_product_locations_quantity',
        'idx_product_locations_expire',
        'idx_activity_username',
        'idx_activity_created',
        'idx_points_log_customer_date',
        'idx_points_log_type',
        'idx_purchase_orders_supplier',
        'idx_purchase_orders_status',
        'idx_purchase_orders_date',
        'idx_po_items_product',
        'idx_po_items_po'
    ]
    
    with DBContext() as conn:
        cursor = conn.cursor()
        dropped = 0
        
        for idx in indexes:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {idx}")
                dropped += 1
            except Exception as e:
                logger.error(f"Failed to drop index {idx}: {e}")
        
        conn.commit()
        logger.info(f"Dropped {dropped} indexes")
        return dropped


def analyze_query_performance():
    """
    Analyze which queries are slow and suggest indexes.
    """
    with DBContext() as conn:
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        suggestions = []
        
        for table in tables:
            # Check if table has indexes
            cursor.execute(f"PRAGMA index_list({table})")
            indexes = cursor.fetchall()
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Suggest indexes for foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            fks = cursor.fetchall()
            
            for fk in fks:
                fk_column = fk[3]  # 'from' column
                if fk_column in columns:
                    # Check if index exists for this column
                    has_index = False
                    for idx in indexes:
                        cursor.execute(f"PRAGMA index_info({idx[1]})")
                        idx_cols = [col[2] for col in cursor.fetchall()]
                        if fk_column in idx_cols:
                            has_index = True
                            break
                    
                    if not has_index:
                        suggestions.append({
                            'table': table,
                            'column': fk_column,
                            'type': 'foreign_key',
                            'sql': f"CREATE INDEX idx_{table}_{fk_column} ON {table}({fk_column});"
                        })
        
        return suggestions


def create_suggested_indexes():
    """
    Create suggested indexes for better performance.
    """
    suggestions = analyze_query_performance()
    
    if not suggestions:
        logger.info("No index suggestions found")
        return
    
    with DBContext() as conn:
        cursor = conn.cursor()
        created = 0
        
        for suggestion in suggestions:
            try:
                cursor.execute(suggestion['sql'])
                logger.info(f"Created index: {suggestion['sql']}")
                created += 1
            except Exception as e:
                logger.warning(f"Could not create index: {e}")
        
        conn.commit()
        logger.info(f"Created {created} new indexes")
        return created


def get_index_usage_stats():
    """
    Get statistics about index usage.
    """
    with DBContext() as conn:
        cursor = conn.cursor()
        
        # Get all indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        stats = {}
        for idx in indexes:
            # Get index info
            cursor.execute(f"PRAGMA index_info({idx})")
            columns = [col[2] for col in cursor.fetchall()]
            
            # Try to get index size
            try:
                cursor.execute(f"SELECT count(*) FROM {idx}")
                size = cursor.fetchone()[0]
            except:
                size = 0
            
            stats[idx] = {
                'columns': columns,
                'size': size
            }
        
        return stats


def check_indexes():
    """
    Check which indexes exist and their status.
    """
    with DBContext() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        indexes = cursor.fetchall()
        
        result = {
            'total': len(indexes),
            'indexes': []
        }
        
        for name, sql in indexes:
            # Get table name from sql
            table = 'unknown'
            if sql:
                import re
                match = re.search(r'ON\s+(\w+)', sql, re.IGNORECASE)
                if match:
                    table = match.group(1)
            
            result['indexes'].append({
                'name': name,
                'table': table,
                'sql': sql
            })
        
        return result