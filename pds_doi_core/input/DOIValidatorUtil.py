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

from const import *;

from pds_doi_core.references.DOIContributorUtil import DOIContributorUtil;

class DOIValidatorUtil:
    # This class DOIValidatorUtil provides functions to validate various values.

    global m_debug_mode;
    m_module_name = 'DOIValidatorUtil:'
    m_debug_mode = False;
    m_module_name = 'DOIValidatorUtil:'
    m_doiContributorUtil = DOIContributorUtil();

    def ValidateContributorValue(self,target_url,i_contributor):
        # Function ValidateContributorValue validates the given contributor for correctness by extracting valid values from 
        # DOI_CORE_CONST_PUBLISHER_URL variable defined in const.py. The match has to be exact.
        function_name = self.m_module_name + 'ValidateContributorValue:';
        PDS_NODE_IDENTIFIER = '0001_NASA_PDS_1.pds.Node.pds.name'

        o_found_dict = None;
        o_contributor_is_valid_flag = False;
        o_permissible_contributor_list = [];

        # Read from URL if starts with 'http' otherwise read from local file.
        if target_url.startswith('http'):
            #print(function_name,'READ_AS_URI',target_url);
            timer_start = time.time()
            use_new_method = True;
            #use_new_method = False;
            #print(function_name,"use_new_method",use_new_method);
            #print(function_name,"TIMER_START:timer_start",timer_start);

            if not use_new_method:
                # Old method:
                from urllib.request import urlopen
                #print(function_name,"TIMER_START:urlopen",target_url);
                response = urlopen(target_url)
                #print(function_name,"TIMER_START:reponse.read()");
                web_data  = response.read().decode('utf-8');
                json_data = json.loads(web_data);
            else:
                # New method:
                ##response = requests.get(target_url)
                #response = requests.get(target_url,stream=False)
                #print(function_name,"TIMER_START:request.get",target_url);

                # See https://github.com/psf/requests/issues/4023 about sending an optional
                # header to speed up the get() function.

                #print(function_name,"TIMER_START:request.head",target_url);
                response = requests.get(target_url,stream=False,headers={'Connection': 'close'})
                #response = requests.head(target_url,allow_redirects=False)
                #print(function_name,"TIMER_START:response.text");
                #web_data  = response.text;
                web_data  = response.json();
                json_data = web_data;
                #print(function_name,"TIMER_END:timer_elapsed",time.time() - timer_start);
                #print(function_name,"TIMER_START:response.headers",response.headers);
                #print(function_name,"TIMER_START:len(web_data)",len(web_data));

            timer_end = time.time()
            timer_elapsed = timer_end - timer_start;
            #print(function_name,"TIMER_END:timer_end",timer_end);
            #print(function_name,"TIMER_ELAPSED:timer_elapsed",timer_elapsed);
            #exit(0);
            #json_data = json.loads(web_data);
        # Because web_data is actually a list, we just want the 0 element
        #:json_data = json.loads(web_data[0]);
        else:
            #print(function_name,'READ_AS_FILE',target_url);
            with open(target_url) as f:
                json_data = json.load(f)

        #print(function_name,'type(json_data)',type(json_data));
        #print(function_name,'len(json_data)',len(json_data));
        #print(function_name,'type(json_data[0])',type(json_data[0]));
        #print(function_name,'len(json_data[0])',len(json_data[0]));

        #print(function_name,'json_data[0]',json_data[0])
        #print(function_name,'json_data',json_data)

        # Now that the json_data is in memory, we can look for the identifier value in PDS_NODE_IDENTIFIER
        # Because json_data is a list of one dictionary, we just want the 0 element.

        json_dict = json_data[0];
        found_key_1 = None
        found_key_2 = None
        found_key_3 = None
        found_key_4 = None
        found_key_5 = None
        found_index_1 = -1;
        found_index_2 = -1;
        class_index = -1;

        for json_key, json_value in json_data[0].items():
            #print('json_key',json_key);
            #print('type(json_value)',type(json_value));
            #print("    len(json_dict['dataDictionary']['classDictionary'])",len(json_dict['dataDictionary']['classDictionary']));
            for json_key_1, json_value_1 in json_value.items():
                #print("    json_key_1",json_key_1);
                if isinstance(json_value_1,list):
                    #print("    json_key_1,type(json_value_1),len(json_value_1)",json_key_1,type(json_value_1),len(json_value_1));
                    pass;
                else:
                    #print("    json_key_1,type(json_value_1)",json_key_1,type(json_value_1));
                    pass;

                o_permissible_value_list = self.m_doiContributorUtil.GetPermissibleValues(json_value_1,json_key_1);

                if len(o_permissible_value_list) > 0 and not o_contributor_is_valid_flag:
                    num_permissible_names_matched = 0;
                    for mmm in range(0,len(o_permissible_value_list)):
                        #print(function_name,"mmm,o_permissible_value_list[mmm]publisher,",mmm,o_permissible_value_list[mmm],i_contributor);
                        o_permissible_contributor_list.append(o_permissible_value_list[mmm]['PermissibleValue']['value']);
                        #if o_permissible_value_list[mmm]['PermissibleValue']['value'] in i_contributor:
                        if o_permissible_value_list[mmm]['PermissibleValue']['value'] == i_contributor:
                            num_permissible_names_matched += 1;
                            #print(function_name,"FOUND_VALID_PUBLISHER");
                    # If at least one name matched, the valule publisher is valid.
                    if num_permissible_names_matched > 0:
                        o_contributor_is_valid_flag = True;
                    #print(function_name,"publisher,num_permissible_names_matched",publisher,num_permissible_names_matched);
                    #print(function_name,"FOUND_VALID_PUBLISHER");
                    #exit(0);

            # If json_value_1 is a list and the json_key_1 is 'classDictionary' , we dig to the next level
            #if isinstance(json_value_1,list) and json_key_1 == 'classDictionary':
            if 2 == 3:
                for ii in range(0,len(json_value_1)):
                    for json_key_2, json_value_2 in json_value_1[ii].items():
                    #print("        ii,json_key_2,type(json_value_2)",ii,json_key_2,type(json_value_2));
                    # Each json_value_2 is a dictionary, we loop through.
                        if isinstance(json_value_2,dict):
                            for json_key_3, json_value_3 in json_value_2.items():
                                #print("            ii,json_key_3,type(json_value_3)",ii,json_key_3,type(json_value_3));
                                # If the type of json_value_3 is a list, we look through for PDS_NODE_IDENTIFIER
                                if isinstance(json_value_3,list):
                                    for kk in range(0,len(json_value_3)):
                                    #print("            ii,kk,json_key_3 is list:",json_key_3);
                                        for json_key_4, json_value_4 in json_value_3[kk].items():
                                            #print("            ii,kk,json_key_3,json_key_4,type(json_value_4),json_value_4",ii,kk,json_key_3,json_key_4,type(json_value_4),json_value_4);
                                            #print("            ii,kk,json_key_3,ASSOCIATION_KEY,json_key_4,type(json_value_4),json_value_4",ii,kk,json_key_3,json_key_4,type(json_value_4),json_value_4);
                                        # If the type of json_value_4 is dict, we look for 'identifier' 
                                            if isinstance(json_value_4,dict):
                                                #print("            FOUND_JASON_VALUE_4_DICT",json_value_4);
                                                #exit(0);
                                                for json_key_5, json_value_5 in json_value_4.items():
                                                    if json_key_5 == 'identifier' and json_value_5 == PDS_NODE_IDENTIFIER:
                                                        # Save where we found it.
                                                        o_found_dict = json_value_4;
                                                        found_key_1 = json_key_1;
                                                        found_key_2 = json_key_2;
                                                        found_key_3 = json_key_3;
                                                        found_key_4 = json_key_4;
                                                        found_key_5 = json_key_5;
                                                        found_index_1 = ii; # Found this in index ii in found_key_1
                                                        found_index_2 = kk; # Found this in index kk of found_key_3
                                                        print("            FOUND_PDS_NODE_IDENTIFIER,json_value_3",json_value_3);
                                                        print("            FOUND_PDS_NODE_IDENTIFIER,json_value_4",json_value_4);
                                                        exit(0);
                                            if isinstance(json_value_4,list):
                                                print("            FOUND_LIST:len(json_value_4)",len(json_value_4));
                                                print("            FOUND_LIST:json_value_4",json_value_4);
                                                print("            FOUND_LIST:json_key_1,json_key_2,json_key_3,json_key_4",json_key_1,json_key_2,json_key_3,json_key_4);
                                                exit(0);

                # If json_value_2 is a list, we dig to the next level

            #print("    json_dict['dataDictionary']['classDictionary']",json_dict['dataDictionary']['classDictionary']);
            #print("    len(json_dict['dataDictionary']['classDictionary'])",len(json_dict['dataDictionary']['classDictionary']));
            #         #print('x, y',x,y) 
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
        #print(function_name,"early#exit#0002");

        #print("o_found_dict",o_found_dict);
        if o_found_dict is not None:
            for found_key,found_value in o_found_dict.items():
                print("found_key,found_value",found_key,found_value);

    #    print("");
    #    print("found_key_1",found_key_1);
    #    print("found_key_2",found_key_2);
    #    print("found_key_3",found_key_3);
    #    print("found_key_4",found_key_4);
    #    print("found_key_5",found_key_5);
    #    print("found_index_1,from found_key_1",found_index_1,found_key_1);
    #    print("found_index_2,from found_key_3",found_index_2,found_key_3);
    #    print("");
    #    print("json_dict['dataDictionary'][found_key_1][found_index_1][found_key_2][found_key_3][found_index_2]",json_dict['dataDictionary'][found_key_1][found_index_1][found_key_2][found_key_3][found_index_2])
    #
    #    print("early#exit#0044");
    #    exit(0);

        return(o_contributor_is_valid_flag,o_permissible_contributor_list);


if __name__ == '__main__':
    global m_debug_mode
    function_name = 'main:';
    #print(function_name,'entering');
    m_debug_mode = True;
    m_debug_mode = False;
    doiValidatorUtil = DOIValidatorUtil();
    exit(0);

    xls_filepath = '.' + os.path.sep + 'input' + os.path.sep + 'DOI_Reserved_GEO_200318.xlsx';

    doiInputUtil = DOIInputUtil();
    doiConfigUtil = DOIConfigUtil();

    # Get the default configuration from external file.  Location may have to be absolute.
    xmlConfigFile = '.' + os.path.sep + 'config' + os.path.sep + 'default_config.xml';

    dict_configList = {}
    dict_fixedList  = {}
    (dict_configList, dict_fixedList) = doiConfigUtil.GetConfigFileMetaData(xmlConfigFile);

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

    o_num_files_created = doiInputUtil.ParseSXLSFile(appBasePath,xls_filepath,dict_fixedList=dict_fixedList,dict_configList=dict_configList,dict_ConditionData=dict_ConditionData);
    print(function_name,"o_num_files_created",o_num_files_created);
