# models/database/auto_maintenance.py
"""
Automated database maintenance.
"""

import threading
import time
from datetime import datetime
from loguru import logger
from models.database.maintenance import optimize_database, vacuum_database


class DatabaseMaintenanceScheduler:
    """Automated database maintenance scheduler."""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_maintenance = None
        self.maintenance_interval = 3600  # 1 hour
    
    def start(self):
        """Start the maintenance scheduler."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Database maintenance scheduler started")
    
    def stop(self):
        """Stop the maintenance scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Database maintenance scheduler stopped")
    
    def _run(self):
        """Maintenance loop."""
        while self.running:
            try:
                self._perform_maintenance()
                time.sleep(self.maintenance_interval)
            except Exception as e:
                logger.error(f"Maintenance failed: {e}")
                time.sleep(60)
    
    def _perform_maintenance(self):
        """Perform maintenance tasks."""
        # Check if maintenance is needed
        if self.last_maintenance:
            time_diff = datetime.now() - self.last_maintenance
            if time_diff.total_seconds() < self.maintenance_interval:
                return
        
        logger.info("Starting database maintenance...")
        optimize_database()
        self.last_maintenance = datetime.now()
        logger.info("Database maintenance completed")


# Global scheduler instance
_maintenance_scheduler = DatabaseMaintenanceScheduler()


def start_auto_maintenance():
    """Start automatic database maintenance."""
    _maintenance_scheduler.start()


def stop_auto_maintenance():
    """Stop automatic database maintenance."""
    _maintenance_scheduler.stop()