#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
=======================
osti_web_client.py
=======================

Contains client functions for interfacing with the OSTI DOI submission service.
It allows the user to draft a DOI object by communicating with a currently
running web server for DOI services.
"""

from lxml import etree
from requests.auth import HTTPBasicAuth
import requests

from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser

logger = get_logger('pds_doi_core.cmd.pds_doi_cmd')


class DOIOstiWebClient:
    _web_parser = DOIOstiWebParser()

    def webclient_draft_doi(self, target_url, contributor_value):
        """Draft a DOI from input by making a request to the server."""
        parameters = {
            'target_url': target_url,
            'contributor': contributor_value
        }

        response = requests.get(target_url, params=parameters)
        logger.debug(f'response {response}')

        # Return the response as text and let the user decide what to do with it.
        return response.text

    def webclient_reserve_doi(self, target_url, contributor_value):
        """Reserve a DOI from input by making a request to the server."""
        params = {
            'target_url': target_url,
            'contributor': contributor_value
        }

        response = requests.get(target_url, params=params)
        logger.debug(f'reserve doi {response.request}')

        return response.text

    def webclient_submit_existing_content(self, payload, i_url=None,
                                          i_username=None, i_password=None):
        """Submit the content (payload already in memory)."""
        auth = HTTPBasicAuth(i_username, i_password)

        headers = {
            'Accept': 'application/xml',
            'Content-Type': 'application/xml'
        }

        response = requests.post(i_url, auth=auth, data=payload, headers=headers)

        # Re-use the parse function response_get_parse_osti_xml() from
        # DOIOstiWebParser class instead of duplicating code.
        doi, _ = self._web_parser.response_get_parse_osti_xml(response.text)

        logger.debug(f"o_status {doi}")

        return doi, response.text

    def webclient_submit_doi(self, payload_filename):
        """Submit the content external file as a DOI to server."""
        logger.debug(f"payload_filename {payload_filename}")

        with open(payload_filename, 'rb') as payload:
            o_status, doc = self.webclient_submit_existing_content(payload)

        return o_status, doc

    def webclient_query_doi(self, i_url, query_dict=None, i_username=None, i_password=None):
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
        MAX_TOTAL_ROWS_RETRIEVE= 1000000000

        auth = HTTPBasicAuth(i_username, i_password)

        headers = {
            'Accept': 'application/xml',
            'Content-Type': 'application/xml'
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

        osti_response = requests.get(i_url,
                                     auth=auth,
                                     params=query_dict,
                                     headers=headers)

        return osti_response.text

    def _verify_osti_reserved_status(self, i_doi_label):
        """
        Verifies that all the status attributes in all records are 'Reserved'
        as expected.
        """
        o_reserved_flag = True

        if i_doi_label is None:
            logger.error(f"The value of i_doi_label is none. Will not continue.")
            exit(1)

        doc = etree.fromstring(i_doi_label.encode())

        # Do a sanity check on the 'status' attribute for each record.
        # If not equal to 'Reserved' exit.
        my_root = doc.getroottree()
        num_reserved_statuses = 0
        num_record_records = 0

        for element in my_root.findall('record'):
            num_record_records += 1
            my_record = my_root.xpath(element.tag)[0]

            if my_record.attrib['status'] == DoiStatus.Reserved:
                num_reserved_statuses += 1
            else:
                logger.warning("Expected 'status' attribute to be 'reserved' "
                               f"but it is {my_record.attrib['status']}")
                my_record.attrib['status'] = DoiStatus.Reserved
                logger.warning("Reset status to 'reserved'")

                num_reserved_statuses += 1

        logger.debug("num_record_records,num_reserved_statuses "
                     f"{num_record_records} {num_reserved_statuses}")

        if num_record_records != num_reserved_statuses:
            logger.error("num_record_records is not the same as num_reserved_statuses "
                         f"{num_record_records} {num_reserved_statuses}")
            exit(1)

        o_out_text = etree.tostring(doc, pretty_print=True)
        logger.debug(f'o_out_text {o_out_text}')
        logger.debug(f'doc {doc}')

        return o_reserved_flag, o_out_text
