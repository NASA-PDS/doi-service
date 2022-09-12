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
import hashlib
import logging
import re
from html import escape
from html import unescape
from urllib.parse import quote
from urllib.parse import unquote
from urllib.parse import urlparse

from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.logging import get_logger as _get_logger

PDS3_URL_TEMPLATE = "https://pds.nasa.gov/ds-view/pds/viewDataset.jsp?dsid={identifier}"
"""The landing page URL template for PDS3 datasets"""

PDS4_URL_TEMPLATE = "https://pds.nasa.gov/ds-view/pds/view{product_type}.jsp?{identifier_query}{amp}{version_query}"
"""The landing page URL template for PDS4 datasets"""


def checksum(record_payload):
    """
    Returns a md5 checksum calculated from the provided DOI record payload.

    Parameters
    ----------
    record_payload : str
        Text contents of a DOI record to generate the checksum for.

    Returns
    -------
    hex_digest : str
        The hex digest of the md5 checksum.

    """
    md5 = hashlib.md5()
    md5.update(record_payload.encode())
    return md5.hexdigest()


def get_logger(module_name=None):
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
    module_name : str, optional
        If provided, the module name to create logger for. Defaults to the name
        of the current module.

    Returns
    -------
    logger : logging.logger
        The logger object.

    """
    config = DOIConfigUtil().get_config()
    logging_level = config.get("OTHER", "logging_level")
    return _get_logger(name=module_name, logging_level=logging_level)


logger = get_logger(__name__)


def parse_identifier_from_site_url(site_url):
    """
    For some records, the PDS identifier can be parsed from the site url as a
    last resort when the identifier cannot be obtained elsewhere from a label.

    Ex:
    PDS4: https://...?identifier=urn%3Anasa%3Apds%3Ainsight_cameras&amp;version=1.0
    PDS3: https://...?dsid=LRO-L-MRFLRO-2%2F3%2F5-BISTATIC-V1.0

    Parameters
    ----------
    site_url : str
        The site URL to parse an identifier from.

    Returns
    -------
    identifier : str
        The PDS3 or PDS4 identifier parsed from the provide site URL, if
        available. None otherwise.

    """
    identifier = None
    parsed_url = None

    try:
        parsed_url = urlparse(unescape(unquote(site_url)))
    except Exception as err:
        logger.warning('Could not parse provided URL "%s", Reason: %s', site_url, str(err))

    # Must have query portion for there to be any identifier to parse
    if parsed_url and parsed_url.query:
        parsed_query = parsed_url.query.split("&")

        id_token = parsed_query[0]

        # Determine if the query corresponds to a PDS3 or PDS4 identifier
        # PDS4
        if id_token.startswith("identifier="):
            lid = id_token.split("=")[-1]
            vid = None

            if len(parsed_query) > 1:
                version_token = parsed_query[-1]

                if version_token.startswith("version="):
                    vid = version_token.split("=")[-1]

            identifier = f"{lid}::{vid}" if vid else lid

            logger.debug('Parsed PDS4 LIDVID "%s" from site_url "%s"', identifier, site_url)
        # PDS3
        elif id_token.startswith("dsid="):
            identifier = id_token.split("=")[-1]

            logger.debug('Parsed PDS3 ID "%s" from site_url "%s"', identifier, site_url)
        else:
            logger.warning(
                'Could not parse identifier from URL "%s", URL does not conform to expected PDS3 or PDS4 format.',
                site_url,
            )

    return identifier


def is_pds4_identifier(identifier):
    """
    Determines if the provided identifier corresponds to the PDS4 LIDVID format
    or not.

    Parameters
    ----------
    identifier : str
        The identifier to check.

    Returns
    -------
    True if the identifier is a valid PDS4 identifier, False otherwise.

    """
    if identifier.startswith("urn:nasa:pds"):
        return True

    return False


def create_landing_page_url(identifier, product_type):
    """
    Creates the appropriate landing page URL for the provided identifier and
    product type.

    Parameters
    ----------
    identifier : str
        The identifier to create the URL for. Both PDS3 and PDS4 identifiers are
        supported.
    product_type : ProductType
        The product type to create the URL for.

    Returns
    -------
    site_url : str
        The landing page URL.

    """
    if is_pds4_identifier(identifier):
        logger.debug('Creating URL for PDS4 identifier "%s"', identifier)

        template = PDS4_URL_TEMPLATE

        lidvid_tokens = identifier.split("::")
        lid = lidvid_tokens[0]

        if len(lidvid_tokens) > 1:
            vid = lidvid_tokens[-1]
            site_url = template.format(
                product_type=product_type.value,
                identifier_query=f"identifier={quote(lid)}",
                amp="&",
                version_query=f"version={quote(vid)}",
            )
        else:
            site_url = template.format(
                product_type=product_type.value, identifier_query=f"identifier={quote(lid)}", amp="", version_query=""
            )
    else:
        logger.debug('Creating URL for PDS3 identifier "%s"', identifier)

        template = PDS3_URL_TEMPLATE
        site_url = template.format(identifier=quote(identifier))

    site_url = escape(site_url)
    logger.debug('Created URL "%s"', site_url)

    return site_url


def get_global_keywords():
    """
    Returns the global keywords (which should get assigned to each Doi object)
    from the INI config as a set.

    Returns
    -------
    global_keywords : set
        The set of global keywords as parsed from the INI. Any leading/trailing
        whitespace is removed from each keyword once its been parsed.

    """
    config = DOIConfigUtil().get_config()

    global_keyword_values = config.get("OTHER", "global_keyword_values")

    # Some older versions of the INI config delimited keywords by semi-colon,
    # so replace with comma here
    global_keyword_values = global_keyword_values.replace(";", ",")

    # Parse keywords into list
    global_keyword_list = global_keyword_values.split(",")

    # Convert all values to string, if for whatever reason a number is being used as a keyword
    global_keyword_list = map(str, global_keyword_list)

    # Sanitize any leading/trailing whitespace, then convert to a set
    global_keyword_set = set(map(str.strip, global_keyword_list))

    # It's possible for the empty string to sneak in in certain circumstances,
    # (trailing comma/semi-colon) so manually remove it, if present
    global_keyword_set.discard("")

    return global_keyword_set


def sanitize_json_string(string):
    """
    Cleans up extraneous whitespace and escape quotation marks from the provided string so it may
    be written to a JSON file. Extraneous whitespace include any before or after the provided
    string, as well as between words.

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
    stripped = re.sub(r"\s+", " ", string, flags=re.UNICODE).strip()

    # Now escape those quotation marks
    return re.sub(r'"', r"\"", stripped, flags=re.UNICODE)
