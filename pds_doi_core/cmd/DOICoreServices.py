#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

#------------------------------                                                                                                 
# Import the Python libraries                                                                                                   
#------------------------------                                                                                                 

from lxml import etree

from const import *;

from pds_doi_core.util.DOIConfigUtil import DOIConfigUtil;
from pds_doi_core.util.DOIGeneralUtil import DOIGeneralUtil;
from pds_doi_core.input.DOIInputUtil import DOIInputUtil;
from pds_doi_core.input.DOIPDS4LabelUtil import DOIPDS4LabelUtil;
from pds_doi_core.input.DOIValidatorUtil import DOIValidatorUtil;
from pds_doi_core.cmd.DOIWebClient import DOIWebClient;

class DOICoreServices:
    global m_debug_mode;
    m_debug_mode = False;
    #m_debug_mode = True;
    #m_debug_mode = False;
    m_module_name = 'DOICoreServices:'

    m_doiConfigUtil = DOIConfigUtil();
    m_doiGeneralUtil = DOIGeneralUtil();
    m_doiInputUtil = DOIInputUtil();
    m_doiPDS4LabelUtil = DOIPDS4LabelUtil();
    m_doiValidatorUtil =  DOIValidatorUtil();
    m_doiWebClient =  DOIWebClient();

    def ReserveDOILabel(self,target_url,publisher_value,contributor_value):
        # Function receives a URI containing either XML, SXLS or CSV and create one or many labels to disk TBD on how to submit them.
        function_name = self.m_module_name + 'ReserveDOILabel:';
        global m_debug_mode
        #m_debug_mode = True;
        o_doi_label = None;
        type_is_valid = False;
        action_type = 'reserve_osti_label';
        o_doi_label = 'invalid action type:action_type ' + action_type;

        if m_debug_mode:
            print(function_name,"target_url,action_type",target_url,action_type);

        file_is_parsed_flag = False;
        if action_type == 'reserve_osti_label':
            if target_url.endswith('.xml'):
                #o_doi_label = self.ParsePDS4LabelViaURI(target_url,publisher_value,contributor_value);
                o_doi_label = self.m_doiPDS4LabelUtil.ParsePDS4LabelViaURI(target_url,publisher_value,contributor_value);
                type_is_valid = True;
                file_is_parsed_flag = True;

            if target_url.endswith('.xlsx'):
                type_is_valid = True;
                o_doi_label = None; # Since we are dealing with Excel spreadsheet, we may not return a label.

                xls_filepath = target_url;
                # Get the default configuration from external file.  Location may have to be absolute.
                xmlConfigFile = '.' + os.path.sep + 'config' + os.path.sep + 'default_config.xml';

                dict_configList = {}
                dict_fixedList  = {}
                (dict_configList, dict_fixedList) = self.m_doiConfigUtil.GetConfigFileMetaData(xmlConfigFile)

                appBasePath = os.path.abspath(os.path.curdir)
                #------------------------------
                # Set the values for the common parameters
                #------------------------
                root_path = dict_configList.get("root_path")
                pds_uri   = dict_fixedList.get("pds_uri")

                dict_ConditionData = {}

                (o_num_files_created,o_aggregated_DOI_content) = self.m_doiInputUtil.ParseSXLSFile(appBasePath,xls_filepath,dict_fixedList=dict_fixedList,dict_configList=dict_configList,dict_ConditionData=dict_ConditionData);
                o_doi_label = o_aggregated_DOI_content;
                file_is_parsed_flag = True;

            if target_url.endswith('.csv'):
                type_is_valid = True;
                o_doi_label = None; # Since we are dealing with Excel spreadsheet, we may not return a label.

                xls_filepath = target_url;
                # Get the default configuration from external file.  Location may have to be absolute.
                xmlConfigFile = '.' + os.path.sep + 'config' + os.path.sep + 'default_config.xml';

                dict_configList = {}
                dict_fixedList  = {}
                (dict_configList, dict_fixedList) = self.m_doiConfigUtil.GetConfigFileMetaData(xmlConfigFile)

                appBasePath = os.path.abspath(os.path.curdir)
                #------------------------------
                # Set the values for the common parameters
                #------------------------
                root_path = dict_configList.get("root_path")
                pds_uri   = dict_fixedList.get("pds_uri")

                dict_ConditionData = {}

                (o_num_files_created,o_aggregated_DOI_content) = self.m_doiInputUtil.ParseCSVFile(appBasePath,xls_filepath,dict_fixedList=dict_fixedList,dict_configList=dict_configList,dict_ConditionData=dict_ConditionData);
                o_doi_label = o_aggregated_DOI_content;
                file_is_parsed_flag = True;

            # Check to see if the given file has an attempt to process.
            if not file_is_parsed_flag:
                print(function_name,"ERROR: File type has not been implemented:target_url",target_url);
                exit(0);

        if o_doi_label is None:
            print(function_name,"ERROR: The value of o_doi_label is none.  Will not continue.");
            exit(0);

        # If the type of o_doi_label remains as string, and starts with 'invalid', we had a bad time parsing.
        if str(type(o_doi_label)) == 'str' and o_doi_label.startswith ('invalid'):
            print(function_name,"ERROR: Cannot parse given target_url",target_url);
            exit(0);

        # The parsing was successful, convert from bytes to string so we can build a tree.
        xmlText = self.m_doiGeneralUtil.DecodeBytesToString(o_doi_label)

        #m_debug_mode = True;
        if m_debug_mode:
            print(function_name,'type(o_doi_label)',type(o_doi_label));  # The type of o_doi_label is bytes
            print(function_name,'o_doi_label',o_doi_label);  # The type of o_doi_label is bytes
            print(function_name,'xmlText',xmlText);
            print(function_name,'type(xmlText)',type(xmlText));

        if isinstance(xmlText,bytes):
            doc = etree.fromstring(xmlText);
        else:
            doc  = etree.fromstring(xmlText.encode());

        # Do a sanity check on the 'status' attribute for each record.  If not equal to 'Reserved' exit.
        my_root = doc.getroottree();
        num_reserved_statuses = 0;
        num_record_records    = 0;
        for element in my_root.iter():
            if element.tag == 'record':
                num_record_records += 1;
                my_record = my_root.xpath(element.tag)[0]
                if my_record.attrib['status'] == 'Reserved':
                    num_reserved_statuses += 1;
                else:
                    print(function_name,"WARN: Expected 'status' attribute to be 'Reserved' but is not",my_record.attrib['status']);
                    my_record.attrib['status'] = 'Reserved';
                    print(function_name,"WARN: Reset status to 'Reserved'");
                    num_reserved_statuses += 1;
                
        if m_debug_mode:
            print(function_name,"num_record_records,num_reserved_statuses",num_record_records,num_reserved_statuses);
        if num_record_records != num_reserved_statuses:
            print(function_name,"ERROR: num_record_records is not the same as num_reserved_statuses",num_record_records,num_reserved_statuses);
            exit(0);

        sOutText = etree.tostring(doc,pretty_print=True)
        if m_debug_mode:
            print(function_name,'sOutText',sOutText);
            print(function_name,'doc',doc);

        # The xmlText now contain all the records built with 'Reserved' status, we can now send it
        o_status = self.m_doiWebClient.WebClientSubmitExistingContent(xmlText);
        print(function_name,'o_status',o_status);
        exit(0);

        # At this point, the sOutText would contain tag "status = 'Reserved'" in each record tags.
        return(sOutText);

    def CreateDOILabel(self,target_url,contributor_value):
        # Function receives a URI containing either XML or a local file and draft a Data Object Identifier (DOI).
        function_name = self.m_module_name + 'CreateDOILabel:';
        global m_debug_mode
        #m_debug_mode = True;
        o_doi_label = None;

        action_type = 'create_osti_label';
        publisher_value = DOI_CORE_CONST_PUBLISHER_VALUE;  # There is only one publisher of these DOI.
        o_contributor_is_valid_flag = False;

        # Make sure the contributor is valid before proceeding.
        (o_contributor_is_valid_flag,o_permissible_contributor_list) = self.m_doiValidatorUtil.ValidateContributorValue(DOI_CORE_CONST_PUBLISHER_URL,contributor_value);
        if m_debug_mode:
            print(function_name,"o_contributor_is_valid_flag:",o_contributor_is_valid_flag);
            print(function_name,"permissible_contributor_list",o_permissible_contributor_list);

        if (not o_contributor_is_valid_flag):
            print(function_name,"ERROR: The value of given contributor is not valid:",contributor_value);
            print(function_name,"permissible_contributor_list",o_permissible_contributor_list);
            exit(0);

        type_is_valid = False;
        o_doi_label = 'invalid action type:action_type ' + action_type;

        if action_type == 'create_osti_label':
            #print(function_name,"target_url.startswith('http')",target_url.startswith('http'));
            #if target_url.startswith('http'):
            if 2 == 2: 
                o_doi_label = self.m_doiPDS4LabelUtil.ParsePDS4LabelViaURI(target_url,publisher_value,contributor_value);
                #o_doi_label = self.m_doiPDS4LabelUtil.ParsePDS4LabelViaURI(target_url,publisher_value,contributor_value);
                type_is_valid = True;

        if not type_is_valid:
            print(function_name,"ERROR:",o_doi_label);
            print(function_name,"action_type",action_type);
            print(function_name,"target_url",target_url);
            exit(0);

        if m_debug_mode:
           print(function_name,"o_doi_label",o_doi_label.decode());
           print(function_name,"target_url,DOI_OBJECT_CREATED_SUCCESSFULLY",target_url);

        return(o_doi_label);
        
