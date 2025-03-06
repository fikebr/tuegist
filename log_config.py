from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

cfg = Config()

LOG_FORMAT = "%(asctime)s %(levelname)s %(lineno)d - %(message)s"  # %(filename)s
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = cfg.logfile_path
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


# Usage:
# import logging
# from log import setup_logging
# setup_logging()
# logging.error("This is an error message")


def setup_logging():
    """
    Configure logging settings for the application.

    Logs are written to a rotating file with a maximum size of 10 MB.
    The log format includes the date, time, log level, line number, and message.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create the log directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating log directory: {e}")
            return

    # Set up the rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=LOG_FILE_MAX_SIZE, backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    # Also log to the console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)
