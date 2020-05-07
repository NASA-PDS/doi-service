#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

import os
#import shutil
import sys
#import unicodedata

from xml.etree import ElementTree
#from lxml import etree
#from lxml import html

from datetime import datetime
from time import gmtime,strftime
#import xlrd

from const import *;

class DOIContributorUtil: 

    global m_debug_mode;
    global f_log
    m_module_name = 'DOIContributorUtil:'
    m_debug_mode = False;
    f_log = None;

    def GetPermissibleValues(self,json_value_1,json_key_1):
            # Function returns the PerrmissibleValueList for attributeDictionary where one element matches with PDS_NODE_IDENTIFIER.
            function_name = self.m_module_name + 'GetPermissibleValues:'
            PDS_NODE_IDENTIFIER = '0001_NASA_PDS_1.pds.Node.pds.name'

            #print(function_name,"json_key_1",json_key_1);
            found_identifier_flag = False;
            found_permissible_value_flag = False
            o_permissible_value_list = []; # Is a list of dict, where each dict has a key 'PermissibleValue' points to a dict with key 'value' to the actual value.
            #print(function_name,"json_value_1",json_value_1);
            # If json_value_1 is a list and the json_key_1 is 'classDictionary' , we dig to the next level

            if isinstance(json_value_1,list) and json_key_1 == 'attributeDictionary':
                for ii in range(0,len(json_value_1)):
                  if not found_permissible_value_flag:
                    for json_key_2, json_value_2 in json_value_1[ii].items():
                      if not found_permissible_value_flag:
                        #print("        ii,json_key_2,type(json_value_2)",ii,json_key_2,type(json_value_2));
                        #exit(0);
                        # Each json_value_2 is a dictionary, we loop through.
                        if isinstance(json_value_2,dict):
                            for json_key_3, json_value_3 in json_value_2.items():
                                #print("            ii,json_key_3,type(json_value_3)",ii,json_key_3,type(json_value_3));
                                #print("            ii,json_key_3,json_value_3",ii,json_key_3,json_value_3);
                                #exit(0);
                                # If the type of json_value_3 is a list, we look through for PDS_NODE_IDENTIFIER
                                if isinstance(json_value_3,list):
                                    if found_identifier_flag and json_key_3 == 'PermissibleValueList':
                                        #print(function_name,"            #0001:FOUND_PDS_NODE_IDENTIFIER,json_key_3,json_value_3",json_key_3,json_value_3);
                                        #print(function_name,"            PermissibleValueList:json_value_3",json_value_3);
                                        #print(function_name,"            PermissibleValueList:len(json_value_3)",len(json_value_3));
                                        o_permissible_value_list = json_value_3;
                                        found_permissible_value_flag = True;  # Setting this to True allow the code to return immediatey.
                                        break;  # Break out of json_key_3, json_value_3 loop.
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
                                                        print(function_name,"            #0002:FOUND_PDS_NODE_IDENTIFIER,json_value_3",json_value_3);
                                                        print(function_name,"            FOUND_PDS_NODE_IDENTIFIER,json_value_4",json_value_4);
                                                        exit(0);
                                            if isinstance(json_value_4,list):
                                                print(function_name,"            FOUND_LIST:len(json_value_4)",len(json_value_4));
                                                print(function_name,"            FOUND_LIST:json_value_4",json_value_4);
                                                print(function_name,"            FOUND_LIST:json_key_1,json_key_2,json_key_3,json_key_4",json_key_1,json_key_2,json_key_3,json_key_4);
                                                exit(0);
                                else:
                                    #print(function_name,"JSON_KEY_3:",json_key_3,json_value_3);
                                    if json_key_3 == 'identifier' and json_value_3 == PDS_NODE_IDENTIFIER:
                                    #print(function_name,"            FOUND_PDS_NODE_IDENTIFIER,json_key_3,json_value_3",json_key_3,json_value_3);
                                        found_identifier_flag = True;
                                    if found_identifier_flag and json_key_3 == 'PermissibleValueList':
                                        print(function_name,"            FOUND_PDS_NODE_IDENTIFIER,json_key_3,json_value_3",json_key_3,json_value_3);
                                        print(function_name,"            PermissibleValueList",PermissibleValueList);
                                        exit(0);

                        # If json_value_2 is a list, we dig to the next level
                        if isinstance(json_value_2,list):
                            print(function_name,"        FOUND_LIST:json_key_1,json_key_2",json_key_1,json_key_2);
                            exit(0);
                    # end for ii in range(0,len(json_value_1)):

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
            if found_permissible_value_flag:
                pass;
            #print(function_name,"o_permissible_value_list",o_permissible_value_list);
            #print(function_name,"early#exit#0003");
            #exit(0);
            # end if isinstance(json_value_1,list) and json_key_1 == 'attributeDictionary':
            #print(function_name,"early#exit#0001");
            #exit(0);
            return(o_permissible_value_list);


if __name__ == '__main__':
    global f_log   
    global m_debug_mode
    function_name = 'main:';
    #print(function_name,'entering');
    f_log     = None; 
    m_debug_mode = True;
    m_debug_mode = False;
    doiContributorUtil = DOIContributorUtil();
