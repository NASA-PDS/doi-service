#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

# This file DOIWebClient.py is the web client for DOI services.  It allows the user to draft a DOI object by communicating
# with a currently running web server for DOI services.
#
# pip install -r requirements.txt
#
# Example from command line:
#
# python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml http://127.0.0.1:5000/create_osti_label
# python3 DOIWebClient.py reserve_osti_label 'dummy_1' input/DOI_Reserved_GEO_200318.xlsx http://127.0.0.1:5000/reserve_osti_label
#
# A valid XML text will be returned.  A redirect can be done to capture the output with '> my_out.xml'
#
# Notes:
#
#   1. TBD 

import json
import logging
import netrc
import os
import requests
import sys
import xmltodict

from collections import OrderedDict;
from lxml import etree
from requests.auth import HTTPBasicAuth;

class DOIWebClient:
    m_module_name = "DOIWebClient:";
    m_debug_mode = False;
    if (os.getenv('PDS_DOI_CORE_DEBUG_FLAG','') == 'true'):
        m_debug_mode  = True;

    def WebClientDraftDOI(self,target_url,contributor_value):
        function_name = self.m_module_name + "WebClientDraftDOI:";

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        target_url_query_str = 'target_url="' + target_url + '"';
        #contributor_query_str= 'contributor="' + contributor_value.replace(' ','%20'); # Replace all spaces with '%20' since cannot have spaces in query string.
        # Replace all spaces with '%20' since cannot have spaces in query string.
        # Replace all double quotes '' since cannot have double quotes in contributor value.
        contributor_query_str= 'contributor=' + contributor_value.replace(' ','%20').replace('%22',''); # Replace all spaces with '%20' since cannot have spaces in query string.

        # Build the actual query string to append request.
        query_string = '?' + target_url_query_str + '&' + contributor_query_str;
        #print(function_name,"query_string[",query_string,"]");
        #exit(0);

        response = requests.get(get_url + query_string);

        if self.m_debug_mode:
            print(function_name,response.encoding);    # returns 'utf-8'
            print(function_name,response.status_code); # returns 200
            print(function_name,response.elapsed);     # returns datetime.timedelta(0, 1, 666890)
            print(function_name,response.url);         # returns the value of get_url + query_string)
            print(response.text);                      # returns the content of request as text

        # Return the reponse as text and let the user decide what to do with it.
        return(response.text);

    def WebClientReserveDOI(self,target_url,contributor_value):
        function_name = self.m_module_name + "WebClientReserveDOI:";

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        target_url_query_str = 'target_url="' + target_url + '"';
        contributor_query_str= 'contributor=' + contributor_value.replace(' ','%20').replace('%22',''); # Replace all spaces with '%20' since cannot have spaces in query string.

        # Build the actual query string to append request.
        query_string = '?' + target_url_query_str + '&' + contributor_query_str;
        #print(function_name,"query_string[",query_string,"]");
        #exit(0);

        print(function_name,"get_url",get_url);
        response = requests.get(get_url + query_string);

        if self.m_debug_mode:
            print(function_name,response.encoding);    # returns 'utf-8'
            print(function_name,response.status_code); # returns 200
            print(function_name,response.elapsed);     # returns datetime.timedelta(0, 1, 666890)
            print(function_name,response.url);         # returns the value of get_url + query_string)
            print(response.text);                      # returns the content of request as text

        # Return the reponse as text and let the user decide what to do with it.
        print(function_name,"get_url",get_url);
        print(function_name,"query_string",query_string);
        response_text = 'hello_world';
        #return(response_text);
        return(response.text);



        return(1);

    def WebClientSubmitExistingContent(self,payload,i_username=None,i_password=None):
        # Function submit the content (payload already in memory).
        function_name = self.m_module_name + "WebClientSubmitExistingContent:";
        o_status = 'DEFAULT_STATUS';
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        iad_url         = "https://www.osti.gov/iad2test/api/records";  # This should really come from config file.
        remoteHostName  = "www.osti.gov";

        if i_username is None and i_password is None:
            netrc_info  = netrc.netrc()
            remoteHostName  = "www.osti.gov"
            authTokens = netrc_info.authenticators(remoteHostName)
            auth = HTTPBasicAuth(authTokens[0],authTokens[2]);  # Fetch the user name and password from netrc file.
        else:
            auth = HTTPBasicAuth(i_username,i_password);

        headers = {'Accept': 'application/xml',
                   'Content-Type': 'application/xml'}

        response = requests.post(iad_url,
                                 auth    = auth,
                                 data    = payload,
                                 headers = headers);
        #print(function_name,"after_post:iad_url,response",iad_url,response);
        #records = response.json();
        records_as_text_xml = response.text;   # This gives us the entire response as text and in XML format.
        xmlText = records_as_text_xml;
        if isinstance(xmlText,bytes):
            doc = etree.fromstring(xmlText);
        else:
            doc  = etree.fromstring(xmlText.encode());

        o_status = [];
        # Do a sanity check on the 'status' attribute for each record.  If not equal to 'Reserved' exit.
        my_root = doc.getroottree();
        num_reserved_statuses = 0;
        num_record_records    = 0;
        element_index = 0;

        for element in my_root.iter():
            one_tuple = ()
            if element.tag == 'record':
                num_record_records += 1;
                my_record = my_root.xpath(element.tag)[0]
                if my_record.attrib['status'] == 'Reserved':
                    num_reserved_statuses += 1;
                my_id     = my_root.xpath('record/id')   [element_index];
                my_doi    = my_root.xpath('record/doi')  [element_index];
                my_title  = my_root.xpath('record/title')[element_index];

                if self.m_debug_mode:
                    print(function_name,"element_index,num_record_records,my_id.tag,my_id.text",element_index,my_id.tag,my_id.text);
                    print(function_name,"element_index,num_record_records,my_doi.tag,my_doi.text",element_index,my_id.tag,my_doi.text);
                    print(function_name,"element_index,num_record_records,my_title.tag,my_title.text",element_index,my_id.tag,my_title.text);
                # Save each tuple we have collected to o_status.  More can be added.
                one_tuple = (my_id.text,my_doi.text,my_title.text,my_record.attrib['status'])
                o_status.append(one_tuple);
                element_index += 1;

        if self.m_debug_mode:
            print(function_name,"num_record_records,num_reserved_statuses",num_record_records,num_reserved_statuses);
            print(function_name,"o_status",o_status);

        logger.info(f"DOI records submitted with status {response.status_code}")
        #logger.info(f"DOI records submitted with status ZZZ")

        return(o_status) 

    def WebClientSubmitDOI(self,payload_filename,i_username=None,i_password=None):
        function_name = self.m_module_name + "WebClientSubmitDOI:";

        o_status = 'DEFAULT_STATUS';

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        # Do a sanity check first for file existence.
        if not os.path.isfile(payload_filename):
            print(function_name,"ERROR: File not exist",payload_filename);
            exit(0);

        with open(payload_filename,'rb') as payload:
            o_status = self.WebClientSubmitExistingContent(payload,i_username=None,i_password=None);
        return(o_status);

    def WebClientTrackSubmitedDOI(self,submitted_status):
        function_name = self.m_module_name + "WebClientTrackSubmitedDOI:";
        return(1);

