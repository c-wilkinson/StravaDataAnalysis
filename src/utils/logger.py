"""
Central logger configuration.
"""

import logging
import sys

LOGGER = logging.getLogger("StravaDataAnalysis")
LOGGER.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)


def get_logger() -> logging.Logger:
    """
    Returns the shared logger instance.
    """
    return LOGGER
