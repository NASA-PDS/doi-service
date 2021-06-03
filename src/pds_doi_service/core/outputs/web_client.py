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
from pds_doi_service.core.util.config_parser import DOIConfigUtil


class DOIWebClient:
    """Abstract base class for clients of an HTTP DOI service endpoint"""
    _config_util = DOIConfigUtil()
    _service_name = None
    _web_parser = None
    _content_type_map = {}

    def _submit_content(self, payload, url, username, password,
                        content_type=CONTENT_TYPE_XML):
        """
        Submits a payload to a DOI service endpoint via the POST action.

        The action taken by the service is determined by the contents of the
        payload.

        Parameters
        ----------
        payload : str
            Payload to submit to the DOI service.
        url : str
            The URL of the DOI service endpoint.
        username : str
            The user name to authenticate to the DOI service as.
        password : str
            The password to authenticate to the DOI service with.
        content_type : str
            The content type to specify the format of the payload, as well as
            the format of the response from the endpoint.

        Returns
        -------
        response_text : str
            Body of the response text from the endpoint.

        """
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

    def submit_content(self, payload, content_type=CONTENT_TYPE_XML):
        """
        Submits the provided payload to a DOI service endpoint via the POST
        action.

        Inheritors of DOIWebClient should pull any required endpoint specific
        parameters (URL, username, password, etc...) from the configuration
        util bundled with the class.

        Inheritors should also take the extra step of parsing and returning any
        Doi objects from the response text (if request was successful).

        Parameters
        ----------
        payload : str
            Payload to submit to the DOI service.
        content_type : str
            The content type to specify the format of the payload, as well as
            the format of the response from the endpoint.

        Returns
        -------
        dois : list of Doi
            Doi objects parsed from the response text.
        response_text : str
            Body of the response text.

        """
        raise NotImplementedError(
            f'Subclasses of {self.__class__.__name__} must provide an '
            f'implementation for submit_content()'
        )

    def query_doi(self, query, content_type=CONTENT_TYPE_XML):
        """
        Queries the DOI endpoint for the status of one or more DOI submissions.

        Inheritors of DOIWebClient should pull any required endpoint specific
        parameters (URL, username, password, etc...) from the configuration
        util bundled with the class.

        Parameters
        ----------
        query : dict
            Key/value pairs to append as parameters to the URL for the GET
            endpoint.
        content_type : str
            The content type to specify the the format of the response from the
            endpoint.

        Returns
        -------
        response_text : str
            Body of the response text from the endpoint.

        """
        raise NotImplementedError(
            f'Subclasses of {self.__class__.__name__} must provide an '
            f'implementation for query_doi()'
        )