if __name__ == '__main__':
    global m_debug_mode
    function_name = 'main';
    #print(function_name,'entering');

    default_run_dir     = '.' + os.path.sep 
    default_action_type = 'create_osti_label'
    default_target_url  = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml';

    #default_publisher_url  = 'https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_JSON_1D00.JSON';
    run_dir     = default_run_dir;

    #m_debug_mode = True;
    m_debug_mode = False;

    publisher_value = DOI_CORE_CONST_PUBLISHER_VALUE;

    # to be done: argparse
    if (len(sys.argv) > 1):
        action_type       = sys.argv[1];
        contributor_value = sys.argv[2].lstrip().rstrip();  # Remove any leading and trailing blanks.
        target_url        = sys.argv[3];
    else:
        # If not specified, set to default values for testing.
        print(function_name,"ERROR: Must provide contributor and target_url");
        exit(0);

    if m_debug_mode:
        print(function_name,"run_dir",run_dir);
        print(function_name,"publisher_value",publisher_value);
        print(function_name,"target_url",target_url);
        print(function_name,"contributor_value[" + contributor_value + "]");

    doiCoreServices  = DOICoreServices();
    doiValidatorUtil = DOIValidatorUtil();

    if action_type == 'create_osti_label':
        #doiCoreServices = DOICoreServices();
        o_doi_label = doiCoreServices.CreateDOILabel(target_url,contributor_value);
        print(o_doi_label.decode());

    if action_type == 'reserve_osti_label':
        #print(function_name,"target_url.startswith('http')",target_url.startswith('http'));
        #if target_url.startswith('http'):
        if 2 == 2:
            #doiCoreServices = DOICoreServices();
            o_doi_label = doiCoreServices.ReserveDOILabel(target_url,publisher_value,contributor_value);
            type_is_valid = True;
            print(o_doi_label.decode());
    #print(function_name,"early#exit#0044");
    #exit(0);

