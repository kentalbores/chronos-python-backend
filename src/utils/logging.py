# llm-hub/llm-hub/app/utils/logging.py
import logging
import sys
from logging import Filter, LogRecord
from typing import Optional

# Import colorlog
import colorlog

# Define a standard log format (colorlog will prepend color codes)
LOG_FORMAT_BASE = "%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s"
# Define a date format for logs
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Define log colors
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red,bg_white",
}


# Optional: Filter to add extra context like request ID if available
# (Requires integration with middleware later if needed)
class RequestIdFilter(Filter):
    def __init__(self, name: str = "", request_id: Optional[str] = None):
        super().__init__(name)
        self.request_id = request_id

    def filter(self, record: LogRecord) -> bool:
        # This is a placeholder; actual request ID injection needs middleware
        record.request_id = self.request_id or "N/A"
        # If you use request_id in LOG_FORMAT, ensure it's handled correctly
        # For example, add %(request_id)s to LOG_FORMAT_BASE
        return True


def setup_logging(log_level: str = "INFO"):
    """
    Configures the root logger for the application with colored output.

    Args:
        log_level (str): The minimum log level to capture
        (e.g., "DEBUG", "INFO", "WARNING", "ERROR"). Defaults to "INFO".
    """
    log_level_upper = log_level.upper()
    numeric_level = getattr(logging, log_level_upper, None)
    if not isinstance(numeric_level, int):
        # Fallback to INFO if invalid level is provided
        print(
            f"Warning: Invalid log level '{log_level}'. Defaulting to INFO.",
            file=sys.stderr,
        )
        numeric_level = logging.INFO
        log_level_upper = "INFO"

    # Create colorlog formatter
    # The %(log_color)s placeholder is where colorlog injects the color codes
    formatter = colorlog.ColoredFormatter(
        f"%(log_color)s{LOG_FORMAT_BASE}",
        datefmt=DATE_FORMAT,
        reset=True,  # Resets the color after each log message
        log_colors=LOG_COLORS,
        secondary_log_colors={},  # Optional: for coloring parts of the message
        style="%",  # Use %-style formatting
    )

    # Create handler (StreamHandler for console output)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    # Optional: Add the RequestIdFilter if you plan to implement request tracing
    # handler.addFilter(RequestIdFilter())

    # Get the root logger
    root_logger = logging.getLogger()

    # Clear existing handlers from the root logger to avoid duplicate outputs
    # or conflicts if this function is called multiple times.
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Add the new handler
    root_logger.addHandler(handler)
    # Set the level on the root logger
    root_logger.setLevel(numeric_level)

    # No longer using basicConfig directly, as we've manually configured the root logger
    # logging.basicConfig(...) would try to set up its own handlers.

    # Log confirmation message using the configured logger
    # Get a logger specific to this module
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"Logging configured with level {log_level_upper} and colors.")


"""--- How to use in other modules ---
    import logging
    logger = logging.getLogger(__name__) # Get logger for the current module

    Example usage:
    def my_function():
        logger.debug("Detailed information, typically of interest only when diagnosing problems.")  # noqa
        logger.info("Confirmation that things are working as expected.")
        logger.warning("An indication that something unexpected happened.")
        try:
            x = 1 / 0
        except ZeroDivisionError:
            logger.error("Due to a more serious problem, the software has not been able to perform some function.", exc_info=True)  # noqa
        logger.critical("A serious error, indicating that the program itself may be unable to continue running.")   # noqa
"""
