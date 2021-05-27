#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
=======
osti.py
=======

Contains OSTI-specific implementations of classes used to create, submit, and
parse DOI records.
"""

import datetime
import html
import json
import pprint
from os.path import exists

import pystache
import requests
from pkg_resources import resource_filename
from requests.auth import HTTPBasicAuth

from pds_doi_service.core.entities.doi import Doi, ProductType
from pds_doi_service.core.input.exceptions import WebRequestException
from pds_doi_service.core.outputs.doi_record import (DOIRecord,
                                                     CONTENT_TYPE_XML,
                                                     CONTENT_TYPE_JSON,
                                                     VALID_CONTENT_TYPES)
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.outputs.web_client import DOIWebClient
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOIOstiRecord(DOIRecord):
    def __init__(self):
        """Creates a new DOIOutputOsti instance"""
        # Need to find the mustache DOI templates
        self._xml_template_path = resource_filename(
            __name__, 'DOI_IAD2_template_20200205-mustache.xml'
        )
        self._json_template_path = resource_filename(
            __name__, 'DOI_IAD2_template_20210216-mustache.json'
        )

        if (not exists(self._xml_template_path)
                or not exists(self._json_template_path)):
            raise RuntimeError(
                f'Could not find one or more DOI templates needed by this module\n'
                f'Expected XML template: {self._xml_template_path}\n'
                f'Expected JSON template: {self._json_template_path}'
            )

        self._template_map = {
            CONTENT_TYPE_XML: self._xml_template_path,
            CONTENT_TYPE_JSON: self._json_template_path
        }

    def create_doi_record(self, dois, content_type=CONTENT_TYPE_XML):
        if content_type not in VALID_CONTENT_TYPES:
            raise ValueError('Invalid content type requested, must be one of '
                             f'{",".join(VALID_CONTENT_TYPES)}')

        # If a single DOI was provided, wrap it in a list so the iteration
        # below still works
        if isinstance(dois, Doi):
            dois = [dois]

        doi_fields_list = []

        for index, doi in enumerate(dois):
            # Filter out any keys with None as the value, so the string literal
            # "None" is not written out as an XML tag's text body
            doi_fields = (
                dict(filter(lambda elem: elem[1] is not None, doi.__dict__.items()))
            )

            # Escape any necessary HTML characters from the site-url,
            # we perform this step rather than pystache to avoid
            # unintentional recursive escapes
            if doi.site_url:
                doi_fields['site_url'] = html.escape(doi.site_url)

            # Convert set of keywords back to a semi-colon delimited string
            if doi.keywords:
                doi_fields['keywords'] = ";".join(sorted(doi.keywords))
            else:
                doi_fields.pop('keywords')

            # Remove any extraneous whitespace from a provided description
            if doi.description:
                doi.description = str.strip(doi.description)

            # publication_date is assigned to a Doi object as a datetime,
            # need to convert to a string for the OSTI label. Note that
            # even if we only had the publication year from the PDS4 label,
            # the OSTI schema still expects YYYY-mm-dd format.
            if isinstance(doi.publication_date, datetime.datetime):
                doi_fields['publication_date'] = doi.publication_date.strftime('%Y-%m-%d')

            # Same goes for date_record_added and date_record_updated
            if (doi.date_record_added and
                    isinstance(doi.date_record_added, datetime.datetime)):
                doi_fields['date_record_added'] = doi.date_record_added.strftime('%Y-%m-%d')

            if (doi.date_record_updated and
                    isinstance(doi.date_record_updated, datetime.datetime)):
                doi_fields['date_record_updated'] = doi.date_record_updated.strftime('%Y-%m-%d')

            # Pre-convert author map into a JSON string to make it play nice
            # with pystache rendering
            if doi.authors and content_type == CONTENT_TYPE_JSON:
                doi_fields['authors'] = json.dumps(doi.authors)

            # The OSTI IAD schema does not support 'Bundle' as a product type,
            # so convert to collection here
            if doi.product_type == ProductType.Bundle:
                doi_fields['product_type'] = ProductType.Collection

            # Lastly, we need a kludge to inform the mustache template whether
            # to include a comma between consecutive entries (JSON only)
            if content_type == CONTENT_TYPE_JSON and index < len(dois) - 1:
                doi_fields['comma'] = True

            doi_fields_list.append(doi_fields)

        renderer = pystache.Renderer()

        rendered_template = renderer.render_path(
            self._template_map[content_type], {'dois': doi_fields_list}
        )

        # Reindent the output JSON to account for the kludging of the authors field
        if content_type == CONTENT_TYPE_JSON:
            rendered_template = json.dumps(json.loads(rendered_template), indent=4)

        return rendered_template


class DOIOstiWebClient(DOIWebClient):
    _service_name = 'OSTI'
    _web_parser = DOIOstiWebParser()
    _content_type_map = {
        CONTENT_TYPE_XML: 'application/xml',
        CONTENT_TYPE_JSON: 'application/json'
    }

    ACCEPTABLE_FIELD_NAMES_LIST = [
        'id', 'doi', 'accession_number', 'published_before', 'published_after',
        'added_before', 'added_after', 'updated_before', 'updated_after',
        'first_registered_before', 'first_registered_after', 'last_registered_before',
        'last_registered_after', 'status', 'start', 'rows', 'sort', 'order'
    ]

    MAX_TOTAL_ROWS_RETRIEVE = 1000000000
    """Maximum numbers of rows to request from a query to OSTI"""

    def submit_content(self, payload, url, username, password,
                       content_type=CONTENT_TYPE_XML):
        response_text = super().submit_content(
            payload, url, username, password, content_type
        )

        # Re-use the parse functions from DOIOstiWebParser class to get the
        # list of Doi objects to return
        dois, _ = self._web_parser.parse_dois_from_label(response_text, content_type)

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
            query_dict = self._validate_field_names(initial_payload)
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
