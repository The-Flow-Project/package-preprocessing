"""
Logger configuration for the flow-preprocessing package with loguru.
"""
from flow_segmenter import setup_logger as segmenter_setup_logger
from loguru import logger
from pathlib import Path
import sys


def setup_logger(level: str = "DEBUG", log_files: bool = False) -> None:
    """
    Configure the loguru logger with console and file handlers.

    Args:
        level: Log level for the console handler (default: "DEBUG").
        log_files: Write logging to files (defaults: False).
    """
    try:
        logger.remove(0)
    except ValueError:
        pass  # Default handler doesn't exist

    diagnose = True if level == "DEBUG" else False

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

    # File handler for all logs with rotation
    if log_files:
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            logs_dir / "flow-preprocessing.log",
            rotation="5 MB",
            retention="10 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            backtrace=True,
            diagnose=diagnose,
            enqueue=True,  # Thread-safe async logging
        )

        # Separate error log file
        logger.add(
            logs_dir / "flow-preprocessing_errors.log",
            rotation="5 MB",
            retention="30 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            backtrace=True,
            diagnose=diagnose,
            enqueue=True,
        )

    segmenter_setup_logger(level=level, log_files=log_files)

    logger.debug(f"Logger initialized with level: {level}")
