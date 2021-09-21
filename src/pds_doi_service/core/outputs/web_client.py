#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
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
from typing import Optional

import requests
from pds_doi_service.core.input.exceptions import WebRequestException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.web_parser import DOIWebParser
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from requests.auth import HTTPBasicAuth

WEB_METHOD_GET = "GET"
WEB_METHOD_POST = "POST"
WEB_METHOD_PUT = "PUT"
WEB_METHOD_DELETE = "DELETE"
VALID_WEB_METHODS = [WEB_METHOD_GET, WEB_METHOD_POST, WEB_METHOD_PUT, WEB_METHOD_DELETE]
"""Constants for HTTP method types"""


class DOIWebClient:
    """Abstract base class for clients of an HTTP DOI service endpoint"""

    _config_util = DOIConfigUtil()
    _service_name: Optional[str]
    _service_name = None
    _web_parser: Optional[DOIWebParser]
    _web_parser = None
    _content_type_map: dict[str, str] = {}

    def _submit_content(self, payload, url, username, password, method=WEB_METHOD_POST, content_type=CONTENT_TYPE_XML):
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
        method : str, optional
            The HTTP method type to use with the request. Should be one of
            GET, POST, PUT or DELETE. Defaults to POST.
        content_type : str, optional
            The content type to specify the format of the payload, as well as
            the format of the response from the endpoint. Defaults to
            xml.

        Returns
        -------
        response_text : str
            Body of the response text from the endpoint.

        """
        if method not in VALID_WEB_METHODS:
            raise ValueError("Invalid method requested, must be one of " f'{",".join(VALID_WEB_METHODS)}')

        if content_type not in self._content_type_map:
            raise ValueError(
                "Invalid content type requested, must be one of " f'{",".join(list(self._content_type_map.keys()))}'
            )

        auth = HTTPBasicAuth(username, password)

        headers = {"Accept": self._content_type_map[content_type], "Content-Type": self._content_type_map[content_type]}

        response = requests.request(method, url, auth=auth, data=payload, headers=headers)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            # Detail text is not always present, which can cause json parsing
            # issues
            details = f"Details: {pprint.pformat(response.text)}" if response.text else ""

            raise WebRequestException(
                f"DOI submission request to {self._service_name} service failed, " f"reason: {str(http_err)}\n{details}"
            )

        return response.text

    def submit_content(
        self, payload, url=None, username=None, password=None, method=WEB_METHOD_POST, content_type=CONTENT_TYPE_XML
    ):
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
            Payload to submit to the DOI service. Should only correspond
            to a single DOI record.
        url : str, optional
            The URL to submit the request to. If not submitted, it is pulled
            from the INI config for the appropriate service provider.
        username : str, optional
            The username to authenticate the request as. If not submitted, it
            is pulled from the INI config for the appropriate service provider.
        password : str, optional
            The password to authenticate the request with. If not submitted, it
            is pulled from the INI config for the appropriate service provider.
        method : str, optional
            The HTTP method type to use with the request. Should be one of
            GET, POST, PUT or DELETE. Defaults to POST.
        content_type : str, optional
            The content type to specify the format of the payload, as well as
            the format of the response from the endpoint. Defaults to xml.

        Returns
        -------
        doi : Doi
            Doi object parsed from the response text.
        response_text : str
            Body of the response text.

        """
        raise NotImplementedError(
            f"Subclasses of {self.__class__.__name__} must provide an " f"implementation for submit_content()"
        )

    def query_doi(self, query, url=None, username=None, password=None, content_type=CONTENT_TYPE_XML):
        """
        Queries the DOI endpoint for the status of a DOI submission.
        The query utilizes the GET HTTP method of the URL endpoint.

        Inheritors of DOIWebClient should pull any required endpoint specific
        parameters (URL, username, password, etc...) from the configuration
        util bundled with the class for optional arguments not provided by
        the user.

        Parameters
        ----------
        query : dict
            Key/value pairs to append as parameters to the URL for the GET
            endpoint.
        url : str, optional
            The URL to submit the request to. If not submitted, it is pulled
            from the INI config for the appropriate service provider.
        username : str, optional
            The username to authenticate the request as. If not submitted, it
            is pulled from the INI config for the appropriate service provider.
        password : str, optional
            The password to authenticate the request with. If not submitted, it
            is pulled from the INI config for the appropriate service provider.
        content_type : str, optional
            The content type to specify the the format of the response from the
            endpoint. Defaults to xml.

        Returns
        -------
        response_text : str
            Body of the response text from the endpoint.

        """
        raise NotImplementedError(
            f"Subclasses of {self.__class__.__name__} must provide an " f"implementation for query_doi()"
        )
