# models/database/migrations_data.py
"""
Migration definitions with rollback support.
"""

from models.database.migration_manager import Migration

MIGRATIONS = [
    Migration(
        version="1.0.0",
        name="Initial Schema",
        description="Create all initial tables (handled by create_tables)",
        up_sql="SELECT 1;",
        down_sql="SELECT 1;"
    ),
    
    Migration(
        version="1.1.0",
        name="Add Credit Limit to Customers",
        description="Add credit_limit, current_balance, and remarks columns to customers table",
        up_sql="SELECT 1;",  # Columns are added via safe_add_column in migrations.py
        down_sql="SELECT 1;"
    ),
    
    Migration(
        version="1.2.0",
        name="Add Business Info to Settings",
        description="Add shop_phone, shop_address, shop_footer_message to settings",
        up_sql="""
            INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_phone', '');
            INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_address', '');
            INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_footer_message', '');
        """,
        down_sql="""
            DELETE FROM settings WHERE key IN ('shop_phone', 'shop_address', 'shop_footer_message');
        """
    ),
    
    Migration(
        version="1.3.0",
        name="Add User Roles Table",
        description="Create user_roles table and insert default roles",
        up_sql="""
            CREATE TABLE IF NOT EXISTS user_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                permissions TEXT,
                is_system INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            INSERT OR IGNORE INTO user_roles (name, description, permissions, is_system) VALUES 
            ('Admin', 'Full access to all features', 
             'dashboard,sales,sales_summary,products,inventory,receipts,customers,expense,reports,credit,users,settings,backup,add_product,edit_product,delete_product,add_customer,edit_customer,delete_customer,add_user,edit_user,delete_user,edit_settings,stock_in,stock_out,adjustment,refund_sale,delete_sale,view_users',
             1),
            ('Manager', 'Can manage sales, products, inventory, customers, expenses',
             'dashboard,sales,sales_summary,products,inventory,receipts,customers,expense,reports,credit,add_product,edit_product,add_customer,edit_customer,stock_in,stock_out,adjustment,refund_sale',
             0),
            ('Cashier', 'Can process sales and view receipts',
             'dashboard,sales,receipts,customers,add_customer,refund_sale',
             0),
            ('Viewer', 'Read-only access',
             'dashboard,sales_summary,reports',
             0);
        """,
        down_sql="""
            DROP TABLE IF EXISTS user_roles;
        """
    ),
    
    Migration(
        version="1.4.0",
        name="Add User Activity Log",
        description="Create user_activity_log table",
        up_sql="""
            CREATE TABLE IF NOT EXISTS user_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity_log(user_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_activity_action ON user_activity_log(action);
        """,
        down_sql="""
            DROP TABLE IF EXISTS user_activity_log;
        """,
        dependencies=["1.3.0"]
    ),
    
    Migration(
        version="1.5.0",
        name="Add COGS Columns to Sales",
        description="Add cogs, gross_profit, net_profit to sales table",
        up_sql="SELECT 1;",  # Columns are added via safe_add_column in migrations.py
        down_sql="SELECT 1;"
    ),
    
    Migration(
        version="1.6.0",
        name="Add Auto Backup Settings",
        description="Add auto backup settings to settings table",
        up_sql="""
            INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_backup_enabled', '0');
            INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_backup_interval', '24');
            INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_backup_max', '30');
        """,
        down_sql="""
            DELETE FROM settings WHERE key IN ('auto_backup_enabled', 'auto_backup_interval', 'auto_backup_max');
        """
    ),
    
    Migration(
        version="1.7.0",
        name="Add Product Locations Table",
        description="Support multiple locations per product",
        up_sql="""
            CREATE TABLE IF NOT EXISTS product_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                location TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                batch_no TEXT,
                expire_date TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE(product_id, location)
            );
            
            -- Migrate existing data from products table
            INSERT INTO product_locations (product_id, location, quantity)
            SELECT id, warehouse, stock 
            FROM products 
            WHERE warehouse IS NOT NULL AND warehouse != '' AND stock > 0;
            
            CREATE INDEX IF NOT EXISTS idx_product_locations_product ON product_locations(product_id);
            CREATE INDEX IF NOT EXISTS idx_product_locations_location ON product_locations(location);
        """,
        down_sql="""
            DROP TABLE IF EXISTS product_locations;
        """
    ),
    
    Migration(
        version="1.8.0",
        name="Add Location Column to Stock Movements",
        description="Add location column to stock_movements table",
        up_sql="SELECT 1;",  # Column is added via safe_add_column in migrations.py
        down_sql="SELECT 1;"
    ),
    
    Migration(
        version="1.9.0",
        name="Add Locations Table",
        description="Create locations table for better location management",
        up_sql="""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Insert existing locations from product_locations
            INSERT OR IGNORE INTO locations (name)
            SELECT DISTINCT location FROM product_locations 
            WHERE location IS NOT NULL AND location != '';
            
            -- Insert existing locations from products.warehouse
            INSERT OR IGNORE INTO locations (name)
            SELECT DISTINCT warehouse FROM products 
            WHERE warehouse IS NOT NULL AND warehouse != '';
            
            -- Add location_id columns
            -- These are added via safe_add_column in migrations.py
            
            CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name);
        """,
        down_sql="""
            DROP TABLE IF EXISTS locations;
        """,
        dependencies=["1.7.0"]
    ),
    
    Migration(
        version="2.0.0",
        name="Add Supplier Payments Table",
        description="Create supplier_payments table for tracking payments to suppliers",
        up_sql="""
            CREATE TABLE IF NOT EXISTS supplier_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                reference_no TEXT,
                payment_type TEXT DEFAULT 'Cash',
                notes TEXT,
                purchase_order_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE SET NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_supplier_payments_supplier ON supplier_payments(supplier_id, payment_date DESC);
            CREATE INDEX IF NOT EXISTS idx_supplier_payments_po ON supplier_payments(purchase_order_id);
        """,
        down_sql="""
            DROP TABLE IF EXISTS supplier_payments;
        """
    ),
    
    Migration(
        version="2.1.0",
        name="Add Expense Management Tables",
        description="Create expense_categories, expense_budgets, expense_notification_settings, expense_alerts_log, expense_attachments tables",
        up_sql="""
            -- Expense Categories
            CREATE TABLE IF NOT EXISTS expense_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Insert default categories
            INSERT OR IGNORE INTO expense_categories (name, description) VALUES 
            ('Rent', 'Office/Shop rent'),
            ('Utilities', 'Electricity, Water, Internet'),
            ('Salaries', 'Employee salaries'),
            ('Marketing', 'Advertising, Promotion'),
            ('Maintenance', 'Equipment repair'),
            ('Transport', 'Delivery, Fuel'),
            ('Office Supplies', 'Stationery, Printing'),
            ('Taxes', 'Government taxes'),
            ('Other', 'Miscellaneous expenses');
            
            -- Expense Budgets
            CREATE TABLE IF NOT EXISTS expense_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                budget_amount REAL NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, month, year)
            );
            
            -- Expense Notification Settings
            CREATE TABLE IF NOT EXISTS expense_notification_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enable_notifications INTEGER DEFAULT 1,
                warning_threshold INTEGER DEFAULT 80,
                check_frequency TEXT DEFAULT 'daily',
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            INSERT OR IGNORE INTO expense_notification_settings (enable_notifications, warning_threshold, check_frequency)
            VALUES (1, 80, 'daily');
            
            -- Expense Alerts Log
            CREATE TABLE IF NOT EXISTS expense_alerts_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                month INTEGER,
                year INTEGER,
                budget_amount REAL,
                actual_amount REAL,
                used_percentage REAL,
                alert_type TEXT,
                message TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Expense Attachments
            CREATE TABLE IF NOT EXISTS expense_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                uploaded_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_expense_categories_name ON expense_categories(name);
            CREATE INDEX IF NOT EXISTS idx_expense_budgets_category ON expense_budgets(category, year, month);
            CREATE INDEX IF NOT EXISTS idx_expense_alerts_category ON expense_alerts_log(category, year, month);
            CREATE INDEX IF NOT EXISTS idx_expense_alerts_read ON expense_alerts_log(is_read);
        """,
        down_sql="""
            DROP TABLE IF EXISTS expense_attachments;
            DROP TABLE IF EXISTS expense_alerts_log;
            DROP TABLE IF EXISTS expense_notification_settings;
            DROP TABLE IF EXISTS expense_budgets;
            DROP TABLE IF EXISTS expense_categories;
        """
    ),
    
    Migration(
        version="2.2.0",
        name="Add Credit Sales Tables",
        description="Create credit_sales and credit_payments tables",
        up_sql="""
            CREATE TABLE IF NOT EXISTS credit_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                balance_amount REAL NOT NULL,
                sale_date TEXT NOT NULL,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                sale_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
                FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE SET NULL
            );
            
            CREATE TABLE IF NOT EXISTS credit_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credit_sale_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                payment_method TEXT DEFAULT 'Cash',
                reference_no TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (credit_sale_id) REFERENCES credit_sales(id) ON DELETE CASCADE,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT
            );
            
            CREATE INDEX IF NOT EXISTS idx_credit_sales_customer ON credit_sales(customer_id, status);
            CREATE INDEX IF NOT EXISTS idx_credit_sales_invoice ON credit_sales(invoice_no);
            CREATE INDEX IF NOT EXISTS idx_credit_sales_status ON credit_sales(status);
            CREATE INDEX IF NOT EXISTS idx_credit_payments_customer ON credit_payments(customer_id, payment_date DESC);
            CREATE INDEX IF NOT EXISTS idx_credit_payments_credit_sale ON credit_payments(credit_sale_id);
        """,
        down_sql="""
            DROP TABLE IF EXISTS credit_payments;
            DROP TABLE IF EXISTS credit_sales;
        """
    ),
    
    Migration(
        version="2.3.0",
        name="Add Optimized Indexes",
        description="Create optimized indexes for better query performance",
        up_sql="""
            -- Products table indexes
            CREATE INDEX IF NOT EXISTS idx_products_category_price ON products(category, price);
            CREATE INDEX IF NOT EXISTS idx_products_name_price ON products(name, price);
            CREATE INDEX IF NOT EXISTS idx_products_stock_low ON products(stock, low_stock);
            
            -- Sales table indexes
            CREATE INDEX IF NOT EXISTS idx_sales_customer_date ON sales(customer_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_sales_status_date ON sales(status, created_at);
            CREATE INDEX IF NOT EXISTS idx_sales_payment_type ON sales(payment_type);
            
            -- Sales Items table indexes
            CREATE INDEX IF NOT EXISTS idx_sale_items_product_sale ON sale_items(product_name, sale_id);
            CREATE INDEX IF NOT EXISTS idx_sale_items_sale_product ON sale_items(sale_id, product_name);
            
            -- Customers table indexes
            CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
            CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
            CREATE INDEX IF NOT EXISTS idx_customers_points ON customers(points);
            
            -- Stock Movements table indexes
            CREATE INDEX IF NOT EXISTS idx_stock_movements_type_date ON stock_movements(type, created_at);
            CREATE INDEX IF NOT EXISTS idx_stock_movements_product_date ON stock_movements(product_id, created_at);
            
            -- Expenses table indexes
            CREATE INDEX IF NOT EXISTS idx_expenses_category_date ON expenses(category, expense_date);
            CREATE INDEX IF NOT EXISTS idx_expenses_amount ON expenses(amount);
            
            -- Credit Sales table indexes
            CREATE INDEX IF NOT EXISTS idx_credit_sales_status_date ON credit_sales(status, due_date);
            CREATE INDEX IF NOT EXISTS idx_credit_sales_customer_status ON credit_sales(customer_id, status);
            
            -- Supplier Payments table indexes
            CREATE INDEX IF NOT EXISTS idx_supplier_payments_date ON supplier_payments(payment_date DESC);
            CREATE INDEX IF NOT EXISTS idx_supplier_payments_type ON supplier_payments(payment_type);
            
            -- Product Locations table indexes
            CREATE INDEX IF NOT EXISTS idx_product_locations_quantity ON product_locations(quantity);
            CREATE INDEX IF NOT EXISTS idx_product_locations_expire ON product_locations(expire_date);
            
            -- User Activity Log indexes
            CREATE INDEX IF NOT EXISTS idx_activity_username ON user_activity_log(username);
            CREATE INDEX IF NOT EXISTS idx_activity_created ON user_activity_log(created_at DESC);
            
            -- Customer Points Log indexes
            CREATE INDEX IF NOT EXISTS idx_points_log_customer_date ON customer_points_log(customer_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_points_log_type ON customer_points_log(type);
            
            -- Purchase Orders indexes
            CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id);
            CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);
            CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date DESC);
            
            -- Purchase Order Items indexes
            CREATE INDEX IF NOT EXISTS idx_po_items_product ON purchase_order_items(product_id);
            CREATE INDEX IF NOT EXISTS idx_po_items_po ON purchase_order_items(po_id);
        """,
        down_sql="""
            -- Drop indexes (if needed)
            DROP INDEX IF EXISTS idx_products_category_price;
            DROP INDEX IF EXISTS idx_products_name_price;
            DROP INDEX IF EXISTS idx_products_stock_low;
            DROP INDEX IF EXISTS idx_sales_customer_date;
            DROP INDEX IF EXISTS idx_sales_status_date;
            DROP INDEX IF EXISTS idx_sales_payment_type;
            DROP INDEX IF EXISTS idx_sale_items_product_sale;
            DROP INDEX IF EXISTS idx_sale_items_sale_product;
            DROP INDEX IF EXISTS idx_customers_phone;
            DROP INDEX IF EXISTS idx_customers_email;
            DROP INDEX IF EXISTS idx_customers_points;
            DROP INDEX IF EXISTS idx_stock_movements_type_date;
            DROP INDEX IF EXISTS idx_stock_movements_product_date;
            DROP INDEX IF EXISTS idx_expenses_category_date;
            DROP INDEX IF EXISTS idx_expenses_amount;
            DROP INDEX IF EXISTS idx_credit_sales_status_date;
            DROP INDEX IF EXISTS idx_credit_sales_customer_status;
            DROP INDEX IF EXISTS idx_supplier_payments_date;
            DROP INDEX IF EXISTS idx_supplier_payments_type;
            DROP INDEX IF EXISTS idx_product_locations_quantity;
            DROP INDEX IF EXISTS idx_product_locations_expire;
            DROP INDEX IF EXISTS idx_activity_username;
            DROP INDEX IF EXISTS idx_activity_created;
            DROP INDEX IF EXISTS idx_points_log_customer_date;
            DROP INDEX IF EXISTS idx_points_log_type;
            DROP INDEX IF EXISTS idx_purchase_orders_supplier;
            DROP INDEX IF EXISTS idx_purchase_orders_status;
            DROP INDEX IF EXISTS idx_purchase_orders_date;
            DROP INDEX IF EXISTS idx_po_items_product;
            DROP INDEX IF EXISTS idx_po_items_po;
        """
    ),
]