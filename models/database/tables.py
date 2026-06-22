# models/database/tables.py
"""
Database table creation and schema management.
"""

import os
import hashlib
from loguru import logger
from datetime import datetime, timedelta
from models.database.connection import DBContext

def create_tables():
    """Create all necessary tables and indexes if they don't exist."""
    with DBContext() as conn:
        cursor = conn.cursor()
        logger.info("Creating/verifying database tables...")

        # ---------- Products ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            description TEXT,
            sold_by TEXT DEFAULT 'Each',
            price REAL DEFAULT 0,
            cost REAL DEFAULT 0,
            sku TEXT,
            barcode TEXT,
            stock INTEGER DEFAULT 0,
            expire_date TEXT,
            low_stock INTEGER DEFAULT 0,
            image TEXT,
            supplier_id INTEGER,
            unit TEXT,
            warehouse TEXT,
            batch_no TEXT,
            manufacture_date TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("PRAGMA table_info(products)")
        cols = [c[1] for c in cursor.fetchall()]
        new_prod_cols = {
            'unit': 'TEXT', 'warehouse': 'TEXT', 'batch_no': 'TEXT',
            'manufacture_date': 'TEXT', 'last_updated': 'TIMESTAMP', 'supplier_id': 'INTEGER'
        }
        for col, dtype in new_prod_cols.items():
            if col not in cols:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {dtype}")
                logger.debug(f"Added column {col} to products table")

        # ---------- Sales ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT,
            total REAL,
            payment REAL,
            change_amount REAL,
            customer_id INTEGER,
            status TEXT DEFAULT 'completed',
            payment_type TEXT,
            discount_amount REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cogs REAL DEFAULT 0,
            gross_profit REAL DEFAULT 0,
            net_profit REAL DEFAULT 0
        )
        """)
        cursor.execute("PRAGMA table_info(sales)")
        sales_cols = [c[1] for c in cursor.fetchall()]
        missing_sales_cols = ['customer_id', 'status', 'payment_type', 'discount_amount', 
                             'cogs', 'gross_profit', 'net_profit']
        for col in missing_sales_cols:
            if col not in sales_cols:
                if col == 'customer_id':
                    cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER")
                elif col == 'status':
                    cursor.execute("ALTER TABLE sales ADD COLUMN status TEXT DEFAULT 'completed'")
                elif col == 'payment_type':
                    cursor.execute("ALTER TABLE sales ADD COLUMN payment_type TEXT")
                elif col == 'discount_amount':
                    cursor.execute("ALTER TABLE sales ADD COLUMN discount_amount REAL DEFAULT 0")
                elif col == 'cogs':
                    cursor.execute("ALTER TABLE sales ADD COLUMN cogs REAL DEFAULT 0")
                elif col == 'gross_profit':
                    cursor.execute("ALTER TABLE sales ADD COLUMN gross_profit REAL DEFAULT 0")
                elif col == 'net_profit':
                    cursor.execute("ALTER TABLE sales ADD COLUMN net_profit REAL DEFAULT 0")
                logger.debug(f"Added column {col} to sales table")

        # ---------- Sale Items ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_name TEXT,
            qty INTEGER,
            price REAL,
            total REAL,
            cost REAL DEFAULT 0
        )
        """)
        cursor.execute("PRAGMA table_info(sale_items)")
        sale_items_cols = [c[1] for c in cursor.fetchall()]
        if 'cost' not in sale_items_cols:
            cursor.execute("ALTER TABLE sale_items ADD COLUMN cost REAL DEFAULT 0")
            logger.debug("Added cost column to sale_items table")

        # ---------- Categories ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """)

        # ---------- Customers ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            total_visit INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0,
            points INTEGER DEFAULT 0,
            points_expiry_date TEXT,
            credit_limit REAL DEFAULT 0,
            current_balance REAL DEFAULT 0,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("PRAGMA table_info(customers)")
        cust_cols = [c[1] for c in cursor.fetchall()]
        missing_cust_cols = {
            'points_expiry_date': 'TEXT',
            'credit_limit': 'REAL DEFAULT 0',
            'current_balance': 'REAL DEFAULT 0',
            'remarks': 'TEXT'
        }
        for col, dtype in missing_cust_cols.items():
            if col not in cust_cols:
                cursor.execute(f"ALTER TABLE customers ADD COLUMN {col} {dtype}")
                logger.debug(f"Added column {col} to customers table")
        for col in ['total_visit', 'total_spent', 'points']:
            if col not in cust_cols:
                cursor.execute(f"ALTER TABLE customers ADD COLUMN {col} INTEGER DEFAULT 0")
                logger.debug(f"Added column {col} to customers table")

        # ---------- Payment Types ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1
        )
        """)
        cursor.execute("SELECT COUNT(*) FROM payment_types")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO payment_types (name) VALUES (?)", [("Cash",), ("Card",), ("Mobile Money",)])
            logger.info("Initialized default payment types")

        # ---------- Settings ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        default_settings = [
            ('tax_rate', '0'), ('tax_enabled', '0'),
            ('loyalty_points_per_dollar', '0'), ('loyalty_min_points_for_reward', '100'),
            ('loyalty_reward_discount', '5'), ('discount_enabled', '0'),
            ('discount_type', 'percentage'), ('discount_value', '0'),
            ('currency', 'Kyats (Ks)'),
            ('shop_name', 'ZAY POS'), ('shop_logo', ''),
            ('shop_phone', ''), ('shop_address', ''), ('shop_footer_message', ''),
            ('receipt_header', ''), ('receipt_footer', ''), ('show_customer_name', '1'),
            ('language', 'en'), ('theme', 'Light'),
            ('points_expiry_months', '12'), ('points_dollar_value', '0.01'),
            ('follow_system_theme', '1'),
            ('auto_backup_enabled', '0'), ('auto_backup_interval', '24'), ('auto_backup_max', '30')
        ]
        for key, val in default_settings:
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

        # ---------- Suppliers ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            company_name TEXT,
            tax_number TEXT,
            website TEXT,
            payment_terms TEXT,
            bank_account TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("PRAGMA table_info(suppliers)")
        supp_cols = [c[1] for c in cursor.fetchall()]
        new_supp_cols = {
            'company_name': 'TEXT', 'tax_number': 'TEXT', 'website': 'TEXT',
            'payment_terms': 'TEXT', 'bank_account': 'TEXT', 'status': 'TEXT DEFAULT "Active"'
        }
        for col, dtype in new_supp_cols.items():
            if col not in supp_cols:
                cursor.execute(f"ALTER TABLE suppliers ADD COLUMN {col} {dtype}")
                logger.debug(f"Added column {col} to suppliers table")

        # ---------- Stock Movements ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            type TEXT,
            quantity INTEGER,
            old_stock INTEGER,
            new_stock INTEGER,
            reason TEXT,
            reference TEXT,
            created_by TEXT,
            notes TEXT,
            supplier_id INTEGER,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("PRAGMA table_info(stock_movements)")
        sm_cols = [c[1] for c in cursor.fetchall()]
        if 'notes' not in sm_cols:
            cursor.execute("ALTER TABLE stock_movements ADD COLUMN notes TEXT")
            logger.debug("Added column notes to stock_movements table")
        if 'supplier_id' not in sm_cols:
            cursor.execute("ALTER TABLE stock_movements ADD COLUMN supplier_id INTEGER")
            logger.debug("Added supplier_id column to stock_movements table")
        if 'location' not in sm_cols:
            cursor.execute("ALTER TABLE stock_movements ADD COLUMN location TEXT")
            logger.debug("Added location column to stock_movements table")

        # ---------- Purchase Orders ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_no TEXT UNIQUE,
            supplier_id INTEGER,
            order_date TEXT,
            total_amount REAL,
            status TEXT DEFAULT 'pending',
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'Unpaid',
            received_by TEXT,
            invoice_attachment TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("PRAGMA table_info(purchase_orders)")
        po_cols = [c[1] for c in cursor.fetchall()]
        new_po_cols = {
            'discount': 'REAL', 'tax': 'REAL', 'payment_status': 'TEXT DEFAULT "Unpaid"',
            'received_by': 'TEXT', 'invoice_attachment': 'TEXT', 'notes': 'TEXT'
        }
        for col, dtype in new_po_cols.items():
            if col not in po_cols:
                cursor.execute(f"ALTER TABLE purchase_orders ADD COLUMN {col} {dtype}")
                logger.debug(f"Added column {col} to purchase_orders table")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            total REAL
        )
        """)

        # ---------- Supplier Payments ----------
        cursor.execute("""
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
        )
        """)

        # ---------- Expenses ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_no TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL,
            payment_method TEXT DEFAULT 'Cash',
            reference_no TEXT,
            notes TEXT,
            image TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("PRAGMA table_info(expenses)")
        expense_cols = [c[1] for c in cursor.fetchall()]
        if 'image' not in expense_cols:
            cursor.execute("ALTER TABLE expenses ADD COLUMN image TEXT")
            logger.debug("Added image column to expenses table")

        # ---------- Expense Categories ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("SELECT COUNT(*) FROM expense_categories")
        if cursor.fetchone()[0] == 0:
            default_categories = [
                ('Rent', 'Office/Shop rent'),
                ('Utilities', 'Electricity, Water, Internet'),
                ('Salaries', 'Employee salaries'),
                ('Marketing', 'Advertising, Promotion'),
                ('Maintenance', 'Equipment repair'),
                ('Transport', 'Delivery, Fuel'),
                ('Office Supplies', 'Stationery, Printing'),
                ('Taxes', 'Government taxes'),
                ('Other', 'Miscellaneous expenses')
            ]
            cursor.executemany("INSERT INTO expense_categories (name, description) VALUES (?, ?)", default_categories)
            logger.info("Default expense categories created")

        # ---------- Expense Budgets ----------
        cursor.execute("""
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
        )
        """)

        # ---------- Expense Notification Settings ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_notification_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enable_notifications INTEGER DEFAULT 1,
            warning_threshold INTEGER DEFAULT 80,
            check_frequency TEXT DEFAULT 'daily',
            last_checked TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("SELECT COUNT(*) FROM expense_notification_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO expense_notification_settings (enable_notifications, warning_threshold, check_frequency)
                VALUES (1, 80, 'daily')
            """)
            logger.info("Default expense notification settings created")

        # ---------- Expense Alerts Log ----------
        cursor.execute("""
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
        )
        """)

        # ---------- Expense Attachments ----------
        cursor.execute("""
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
        )
        """)

        # ---------- Credit Sales ----------
        cursor.execute("""
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
        )
        """)
        cursor.execute("PRAGMA table_info(credit_sales)")
        credit_sales_cols = [c[1] for c in cursor.fetchall()]
        if 'sale_id' not in credit_sales_cols:
            cursor.execute("ALTER TABLE credit_sales ADD COLUMN sale_id INTEGER")
            logger.debug("Added sale_id column to credit_sales table")

        # ---------- Credit Payments ----------
        cursor.execute("""
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
        )
        """)

        # ---------- Product Locations ----------
        cursor.execute("""
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
        )
        """)

        # ---------- Locations ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("""
        INSERT OR IGNORE INTO locations (name)
        SELECT DISTINCT location FROM product_locations 
        WHERE location IS NOT NULL AND location != ''
        """)
        cursor.execute("""
        INSERT OR IGNORE INTO locations (name)
        SELECT DISTINCT warehouse FROM products 
        WHERE warehouse IS NOT NULL AND warehouse != ''
        """)

        # ---------- Users ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'cashier',
            full_name TEXT,
            salt TEXT,
            force_password_change INTEGER DEFAULT 0,
            permissions TEXT,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("PRAGMA table_info(users)")
        user_cols = [c[1] for c in cursor.fetchall()]
        if 'salt' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN salt TEXT")
            logger.debug("Added salt column to users table")
        if 'force_password_change' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN force_password_change INTEGER DEFAULT 0")
            logger.debug("Added force_password_change column to users table")
        if 'permissions' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT")
            logger.debug("Added permissions column to users table")
        if 'last_login' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
            logger.debug("Added last_login column to users table")
        if 'is_active' not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
            logger.debug("Added is_active column to users table")

        # ---------- User Roles Table ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            permissions TEXT,
            is_system INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create default roles
        cursor.execute("SELECT COUNT(*) FROM user_roles")
        if cursor.fetchone()[0] == 0:
            default_roles = [
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
                 0),
            ]
            for name, desc, perms, is_system in default_roles:
                cursor.execute("""
                    INSERT INTO user_roles (name, description, permissions, is_system)
                    VALUES (?, ?, ?, ?)
                """, (name, desc, perms, is_system))
            logger.info("Default user roles created")

        # ---------- Fix Existing Admin User Role ----------
        cursor.execute("SELECT id, username, role FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        if admin:
            if admin[2] != 'Admin':
                cursor.execute("UPDATE users SET role = 'Admin' WHERE username = 'admin'")
                logger.info("Fixed admin user role from 'admin' to 'Admin'")

        # Insert default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            salt_bytes = os.urandom(32)
            salt_hex = salt_bytes.hex()
            password_hash = hashlib.pbkdf2_hmac('sha256', 'admin'.encode(), salt_bytes, 100000).hex()
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, full_name, salt, force_password_change, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("admin", password_hash, "Admin", "Administrator", salt_hex, 0, 1))
            logger.info("Default admin user created with role 'Admin'")

        # ---------- Customer Points Log ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_points_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            points INTEGER NOT NULL,
            type TEXT NOT NULL,
            reference TEXT,
            expiry_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        )
        """)

        # ---------- User Activity Log ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
        """)

        # ---------- Default category ----------
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO categories (name) VALUES ('General')")
            logger.info("Default category 'General' created")

        # ---------- Indexes ----------
        logger.debug("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_invoice_no ON sales(invoice_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_status ON sales(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_product_id ON stock_movements(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_log_customer ON customer_points_log(customer_id, created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity_log(user_id, created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_action ON user_activity_log(action)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_payments_supplier ON supplier_payments(supplier_id, payment_date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_categories_name ON expense_categories(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_credit_sales_customer ON credit_sales(customer_id, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_credit_payments_customer ON credit_payments(customer_id, payment_date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_locations_product ON product_locations(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_locations_location ON product_locations(location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name)")

        # ---------- Add default cost and stock values for existing products ----------
        cursor.execute("UPDATE products SET cost = 0 WHERE cost IS NULL")
        cursor.execute("UPDATE products SET stock = 0 WHERE stock IS NULL")
        cursor.execute("UPDATE products SET low_stock = 0 WHERE low_stock IS NULL")
        
        conn.commit()
        logger.info("Database tables and indexes verified/created successfully")
        
        # ---------- Run Migrations ----------
        from models.database.migrations import run_migrations, fix_missing_columns
        try:
            run_migrations()
            fix_missing_columns()
        except Exception as e:
            logger.error(f"Migration failed: {e}")


def ensure_schema():
    """Ensure database schema exists and is up to date."""
    create_tables()