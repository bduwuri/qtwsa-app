import logging

from typing import Literal

LoggingLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

APPLICATION_LOGGER = "qtwsa_app"


def configure_logger(level: LoggingLevel = "INFO"):
    logger = logging.getLogger(APPLICATION_LOGGER)
    logger.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s [%(process)d] [%(name)s] [%(levelname)s] %(message)s",
        datefmt="[%Y-%m-%d %H:%M:%S %z]",
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def get_logger(module_name: str) -> logging.Logger:
    """Convenience function to return an application logger.

    Example:

    >>> logger = get_logger(__name__)
    """
    l_name = f"{APPLICATION_LOGGER}.{module_name}"
    return logging.getLogger(l_name)
