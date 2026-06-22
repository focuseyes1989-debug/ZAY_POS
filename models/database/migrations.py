# models/database/migrations.py
"""
Database migration entry point with auto-update support.
"""

from loguru import logger
from models.database.migration_manager import MigrationManager
from models.database.migrations_data import MIGRATIONS


def get_app_version() -> str:
    """
    Get current application version.
    
    ✅ Bug #4 Fixed: Read from app_metadata or settings
    """
    # Try to get from app_metadata first
    manager = MigrationManager()
    try:
        manager.connect()
        metadata = manager.get_app_metadata()
        if metadata:
            return metadata['app_version']
    except:
        pass
    finally:
        manager.close()
    
    # Fallback: try to get from settings
    try:
        from models.database.queries import get_setting
        app_version = get_setting('app_version', '1.0.0')
        return app_version
    except:
        return '1.0.0'


def set_app_version(version: str):
    """Set application version."""
    try:
        from models.database.queries import update_setting
        update_setting('app_version', version)
    except:
        pass


def run_migrations(target_version: str = None, app_version: str = None) -> dict:
    """
    Run all pending migrations.
    
    Args:
        target_version: Optional version to migrate to
        app_version: Current application version
        
    Returns:
        Dict with migration results
    """
    manager = MigrationManager()
    
    try:
        manager.connect()
        
        # Get app version if not provided
        if not app_version:
            app_version = get_app_version()
        
        return manager.run_migrations(MIGRATIONS, target_version, app_version)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return {'applied': [], 'failed': [{'version': 'unknown', 'error': str(e)}]}
    finally:
        manager.close()


def rollback_to_version(target_version: str) -> dict:
    """
    Rollback migrations to a specific version.
    
    Args:
        target_version: Version to rollback to
        
    Returns:
        Dict with rollback results
    """
    manager = MigrationManager()
    
    try:
        manager.connect()
        return manager.rollback_to_version(MIGRATIONS, target_version)
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return {'rolled_back': [], 'failed': [{'version': 'unknown', 'error': str(e)}]}
    finally:
        manager.close()


def get_migration_status() -> dict:
    """
    Get current migration status.
    
    Returns:
        Dict with migration status
    """
    manager = MigrationManager()
    
    try:
        manager.connect()
        return manager.get_migration_status(MIGRATIONS)
    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        return None
    finally:
        manager.close()


def fix_missing_columns():
    """Fix missing columns without version tracking."""
    manager = MigrationManager()
    
    try:
        manager.connect()
        
        # Safe column additions
        safe_additions = [
            ('customers', 'credit_limit', 'REAL DEFAULT 0'),
            ('customers', 'current_balance', 'REAL DEFAULT 0'),
            ('customers', 'remarks', 'TEXT'),
            ('sales', 'cogs', 'REAL DEFAULT 0'),
            ('sales', 'gross_profit', 'REAL DEFAULT 0'),
            ('sales', 'net_profit', 'REAL DEFAULT 0'),
            ('sale_items', 'cost', 'REAL DEFAULT 0'),
            ('expenses', 'image', 'TEXT'),
            ('stock_movements', 'location', 'TEXT'),
            ('products', 'last_updated', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
        ]
        
        for table, column, column_def in safe_additions:
            manager.safe_add_column(table, column, column_def)
        
        # Safe settings
        safe_settings = [
            ('shop_phone', ''),
            ('shop_address', ''),
            ('shop_footer_message', ''),
            ('auto_backup_enabled', '0'),
            ('auto_backup_interval', '24'),
            ('auto_backup_max', '30'),
            ('app_version', '1.0.0'),
        ]
        
        for key, value in safe_settings:
            manager.safe_add_setting(key, value)
        
        manager.conn.commit()
        logger.info("Fixed missing columns and settings")
        
    except Exception as e:
        logger.error(f"Failed to fix missing columns: {e}")
        if manager.conn:
            manager.conn.rollback()
    finally:
        manager.close()


def check_and_run_migrations():
    """
    Check app version and run migrations automatically.
    
    ✅ Bug #4 Fixed: Auto-migration on startup
    """
    logger.info("Checking for pending migrations...")
    
    status = get_migration_status()
    if not status:
        logger.warning("Could not get migration status")
        return
    
    if status['pending']:
        logger.info(f"Found {len(status['pending'])} pending migrations: {status['pending']}")
        
        # Get app version
        app_version = get_app_version()
        logger.info(f"Current app version: {app_version}")
        
        # Run migrations
        result = run_migrations(app_version=app_version)
        
        if result['applied']:
            logger.info(f"Applied {len(result['applied'])} migrations: {result['applied']}")
            
            # Update app version in app_metadata
            manager = MigrationManager()
            try:
                manager.connect()
                manager.update_app_metadata(
                    app_version=app_version,
                    db_version=result['applied'][-1],
                    notes=f"Auto migration on startup: {len(result['applied'])} migrations applied"
                )
            except Exception as e:
                logger.error(f"Failed to update app metadata: {e}")
            finally:
                manager.close()
        elif result['failed']:
            logger.error(f"Failed migrations: {result['failed']}")
    else:
        logger.info("No pending migrations found. Database is up to date.")


# ✅ Bug #4 Fixed: CLI with auto-migration
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Tool")
    parser.add_argument("command", choices=["up", "down", "status", "fix", "auto"],
                       help="Migration command")
    parser.add_argument("--target", help="Target version")
    parser.add_argument("--app-version", help="Application version")
    
    args = parser.parse_args()
    
    if args.command == "status":
        status = get_migration_status()
        if status:
            print("=" * 60)
            print("DATABASE MIGRATION STATUS")
            print("=" * 60)
            print(f"App Version     : {status.get('app_version', 'Unknown')}")
            print(f"DB Version      : {status['current_version']}")
            print(f"Applied         : {len(status['applied'])}")
            print(f"Pending         : {len(status['pending'])}")
            print(f"Failed          : {len(status['failed'])}")
            print(f"Total           : {status['total']}")
            if status['pending']:
                print(f"\nPending versions: {', '.join(status['pending'])}")
            if status['failed']:
                print(f"\nFailed versions: {', '.join(status['failed'])}")
            if status.get('last_updated'):
                print(f"Last Updated    : {status['last_updated']}")
            print("=" * 60)
    
    elif args.command == "up":
        result = run_migrations(args.target, args.app_version)
        print(f"Applied: {result['applied']}")
        if result['failed']:
            print(f"Failed: {result['failed']}")
    
    elif args.command == "down":
        if not args.target:
            print("Target version required for rollback")
        else:
            result = rollback_to_version(args.target)
            print(f"Rolled back: {result['rolled_back']}")
            if result['failed']:
                print(f"Failed: {result['failed']}")
    
    elif args.command == "fix":
        fix_missing_columns()
        print("Fixed missing columns and settings")
    
    elif args.command == "auto":
        check_and_run_migrations()
        print("Auto-migration completed")