# utils/logger.py
"""
Logging configuration for ZAY POS
"""

import sys
import os
from datetime import datetime
from loguru import logger


def setup_logging():
    """Setup logging configuration."""
    # Remove default handler
    logger.remove()
    
    # Create logs directory
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file name with date
    log_file = os.path.join(log_dir, f"zay_pos_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Console handler (for development)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True
    )
    
    # File handler (for production)
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Error file handler
    error_log_file = os.path.join(log_dir, f"zay_pos_errors_{datetime.now().strftime('%Y%m%d')}.log")
    logger.add(
        error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("Logging initialized")