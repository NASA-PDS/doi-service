#
#  Copyright 2021 by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
======================
datacite_web_client.py
======================

Contains classes used to submit labels to the DataCite DOI service endpoint.
"""
import json
import pprint

import requests
from pds_doi_service.core.input.exceptions import WebRequestException
from pds_doi_service.core.outputs.datacite.datacite_web_parser import DOIDataCiteWebParser
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.web_client import DOIWebClient
from pds_doi_service.core.outputs.web_client import WEB_METHOD_GET
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST
from pds_doi_service.core.util.general_util import get_logger
from requests.auth import HTTPBasicAuth

logger = get_logger(__name__)


class DOIDataCiteWebClient(DOIWebClient):
    """
    Class used to submit HTTP requests to the DataCite DOI service.
    """

    _service_name = "DataCite"
    _web_parser = DOIDataCiteWebParser()
    _content_type_map = {CONTENT_TYPE_JSON: "application/vnd.api+json"}

    def submit_content(
        self, payload, url=None, username=None, password=None, method=WEB_METHOD_POST, content_type=CONTENT_TYPE_JSON
    ):
        """
        Submits a payload to the DataCite DOI service via the POST action.

        The action taken by the service is determined by the contents of the
        payload.

        Parameters
        ----------
        payload : str
            Payload to submit to the DataCite DOI service. Should correspond to
            an DataCite-format label file (JSON) containing a single DOI record.
        url : str, optional
            The URL to submit the request to. If not submitted, it is pulled
            from the INI config DATACITE url field.
        username : str, optional
            The username to authenticate the request as. If not submitted, it
            is pulled from the INI config DATACITE user field.
        password : str, optional
            The password to authenticate the request with. If not submitted, it
            is pulled from the INI config DATACITE password field.
        method : str, optional
            The HTTP method type to use with the request. Should be one of
            GET, POST, PUT or DELETE. Defaults to POST.
        content_type : str, optional
            The content type to specify the format of the payload, as well as
            the format of the response from OSTI. Currently, only 'json' is
            supported.

        Returns
        -------
        doi : Doi
            Doi object parsed from the response label from DataCite.
        response_text : str
            Body of the response label from DataCite.

        """
        config = self._config_util.get_config()

        response_text = super()._submit_content(
            payload,
            url=url or config.get("DATACITE", "url"),
            username=username or config.get("DATACITE", "user"),
            password=password or config.get("DATACITE", "password"),
            method=method,
            content_type=content_type,
        )

        dois, _ = self._web_parser.parse_dois_from_label(response_text)

        return dois[0], response_text

    def query_doi(self, query, url=None, username=None, password=None, content_type=CONTENT_TYPE_JSON):
        """
        Queries the DataCite DOI endpoint for the status of DOI submissions.

        Notes
        -----
        Queries are NOT automatically filtered by this method. Callers should be
        prepared to filter results as desired if more results are returned
        by their query than expected.

        Parameters
        ----------
        query : str or dict
            If a string is provided, it is used as the single query term to
            search against all fields of all submitted DOI entries.
            If a dictionary is provided, the key/value pairs are appended as
            specific query parameters to search against all submitted DOI entries.
        url : str, optional
            The URL to submit the request to. If not submitted, it is pulled
            from the INI config DATACITE url field.
        username : str, optional
            The username to authenticate the request as. If not submitted, it
            is pulled from the INI config DATACITE user field.
        password : str, optional
            The password to authenticate the request with. If not submitted, it
            is pulled from the INI config DATACITE password field.
        content_type : str
            The content type to specify the the format of the response from the
            endpoint. Only 'json' is currently supported.

        Returns
        -------
        response_text : str
            Body of the response text from the DataCite endpoint.

        """
        config = self._config_util.get_config()

        if content_type not in self._content_type_map:
            raise ValueError(
                "Invalid content type requested, must be one of " f'{",".join(list(self._content_type_map.keys()))}'
            )

        auth = HTTPBasicAuth(username or config.get("DATACITE", "user"), password or config.get("DATACITE", "password"))

        headers = {"Accept": self._content_type_map[content_type]}

        if isinstance(query, dict):
            query_string = " ".join([f"{k}:{v}" for k, v in query.items()])
        else:
            query_string = str(query)

        url = url or config.get("DATACITE", "url")

        logger.debug("query_string: %s", query_string)
        logger.debug("url: %s", url)

        datacite_response = requests.request(
            WEB_METHOD_GET, url=url, auth=auth, headers=headers, params={"query": query_string}
        )

        try:
            datacite_response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            # Detail text is not always present, which can cause json parsing
            # issues
            details = f"Details: {pprint.pformat(json.loads(datacite_response.text))}" if datacite_response.text else ""

            raise WebRequestException(
                "DOI submission request to OSTI service failed, " f"reason: {str(http_err)}\n{details}"
            )

        return datacite_response.text
