#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

import os
import shutil
import sys
#import unicodedata

from xml.etree import ElementTree
from lxml import etree
from lxml import html

from datetime import datetime
from time import gmtime,strftime
import xlrd

from const import *;

from DOIOutputUtil import DOIOutputUtil;

class DOIConfigUtil:
    global m_debug_mode;
    m_module_name = 'DOIConfigUtil:'
    m_debug_mode = False;
    #m_debug_mode = True;
    #m_debug_mode = False;
    m_DOIOutputUtil = DOIOutputUtil();

    def GetConfigFileMetaData(self,filename):
    #------------------------------
    #------------------------------
        function_name = self.m_module_name + 'GetConfigFileMetaData:'

        if (not os.path.exists(filename)):
            print("exiting: configuration file not found - " + filename);
            sys.exit();

        else:
            #------------------------------
            # Read the metadata in the configuration file
            #------------------------------
            with open(filename, 'rt') as f:
                tree = ElementTree.parse(f)
                doc  = tree.getroot()

        #------------------------------
        # Get the number of options in the config file
        #   <options numOptions="12">
        #------------------------------
        numOptions = tree.getroot().attrib.get("numOptions")
        #print "numOptions = '" + numOptions + "'"

        #------------------------------
        # Populate the dictionary with the options
        #------------------------------
        dict_configList = {}
        dict_configList = dict((e.tag, e.text) for e in doc)

        if (int(numOptions) == len(dict_configList)):
            #print("dict_configList: found correct number of options in dictionary: '" + numOptions + "'");
            pass;
        else:
            print("exiting: dict_configList -- number of options ('" + numOptions + "') doesn't match elements in dictionary: '" + str(len(dict_configList)) + "'");
            sys.exit()

    #      for eachElement in dict_configList:
    #         print "dict_configList." + eachElement + " == '" + dict_configList.get(eachElement) + "'"

        #------------------------------
        # Populate the dictionary with the fixed_attribute options
        #------------------------------
        e = doc.find("fixed_attributes")
        numOptions = e.attrib.get("numOptions")

        dict_fixedList = {}

        for e in doc.find('fixed_attributes'):
            dict_fixedList[e.tag] = e.text
        if (int(numOptions) == len(dict_fixedList)):
            #print("dict_fixedList: found correct number of options in dictionary: '" + numOptions + "'");
            pass;
        else:
            print("exiting: dict_fixedList -- number of options ('" + numOptions + "') doesn't match elements in dictionary: '" + str(len(dict_fixedList)) + "'");
            sys.exit();

        return(dict_configList, dict_fixedList);

if __name__ == '__main__':
    global m_debug_mode
    function_name = 'main:';
    #print(function_name,'entering');
    m_debug_mode = True;
    m_debug_mode = False;

    doiConfigUtil = DOIConfigUtil();

    # Get the default configuration from external file.  Location may have to be absolute.
    xmlConfigFile = '.' + os.path.sep + 'config' + os.path.sep + 'default_config.xml';

    dict_configList = {}
    dict_fixedList  = {}
    (dict_configList, dict_fixedList) = doiConfigUtil.GetConfigFileMetaData(xmlConfigFile);
    print(function_name,"dict_configList",dict_configList);
    print(function_name,"dict_fixedList",dict_fixedList);
