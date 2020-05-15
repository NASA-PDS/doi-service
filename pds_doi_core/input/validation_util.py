#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

import json;
import requests
import time

from pds_doi_core.util.const import *

from pds_doi_core.references.contributors import DOIContributorUtil
from pds_doi_core.util.general_util import DOIGeneralUtil, get_logger

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.input.validation_util')
logger.setLevel(logging.INFO)  # Comment this line once happy with the level of logging set in get_logger() function.
#logger.setLevel(logging.DEBUG)  # Comment this line once happy with the level of logging set in get_logger() function.
# Note that the get_logger() function may already set the level higher (e.g. DEBUG).  Here, we may reset
# to INFO if we don't want debug statements.

class DOIValidatorUtil:
    # This class DOIValidatorUtil provides functions to validate various values.
    m_doiContributorUtil = DOIContributorUtil()

    def validate_contributor_value(self,target_url,i_contributor):
        # Function ValidateContributorValue validates the given contributor for corrxxfectness by extracting valid values from
        # DOI_CORE_CONST_PUBLISHER_URL variable defined in const.py. The match has to be exact.
        PDS_NODE_IDENTIFIER = '0001_NASA_PDS_1.pds.Node.pds.name'

        o_found_dict = None
        o_contributor_is_valid_flag = False
        o_permissible_contributor_list = []

        logger.debug(f"target_url,i_contributor {target_url},{i_contributor}")

        # Read from URL if starts with 'http' otherwise read from local file.
        if target_url.startswith('http'):
            timer_start = time.time()
            use_new_method = True

            if not use_new_method:
                # Old method:
                from urllib.request import urlopen
                response = urlopen(target_url)
                web_data  = response.read().decode('utf-8')
                json_data = json.loads(web_data)
            else:
                # New method:
                # See https://github.com/psf/requests/issues/4023 about sending an optional
                # header to speed up the get() function.
                response = requests.get(target_url,stream=False,headers={'Connection': 'close'})
                web_data  = response.json()
                json_data = web_data

            timer_end = time.time()
            timer_elapsed = timer_end - timer_start
        # Because web_data is actually a list, we just want the 0 element
        #:json_data = json.loads(web_data[0])
        else:
            with open(target_url) as f:
                json_data = json.load(f)

        # Now that the json_data is in memory, we can look for the identifier value in PDS_NODE_IDENTIFIER
        # Because json_data is a list of one dictionary, we just want the 0 element.

        json_dict = json_data[0]
        found_key_1 = None
        found_key_2 = None
        found_key_3 = None
        found_key_4 = None
        found_key_5 = None
        found_index_1 = -1
        found_index_2 = -1
        class_index = -1

        for json_key, json_value in json_data[0].items():
            for json_key_1, json_value_1 in json_value.items():
                if isinstance(json_value_1,list):
                    pass
                else:
                    pass

                o_permissible_value_list = self.m_doiContributorUtil.get_permissible_values(json_value_1,json_key_1)

                if len(o_permissible_value_list) > 0 and not o_contributor_is_valid_flag:
                    num_permissible_names_matched = 0
                    for mmm in range(0,len(o_permissible_value_list)):
                        o_permissible_contributor_list.append(o_permissible_value_list[mmm]['PermissibleValue']['value'])
                        #if o_permissible_value_list[mmm]['PermissibleValue']['value'] in i_contributor:
                        if o_permissible_value_list[mmm]['PermissibleValue']['value'] == i_contributor:
                            num_permissible_names_matched += 1
                    # If at least one name matched, the valule publisher is valid.
                    if num_permissible_names_matched > 0:
                        o_contributor_is_valid_flag = True

            # If json_value_1 is a list and the json_key_1 is 'classDictionary' , we dig to the next level
            #if isinstance(json_value_1,list) and json_key_1 == 'classDictionary':
            if 2 == 3:
                for ii in range(0,len(json_value_1)):
                    for json_key_2, json_value_2 in json_value_1[ii].items():
                    # Each json_value_2 is a dictionary, we loop through.
                        if isinstance(json_value_2,dict):
                            for json_key_3, json_value_3 in json_value_2.items():
                                # If the type of json_value_3 is a list, we look through for PDS_NODE_IDENTIFIER
                                if isinstance(json_value_3,list):
                                    for kk in range(0,len(json_value_3)):
                                        for json_key_4, json_value_4 in json_value_3[kk].items():
                                            pass
                                        # If the type of json_value_4 is dict, we look for 'identifier' 
                                            if isinstance(json_value_4,dict):
                                                for json_key_5, json_value_5 in json_value_4.items():
                                                    if json_key_5 == 'identifier' and json_value_5 == PDS_NODE_IDENTIFIER:
                                                        # Save where we found it.
                                                        o_found_dict = json_value_4
                                                        found_key_1 = json_key_1
                                                        found_key_2 = json_key_2
                                                        found_key_3 = json_key_3
                                                        found_key_4 = json_key_4
                                                        found_key_5 = json_key_5
                                                        found_index_1 = ii # Found this in index ii in found_key_1
                                                        found_index_2 = kk # Found this in index kk of found_key_3
                                                        logger.info(f"FOUND_PDS_NODE_IDENTIFIER,json_value_3 {json_value_3}")
                                                        logger.info(f"FOUND_PDS_NODE_IDENTIFIER,json_value_4 {json_value_4}")
                                                        exit(0) # Should never get here.
                                            if isinstance(json_value_4,list):
                                                logger.info(f"FOUND_LIST:len(json_value_4) {len(json_value_4)}")
                                                logger.info(f"FOUND_LIST:json_value_4 {json_value_4}")
                                                logger.info(f"FOUND_LIST:json_key_1,json_key_2,json_key_3,json_key_4 {json_key_1,json_key_2,json_key_3,json_key_4}")
                                                exit(0) # Should never get here.

                # If json_value_2 is a list, we dig to the next level

            #  json_key_1 Title
            #  json_key_1 Version
            #  json_key_1 Date
            #  json_key_1 Description
            #  json_key_1 classDictionary
            #  json_key_1 attributeDictionary
            #  json_key_1 dataTypeDictionary
            #  json_key_1 unitDictionary

            # end if isinstance(json_value_1,list) and json_key_1 == 'classDictionary':
        # end for json_key_1, json_value_1 in json_value.items():

        if o_found_dict is not None:
            for found_key,found_value in o_found_dict.items():
                logger.debug(f"found_key,found_value {found_key,found_value}")

        logger.debug(f"o_contributor_is_valid_flag,target_url,i_contributor {o_contributor_is_valid_flag},{target_url},{i_contributor}")
        logger.debug(f"o_contributor_is_valid_flag,i_contributor,o_permissible_contributor_list {o_contributor_is_valid_flag},{target_url},{o_permissible_contributor_list}")
        return(o_contributor_is_valid_flag,o_permissible_contributor_list)


