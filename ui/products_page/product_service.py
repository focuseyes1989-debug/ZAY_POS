from PyQt6.QtCore import QDate
from models.database import connect_db
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from loguru import logger
from utils.activity_logger import log_activity
import csv


class ProductService:
    def __init__(self, parent=None):
        self.parent = parent

    def load_products(self, page=1, page_size=50, search_text="", category=""):
        use_category = category != "All Categories" and category != "အားလုံး"
        conn = connect_db()
        cursor = conn.cursor()

        count_params = []
        count_where = []
        if use_category:
            count_where.append("category = ?")
            count_params.append(category)
        if search_text:
            like = f'%{search_text}%'
            count_where.append("(LOWER(name) LIKE ? OR LOWER(sku) LIKE ? OR LOWER(barcode) LIKE ?)")
            count_params.extend([like, like, like])

        count_sql = "SELECT COUNT(*) FROM products"
        if count_where:
            count_sql += " WHERE " + " AND ".join(count_where)
        cursor.execute(count_sql, count_params)
        total_items = cursor.fetchone()[0]

        offset = (page - 1) * page_size
        select_params = []
        where_clauses = []
        if use_category:
            where_clauses.append("category = ?")
            select_params.append(category)
        if search_text:
            like = f'%{search_text}%'
            where_clauses.append("(LOWER(name) LIKE ? OR LOWER(sku) LIKE ? OR LOWER(barcode) LIKE ?)")
            select_params.extend([like, like, like])

        select_sql = """
            SELECT id, name, price, COALESCE(stock, 0) as stock, COALESCE(low_stock, 0) as low_stock, 
                   COALESCE(sold_by, 'Each') as sold_by, image
            FROM products
        """
        if where_clauses:
            select_sql += " WHERE " + " AND ".join(where_clauses)
        select_sql += " ORDER BY name LIMIT ? OFFSET ?"
        cursor.execute(select_sql, select_params + [page_size, offset])
        rows = cursor.fetchall()
        conn.close()
        return rows, total_items

    def filter_by_type(self, filter_type, page=1, page_size=50):
        conn = connect_db()
        cursor = conn.cursor()

        if filter_type == 'out_of_stock':
            cursor.execute("SELECT COUNT(*) FROM products WHERE (sold_by IS NULL OR sold_by != 'Service') AND COALESCE(stock, 0) = 0")
            total = cursor.fetchone()[0]
            offset = (page - 1) * page_size
            cursor.execute("""
                SELECT id, name, price, COALESCE(stock, 0) as stock, COALESCE(low_stock, 0) as low_stock,
                       COALESCE(sold_by, 'Each') as sold_by, image
                FROM products WHERE (sold_by IS NULL OR sold_by != 'Service') AND COALESCE(stock, 0) = 0
                ORDER BY name LIMIT ? OFFSET ?
            """, (page_size, offset))
            rows = cursor.fetchall()
        elif filter_type == 'low_stock':
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE (sold_by IS NULL OR sold_by != 'Service') 
                  AND COALESCE(stock, 0) > 0 
                  AND COALESCE(stock, 0) <= COALESCE(low_stock, 0)
            """)
            total = cursor.fetchone()[0]
            offset = (page - 1) * page_size
            cursor.execute("""
                SELECT id, name, price, COALESCE(stock, 0) as stock, COALESCE(low_stock, 0) as low_stock,
                       COALESCE(sold_by, 'Each') as sold_by, image
                FROM products 
                WHERE (sold_by IS NULL OR sold_by != 'Service') 
                  AND COALESCE(stock, 0) > 0 
                  AND COALESCE(stock, 0) <= COALESCE(low_stock, 0)
                ORDER BY name LIMIT ? OFFSET ?
            """, (page_size, offset))
            rows = cursor.fetchall()
        elif filter_type == 'expiring_soon':
            today = QDate.currentDate()
            today_str = today.toString("yyyy-MM-dd")
            week_later_str = today.addDays(7).toString("yyyy-MM-dd")
            cursor.execute("SELECT COUNT(*) FROM products WHERE expire_date >= ? AND expire_date <= ?", (today_str, week_later_str))
            total = cursor.fetchone()[0]
            offset = (page - 1) * page_size
            cursor.execute("""
                SELECT id, name, price, COALESCE(stock, 0) as stock, COALESCE(low_stock, 0) as low_stock,
                       COALESCE(sold_by, 'Each') as sold_by, image
                FROM products WHERE expire_date >= ? AND expire_date <= ?
                ORDER BY name LIMIT ? OFFSET ?
            """, (today_str, week_later_str, page_size, offset))
            rows = cursor.fetchall()
        elif filter_type == 'expired':
            today = QDate.currentDate()
            today_str = today.toString("yyyy-MM-dd")
            cursor.execute("SELECT COUNT(*) FROM products WHERE expire_date < ?", (today_str,))
            total = cursor.fetchone()[0]
            offset = (page - 1) * page_size
            cursor.execute("""
                SELECT id, name, price, COALESCE(stock, 0) as stock, COALESCE(low_stock, 0) as low_stock,
                       COALESCE(sold_by, 'Each') as sold_by, image
                FROM products WHERE expire_date < ?
                ORDER BY name LIMIT ? OFFSET ?
            """, (today_str, page_size, offset))
            rows = cursor.fetchall()
        else:
            rows, total = [], 0

        conn.close()
        return rows, total

    def export_products(self, rows, parent):
        if not rows:
            QMessageBox.warning(parent, "No Data", "No products to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(parent, "Export Products", "", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                headers = ["SKU", "Name", "Category", "Barcode", "Price", "Stock", "Sold By"]
                writer.writerow(headers)
                for row in rows:
                    conn = connect_db()
                    cursor = conn.cursor()
                    cursor.execute("SELECT sku, category FROM products WHERE id=?", (row[0],))
                    prod_data = cursor.fetchone()
                    conn.close()
                    if prod_data:
                        sku, category = prod_data
                        writer.writerow([sku or "", row[1], category or "", "", row[2], row[3], row[5]])
                    else:
                        writer.writerow(["", row[1], "", "", row[2], row[3], row[5]])
            QMessageBox.information(parent, "Success", f"Exported {len(rows)} products to {file_path}")
            logger.info(f"Exported {len(rows)} products")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(parent, "Error", f"Export failed: {e}")

    def import_products(self, parent, refresh_callback):
        file_path, _ = QFileDialog.getOpenFileName(parent, "Import Products", "", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                imported = 0
                updated = 0
                errors = []
                conn = connect_db()
                cursor = conn.cursor()
                for row_num, row in enumerate(reader, start=2):
                    if len(row) < 7:
                        errors.append(f"Row {row_num}: Insufficient columns")
                        continue
                    sku, name, category, barcode, price_str, stock_str, sold_by = row[:7]
                    try:
                        price = float(price_str) if price_str else 0.0
                        stock = int(stock_str) if stock_str else 0
                    except ValueError as e:
                        errors.append(f"Row {row_num}: Invalid number - {e}")
                        continue
                    try:
                        cursor.execute("SELECT id FROM products WHERE sku=?", (sku,))
                        existing = cursor.fetchone()
                        if existing:
                            cursor.execute("""
                                UPDATE products SET name=?, category=?, barcode=?, price=?, stock=?, sold_by=?
                                WHERE sku=?
                            """, (name, category, barcode, price, stock, sold_by, sku))
                            updated += 1
                        else:
                            cursor.execute("""
                                INSERT INTO products (sku, name, category, barcode, price, stock, sold_by, cost, low_stock)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
                            """, (sku, name, category, barcode, price, stock, sold_by))
                            imported += 1
                    except Exception as e:
                        errors.append(f"Row {row_num}: DB error - {e}")
                        continue
                conn.commit()
                conn.close()
                msg = f"Imported: {imported}\nUpdated: {updated}\nErrors: {len(errors)}"
                if errors:
                    error_details = "\n".join(errors[:10])
                    if len(errors) > 10:
                        error_details += f"\n... and {len(errors)-10} more errors."
                    QMessageBox.warning(parent, "Import Completed with Errors", f"{msg}\n\nError details:\n{error_details}")
                else:
                    QMessageBox.information(parent, "Import Complete", msg)
                logger.info(f"Import completed: {imported} new, {updated} updated, {len(errors)} errors")
                refresh_callback()
        except Exception as e:
            logger.error(f"Import failed: {e}")
            QMessageBox.critical(parent, "Error", f"Import failed: {e}")

    def log_activity(self, user_id, username, action, details):
        log_activity(user_id, username, action, details)