#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
===============
general_util.py
===============

General utility functions for things like logging.
"""
import logging
import re

from pds_doi_service.core.util.config_parser import DOIConfigUtil


def sanitize_json_string(string):
    """
    Cleans up extraneous whitespace from the provided string so it may be
    written to a JSON file. Extraneous whitespace include any before or after
    the provided string, as well as between words.

    Parameters
    ----------
    string : str
        The string to sanitize.

    Returns
    -------
    string : str
        The provided string, sanitized of extraneous whitespace.

    """
    # Clean up whitespace (including line breaks) both between words and
    # at the ends of the string
    return re.sub(r"\s+", " ", string, flags=re.UNICODE).strip()


def get_logger(module_name=""):
    # If the user specifies the module name, we can use it.
    if module_name:
        logger = logging.getLogger(module_name)
    else:
        logger = logging.getLogger(__name__)

    my_format = "%(levelname)s %(name)s:%(funcName)s %(message)s"

    logging.basicConfig(format=my_format, filemode="a")

    config = DOIConfigUtil().get_config()
    logging_level = config.get("OTHER", "logging_level")
    logger.setLevel(getattr(logging, logging_level.upper()))

    return logger
