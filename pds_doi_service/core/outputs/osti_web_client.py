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

from pds_doi_service.core.input.exceptions import WebRequestException
from pds_doi_service.core.outputs.doi_record import (CONTENT_TYPE_XML,
                                                     CONTENT_TYPE_JSON)
from pds_doi_service.core.outputs.web_client import DOIWebClient
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOIOstiWebClient(DOIWebClient):
    _service_name = 'OSTI'
    _web_parser = DOIOstiWebParser()
    _content_type_map = {
        CONTENT_TYPE_XML: 'application/xml',
        CONTENT_TYPE_JSON: 'application/json'
    }

    MAX_TOTAL_ROWS_RETRIEVE = 1000000000
    """Maximum numbers of rows to request from a query to OSTI"""

    def submit_content(self, payload, url, username, password,
                       content_type=CONTENT_TYPE_XML):
        response_text = super().submit_content(
            payload, url, username, password, content_type
        )

        # Re-use the parse functions from DOIOstiWebParser class to get the
        # list of Doi objects to return
        if content_type == CONTENT_TYPE_XML:
            dois, _ = self._web_parser.parse_osti_response_xml(response_text)
        else:
            dois, _ = self._web_parser.parse_osti_response_json(response_text)

        return dois, response_text

    def query_doi(self, url, query, username, password,
                  content_type=CONTENT_TYPE_XML):
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
        if content_type not in self._content_type_map:
            raise ValueError('Invalid content type requested, must be one of '
                             f'{",".join(list(self._content_type_map.keys()))}')

        auth = HTTPBasicAuth(username, password)

        headers = {
            'Accept': self._content_type_map[content_type],
            'Content-Type': self._content_type_map[content_type]
        }

        # OSTI server requires 'rows' field to know how many max rows to fetch at once.
        initial_payload = {'rows': self.MAX_TOTAL_ROWS_RETRIEVE}

        # If user provided a query_dict, append to our initial payload.
        if query:
            initial_payload.update(query)
            # Do a sanity check and only fetch valid field names.
            query_dict = self._web_parser.validate_field_names(initial_payload)
        else:
            query_dict = initial_payload

        logger.debug("initial_payload: %s", initial_payload)
        logger.debug("query_dict: %s", query_dict)
        logger.debug("i_url: %s", url)

        osti_response = requests.get(
            url, auth=auth, params=query_dict, headers=headers
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

            raise WebRequestException(
                'DOI submission request to OSTI service failed, '
                f'reason: {str(http_err)}\n{details}'
            )

        return osti_response.text
