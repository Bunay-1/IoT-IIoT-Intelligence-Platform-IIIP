import logging
import sys
from typing import Optional

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Returns a configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    return logger

class LoggerMixin:
    """
    Mixin to add a logger property to a class.
    """
    @property
    def logger(self) -> logging.Logger:
        return get_logger(self.__class__.__name__)
