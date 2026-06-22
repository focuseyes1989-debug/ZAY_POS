# models/database/queries.py
"""
Database query functions for CRUD operations.
"""

import sqlite3
from loguru import logger
from models.database.connection import DBContext


# ========== PRODUCTS ==========

def get_products(category=None, search=None, limit=None, offset=None):
    """Get products with optional filters."""
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if search:
        query += " AND (name LIKE ? OR sku LIKE ? OR barcode LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    query += " ORDER BY name"
    
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
    
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def get_product(product_id):
    """Get a single product by ID."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return cursor.fetchone()


def add_product(name, category=None, price=0, cost=0, stock=0, sku=None, barcode=None, 
                low_stock=0, description=None, sold_by="Each", image=None, supplier_id=None,
                unit=None, warehouse=None, batch_no=None, manufacture_date=None, expire_date=None):
    """Add a new product."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, category, description, sold_by, price, cost, sku, barcode,
                                 stock, expire_date, low_stock, image, supplier_id, unit, warehouse,
                                 batch_no, manufacture_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, category, description, sold_by, price, cost, sku, barcode,
              stock, expire_date, low_stock, image, supplier_id, unit, warehouse,
              batch_no, manufacture_date))
        conn.commit()
        return cursor.lastrowid


def update_product(product_id, **kwargs):
    """Update a product."""
    if not kwargs:
        return False
    
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    query = f"UPDATE products SET {set_clause}, last_updated = CURRENT_TIMESTAMP WHERE id = ?"
    
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute(query, list(kwargs.values()) + [product_id])
        conn.commit()
        return cursor.rowcount > 0


def delete_product(product_id):
    """Delete a product."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return cursor.rowcount > 0


# ========== SALES ==========

def get_sales(from_date=None, to_date=None, status='completed', limit=None, offset=None):
    """Get sales with optional filters."""
    query = """
        SELECT s.*, c.name as customer_name 
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE 1=1
    """
    params = []
    
    if status:
        query += " AND s.status = ?"
        params.append(status)
    
    if from_date:
        query += " AND date(s.created_at) >= ?"
        params.append(from_date)
    
    if to_date:
        query += " AND date(s.created_at) <= ?"
        params.append(to_date)
    
    query += " ORDER BY s.created_at DESC"
    
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
    
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def get_sale(sale_id):
    """Get a single sale by ID."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, c.name as customer_name 
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE s.id = ?
        """, (sale_id,))
        return cursor.fetchone()


def get_sale_items(sale_id):
    """Get items for a sale."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,))
        return cursor.fetchall()


def add_sale(invoice_no, total, payment, change_amount, customer_id=None, 
             payment_type='Cash', discount_amount=0, status='completed', items=None):
    """Add a new sale with items."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sales (invoice_no, total, payment, change_amount, customer_id,
                              payment_type, discount_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_no, total, payment, change_amount, customer_id,
              payment_type, discount_amount, status))
        sale_id = cursor.lastrowid
        
        # Add sale items
        if items:
            for item in items:
                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_name, qty, price, total, cost)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sale_id, item['product_name'], item['qty'], item['price'], 
                      item['total'], item.get('cost', 0)))
        
        conn.commit()
        return sale_id


def update_sale(sale_id, **kwargs):
    """Update a sale."""
    if not kwargs:
        return False
    
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    query = f"UPDATE sales SET {set_clause} WHERE id = ?"
    
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute(query, list(kwargs.values()) + [sale_id])
        conn.commit()
        return cursor.rowcount > 0


def delete_sale(sale_id):
    """Delete a sale (cascade will delete items)."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
        conn.commit()
        return cursor.rowcount > 0


# ========== CUSTOMERS ==========

def get_customers(search=None, limit=None, offset=None):
    """Get customers with optional filters."""
    query = "SELECT * FROM customers WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    query += " ORDER BY name"
    
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
    
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def get_customer(customer_id):
    """Get a single customer by ID."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        return cursor.fetchone()


def add_customer(name, phone=None, email=None, address=None, credit_limit=0, remarks=None):
    """Add a new customer."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customers (name, phone, email, address, credit_limit, remarks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone, email, address, credit_limit, remarks))
        conn.commit()
        return cursor.lastrowid


def update_customer(customer_id, **kwargs):
    """Update a customer."""
    if not kwargs:
        return False
    
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    query = f"UPDATE customers SET {set_clause} WHERE id = ?"
    
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute(query, list(kwargs.values()) + [customer_id])
        conn.commit()
        return cursor.rowcount > 0


def delete_customer(customer_id):
    """Delete a customer."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        return cursor.rowcount > 0


# ========== EXPENSES ==========

def get_expenses(from_date=None, to_date=None, category=None, limit=None, offset=None):
    """Get expenses with optional filters."""
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if from_date:
        query += " AND expense_date >= ?"
        params.append(from_date)
    
    if to_date:
        query += " AND expense_date <= ?"
        params.append(to_date)
    
    query += " ORDER BY expense_date DESC"
    
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
    
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def get_expense(expense_id):
    """Get a single expense by ID."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        return cursor.fetchone()


def add_expense(expense_no, category, description, amount, expense_date, 
                payment_method='Cash', reference_no=None, notes=None, image=None, created_by=None):
    """Add a new expense."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (expense_no, category, description, amount, expense_date,
                                 payment_method, reference_no, notes, image, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (expense_no, category, description, amount, expense_date,
              payment_method, reference_no, notes, image, created_by))
        conn.commit()
        return cursor.lastrowid


def update_expense(expense_id, **kwargs):
    """Update an expense."""
    if not kwargs:
        return False
    
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    query = f"UPDATE expenses SET {set_clause} WHERE id = ?"
    
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute(query, list(kwargs.values()) + [expense_id])
        conn.commit()
        return cursor.rowcount > 0


def delete_expense(expense_id):
    """Delete an expense."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return cursor.rowcount > 0


# ========== SETTINGS ==========

def get_settings():
    """Get all settings."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return dict(cursor.fetchall())


def get_setting(key, default=None):
    """Get a single setting."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default


def update_setting(key, value):
    """Update a setting."""
    with DBContext() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        return True