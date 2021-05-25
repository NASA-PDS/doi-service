#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
=============
web_client.py
=============

Contains the abstract base class for interfacing with a DOI submission service
endpoint.
"""

import pprint
import json
import requests
from requests.auth import HTTPBasicAuth

from pds_doi_service.core.input.exceptions import WebRequestException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML


class DOIWebClient:
    _service_name = None
    _web_parser = None
    _content_type_map = {}

    def submit_content(self, payload, url, username, password,
                       content_type=CONTENT_TYPE_XML):
        if content_type not in self._content_type_map:
            raise ValueError('Invalid content type requested, must be one of '
                             f'{",".join(list(self._content_type_map.keys()))}')

        auth = HTTPBasicAuth(username, password)

        headers = {
            'Accept': self._content_type_map[content_type],
            'Content-Type': self._content_type_map[content_type]
        }

        response = requests.post(url, auth=auth, data=payload, headers=headers)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            # Detail text is not always present, which can cause json parsing
            # issues
            details = (
                f'Details: {pprint.pformat(json.loads(response.text))}'
                if response.text else ''
            )

            raise WebRequestException(
                f'DOI submission request to {self._service_name} service failed, '
                f'reason: {str(http_err)}\n{details}'
            )

        return response.text

    def query_doi(self, url, query, username, password,
                  content_type=CONTENT_TYPE_XML):
        raise NotImplementedError(
            'Subclasses of DOIWebClient must provide an implementation for '
            'query_doi()'
        )
