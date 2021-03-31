#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
==================
osti_web_client.py
==================

Contains client functions for interfacing with the OSTI DOI submission service.
It allows the user to submit a DOI object by communicating with a currently
running web server for DOI services.
"""

import pprint
import json
import requests
from requests.auth import HTTPBasicAuth

from pds_doi_service.core.outputs.osti import (CONTENT_TYPE_XML,
                                               CONTENT_TYPE_JSON,
                                               VALID_CONTENT_TYPES)
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.input.exceptions import OSTIRequestException
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser

logger = get_logger('pds_doi_service.core.outputs.osti_web_client')

CONTENT_TYPE_MAP = {
    CONTENT_TYPE_XML: 'application/xml',
    CONTENT_TYPE_JSON: 'application/json'
}
"""Mapping of content type constants to the corresponding MIME identifier"""

MAX_TOTAL_ROWS_RETRIEVE = 1000000000
"""Maximum numbers of rows to request from a query to OSTI"""


class DOIOstiWebClient:
    _web_parser = DOIOstiWebParser()

    def webclient_submit_existing_content(self, payload, i_url=None,
                                          i_username=None, i_password=None,
                                          content_type=CONTENT_TYPE_XML):
        """Submit the content (payload already in memory)."""
        if content_type not in VALID_CONTENT_TYPES:
            raise ValueError('Invalid content type requested, must be one of '
                             f'{",".join(VALID_CONTENT_TYPES)}')

        auth = HTTPBasicAuth(i_username, i_password)

        headers = {
            'Accept': CONTENT_TYPE_MAP[content_type],
            'Content-Type': CONTENT_TYPE_MAP[content_type]
        }

        osti_response = requests.post(i_url, auth=auth, data=payload, headers=headers)

        try:
            osti_response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            # Detail text is not always present, which can cause json parsing
            # issues
            details = (
                f'Details: {pprint.pformat(json.loads(osti_response.text))}'
                if osti_response.text else ''
            )

            raise OSTIRequestException(
                'DOI submission request to OSTI service failed, '
                f'reason: {str(http_err)}\n{details}'
            )

        # Re-use the parse functions from DOIOstiWebParser class to get the
        # list of Doi objects to return
        if content_type == CONTENT_TYPE_XML:
            doi, _ = self._web_parser.parse_osti_response_xml(osti_response.text)
        else:
            doi, _ = self._web_parser.parse_osti_response_json(osti_response.text)

        logger.debug(f"o_status {doi}")

        return doi, osti_response.text

    def webclient_query_doi(self, i_url, query_dict=None, i_username=None,
                            i_password=None, content_type=CONTENT_TYPE_XML):
        """
        Queries the status of a DOI from the OSTI server and returns the
        response text.

        The format of i_url is: https://www.osti.gov/iad2test/api/records/
        and will be appended by fields in query_dict:

            if query_dict = {'id':14108,'status':'Error'}
                then https://www.osti.gov/iad2test/api/records?id=14108&status=Error

            if query_dict = {'id'=1327397,'status'='Registered'}
                then https://www.osti.gov/iad2test/api/records?id=1327397&status=Registered
        """
        if content_type not in VALID_CONTENT_TYPES:
            raise ValueError('Invalid content type requested, must be one of '
                             f'{",".join(VALID_CONTENT_TYPES)}')

        auth = HTTPBasicAuth(i_username, i_password)

        headers = {
            'Accept': CONTENT_TYPE_MAP[content_type],
            'Content-Type': CONTENT_TYPE_MAP[content_type]
        }

        # OSTI server requires 'rows' field to know how many max rows to fetch at once.
        initial_payload = {'rows': MAX_TOTAL_ROWS_RETRIEVE}

        # If user provided a query_dict, append to our initial payload.
        if query_dict:
            initial_payload.update(query_dict)
            # Do a sanity check and only fetch valid field names.
            query_dict = self._web_parser.validate_field_names(initial_payload)
        else:
            query_dict = initial_payload

        logger.debug(f"initial_payload {initial_payload}")
        logger.debug(f"query_dict {query_dict}")
        logger.debug(f"i_url {i_url}")

        osti_response = requests.get(
            i_url, auth=auth, params=query_dict, headers=headers
        )

        try:
            osti_response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            # Detail text is not always present, which can cause json parsing
            # issues
            details = (
                f'Details: {pprint.pformat(json.loads(osti_response.text))}'
                if osti_response.text else ''
            )

            raise OSTIRequestException(
                'DOI submission request to OSTI service failed, '
                f'reason: {str(http_err)}\n{details}'
            )

        return osti_response.text
