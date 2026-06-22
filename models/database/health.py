# models/database/health.py
"""
Database health monitoring.
"""

from loguru import logger
from models.database.connection import DBContext


def check_database_health():
    """
    Check database health.
    
    Returns:
        Dict with health status
    """
    health = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check 1: Connection test
    try:
        with DBContext() as conn:
            conn.execute("SELECT 1").fetchone()
        health['checks']['connection'] = {'status': 'pass'}
    except Exception as e:
        health['status'] = 'unhealthy'
        health['checks']['connection'] = {'status': 'fail', 'error': str(e)}
    
    # Check 2: Integrity
    try:
        with DBContext() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            health['checks']['integrity'] = {
                'status': 'pass' if result == 'ok' else 'fail',
                'result': result
            }
            if result != 'ok':
                health['status'] = 'unhealthy'
    except Exception as e:
        health['checks']['integrity'] = {'status': 'fail', 'error': str(e)}
        health['status'] = 'unhealthy'
    
    return health