# First time:
# cd ~/sandbox/pds-doi-service
# pip install virtualenv
# python3 -m venv venv
# source venv/bin/activate
#
# or
#
# pip install -r requirements.txt
# python3 DOICoreServices.py create_osti_label 'Cartography and Imaging Sciences Discipline' 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'

# Second time:
# python3 DOICoreServices.py create_osti_label 'Cartography and Imaging Sciences Discipline' 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'
# python3 DOICoreServices.py create_osti_label 'Cartography and Imaging Sciences Discipline' input/bundle_in_with_contributors.xml 
# python3 DOICoreServices.py reserve_osti_label 'Cartography and Imaging Sciences Discipline' input/DOI_Reserved_GEO_200318.xlsx
# python3 DOICoreServices.py reserve_osti_label 'Cartography and Imaging Sciences Discipline' input/DOI_Reserved_GEO_200318.csv
# CSV is not supported.  It was a one-time deal from Ron.
# python3 DOICoreServices.py reserve_osti_label 'Cartography and Imaging Sciences Discipline' input/OSTI_IAD_submitted_records_Reserved-only_20200304.csv 
# python3 DOICoreServices.py create_osti_label 'Cartography and Imaging Sciences Discipline' 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml'
#
# Unit test is in file DOICoreServices_test.py
# python3 DOICoreServices_test.py create_osti_label 'Cartography and Imaging Sciences Discipline' dummy1
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
