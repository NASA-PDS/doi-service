import logging
from typing import Optional


def get_logger(name: Optional[str] = None, logging_level: int = logging.INFO):
    """
    Creates and returns a logging object for the provided module name. The
    logger is configured according to the settings of the INI config.

    Notes
    -----
    This function should be defined first in this module, so we can
    use it to define a logger object for use with the other general_util
    functions.

    Parameters
    ----------
    name : str, optional
        If provided, the name to create logger for. Defaults to the name of the current module.
    logging_level: int, optional
        If provided, the logging level.  Defaults to INFO

    Returns
    -------
    logger : logging.logger
        The logger object.

    """
    if name is not None:
        _logger = logging.getLogger(name)
    else:
        _logger = logging.getLogger(__name__)

    log_format = "%(levelname)s %(name)s:%(funcName)s %(message)s"
    logging.basicConfig(format=log_format, filemode="a")
    _logger.setLevel(logging_level)

    return _logger
