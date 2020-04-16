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
#
# A valid XML text will be returned.  A redirect can be done to capture the output with '> my_out.xml'
#
# Notes:
#
#   1. TBD 

import logging
import os
import requests
import sys

from requests.auth import HTTPBasicAuth

if __name__ == '__main__':
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml http://127.0.0.1:5000/create_osti_label
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml http://127.0.0.1:5000/create_osti_label
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml http://127.0.0.1:5000/create_osti_label
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml http://127.0.0.1:5000/create_osti_label
    # python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml http://127.0.0.1:5000/create_osti_label

    global m_debug_mode
    function_name = 'main:';

    default_action_type = 'create_osti_label'
    default_target_url  = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml';
    default_get_url     = "http://127.0.0.1:5000/create_osti_label"

    m_debug_mode = True;
    m_debug_mode = False;

    if m_debug_mode:
        print(function_name,'entering');

    if (len(sys.argv) > 1):
        action_type       = sys.argv[1];
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


    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    target_url_query_str = 'target_url="' + target_url + '"';
    contributor_query_str= 'contributor="' + contributor_value.replace(' ','%20'); # Replace all spaces with '%20' since cannot have spaces in query string.

    # Build the actual query string to append request.
    query_string = '?' + target_url_query_str + '&' + contributor_query_str;

    response = requests.get(get_url + query_string);

    if m_debug_mode:
        print(function_name,response.encoding);    # returns 'utf-8'
        print(function_name,response.status_code); # returns 200
        print(function_name,response.elapsed);     # returns datetime.timedelta(0, 1, 666890)
        print(function_name,response.url);         # returns the value of get_url + query_string)
        print(response.text);        # returns the content of request in JSON

    print(response.text); # Prints the content of request as text.
    #logger.info("Hello, world")
    exit(0);

# First time:
# cd ~/sandbox/pds-doi-service
# pip install -r environments.txt
# python3 DOIWebClient.py create_osti_label 'Cartography and Imaging Sciences Discipline' https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml http://127.0.0.1:5000/create_osti_label
