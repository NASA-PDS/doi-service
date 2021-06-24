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
from requests.auth import HTTPBasicAuth

from pds_doi_service.core.input.exceptions import WebRequestException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.web_client import DOIWebClient
from pds_doi_service.core.outputs.datacite.datacite_web_parser import DOIDataCiteWebParser
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOIDataCiteWebClient(DOIWebClient):
    """
    Class used to submit HTTP requests to the DataCite DOI service.
    """
    _service_name = 'DataCite'
    _web_parser = DOIDataCiteWebParser()
    _content_type_map = {
        CONTENT_TYPE_JSON: 'application/vnd.api+json'
    }

    def submit_content(self, payload, content_type=CONTENT_TYPE_JSON):
        """
        Submits a payload to the DataCite DOI service via the POST action.

        The action taken by the service is determined by the contents of the
        payload.

        The DataCite endpoint URL and authentication credentials for the request
        are automatically pulled from the configuration file.

        Parameters
        ----------
        payload : str
            Payload to submit to the DataCite DOI service. Should correspond to
            an DataCite-format label file (JSON) containing a single DOI record.
        content_type : str
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
            url=config.get('DATACITE', 'url'),
            username=config.get('DATACITE', 'user'),
            password=config.get('DATACITE', 'password'),
            content_type=content_type
        )

        doi = self._web_parser.parse_dois_from_label(response_text)

        return doi, response_text

    def query_doi(self, query, content_type=CONTENT_TYPE_JSON):
        """
        Queries the DataCite DOI endpoint for the status of one or more DOI
        submissions.

        The DataCite endpoint URL and authentication credentials for the request
        are automatically pulled from the configuration file.

        Parameters
        ----------
        query : dict
            Key/value pairs to append as parameters to the URL for the GET
            endpoint.
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
            raise ValueError('Invalid content type requested, must be one of '
                             f'{",".join(list(self._content_type_map.keys()))}')

        auth = HTTPBasicAuth(
            config.get('DATACITE', 'user'), config.get('DATACITE', 'password')
        )

        headers = {
            'Accept': self._content_type_map[content_type]
        }

        if isinstance(query, dict):
            query_string = ' '.join([f'{k}:{v}' for k, v in query.items()])
        else:
            query_string = ' '.join(list(map(str, query)))

        url = config.get('DATACITE', 'url')

        logger.debug('query_string: %s', query_string)
        logger.debug('url: %s', url)

        datacite_response = requests.get(
            url=url, auth=auth, headers=headers,
            params={"query": query_string,
                    'client-id': config.get('DATACITE', 'user').lower()}
        )

        try:
            datacite_response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            # Detail text is not always present, which can cause json parsing
            # issues
            details = (
                f'Details: {pprint.pformat(json.loads(datacite_response.text))}'
                if datacite_response.text else ''
            )

            raise WebRequestException(
                'DOI submission request to OSTI service failed, '
                f'reason: {str(http_err)}\n{details}'
            )

        return datacite_response.text
