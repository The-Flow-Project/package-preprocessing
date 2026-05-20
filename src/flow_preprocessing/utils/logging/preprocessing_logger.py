"""
Logger configuration for the flow-preprocessing package with loguru.
"""

import sys
from loguru import logger

# AIDEV-NOTE: Silence this package's logs by default — host apps opt in via logger.enable("flow_preprocessing").
# setup_logger() is intended for standalone use only, not when imported as a library.
logger.disable("flow_preprocessing")


def setup_logger(level: str = "DEBUG") -> None:
    """
    Configure the loguru logger with console and file handlers.

    Args:
        level: Log level for the console handler (default: "DEBUG").
    """
    logger.remove()

    diagnose = level == "DEBUG"

    # Console handler with colored output
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> |"
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
        backtrace=False,
        diagnose=diagnose,
        enqueue=False,  # stderr is fast; no need for async queue
    )

    logger.enable("flow_segmenter")
    logger.enable("pagexml_hf")

    logger.debug(f"Logger initialized with level: {level}")
