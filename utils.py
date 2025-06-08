from definitions import *


def init_default_logger(name: str) -> typing.Tuple[logging.Logger, Path]:
    """Initialise default logger with given name. It will generate a log file daily,
    keeping last 7 days backup.

    This will create a directory at LOGS_DIR_PATH / name
    and the log file will be a file in that directory called "log".

    Returns the newly created logger, and the directory Path"""

    logger = logging.getLogger(name)
    logs_dir_path = LOGS_DIR_PATH / name
    logs_dir_path.mkdir(parents=True, exist_ok=True)

    log_path = os.path.join(logs_dir_path, "log")
    logger.setLevel(LOG_LEVEL_DEFAULT)
    handler = TimedRotatingFileHandler(
        log_path, when="midnight", backupCount=LOG_NUM_DAYS_BACKUP_DEFAULT
    )
    handler.suffix = LOG_HANDLER_SUFFIX_DEFAULT
    handler.setLevel(LOG_LEVEL_DEFAULT)
    handler.setFormatter(LOG_FORMATTER_DEFAULT)
    logger.addHandler(handler)

    return logger, logs_dir_path
