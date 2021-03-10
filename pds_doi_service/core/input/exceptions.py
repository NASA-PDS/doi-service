#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
=============
exceptions.py
=============

Contains exception classes and functions for collecting and managing exceptions.
"""

from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_service.core.input.exceptions')


class InputFormatException(Exception):
    """Raised when an input file is not formatted as expected."""
    pass


class UnknownNodeException(Exception):
    """Raised when an unknown PDS Node identifier is provided."""
    pass


class UnknownLIDVIDException(Exception):
    """Raised when no corresponding DOI entry can be found for a given LIDVID."""
    pass


class NoTransactionHistoryForLIDVIDException(Exception):
    """Raised when no transaction database entry can be found for a given LIDVID."""
    pass


class DuplicatedTitleDOIException(Exception):
    """Raised when a DOI title has already been used with another LIDVID."""
    pass


class IllegalDOIActionException(Exception):
    """Raised when attempting to create or modify a DOI for an existing LIDVID."""
    pass


class UnexpectedDOIActionException(Exception):
    """
    Raised when a DOI has an unexpected status, or a requested action
    circumvents the expected DOI workflow.
    """
    pass


class TitleDoesNotMatchProductTypeException(Exception):
    """Raised when a DOI's title does not contain the product type."""
    pass


class CriticalDOIException(Exception):
    """Raised for any exceptions that are not handled with another class."""
    pass


class WarningDOIException(Exception):
    """
    Used to roll up multiple exceptions or warnings encountered while
    processing multiple DOI entries.
    """
    pass


class SiteURLNotExistException(Exception):
    """Raised when a DOI's site URL cannot be reached."""
    pass


class OSTIRequestException(Exception):
    """Raised when a request to the OSTI service fails."""


def collect_exception_classes_and_messages(single_exception,
                                           io_exception_classes,
                                           io_exception_messages):
    """
    Given a single exception, collect the exception class name and message.
    The variables io_exception_classes and io_exception_messages are both
    input and output.

    Parameters
    ----------
    single_exception : Exception
        The exception to collect the class and message for.
    io_exception_classes : list of str
        List to append the provided exception's class name to.
    io_exception_messages : list of str
        List to append the provided exception's message to.

    Returns
    -------
    io_exception_classes : list of str
        The updated list of exception class names.
    io_exception_messages : list of str
        The updated list of exception messages.

    """
    # ex: SiteURNotExistException
    actual_class_name = type(single_exception).__name__
    logger.debug("actual_class_name,type(actual_class_name) "
                 f"{actual_class_name},{type(actual_class_name)}")

    io_exception_classes.append(actual_class_name)

    # ex: "site_url http://mysite.example.com/link/to/my-dataset-id-25901.html not exist"
    io_exception_messages.append(str(single_exception))

    return io_exception_classes, io_exception_messages


def raise_or_warn_exceptions(exception_classes, exception_messages, log=False):
    """
    Raise a WarningDOIException or log a warning message that rolls up all the
    of the provided exception class names and messages.

    Parameters
    ----------
    exception_classes : list of str
        The list of exception class names to include in the WarningDOIException
    exception_messages : list of str
        The list of exception messages to include in the WarningDOIException
    log : bool
        If True, log the combined message as a warning, otherwise raise
        A WarningDOIException

    Raises
    ------
    WarningDOIException
        The single exception containing all the provided exception class names
        and messages.

    """
    message_to_raise = ''

    for ii in range(len(exception_classes)):
        if ii == 0:
            message_to_raise = (message_to_raise
                                + exception_classes[ii]
                                + ' : ' + exception_messages[ii])
        else:
            # Add a comma after every message.
            message_to_raise = (message_to_raise
                                + ', ' + exception_classes[ii]
                                + ' : ' + exception_messages[ii])

    if log:
        logger.warning(message_to_raise)
    else:
        raise WarningDOIException(message_to_raise)
