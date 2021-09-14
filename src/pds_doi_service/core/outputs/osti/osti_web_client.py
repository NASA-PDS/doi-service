#
#  Copyright 2021, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
==================
osti_web_client.py
==================

Contains classes used to submit labels to the OSTI DOI service endpoint.
"""
import json
import pprint

import requests
from pds_doi_service.core.input.exceptions import WebRequestException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.osti.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.outputs.web_client import DOIWebClient
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST
from pds_doi_service.core.util.general_util import get_logger
from requests.auth import HTTPBasicAuth

logger = get_logger(__name__)


class DOIOstiWebClient(DOIWebClient):
    """
    Class used to submit HTTP requests to the OSTI DOI service.
    """

    _service_name = "OSTI"
    _web_parser = DOIOstiWebParser()
    _content_type_map = {CONTENT_TYPE_XML: "application/xml", CONTENT_TYPE_JSON: "application/json"}

    ACCEPTABLE_FIELD_NAMES_LIST = [
        "id",
        "doi",
        "accession_number",
        "published_before",
        "published_after",
        "added_before",
        "added_after",
        "updated_before",
        "updated_after",
        "first_registered_before",
        "first_registered_after",
        "last_registered_before",
        "last_registered_after",
        "status",
        "start",
        "rows",
        "sort",
        "order",
    ]

    MAX_TOTAL_ROWS_RETRIEVE = 1000000000
    """Maximum numbers of rows to request from a query to OSTI"""

    def submit_content(
        self, payload, url=None, username=None, password=None, method=WEB_METHOD_POST, content_type=CONTENT_TYPE_XML
    ):
        """
        Submits a payload to the OSTI DOI service via the POST action.

        The action taken by the service is determined by the contents of the
        payload.

        The OSTI endpoint URL and authentication credentials for the request
        are automatically pulled from the configuration file.

        Parameters
        ----------
        payload : str
            Payload to submit to the OSTI DOI service. Should correspond to
            an OSTI-format label file containing a single DOI record.
        url : str, optional
            The URL to submit the request to. If not submitted, it is pulled
            from the INI config OSTI url field.
        username : str, optional
            The username to authenticate the request as. If not submitted, it
            is pulled from the INI config OSTI user field.
        password : str, optional
            The password to authenticate the request with. If not submitted, it
            is pulled from the INI config OSTI password field.
        method : str, optional
            The HTTP method type to use with the request. Should be one of
            GET, POST, PUT or DELETE. Defaults to POST.
        content_type : str, optional
            The content type to specify the format of the payload, as well as
            the format of the response from OSTI. Currently, 'xml' and 'json'
            are supported. Defaults to xml.

        Returns
        -------
        doi : Doi
            Doi object parsed from the response label from OSTI.
        response_text : str
            Body of the response label from OSTI.

        """
        config = self._config_util.get_config()

        response_text = super()._submit_content(
            payload,
            url=url or config.get("OSTI", "url"),
            username=username or config.get("OSTI", "user"),
            password=password or config.get("OSTI", "password"),
            method=method,
            content_type=content_type,
        )

        # Re-use the parse functions from DOIOstiWebParser class to get the
        # list of Doi objects to return
        dois, _ = self._web_parser.parse_dois_from_label(response_text, content_type)

        return dois[0], response_text

    def query_doi(self, query, url=None, username=None, password=None, content_type=CONTENT_TYPE_XML):
        """
        Queries the status of a DOI from the OSTI server and returns the
        response text.

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
            is pulled from the INI config OSTI user field.
        password : str, optional
            The password to authenticate the request with. If not submitted, it
            is pulled from the INI config OSTI password field.
        content_type : str, optional
            The content type to specify the format of the payload, as well as
            the format of the response from OSTI. Currently, 'xml' and 'json'
            are supported. Defaults to xml.

        Returns
        -------
        response_text : str
            Body of the response text from the endpoint.

        """
        config = self._config_util.get_config()

        if content_type not in self._content_type_map:
            raise ValueError(
                "Invalid content type requested, must be one of " f'{",".join(list(self._content_type_map.keys()))}'
            )

        auth = HTTPBasicAuth(username or config.get("OSTI", "user"), password or config.get("OSTI", "password"))

        headers = {"Accept": self._content_type_map[content_type], "Content-Type": self._content_type_map[content_type]}

        # OSTI server requires 'rows' field to know how many max rows to fetch at once.
        initial_payload = {"rows": self.MAX_TOTAL_ROWS_RETRIEVE}

        # If user provided a query_dict, append to our initial payload.
        if query:
            initial_payload.update(query)
            # Do a sanity check and only fetch valid field names.
            query = self._validate_field_names(initial_payload)
        else:
            query = initial_payload

        url = url or config.get("OSTI", "url")

        logger.debug("initial_payload: %s", initial_payload)
        logger.debug("query_dict: %s", query)
        logger.debug("url: %s", url)

        osti_response = requests.get(url=url, auth=auth, params=query, headers=headers)

        try:
            osti_response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            # Detail text is not always present, which can cause json parsing
            # issues
            details = f"Details: {pprint.pformat(json.loads(osti_response.text))}" if osti_response.text else ""

            raise WebRequestException(
                "DOI submission request to OSTI service failed, " f"reason: {str(http_err)}\n{details}"
            )

        return osti_response.text

    def _validate_field_names(self, query_dict):
        """
        Validates the provided fields by the user to make sure they match the
        expected fields by OSTI:

            https://www.osti.gov/iad2test/docs#endpoints-recordlist

        """
        o_validated_dict = {}

        for key in query_dict:
            # If the key is valid, save the field and value to return.
            if key in self.ACCEPTABLE_FIELD_NAMES_LIST:
                o_validated_dict[key] = query_dict[key]
            else:
                logger.error(f"Unexpected field name '{key}' in query_dict")
                exit(1)

        return o_validated_dict
