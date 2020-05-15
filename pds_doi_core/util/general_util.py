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
    def return_doi_date(self,f_debug, debug_flag, i_prod_date):
    #------------------------------
    # 20171207 -- i_prod_date -- date in: <modification_date>2015-07-14</modification_date>
    #              o_doi_date -- date formatted as: 'yyyy-mm-dd'
    #------------------------------

        o_doi_date = datetime.strptime(i_prod_date, '%Y-%m-%d').strftime('%m/%d/%Y')
        return(o_doi_date)

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def return_keyword_values(self,i_dict_config_list, i_list_keyword_values):
    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
        o_keywords = ""

        #------------------------------                                                                                                 
        # Add the global keyword values in the Config file to those scraped from the Product label
        #    -- <keywords> using the items in list_keyword_values
        #  -- each value must be separated by semi-colon (e.g., "test1 test2")
        # 
        # global_keyword_values preceed values scraped from Product label
        #------------------------------   
        global_keywords = i_dict_config_list.get("global_keyword_values", 'None')

        logger.debug("global_keywords " + str(global_keywords))

        if (global_keywords is not None):
            if ("" in global_keywords):
                kv = global_keywords.split(";")  # Split using semi-colon

                for items in kv:
                    if (not items == ""):
                        o_keywords += items + "; " # Add semi-colon between each keyword
            else:
                if (not len(global_keywords) == 0):
                    o_keywords = global_keywords
                else:
                    o_keywords = "PDS "
        else:
            o_keywords = ""

        #------------------------------                                                                                                 
        # Add the keyword values that were scraped from the Product label
        #    -- ensure no duplicate values between global and scraped
        #------------------------------   
        if (not len(i_list_keyword_values) == 0):
            for items in i_list_keyword_values:
                if (items not in o_keywords):
                    o_keywords += " " + items

        logger.debug("i_list_keyword_values " + str(len(i_list_keyword_values)) + str(i_list_keyword_values))

        return(o_keywords)


    #------------------------------
    #------------------------------
    def return_name_space_dictionary(self,f_debug, debug_flag, i_xml_file,i_xml_content=None):
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
        if (i_xml_content is not None):
            from io import StringIO ## for Python 3
            # If the type of i_xml_content are bytes, we convert it to string.
            #i_xml_content_as_string = i_xml_content
            #if isinstance(i_xml_content,bytes):
            #    i_xml_content_as_string = i_xml_content.decode()
            xml_content_as_string = self.decode_bytes_to_string(i_xml_content)
            o_dict_namespaces = dict([
                node for _, node in ElementTree.iterparse(StringIO(xml_content_as_string), events=['start-ns'])
        ])
            return o_dict_namespaces

        #------------------------------
        # Create a DICT of namespaces identified in the XML label
        #------------------------------
        o_dict_namespaces = dict([
        node for _, node in ElementTree.iterparse(i_xml_file, events=['start-ns'])
        ])

        return o_dict_namespaces

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def return_relative_path_and_filename(self,i_root_path, i_pathname):                                                                         
    #------------------------------                                                                                                 
    #-------------------------                                                                                                      
        #RelPath  = ""
        #FileName = ""
        o_rel_path  = ""
        o_filename  = ""

        #------------------------------                                                                                             
        # establish the path for the working directory                                                                              
        #  -- C:\\test\test.xml                                                                                                     
        #------------------------------                                                                                             

        #------------------------------                                                                                             
        # Remove the working directory from the Path&FileName                                                                       
        #   --- residual is either just a filename or child subdirectories and a filename                                           
        #------------------------------                                                                                             
        a = i_pathname.replace(i_root_path, "")

        #------------------------------                                                                                             
        # Check is there are 1 or more child directories                                                                            
        #------------------------------                                                                                             
        chr_92 = os.path.sep
        if (chr_92 in a):
            fields = a.split(chr_92)

            iFields = len(fields)

            if (iFields == 2):
                o_rel_path = ""
                o_filename = fields[1]
            elif (iFields == 3):
                o_rel_path = fields[1]
                o_filename = fields[2]
            elif (iFields > 3):
                o_filename = fields[iFields-1]
                o_rel_path = fields[1] + chr_92

                iCount  = 0

                for eachField in fields:
                    if (iCount > 1) and (iCount < iFields-1):
                        o_rel_path += fields[iCount]

                        util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iCount: " + str(iCount) + "\n")  
                        util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.o_rel_path: " + o_rel_path + "\n")     

                        #------------------------------                                                                             
                        # No trailing file delimiter                                                                                
                        #------------------------------                                                                             
                        if (iCount < (iFields-2)):
                            o_rel_path += chr_92

                    iCount += 1

            else:                                                                                                                       
                o_rel_path = ""                                                                                                            
                o_filename = a                                                                                                            

        logger.debug("o_rel_path %s" % o_rel_path)
        logger.debug("o_filename %s" % o_filename)

        return o_rel_path, o_filename

    def decode_bytes_to_string(self,i_xml_content):
        o_string = None
        o_xml_content_as_string = i_xml_content
        if isinstance(i_xml_content,bytes):
            o_xml_content_as_string = i_xml_content.decode()

        return(o_xml_content_as_string)

if __name__ == '__main__':
    from pds_doi_core.input.input_util import DOIInputUtil
    from pds_doi_core.util.config_parser import DOIConfigUtil

    function_name = 'main:'

    xls_filepath = os.path.join('.','input','DOI_Reserved_GEO_200318.xlsx')

    doiInputUtil = DOIInputUtil()
    doiConfigUtil = DOIConfigUtil()
    doiGeneralUtil = DOIGeneralUtil()

    i_root_path = './'
    i_pathname ='./zzz'
    (o_rel_path,o_filename) = doiGeneralUtil.return_relative_path_and_filename(i_root_path, i_pathname)

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
