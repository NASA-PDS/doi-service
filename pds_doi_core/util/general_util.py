#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------
import logging
from xml.etree import ElementTree
from datetime import datetime
from pds_doi_core.util.const import *

# Put the function get_logger here in the beginning of the file so we can call it.
def get_logger(module_name=''):
    # If the user specify the module name, we can use it.
    if module_name != '':
        logger =logging.getLogger(module_name)
    else:
        logger =logging.getLogger(__name__)
    my_format = "%(levelname)s %(name)s:%(funcName)s %(message)s"
    logging.basicConfig(filename="pds_doi_core.log",
                        format=my_format,
                        filemode='a')

    logger.setLevel(logging.DEBUG)
    return logger

# Get the common logger and set the level for this file.
import logging
logger = get_logger()
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

class DOIGeneralUtil:
    global f_debug
    m_module_name = 'DOIGeneralUtil:'
    f_debug = None 

    #------------------------------
    #------------------------------
    def return_doi_date(self,f_debug, debug_flag, prodDate):
    #------------------------------
    # 20171207 -- prodDate -- date in: <modification_date>2015-07-14</modification_date>
    #              doiDate -- date formatted as: 'yyyy-mm-dd'
    #------------------------------

        doiDate = datetime.strptime(prodDate, '%Y-%m-%d').strftime('%m/%d/%Y')
        return(doiDate)

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def return_keyword_values(self,dict_configList, list_keyword_values):
    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
        keywords = ""

        #------------------------------                                                                                                 
        # Add the global keyword values in the Config file to those scraped from the Product label
        #    -- <keywords> using the items in list_keyword_values
        #  -- each value must be separated by semi-colon (e.g., "test1 test2")
        # 
        # global_keyword_values preceed values scraped from Product label
        #------------------------------   
        global_keywords = dict_configList.get("global_keyword_values", 'None')

        logger.debug("global_keywords " + str(global_keywords))

        if (global_keywords is not None):
            if ("" in global_keywords):
                kv = global_keywords.split(";")  # Split using semi-colon

                for items in kv:
                    if (not items == ""):
                        keywords += items + " "
            else:
                if (not len(global_keywords) == 0):
                    keywords = global_keywords
                else:
                    keywords = "PDS "
        else:
            keywords = ""

        #------------------------------                                                                                                 
        # Add the keyword values that were scraped from the Product label
        #    -- ensure no duplicate values between global and scraped
        #------------------------------   
        if (not len(list_keyword_values) == 0):
            for items in list_keyword_values:
                if (items not in keywords):
                    keywords += " " + items

        logger.debug("list_keyword_values " + str(len(list_keyword_values)) + str(list_keyword_values))

        return(keywords)


    #------------------------------
    #------------------------------
    def return_name_space_dictionary(self,f_debug, debug_flag, xmlFile,xmlContent=None):
    #------------------------------
    # 20170513 -- http://stackoverflow.com/questions/14853243/parsing-xml-with-namespace-in-python-via-elementtree
    #                -- generates dictionary of namespaces defined in the XML preamble
    #
    # eg:  {'': '"http://pds.nasa.gov/pds4/pds/v1',
    #        'pds': 'http://pds.nasa.gov/pds4/pds/v1',
    #        'dph': 'http://pds.nasa.gov/pds4/dph/v01'}
    #------------------------------

        #------------------------------
        # Create a DICT of namespaces identified in the XML label
        #------------------------------
        # 04/03/2020: New code: if the content of the XML is already in memory, we can use it.
        if (xmlContent is not None):
            from io import StringIO ## for Python 3
            # If the type of xmlContent are bytes, we convert it to string.
            #xmlContent_as_string = xmlContent
            #if isinstance(xmlContent,bytes):
            #    xmlContent_as_string = xmlContent.decode()
            xmlContent_as_string = self.decode_bytes_to_string(xmlContent)
            dict_namespaces = dict([
                node for _, node in ElementTree.iterparse(StringIO(xmlContent_as_string), events=['start-ns'])
        ])
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
    def return_relative_path_and_filename(self,rootPath, pathName):                                                                         
    #------------------------------                                                                                                 
    #-------------------------                                                                                                      
        RelPath  = ""
        FileName = ""

        #------------------------------                                                                                             
        # establish the path for the working directory                                                                              
        #  -- C:\\test\test.xml                                                                                                     
        #------------------------------                                                                                             

        #------------------------------                                                                                             
        # Remove the working directory from the Path&FileName                                                                       
        #   --- residual is either just a filename or child subdirectories and a filename                                           
        #------------------------------                                                                                             
        a = pathName.replace(rootPath, "")

        #------------------------------                                                                                             
        # Check is there are 1 or more child directories                                                                            
        #------------------------------                                                                                             
        chr_92 = os.path.sep
        if (chr_92 in a):
            fields = a.split(chr_92)

            iFields = len(fields)

            if (iFields == 2):
                RelPath = ""
                FileName = fields[1]
            elif (iFields == 3):
                RelPath = fields[1]
                FileName = fields[2]
            elif (iFields > 3):
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

        logger.debug("RelPath %s" % RelPath)
        logger.debug("FileName %s" % FileName)

        return RelPath, FileName

    def decode_bytes_to_string(self,xmlContent):
        o_string = None
        o_xmlContent_as_string = xmlContent
        if isinstance(xmlContent,bytes):
            o_xmlContent_as_string = xmlContent.decode()

        return(o_xmlContent_as_string)

if __name__ == '__main__':
    from pds_doi_core.input.input_util import DOIInputUtil
    from pds_doi_core.util.config_parser import DOIConfigUtil

    function_name = 'main:'

    xls_filepath = os.path.join('.','input','DOI_Reserved_GEO_200318.xlsx')

    doiInputUtil = DOIInputUtil()
    doiConfigUtil = DOIConfigUtil()
    doiGeneralUtil = DOIGeneralUtil()

    rootPath = './'
    pathName ='./zzz'
    (RelPath,FileName) = doiGeneralUtil.return_relative_path_and_filename(rootPath, pathName)

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
