"""
File: logging.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Centralized logging configuration. Sets up standardized stream 
             handlers and formatters for the application and its dependencies.
"""

import logging
import sys


def configure_logging() -> None:
    """
    Configures the root logger and specific third-party loggers.
    Outputs to stdout with a clear timestamp-prefixed format.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    
    root = logging.getLogger()
    # Reset handlers to ensure no duplicates if called multiple times
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    
    # Ensure uvicorn access logs are captured at the same level
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
