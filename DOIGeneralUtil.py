#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

import os

from xml.etree import ElementTree

from datetime import datetime
from time import gmtime,strftime                                                                                                

from const import *;

class DOIGeneralUtil:
    global m_debug_mode;
    global f_debug
    m_module_name = 'DOIGeneralUtil:'
    m_debug_mode = False;
    f_debug = None; 

    #------------------------------
    #------------------------------
    def ReturnDOIDate(self,f_debug, debug_flag, prodDate):
    #------------------------------
    # 20171207 -- prodDate -- date in: <modification_date>2015-07-14</modification_date>
    #              doiDate -- date formatted as: 'yyyy-mm-dd'
    #------------------------------

        doiDate = datetime.strptime(prodDate, '%Y-%m-%d').strftime('%m/%d/%Y');
        return(doiDate);

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def ReturnKeywordValues(self,dict_configList, list_keyword_values):
    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
        function_name = self.m_module_name + 'ReturnKeywordValues:';
        global m_debug_mode;
        #m_debug_mode = True;

        keywords = ""

        #------------------------------                                                                                                 
        # Add the global keyword values in the Config file to those scraped from the Product label
        #    -- <keywords> using the items in list_keyword_values
        #  -- each value must be separated by semi-colon (e.g., "test1; test2")
        # 
        # global_keyword_values preceed values scraped from Product label
        #------------------------------   
        global_keywords = dict_configList.get("global_keyword_values", 'None')
        if m_debug_mode:
            print(function_name,"global_keywords",global_keywords);

        if (global_keywords is not None):
            if (";" in global_keywords):
                kv = global_keywords.split(";")

                for items in kv:
                    if (not items == ""):
                        keywords += items + "; "
            else:
                if (not len(global_keywords) == 0):
                    keywords = global_keywords
                else:
                    keywords = "PDS; "
        else:
            keywords = ""

        #------------------------------                                                                                                 
        # Add the keyword values that were scraped from the Product label
        #    -- ensure no duplicate values between global and scraped
        #------------------------------   
        if (not len(list_keyword_values) == 0):
            for items in list_keyword_values:
                if (items not in keywords):
                    keywords += "; " + items

        if m_debug_mode:
            print(function_name,"list_keyword_values",len(list_keyword_values),list_keyword_values);

        return(keywords);


    #------------------------------
    #------------------------------
    def ReturnNameSpaceDictionary(self,f_debug, debug_flag, xmlFile,xmlContent=None):
    #------------------------------
    # 20170513 -- http://stackoverflow.com/questions/14853243/parsing-xml-with-namespace-in-python-via-elementtree
    #                -- generates dictionary of namespaces defined in the XML preamble
    #
    # eg:  {'': '"http://pds.nasa.gov/pds4/pds/v1',
    #        'pds': 'http://pds.nasa.gov/pds4/pds/v1',
    #        'dph': 'http://pds.nasa.gov/pds4/dph/v01'}
    #------------------------------

        function_name = self.m_module_name + 'ReturnNameSpaceDictionary:'
        #print(function_name,'xmlFile',xmlFile);
        #print(function_name,'xmlContent',xmlContent);

        #------------------------------
        # Create a DICT of namespaces identified in the XML label
        #------------------------------
        # 04/03/2020: New code: if the content of the XML is already in memory, we can use it.
        if (xmlContent is not None):
            from io import StringIO ## for Python 3
            # If the type of xmlContent are bytes, we convert it to string.
            #xmlContent_as_string = xmlContent;
            #if isinstance(xmlContent,bytes):
            #    xmlContent_as_string = xmlContent.decode();
            #print(function_name,'INSPECT_VARIABLE:type(xmlContent)',type(xmlContent));
            xmlContent_as_string = self.DecodeBytesToString(xmlContent);
            #print(function_name,'INSPECT_VARIABLE:xmlContent_as_string)',xmlContent_as_string);
            #print(function_name,'INSPECT_VARIABLE:type(xmlContent_as_string)',type(xmlContent_as_string));
            dict_namespaces = dict([
                node for _, node in ElementTree.iterparse(StringIO(xmlContent_as_string), events=['start-ns'])
        ])
            #print(function_name,'NAME_SPACE_SUCCESS',dict_namespaces);
            #exit(0);
            return dict_namespaces

        #------------------------------
        # Create a DICT of namespaces identified in the XML label
        #------------------------------
        dict_namespaces = dict([
        node for _, node in ElementTree.iterparse(xmlFile, events=['start-ns'])
        ])

        return dict_namespaces

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def ReturnRelativePathAndFileName(self,rootPath, pathName):                                                                         
    #------------------------------                                                                                                 
    #-------------------------                                                                                                      
        function_name = self.m_module_name + 'ReturnRelativePathAndFileName:'

        RelPath  = "";
        FileName = "";

        #------------------------------                                                                                             
        # establish the path for the working directory                                                                              
        #  -- C:\\test\test.xml                                                                                                     
        #------------------------------                                                                                             
        #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.rootPath: " + rootPath + "\n")                          
        if m_debug_mode:
            print(function_name,"rootPath: " + rootPath);
            print(function_name,"pathName: " + pathName);

        #------------------------------                                                                                             
        # Remove the working directory from the Path&FileName                                                                       
        #   --- residual is either just a filename or child subdirectories and a filename                                           
        #------------------------------                                                                                             
        a = pathName.replace(rootPath, "")
        #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.a: " + a + "\n")                                        
        if m_debug_mode:
            print(function_name,"a: " + a);

        #------------------------------                                                                                             
        # Check is there are 1 or more child directories                                                                            
        #------------------------------                                                                                             
        chr_92 = os.path.sep;
        if m_debug_mode:
            print(function_name,"chr_92 in a",chr_92 in a);
        if (chr_92 in a):
            fields = a.split(chr_92)

            iFields = len(fields)
            if m_debug_mode:
                print(function_name,"fields,iFields",fields,iFields);
        #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iFields: " + str(iFields) + "\n")                   

            if (iFields == 2):
                #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iFields == 2\n")                                
                RelPath = ""
                FileName = fields[1]
            elif (iFields == 3):
                #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iFields == 3\n")                                
                RelPath = fields[1]
                FileName = fields[2]
            elif (iFields > 3):
                #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iFields > 3\n")                                 
                FileName = fields[iFields-1]
                RelPath = fields[1] + chr_92

                iCount  = 0

                for eachField in fields:
                    if (iCount > 1) and (iCount < iFields-1):
                        RelPath += fields[iCount]

                        util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iCount: " + str(iCount) + "\n")  
                        util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.RelPath: " + RelPath + "\n")     

                        #------------------------------                                                                             
                        # No trailing file delimiter                                                                                
                        #------------------------------                                                                             
                        if (iCount < (iFields-2)):
                            RelPath += chr_92

                    iCount += 1

            else:                                                                                                                       
                RelPath = ""                                                                                                            
                FileName = a                                                                                                            

        #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.RelPath: " + RelPath + "\n")                            
        #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.FileName: " + FileName + "\n")                          
        if m_debug_mode:
            print(function_name,"RelPath",RelPath);
            print(function_name,"FileName",FileName);

        return RelPath, FileName

    def DecodeBytesToString(self,xmlContent):
        o_string = None;
        o_xmlContent_as_string = xmlContent
        if isinstance(xmlContent,bytes):
            o_xmlContent_as_string = xmlContent.decode();

        return(o_xmlContent_as_string);

if __name__ == '__main__':
    from DOIInputUtil import DOIInputUtil
    from DOIConfigUtil import DOIConfigUtil
    global m_debug_mode
    function_name = 'main:';
    #print(function_name,'entering');
    m_debug_mode = False;

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
