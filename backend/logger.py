"""
Logging configuration for zemixity backend
Provides structured logging with rotation and proper error tracking
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logger(name: str = "zemixity", level: str = None) -> logging.Logger:
    """
    Set up and configure logger

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Get log level from environment or use default
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        LOGS_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Error file handler (only errors and above)
    error_file_handler = RotatingFileHandler(
        LOGS_DIR / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(console_handler)

    return logger


# Create default logger instance
logger = setup_logger()


def log_request(method: str, path: str, status_code: int, duration_ms: float):
    """Log HTTP request"""
    logger.info(
        f"HTTP {method} {path} - {status_code} - {duration_ms:.2f}ms"
    )


def log_search(query: str, session_id: str, num_sources: int):
    """Log search query"""
    logger.info(
        f"Search query: '{query[:100]}...' | Session: {session_id} | Sources: {num_sources}"
    )


def log_error(error_type: str, error_message: str, context: dict = None):
    """Log error with context"""
    context_str = f" | Context: {context}" if context else ""
    logger.error(f"{error_type}: {error_message}{context_str}")


def log_file_upload(filename: str, file_size: int, mime_type: str, validated: bool):
    """Log file upload"""
    status = " Validated" if validated else " Rejected"
    logger.info(
        f"File upload: {filename} ({mime_type}, {file_size} bytes) - {status}"
    )


def log_database_operation(operation: str, table: str, record_id: str = None):
    """Log database operation"""
    id_str = f" | ID: {record_id}" if record_id else ""
    logger.debug(f"DB {operation}: {table}{id_str}")


def log_api_call(service: str, endpoint: str, duration_ms: float, success: bool):
    """Log external API call"""
    status = " Success" if success else " Failed"
    logger.info(
        f"API Call: {service} - {endpoint} - {duration_ms:.2f}ms - {status}"
    )


# Development mode: Add colored output
if os.getenv("ENVIRONMENT", "development") == "development":
    try:
        import colorlog

        # Replace console handler with colored version
        colored_handler = colorlog.StreamHandler()
        colored_handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        ))

        # Replace the console handler
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                logger.removeHandler(handler)

        logger.addHandler(colored_handler)
    except ImportError:
        # colorlog not installed, continue without colors
        pass


# Example usage:
if __name__ == "__main__":
    logger.info("Logger initialized successfully")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    log_search("test query", "session123", 10)
    log_file_upload("test.pdf", 1024000, "application/pdf", True)
    log_api_call("Google AI", "/generate", 150.5, True)
