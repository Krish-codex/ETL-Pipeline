"""
Logger Setup Module
===================
Sets up a centralized logging system for the entire ETL pipeline.

Why logging instead of just print()?
- Logs are saved to a file so we can debug issues later
- Each log entry has a timestamp, making it easy to track when things happened
- We can set log levels (DEBUG, INFO, WARNING, ERROR) to filter what we see
- This is how real-world data pipelines handle monitoring

"""

import logging
import os
import sys

# Configure Windows terminal to print Unicode characters and Emojis properly
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Add parent directory to path so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_DIR, LOG_FILE


def get_logger(name: str) -> logging.Logger:
    """
    Creates and returns a configured logger instance.

    Args:
        name: Name of the logger (usually the module name like 'fetch_data')

    Returns:
        A configured logging.Logger object
    """
    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)

    # Create a logger with the given name
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding duplicate handlers if get_logger is called multiple times
    if logger.handlers:
        return logger

    # File handler — writes all logs to a file for later review
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    # Console handler — shows logs in the terminal while pipeline runs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Log format: timestamp | level | module | message
    # This format makes it easy to grep through logs when debugging
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
