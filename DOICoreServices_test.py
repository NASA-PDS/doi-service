#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 
import os
import sys

from DOICoreServices import *;

if __name__ == '__main__':
    # This is the unit test for DOICoreServices class.
    # How to run: 
    #     source venv/bin/activate
    #     pip install -r requirements.txt
    #     pip install -r requirements_2.txt
    #     python3 DOICoreServices_test.py
    #
    # The command will loop through all the URIs in the target_urls_list below and create a DOI object for each URIs

    global m_debug_mode
    function_name = 'DOICoreServices_test:';
    #print(function_name,'entering');

    default_run_dir     = '.' + os.path.sep 
    default_action_type = 'create_osti_label'
    default_target_url  = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml';

    contributor_value = 'Cartography and Imaging Sciences Discipline';

    #default_publisher_url  = 'https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_JSON_1D00.JSON';
    run_dir     = default_run_dir;

    m_debug_mode = True;
    m_debug_mode = False;

    publisher_value = DOI_CORE_CONST_PUBLISHER_VALUE;
    action_type     = default_action_type; 
    print(function_name,"publisher_value",publisher_value);

    if (len(sys.argv) > 1):
        action_type       = sys.argv[1];
        contributor_value = sys.argv[2];
        target_url        = sys.argv[3];
    else:
        # If not specified, set to default values for testing.
        print(function_name,"Set values to default:");
        print(function_name,"publisher_value",publisher_value);
        #print(function_name,"target_url",target_url);
        print(function_name,"contributor_value",contributor_value);
        #print(function_name,"ERROR: Must provide contributor and target_url");
        #exit(0);

    if m_debug_mode:
        print(function_name,"run_dir",run_dir);
        print(function_name,"publisher_value",publisher_value);
        print(function_name,"target_url",target_url);
        print(function_name,"contributor_value",contributor_value);

    #prodDate = '2019-01-01';
    #doi_date = ReturnDOIDate(f_debug, debug_flag, prodDate);
    #print(function_name,"doi_date",doi_date);
    #exit(0);

    doiCoreServices = DOICoreServices();
    (o_contributor_is_valid_flag,o_permissible_contributor_list) = doiCoreServices.ValidateContributorValue(DOI_CORE_CONST_PUBLISHER_URL,contributor_value);
    #print(function_name,"o_contributor_is_valid_flag",o_contributor_is_valid_flag);
    if (not o_contributor_is_valid_flag):
        print(function_name,"ERROR: The value of given contribut is not valid:",contributor_value);
        print(function_name,"permissible_contributor_list",o_permissible_contributor_list);
        exit(0);
    #exit(0);

    #exit(0);
    type_is_valid = False;
    o_doi_label = 'invalid action type:action_type ' + action_type;
    target_urls_list = ["https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml",
                   "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml",
                   "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml",
                   "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml",
                   "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml"]
    print(function_name,"target_urls_list:",target_urls_list);

    # Loop through each target and create a DOI object.
    doi_labels_created = 0;
    import requests;

    # Check if all websites exist
    for target_index,target_url in enumerate(target_urls_list):
        try:
            request = requests.get(target_url)
            if request.status_code == 200:
                print('Web site does indeed exists',target_url)
            else:
                print("ERROR:Website " + target_url + " returned response code: {code}".format(code=request.status_code))
                exit(0);
        except ConnectionError:
            print('Web site does not exist',target_url)
            exit(0);


    # Proceed with creating a DOI object, given a target_url.
    for target_index,target_url in enumerate(target_urls_list):
        print(function_name,"target_index,target_url:",target_index,target_url);
        type_is_valid = False;
        o_doi_label = 'invalid action type:action_type ' + action_type;
        if action_type == 'create_osti_label':
            #print(function_name,"target_url.startswith('http')",target_url.startswith('http'));
            if target_url.startswith('http'):
                #o_doi_label = doiCoreServices.ParsePDS4LabelViaURI(target_url+'dummy',publisher_value,contributor_value);
                o_doi_label = doiCoreServices.ParsePDS4LabelViaURI(target_url,publisher_value,contributor_value);
                type_is_valid = True;

        if not type_is_valid:
            print(function_name,"ERROR:",o_doi_label);
            print(function_name,"action_type",action_type);
            print(function_name,"run_dir",run_dir);
            print(function_name,"target_url",target_url);
            exit(0);

        if m_debug_mode:
            print(function_name,"o_doi_label",o_doi_label.decode());
            print(function_name,'leaving');

        #print(function_name,"o_doi_label",o_doi_label.decode());
        print(function_name,"target_index,target_url,DOI_OBJECT_CREATED_SUCCESSFULLY",target_index,target_url);
        #exit(0)

        #print(function_name,"o_doi_label")
        print(o_doi_label.decode());
        doi_labels_created += 1;

    print(function_name,"PROCESSED_TARGETS:target_urls_list:",target_urls_list);
    print(function_name,"DOI_LABELS_CREATE:doi_labels_created:",doi_labels_created);

    exit(0);

    #status = main()
    #status = DOI_IAD2_label_creation();
    #sys.exit(status)


# First time:
# cd ~/sandbox/pds-doi-service
# pip install virtualenv
# pip install -r requirements_2.txt
# python3 -m venv venv
# source venv/bin/activate
# python3 doi_core.py "./" -f aaaConfig_IAD2_IMG_InSight_20191216.xml
# python3 doi_core.py create_osti_label ./ 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml' 

# Second time:
# python3 doi_core.py create_osti_label 'PDS Cartography and Imaging Sciences Discipline (IMG) Node' 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'

# Unit test
# python3 DOICoreServices.py create_osti_label 'Cartography and Imaging Sciences Discipline' dummy1
#    publisher = 'PDS Cartography and Imaging Sciences Discipline (IMG) Node';



#Some details on the use case we want to implement for this sprint (from Jordan's inputs):
#
#A) Input test datasets from these PDS4 Collection and Bundle label via URLs
#
#    Bundle - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml
#    Data Collection - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml
#    Browse Collection - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml
#    Calibration Collection - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml
#    Document Collection - https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml


