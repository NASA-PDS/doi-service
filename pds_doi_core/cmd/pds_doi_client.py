#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

# This file pds_doi_client.py is the web client for DOI services.  It allows the user to draft a DOI object by communicating
# with a currently running web server for DOI services.
#

import json
import logging
import netrc
import os
import requests
import sys
import xmltodict

from pds_doi_core.util.cmd_parser import create_cmd_parser

from pds_doi_core.util.general_util import get_logger

from collections import OrderedDict
from lxml import etree
from requests.auth import HTTPBasicAuth

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.cmd.pds_doi_cmd')

class DOIWebClient:
    def webclient_draft_doi(self,target_url,contributor_value):
        '''Function draft a DOI from input by making a request to the server.'''
        target_url_query_str = 'target_url="' + target_url + '"'
        # Replace all spaces with '%20' since cannot have spaces in query string.
        # Replace all double quotes '' since cannot have double quotes in contributor value.
        contributor_query_str= 'contributor=' + contributor_value.replace(' ','%20').replace('%22','') # Replace all spaces with '%20' since cannot have spaces in query string.

        # Build the actual query string to append request.
        query_string = '?' + target_url_query_str + '&' + contributor_query_str

        response = requests.get(get_url + query_string)
        logger.debug(f'query_string {query_string}')
        logger.debug(f'response {response}')

        # Return the reponse as text and let the user decide what to do with it.
        return response.text

    def webclient_reserve_doi(self,target_url,contributor_value,get_url):
        '''Function reserve  a DOI from input by making a request to the server.'''
        target_url_query_str = 'target_url="' + target_url + '"'
        contributor_query_str= 'contributor=' + contributor_value.replace(' ','%20').replace('%22','') # Replace all spaces with '%20' since cannot have spaces in query string.

        # Build the actual query string to append request.
        query_string = '?' + target_url_query_str + '&' + contributor_query_str
        logger.debug(f'query_string {query_string}')
        logger.debug(f'get_url {get_url}')

        response = requests.get(get_url + query_string)

        return response.text

    def webclient_submit_existing_content(self,payload,i_username=None,i_password=None):
        '''Function submit the content (payload already in memory).'''
        o_status = 'DEFAULT_STATUS'

        iad_url         = "https://www.osti.gov/iad2test/api/records"  # This should really come from config file.
        remoteHostName  = "www.osti.gov"

        if i_username is None and i_password is None:
            netrc_info  = netrc.netrc()
            remoteHostName  = "www.osti.gov"
            authTokens = netrc_info.authenticators(remoteHostName)
            auth = HTTPBasicAuth(authTokens[0],authTokens[2])  # Fetch the user name and password from netrc file.
        else:
            auth = HTTPBasicAuth(i_username,i_password)

        headers = {'Accept': 'application/xml',
                   'Content-Type': 'application/xml'}

        response = requests.post(iad_url,
                                 auth    = auth,
                                 data    = payload,
                                 headers = headers)
        records_as_text_xml = response.text   # This gives us the entire response as text and in XML format.
        xmlText = records_as_text_xml
        if isinstance(xmlText,bytes):
            doc = etree.fromstring(xmlText)
        else:
            doc  = etree.fromstring(xmlText.encode())

        o_status = []
        # Do a sanity check on the 'status' attribute for each record.  If not equal to 'Reserved' exit.
        my_root = doc.getroottree()
        num_reserved_statuses = 0
        num_record_records    = 0
        element_index = 0

        for element in my_root.iter():
            one_tuple = ()
            if element.tag == 'record':
                num_record_records += 1
                my_record = my_root.xpath(element.tag)[0]
                if my_record.attrib['status'] == 'Reserved':
                    num_reserved_statuses += 1
                my_id     = my_root.xpath('record/id')   [element_index]
                my_doi    = my_root.xpath('record/doi')  [element_index]
                my_title  = my_root.xpath('record/title')[element_index]

                # Save each tuple we have collected to o_status.  More can be added.
                one_tuple = (my_id.text,my_doi.text,my_title.text,my_record.attrib['status'])
                o_status.append(one_tuple)
                element_index += 1

        logger.info(f"DOI records submitted with status {response.status_code}")

        return o_status

    def webclient_submit_doi(self,payload_filename,i_username=None,i_password=None):
        '''Function submit the content external file as a DOI to server.'''
        o_status = 'DEFAULT_STATUS'

        # Do a sanity check first for file existence.
        if not os.path.isfile(payload_filename):
            logger.error("File not exist {payload_filename}")
            exit(1)

        with open(payload_filename,'rb') as payload:
            o_status = self.webclient_submit_existing_content(payload,i_username=None,i_password=None)
        return o_status

    def WebClientTrackSubmitedDOI(self,submitted_status):
        return 1
