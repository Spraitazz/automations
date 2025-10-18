import os
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler

from core.paths import PROJECT_ROOT_DIR

LOGS_DIR = PROJECT_ROOT_DIR / "logs"

LOG_LEVEL_DEFAULT = logging.DEBUG
LOG_FORMATTER_DEFAULT = logging.Formatter(
    "%(asctime)s - %(name)s - [%(filename)30s:%(lineno)4s - %(funcName)30s()] "
    "- %(levelname)s - %(message)s"
)
LOG_HANDLER_SUFFIX_DEFAULT = "%Y%m%d"
LOG_NUM_DAYS_BACKUP_DEFAULT = 7


def init_default_logger(name: str) -> tuple[logging.Logger, Path]:
    """
    Initialise default logger with given name. It will generate a log file daily,
    keeping last 7 days backup.

    This will create a directory at LOGS_DIR/ name
    and the log file will be a file in that directory called "log".

    Returns the newly created logger, and the directory Path
    """
    logger = logging.getLogger(name)
    logs_dir = LOGS_DIR / name
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_path = os.path.join(logs_dir, "log")
    logger.setLevel(LOG_LEVEL_DEFAULT)
    handler = TimedRotatingFileHandler(
        log_path, when="midnight", backupCount=LOG_NUM_DAYS_BACKUP_DEFAULT
    )
    handler.suffix = LOG_HANDLER_SUFFIX_DEFAULT
    handler.setLevel(LOG_LEVEL_DEFAULT)
    handler.setFormatter(LOG_FORMATTER_DEFAULT)
    logger.addHandler(handler)

    return logger, logs_dir
