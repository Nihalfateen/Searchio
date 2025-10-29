"""Centralized logging configuration"""

import logging


def setup_logging(level: int = logging.DEBUG):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