if __name__ == '__main__':

    from pds_doi_core.input.input_util import DOIInputUtil
    from pds_doi_core.input.validation_util import DOIValidatorUtil
    from pds_doi_core.util.config_parser import DOIConfigUtil

    function_name = 'main:'
    doiValidatorUtil = DOIValidatorUtil()

    xls_filepath = os.path.join('.','input','DOI_Reserved_GEO_200318.xlsx')

    doiInputUtil = DOIInputUtil()
    doiConfigUtil = DOIConfigUtil()

    # Get the default configuration from external file.  Location may have to be absolute.
    xmlConfigFile = os.path.join('.','config','default_config.xml')

    dict_configList = {}
    dict_fixedList  = {}
    (dict_configList, dict_fixedList) = doiConfigUtil.get_config_file_metadata(xmlConfigFile)

    appBasePath = os.path.abspath(os.path.curdir)
    #------------------------------
    # Set the values for the common parameters
    #------------------------
    root_path = dict_configList.get("root_path")
    pds_uri   = dict_fixedList.get("pds_uri")
   
    dict_fileName_matched_status = {}
    dict_siteURL = {}
    dict_ConditionData = {}
    dict_LIDVID_submitted = {}

    o_num_files_created = doiInputUtil.parse_sxls_file(appBasePath,xls_filepath,dict_fixedList=dict_fixedList,dict_configList=dict_configList,dict_ConditionData=dict_ConditionData)
    print(function_name,"o_num_files_created",o_num_files_created)

    # Make another call with CSV input
    xls_filepath = os.path.join('.','input','DOI_Reserved_GEO_200318.csv')
    o_num_files_created = doiInputUtil.parse_csv_file(appBasePath,xls_filepath,dict_fixedList=dict_fixedList,dict_configList=dict_configList,dict_ConditionData=dict_ConditionData)
    print(function_name,"o_num_files_created",o_num_files_created)
