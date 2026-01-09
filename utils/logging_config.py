# utils/logging_config.py

import logging
import sys
from config import settings

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.logging.level)

    # Prevent adding duplicate handlers
    if not logger.handlers:
        # Console Handler
        if settings.logging.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(settings.logging.format)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # TODO: Add file handler based on config if needed
        # from logging.handlers import RotatingFileHandler
        # file_handler = RotatingFileHandler(
        #     settings.logging.file_path,
        #     maxBytes=settings.logging.max_file_size, # Needs parsing from string like "10MB"
        #     backupCount=settings.logging.backup_count
        # )
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

    return logger