if __name__ == '__main__':
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml http://127.0.0.1:5000/create_osti_label
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml http://127.0.0.1:5000/create_osti_label
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml http://127.0.0.1:5000/create_osti_label
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml http://127.0.0.1:5000/create_osti_label
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml http://127.0.0.1:5000/create_osti_label

    # python3 DOIWebClient.py reserve_osti_label 'dummy' input/DOI_Reserved_GEO_200318.xlsx http://127.0.0.1:5000/create_osti_label

    global m_debug_mode
    function_name = 'main:';

    default_action_type = 'create_osti_label'
    default_target_url  = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml';
    default_get_url     = "http://127.0.0.1:5000/create_osti_label"
    run_dir = "/";
    publisher_value   = 'dummy_publisher_value';
    contributor_value = 'dummy_contributor_value';

    m_debug_mode = True;
    #m_debug_mode = False;

    if m_debug_mode:
        print(function_name,'entering');

    payload_filename = '';
    if (len(sys.argv) > 1):
        action_type       = sys.argv[1];
        if action_type == 'submit_osti_label':
            payload_filename = sys.argv[2]
            print(function_name,'payload_filename',payload_filename);
            target_url        = sys.argv[3];
        else:
            contributor_value = sys.argv[2];
            target_url        = sys.argv[3];
            get_url           = sys.argv[4];
    else:
        # If not specified, set to default values for testing.
        print(function_name,"ERROR: Must provide contributor and target_url and get_url");
        exit(0);

    if m_debug_mode:
        print(function_name,"run_dir",run_dir);
        print(function_name,"publisher_value",publisher_value);
        print(function_name,"target_url",target_url);
        print(function_name,"contributor_value",contributor_value);
    #exit(0);

    doiWebClient  = DOIWebClient()
    o_doi_label = 'invalid action type:action_type ' + action_type;

    type_is_valid = False;
    if action_type == 'create_osti_label' or action_type == 'draft_osti_label':
        type_is_valid = True;
        response_text = doiWebClient.WebClientDraftDOI(target_url,contributor_value);
        o_doi_label = response_text
        print(response_text); # Prints the content of request as text.

    if action_type == 'reserve_osti_label':
        print(function_name,"action_type",action_type);
        type_is_valid = True;
        response_text = doiWebClient.WebClientReserveDOI(target_url,contributor_value);
        o_doi_label = response_text
        print("response_text",response_text); # Prints the content of request as text.

    if action_type == 'submit_osti_label':
        type_is_valid = True;
        submitted_status = doiWebClient.WebClientSubmitDOI(payload_filename);
        print(submitted_status);
        print(type(submitted_status));
        donotcare = doiWebClient.WebClientTrackSubmitedDOI(submitted_status);
        #return(o_status);

    if not type_is_valid:
        print(function_name,"ERROR:",o_doi_label);
        print(function_name,"action_type",action_type);
        print(function_name,"target_url",target_url);

    exit(0);

# First time:
# cd ~/sandbox/pds-doi-service
# pip install -r requirements.txt
# python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml http://127.0.0.1:5000/create_osti_label
# python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml http://127.0.0.1:5000/create_osti_label

# pip install -r requirements_5.txt
# python3 DOIWebClient.py submit_osti_label ./output/bundle_out.xml     http://127.0.0.1:5000/submit_osti_label
# python3 DOIWebClient.py submit_osti_label ./output/reserved_label.xml http://127.0.0.1:5000/submit_osti_label
