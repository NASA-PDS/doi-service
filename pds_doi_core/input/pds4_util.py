#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

from xml.etree import ElementTree
from lxml import etree

import requests

from datetime import datetime                                                                                                   

from pds_doi_core.util.const import *

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import DOIGeneralUtil, get_logger
from pds_doi_core.outputs.output_util import DOIOutputUtil

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.input.pds4_util')
logger.setLevel(logging.INFO)  # Comment this line once happy with the level of logging set in get_logger() function.
#logger.setLevel(logging.DEBUG)  # Comment this line once happy with the level of logging set in get_logger() function.
# Note that the get_logger() function may already set the level higher (e.g. DEBUG).  Here, we may reset
# to INFO if we don't want debug statements.

class DOIPDS4LabelUtil:
    global f_debug
    global debug_flag
    f_debug   = None                                                                                    
    debug_flag= False
    m_module_name = 'DOIPDS4LabelUtil:'

    m_doiConfigUtil = DOIConfigUtil()
    m_doiGeneralUtil = DOIGeneralUtil()
    m_doiOutputUtil = DOIOutputUtil()

    #------------------------------                                                                                                 
    def process_iad2_product_label_metadata(self,dict_fixedList, dict_ConditionData, eachFile, FileName, xmlContent=None):
        global f_debug,debug_flag

        pds_uri    = dict_fixedList.get("pds_uri")
        pds_uri_string = "{" + pds_uri + "}"

        logger.debug(f"eachFile {eachFile} FileName {FileName}")
        logger.debug(f"pds_uri_string {pds_uri_string}")
        logger.debug("len(xmlContent) " + str(len(xmlContent)))

        #------------------------------
        # Read the IM Test_Case manifest file
        #   -- for each <test_case> get dictionary of metadata
        #
        #  dict{0: (tuple),
        #       1: (tuple)}
        #
        # intialize the items in the dictionary to defaults:
        #
        #------------------------------
        #  dict_ConditionData[FileName]["title"]
        #  dict_ConditionData[FileName]["accession_number"]
        #  dict_ConditionData[FileName]["publication_date"]
        #  dict_ConditionData[FileName]["description"]
        #  dict_ConditionData[FileName]["site_url"]
        #  dict_ConditionData[FileName]["product_type"]
        #  dict_ConditionData[FileName]["product_type_specific"]
        #  dict_ConditionData[FileName]["date_record_added"]
        #  dict_ConditionData[FileName]["authors/author/last_name"]
        #  dict_ConditionData[FileName]["authors/author/first_name"] 
        #  dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"]
        #------------------------------          
        dict_ConditionData[FileName] = {}
        
        dict_ConditionData[FileName]["title"] = ""
        dict_ConditionData[FileName]["accession_number"] = ""
        dict_ConditionData[FileName]["publication_date"] = ""
        dict_ConditionData[FileName]["description"] = ""
        dict_ConditionData[FileName]["site_url"] = ""
        dict_ConditionData[FileName]["product_type"] = ""
        dict_ConditionData[FileName]["product_type_specific"] = ""
        dict_ConditionData[FileName]["date_record_added"] = ""
        dict_ConditionData[FileName]["authors/author/last_name"] = ""
        dict_ConditionData[FileName]["authors/author/first_name"]  = ""
        dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"] = ""

        logger.debug(f"processing Product label file: {eachFile}")
        
        #------------------------------
        # Read the XML label
        #   -- generate a DICT of the identified namespaces in the XML preamble
        #         -- etree XML parser errors if encounters 'Null' namespace so delete from DICT
        #------------------------------
        global dict_namespaces
        dict_namespaces = self.m_doiGeneralUtil.return_name_space_dictionary(f_debug, debug_flag, eachFile,xmlContent)
        
        #------------------------------
        # Open the XML label 
        #   --  ElementTree supports 'findall' using dict_namespaces and designation of instances
        #   -- etree doesn't support designation of instances
        #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
        #------------------------------
        # TODO: Remove next line.
        #xmlContent = None
        try:  
            if os.path.isfile(eachFile):
                tree = etree.parse(eachFile)
                xmlProd_root = tree.getroot()
            else:
                    # If the actual content of the XML to be parsed is already in memory, we use it.
                if xmlContent is not None:
                    # If we are reading from string, the value of tree should be set to None.
                    tree = None
                    xmlProd_root = etree.fromstring(xmlContent)
                else:
                    logger.error(f"xmlContent is None and os.path.isfile({eachFile}) is false")
                    exit(1) 
        
        except etree.ParseError as err:
            logger.error(f"Parse error:{err}")
            exit(1)
            sString = "  -- ABORT: the xml 'Product label file (%s) could not be parsed\n" % (eachFile)                
            f_inventory.write(sString)
            sString = "      -- %s\n" % (err)
            f_inventory.write(sString)
            sys.exit(1)
        
        else:                      
            #------------------------------
            #------------------------------
            # Iterate over each <test_case> specified in the TC Manifest file
            #    -- for each <test_case> use the metadata to:
            #         -- create a PDS4 XML label 
            #         -- modify the 'template' using the xpath and value_settings
            #         -- create the XML output label file
            #
            # Each TestCase consists of the following metadata:
            #   -- test_case name: unique identifier of the <test_case>
            #   -- state: isValid | notValid indicates if values in test-case are either valid or not
            #   -- <conditions> values must be paired:
            #        -- xpath: xPath of XML attribute to be modified 
            #        -- value_set: Value or set of values to overwrite value in xPath
            #   -- inFile: XML template to use for modifying metadata
            #   -- outFile: PDS4 XML file to be written as TestCase
            #
            #------------------------------
            #------------------------------

            #------------------------------
            # Initialize the various URIs 
            #------------------------------ 
            objIdentArea_uri  = pds_uri_string + "Identification_Area"
            objBundle_uri     = pds_uri_string + "Bundle"
            objCollection_uri = pds_uri_string + "Collection"
            isBundle          = False
            isCollection      = False

            objLID_uri       = pds_uri_string + "logical_identifier"
            objVID_uri       = pds_uri_string + "version_id"                                                    
            objTitle_uri     = pds_uri_string + "title"
            objProdClass_uri = pds_uri_string + "product_class" 
            objPubYear_uri   = pds_uri_string + "publication_year"
            objPubDate_uri   = pds_uri_string + "modification_date"
            objDescript_uri  = pds_uri_string + "description" 
            objAuthList_uri  = pds_uri_string + "author_list" 
            objEditorList_uri  = pds_uri_string + "editor_list" 
            
            #------------------------------
            # Initialize the Class and Attribute URIs for discovering <keywords>
            #------------------------------ 
            objInvestigArea_uri    = pds_uri_string + "Investigation_Area"
            objCitationInfo_uri    = pds_uri_string + "Citation_Information"
            objObsSysCompArea_uri  = pds_uri_string + "Observing_System_Component"
            objTargetIdentArea_uri = pds_uri_string + "Target_Identification" 
            objPrimResSumArea_uri  = pds_uri_string + "Primary_Result_Summary" 
            objSciFacetsArea_uri   = pds_uri_string + "Science_Facets" 
                
            objName_uri      = pds_uri_string + "name"
            objProcLevel_uri = pds_uri_string + "processing_level"
            objDomain_uri    = pds_uri_string + "domain"
            objDiscpName     = pds_uri_string + "discipline_name"
            objFacet1        = pds_uri_string + "facet1"
            objFacet2        = pds_uri_string + "facet2"
            
            #------------------------------
            # Initialize the List of <keywords> value
            #------------------------------
            list_keyword_values = []
            
            #------------------------------
            # Walk the XML looking for <child> elements
            #------------------------------        
            element_count = 0
            string_to_walk = eachFile
            # If the file is a valid file, walk through it.
            # TODO: Remove next line.
            #xmlContent = None
            if os.path.isfile(eachFile):
                context = etree.iterparse(string_to_walk, events=("start", "end"))
            else:
                # If the value of eachFile is not a valid file, check to see if it has been read into memory already.
                if xmlContent is not None:
                    from io import StringIO # for Python 3
                    string_to_walk = self.m_doiGeneralUtil.decode_bytes_to_string(xmlContent)   # The content may be a bunch of bytes.
                    string_to_walk = StringIO(string_to_walk)          # Convert the bytes to string so we can walk through.
                    context = ElementTree.iterparse(string_to_walk, events=("start", "end"))
                else:
                    logger.error(f"xmlContent is None and os.path.isfile({eachFile}) is false")
                    exit(1) 

            # Old method:
            #    for event, element in etree.iterparse(eachFile, events=("start", "end")):
            # A new way to walk.  If the xml content has already been read into memory, we can walk it.

            parentNode = None  # Added this to we know to look for parent using alternate method.
            for event, element in context:
                #parentNode = None  # Added this to we know to look for parent using alternate method.
                element_count += 1

                #------------------------------
                # <Identification_Area>
                #------------------------------
                if (element.tag == objIdentArea_uri):
                    if (event == "start"):
                        inIdentArea = True
                        parentNode = element # Remember who your parent is for objIdentArea_uri tag.
                    if (event == 'end'):
                        parentNode = None    # Reset parentNode to None to force the next event to set it to valid value.

                # We have to remember the parent for each tag found below.

                parentNode = self.process_parent_node(parentNode,pds_uri_string,element,event)
                       
                #------------------------------
                # <logical_identifier>
                #------------------------------
                if (element.tag == objLID_uri):
                    if (event == "start"):
                        LID_value = element.text
            
                    #------------------------------                                                                                     
                    # Convert LID to URL for <site_url>                                                                                       
                    #------------------------------                                                                                     
                    LID_url_value = LID_value.replace(":", "%3A")

                #------------------------------
                # <version_id> -- <product_nos>
                #  -- use <version_id> in <Identification_Area>
                #  -- DO NOT use <version_id> in <Modification_Detail>
                #------------------------------
                if (element.tag == objVID_uri):
                    if (event == "start"):
                        if (parentNode is not None):
                            pass
                        # For some strange reason, if reading in the XML from memory, the following lines does not work
                        # and complains about "AttributeError: 'xml.etree.ElementTree.Element' object has no attribute 'iterancestors'"
                        # So the solution is to comment it out and put a try and catch and use something else.
                        #parentNode = next(element.iterancestors())
                        if parentNode is None:
                            parentNode = next(element.iterancestors())
                    
                    if (parentNode.tag == objIdentArea_uri):
                        VID_value = element.text                    
                    
                        # Not sure why the below was commented out.  Uncomment it out.
                        dict_ConditionData[FileName]["product_nos"] = LID_value + "::" + VID_value
                        dict_ConditionData[FileName]["accession_number"]  = LID_value + "::" + VID_value                                                
                        dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"]  = LID_value + "::" + VID_value
                    
                #------------------------------
                # <title> -- <title>
                #------------------------------
                if (element.tag == objTitle_uri):
                    if (event == "start"):
                        Title_value = element.text
                        dict_ConditionData[FileName]["title"] = Title_value                                                        

                #------------------------------
                # <product_class> -- <product_type>: Collection | Dataset
                #                 -- <site_url>
                #------------------------------
                if (element.tag == objProdClass_uri):
                    if (event == "start"):
                        ProdClass_value = element.text
                    
                        if ("Bundle" in ProdClass_value):
                            isBundle = True
                    #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&ampversion=" + VID_value
                            url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&version=" + VID_value

                            dict_ConditionData[FileName]["product_type"] = "Collection"
                            dict_ConditionData[FileName]["product_type_specific"] = "PDS4 Bundle"
                            dict_ConditionData[FileName]["site_url"] = url_value
                        elif ("Collection" in ProdClass_value):                        
                            isCollection = True
                    #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&ampversion=" + VID_value
                            url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&version=" + VID_value

                            dict_ConditionData[FileName]["product_type"] = "Dataset"
                            dict_ConditionData[FileName]["product_type_specific"] = "PDS4 Collection"
                            dict_ConditionData[FileName]["site_url"] = url_value

                        elif ("Document" in ProdClass_value):                        
                            logger.error(f"<product_class> in Product XML label is Document (which is not yet supported): {ProdClass_value}")
                            sys.exit(1)

                        else:
                            logger.error(f"<product_class> in Product XML label not Collection or Bundle: {ProdClass_value}")
                            sys.exit(1)
                                        
                #------------------------------
                # <publication_year>  -- <publication_date>
                #   -- convert: yyyy to yyyy to yyyy-mm-dd
                #------------------------------
                if (element.tag == objPubYear_uri) or (element.tag == objPubDate_uri):
                    if (event == "start"):
                        PubDate_value = element.text
                        lenPubDate = len(PubDate_value)
                    
                        if (lenPubDate == 4):
                            PubDate_value = PubDate_value + "-01-01"
                        else:
                            PubDate_value = str(datetime.now().year) + "-01-01"
                    
                        dict_ConditionData[FileName]["publication_date"] = PubDate_value                                             
                        dict_ConditionData[FileName]["date_record_added"] = PubDate_value   
                        dict_ConditionData[FileName]["publication_date"]  = self.m_doiGeneralUtil.return_doi_date(f_debug,debug_flag,PubDate_value) # Conver to DOI format
                        dict_ConditionData[FileName]["date_record_added"] = self.m_doiGeneralUtil.return_doi_date(f_debug,debug_flag,PubDate_value) # Conver to DOI format
                    
                #------------------------------
                # <description> -- <Identification_Area/Citation_Information/description>
                #------------------------------
                if (element.tag == objDescript_uri):
                    #------------------------------
                    # Get the <xpath> value
                    #  -- use <description> in <Bundle> or <Collection>
                    #------------------------------
                    if (event == "start"):
                        #parentNode = next(element.iterancestors())
                        if parentNode is None:
                            parentNode = next(element.iterancestors())
                
                        if (parentNode.tag == objCitationInfo_uri):                   
                            Descript_value = element.text
                            dict_ConditionData[FileName]["description"] = Descript_value                                                        
                        #parentNode = None # Reset parentNode to None to force the next event to set it to valid value.

                #------------------------------
                # <author_list> -- <Identification_Area/Citation_Information/author_list>
                #                      -- <Identification_Area/Citation_Information/editor_list>
                #------------------------------
                #if (element.tag == objAuthList_uri) or (element.tag == objEditorList_uri):
                if (element.tag == objAuthList_uri):
                    #------------------------------
                    # Get the <xpath> value
                    #  -- use <description> in <Bundle> or <Collection>
                    #------------------------------
                    if (event == "start"):
                        #parentNode = next(element.iterancestors())
                        if parentNode is None:
                            parentNode = next(element.iterancestors())
                
                        #------------------------------
                        # Parse <author_list>
                        #  -- split author by '' then split by ',' to get <author_last_name> & <author_first_name>
                        #
                        #  <author_list>French, R. G. McGhee-French, C. A. Gordon, M. K.</author_list>
                        #------------------------------                                
                        if (parentNode.tag == objCitationInfo_uri):                   
                            author_list = element.text
                     
                            items = author_list.split(";")
                            items2 = items[0].split(",")

                        dict_ConditionData[FileName]["authors/author/last_name"] =  items2[0]
                        dict_ConditionData[FileName]["authors/author/first_name"]  =  items2[1]

                        # NOTE_FROM_QUI: <author_list>R. Deen, H. Abarca, P. Zamani, J.Maki</author_list>
                        # Handle special case when the names are delimited using comma instead of 
                        #ProcessIAD2ProductLabelMetadata: len(items),items 1 ['R. Deen, H. Abarca, P. Zamani, J.Maki']
                        #ProcessIAD2ProductLabelMetadata: len(items2),items2 4 ['R. Deen', ' H. Abarca', ' P. Zamani', ' J.Maki']
                        #ProcessIAD2ProductLabelMetadata: element.text R. Deen, H. Abarca, P. Zamani, J.Maki
                        if len(items) == 1:
                            items3 = items[0].split(',')  # Split 'R. Deen, H. Abarca, P. Zamani, J.Maki' into ['R. Deen','H. Abarca','P. Zamani','J.Maki'
                            last_names_list  = []
                            first_names_list = []
                            for ii in range(0,len(items3)):
                                items4 = items3[ii].split('.')  # Split 'R. Deen' into ['R.''Deen']
                                first_names_list.append(items4[0] + '.')  # Collect the first name to first_names_list.  Add the '.' back to first name.
                                last_names_list.append (items4[1])        # Collect the last name to last_names_list.
                            dict_ConditionData[FileName]["authors/author/last_name"]   =  last_names_list
                            dict_ConditionData[FileName]["authors/author/first_name"]  =  first_names_list

                            # Add to creators field.
                            dict_ConditionData[FileName]["creators"] = author_list 
                            #dict_ConditionData[FileName]["accession_number"] = ""

                if (element.tag == objEditorList_uri):
                    #------------------------------
                    # Get the <xpath> value
                    #  -- use <description> in <Bundle> or <Collection>
                    #------------------------------
                    if (event == "start"):
                        #parentNode = next(element.iterancestors())
                        if parentNode is None:
                            parentNode = next(element.iterancestors())
                
                        #------------------------------
                        # Parse <editor_list>
                        #  -- split author by '' then split by ',' to get <author_last_name> & <author_first_name>
                        #
                        #  <editor_list>Smith, P. H. Lemmon, M. Beebe, R. F.</editor_list>

                        #------------------------------                                
                        if (parentNode.tag == objCitationInfo_uri):                   
                            editor_list = element.text
                     
                            items = editor_list.split("")
                            items2 = items[0].split(",")

                        dict_ConditionData[FileName]["contributors/contributor/last_name"] =  items2[0]
                        dict_ConditionData[FileName]["contributors/contributor/first_name"]  =  items2[1]
                        # NOTE_FROM_QUI: <editor_list>Smith, P. H. Lemmon, M. Beebe, R. F.</editor_list>
                        # Handle special case when the names are delimited using comma instead of 
                        #ProcessIAD2ProductLabelMetadata: len(items),items 1 ['R. Deen, H. Abarca, P. Zamani, J.Maki']
                        #ProcessIAD2ProductLabelMetadata: len(items2),items2 4 ['R. Deen', ' H. Abarca', ' P. Zamani', ' J.Maki']
                        #ProcessIAD2ProductLabelMetadata: element.text R. Deen, H. Abarca, P. Zamani, J.Maki
                        if len(items) == 1:
                            items3 = items[0].split(',')  # Split 'R. Deen, H. Abarca, P. Zamani, J.Maki' into ['R. Deen','H. Abarca','P. Zamani','J.Maki'
                            last_names_list  = []
                            first_names_list = []
                            for ii in range(0,len(items3)):
                                items4 = items3[ii].split('.')  # Split 'R. Deen' into ['R.''Deen']
                                first_names_list.append(items4[0] + '.')  # Collect the first name to first_names_list.  Add the '.' back to first name.
                                last_names_list.append (items4[1])        # Collect the last name to last_names_list.
                            dict_ConditionData[FileName]["contributors/contributor/last_name"]   =  last_names_list
                            dict_ConditionData[FileName]["contributors/contributor/first_name"]  =  first_names_list

                            # Add to creators field.
                            dict_ConditionData[FileName]["editors"] = editor_list 
                            #dict_ConditionData[FileName]["accession_number"] = ""
                        else:  # There are more than 1 element in items, which means we have ['Smith, P. H.', ' Lemmon, M.', ' Beebe, R. F.']
                            last_names_list  = []
                            first_names_list = []
                            for ii in range(0,len(items)):
                                items4 = items[ii].split(',')  # Split 'Smith, P. H. into ['Smith','P. H.']
                                last_names_list.append (items4[0])  # Collect the last name to last_names_list.
                                first_names_list.append(items4[1])  # Collect the first name to first_names_list
                            dict_ConditionData[FileName]["contributors/contributor/last_name"]   =  last_names_list
                            dict_ConditionData[FileName]["contributors/contributor/first_name"]  =  first_names_list
                            # Add to editor field.
                            dict_ConditionData[FileName]["editors"] = editor_list 
                # end if (element.tag == objEditorList_uri):

                #------------------------------
                # <keywords>.name
                #   -- parent is: <Investigation_Area>
                #                 <Observing_System_Component>
                #                 <Target_Identification>
                #------------------------------
                if (element.tag == objName_uri):
                    #------------------------------
                    # Get the <xpath> value
                    #  -- use <name> in any of the above named Parent objects
                    #------------------------------
                    if (event == "start"):
                        #parentNode = next(element.iterancestors())
                        if parentNode is None:
                            parentNode = next(element.iterancestors())
                
                        if (parentNode.tag == objInvestigArea_uri) or (parentNode.tag == objObsSysCompArea_uri) or (parentNode.tag == objTargetIdentArea_uri):                   
                            keyword_value = element.text
                    
                            # only check for the presence of keyword_value                        
                            if (not (keyword_value in list_keyword_values)):
                                list_keyword_values.append(keyword_value)
                           
                #------------------------------
                # <keywords>.processing_level
                #   -- parent is: <Primary_Result_Summary>

                #------------------------------
                if (element.tag == objProcLevel_uri):
                    #------------------------------
                    # Get the <xpath> value
                    #  -- use <name> in any of the above named Parent objects
                    #------------------------------
                    if (event == "start"):
                        #parentNode = next(element.iterancestors())
                        if parentNode is None:
                            parentNode = next(element.iterancestors())
                
                        if (parentNode.tag == objPrimResSumArea_uri):                   
                            keyword_value = element.text
                    
                            if (not (keyword_value in list_keyword_values)):
                                list_keyword_values.append(keyword_value)
                                
                #------------------------------
                # <keywords>.science_facets
                #   -- parent is: <Science_Facets>
                #------------------------------
                if (element.tag == objDomain_uri) or (element.tag == objDiscpName) or (element.tag == objFacet1) or (element.tag == objFacet2):
                    #------------------------------
                    # Get the <xpath> value
                    #  -- use <name> in any of the above named Parent objects
                    #------------------------------
                    if (event == "start"):
                        #parentNode = next(element.iterancestors())
                        if parentNode is None:
                            parentNode = next(element.iterancestors())
                
                        if (parentNode.tag == objSciFacetsArea_uri):                   
                            keyword_value = element.text
                    
                            if (not (keyword_value in list_keyword_values)):
                                list_keyword_values.append(keyword_value)

            #------------------------------
            # Found all attributes, captured all metadata in Dictionary
            #------------------------------
            return dict_ConditionData, list_keyword_values
            # end else portion.

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def process_doi_metadata(self,dict_configList, dict_fixedList, dict_ConditionData, FileName, list_keyword_values, DOI_filepath,publisher_value=None,contributor_value=None):
        logger.info(f"DOI_filepath {DOI_filepath}");
        logger.debug(f"publisher_value,contributor_value {publisher_value},{contributor_value}")

        try:
            f_DOI_file = open(DOI_filepath, mode='r')  # Note that we are only opening the file for reading different than previous mode='r+'.
            xmlDOI_Text = f_DOI_file.read()
            f_DOI_file.close()
        except:
            logger.error(f"DOI file (%s) not found for edit\n" % (DOI_filepath))
            sys.exit(1)
        
        #------------------------------                                                                                                 
        # Begin replacing the metadata in the DOI file with that in Product Label                                                                                 
        #------------------------------
        parent_xpath = "/records/record/"
        
        #------------------------------                                                                                                 
        # For each key/value in dictionary (that contains the values for the DOI label)
        #------------------------------  
        dict_value = dict_ConditionData.get(FileName)
        for key, value in dict_value.items():
            attr_xpath = parent_xpath + key
        
        for key, value in dict_value.items():
            attr_xpath = parent_xpath + key
            xmlDOI_Text = self.m_doiOutputUtil.populate_doi_xml_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, value)                          
        #------------------------------                                                                                                 
        # Add the <publisher> metadata defined in the Config file
        #    -- <keywords> using the items in list_keyword_values
        #  -- each value must be separated by semi-colon
        #------------------------------   

        # The value of publisher should come from the commmand line or config file.
        # If we got to there, the value of publisher_value is valid.

        attr_xpath = "/records/record/publisher"
        logger.debug(f"key,value,attr_xpath publisher {publisher_value},{attr_xpath}")
        
        xmlDOI_Text = self.m_doiOutputUtil.populate_doi_xml_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, publisher_value)

        #------------------------------                                                                                                 
        # Add the <contributor> metadata as input from user.
        #------------------------------                                                                                                 
        # If we got to here, the value of contributor_value is valid.

        attr_xpath = "/records/record/contributors/contributor/full_name"
        logger.debug(f"key,value,attr_xpath contributor {contributor_value},{attr_xpath}")

        # If we haven't already prepend 'PDS' and append 'Node', do it now.
        if not contributor_value.startswith('PDS') and not contributor_value.endswith('Node'):
            contributor_value = 'PDS ' + contributor_value + ' Node'  # Prepend 'PDS' and append 'Node' to input contributor value.
        xmlDOI_Text = self.m_doiOutputUtil.populate_doi_xml_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, contributor_value)

        #------------------------------                                                                                                 
        # Add the global keyword values in the Config file to those scraped from the Product label
        #    -- <keywords> using the items in list_keyword_values
        #  -- each value must be separated by semi-colon
        #------------------------------   
        keyword_values = self.m_doiGeneralUtil.return_keyword_values(dict_configList, list_keyword_values)
        if 'None ' in keyword_values:
            keyword_values = keyword_values.replace('None ','')  # Remove the 'None ' value since it doesn't make sense.

        logger.debug(f"keyword_values {keyword_values}")

        attr_xpath = "/records/record/keywords"
        
        xmlDOI_Text = self.m_doiOutputUtil.populate_doi_xml_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, keyword_values)                          
        return(xmlDOI_Text)

    def process_parent_node(self,previous_parent,pds_uri_string,element,event):
        processed_flag = False
        #------------------------------
        # Initialize the various URIs 
        #------------------------------ 
        objIdentArea_uri  = pds_uri_string + "Identification_Area"
        objProductBundle_uri = pds_uri_string + "Product_Bundle"
        objBundle_uri     = pds_uri_string + "Bundle"
        objCollection_uri = pds_uri_string + "Collection"
        objProductCollection_uri = pds_uri_string + "Product_Collection"
        objModification_History_uri = pds_uri_string + "Modification_History"
        objField_Delimited = pds_uri_string + "Field_Delimited"

        objLID_uri       = pds_uri_string + "logical_identifier"
        objVID_uri       = pds_uri_string + "version_id"                                                    
        objTitle_uri     = pds_uri_string + "title"
        objProdClass_uri = pds_uri_string + "product_class" 
        objPubYear_uri   = pds_uri_string + "publication_year"
        objPubDate_uri   = pds_uri_string + "modification_date"
        objDescript_uri  = pds_uri_string + "description" 
        objAuthList_uri  = pds_uri_string + "author_list" 
        objEditorList_uri  = pds_uri_string + "editor_list" 
        
        #------------------------------
        # Initialize the Class and Attribute URIs for discovering <keywords>
        #------------------------------ 
        objInvestigArea_uri    = pds_uri_string + "Investigation_Area"
        objCitationInfo_uri    = pds_uri_string + "Citation_Information"
        objObsSysCompArea_uri  = pds_uri_string + "Observing_System_Component"
        objTargetIdentArea_uri = pds_uri_string + "Target_Identification" 
        objPrimResSumArea_uri  = pds_uri_string + "Primary_Result_Summary" 
        objSciFacetsArea_uri   = pds_uri_string + "Science_Facets" 
            
        #objName_uri      = pds_uri_string + "name"
        #objProcLevel_uri = pds_uri_string + "processing_level"
        #objDomain_uri    = pds_uri_string + "domain"
        objName_uri      = pds_uri_string + "name"
        objProcLevel_uri = pds_uri_string + "processing_level"
        objDomain_uri    = pds_uri_string + "domain"
        objDiscpName     = pds_uri_string + "discipline_name"
        objFacet1        = pds_uri_string + "facet1"
        objFacet2        = pds_uri_string + "facet2"

        o_parentNode = previous_parent

        if (element.tag == objIdentArea_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True

        if (element.tag == objProductBundle_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objBundle_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True

        if (element.tag == objProductCollection_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objCollection_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True

        if (element.tag == objModification_History_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True

        if (element.tag == objField_Delimited):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True




        if (element.tag == objCitationInfo_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objDiscpName):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objDomain_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objFacet1):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objFacet2):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objInvestigArea_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objObsSysCompArea_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objPrimResSumArea_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True
        if (element.tag == objTargetIdentArea_uri):
            if (event == 'start'):
                o_parentNode = element # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True

        if (not processed_flag):
            pass
        return(o_parentNode)

    def dump_tree(self,xmlText):
        # Function dump the xmlText as tree including all the children, their tags and values.
        # Some encoding is necessary if we are dealing with string.
        if isinstance(xmlText,bytes):
            root = etree.fromstring(xmlText)
        else:
            root = etree.fromstring(str(' '.join(xmlText)).encode()) # Have to change the text to bytes then encode it to get it to work.

        logger.info(f'root.tag = {root.tag} => {root.text}') 

        # Inspect all the children elements in the tree.
        for appt in root.getchildren():
            logger.info(f'appt.tag = {appt.tag} => {appt.text}') 
            # Inspect Level 1 children.
            for elem1 in appt.getchildren():
                if not elem1.text:
                    text = 'None'
                else:
                    text = elem1.text 
                    logger.info(f'elem1.tag = {elem1.tag} => {text}') 
                # Inspect Level 2 children.
                for elem2 in elem1.getchildren():


                    if not elem2.text:
                        text = 'None'
                    else:
                        text = elem2.text 
                    logger.info(f'elem2.tag = {elem2.tag} => {text}') 
        return(1)

    def parse_pds4_label_via_uri(self,target_url,publisher_value,contributor_value):
        CONTROL_M = chr(13)
        o_doi_label = None

        logger.info(f"target_url {target_url}");
        logger.debug("target_url,publisher_value,contributor_value {target_url},{publisher_value},{contributor_value}")

        # Get the default configuration from external file.  Location may have to be absolute.
        xmlConfigFile = os.path.join('.','config','default_config.xml')
        logger.debug("xmlConfigFile {xmlConfigFile}")
        dict_configList = {}                                                                                                            
        dict_fixedList  = {}
        (dict_configList, dict_fixedList) = self.m_doiConfigUtil.get_config_file_metadata(xmlConfigFile)

        if not target_url.startswith('http'):
            file_type = 'text_file'
            # Read the file as if it on disk.
            file_input = open(target_url,'r')
            my_file = file_input.readlines()
        else:
            # If the given URL starts with htpp, the content of the file will be a series of bytes.
            file_type = 'bytes_file'
            my_file = requests.get(target_url)

        n_count = 0

        # For now, read one line at a time and process it.
        xmlText = []
        xmlBytes = b""


        # TEMPORARY_CODE: Add preamble for file input because lxml is barfing
        # xml.etree.ElementTree.ParseError: unbound prefix: line 1, column 0
        # Will attempt to add the preamble to xmlText
#"<?xml version='1.0' encoding='utf-8'?>"
# 1234567890123456789012345678901234567890
#"<?xml-model href='https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1B10.sch' schematypens='http://purl.oclc.org/dsdl/schematron'?>"
# 1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
        if file_type == 'bytes_file':
            #xmlText.append("<?xml version='1.0' encoding='utf-8'?>"
            pass
        else:
            preamble_extra_1 = '<?xml version="1.0" encoding="utf-8"?>\n'
            preamble_extra_2 = '<?xml-model href="https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1B10.sch" schematypens="http://purl.oclc.org/dsdl/schematron"?>\n'
            xmlText.append(preamble_extra_1)
            xmlBytes = b"".join([xmlBytes,preamble_extra_1.encode()]) 
            xmlText.append(preamble_extra_2)
            xmlBytes = b"".join([xmlBytes,preamble_extra_2.encode()]) 
            pass

        # This is odd:These are added to the Product_Bundle tag.
        # xmlns="http://pds.nasa.gov/pds4/pds/v1" xmlns:pds="http://pds.nasa.gov/pds4/pds/v1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"

        # <Product_Bundle xmlns="http://pds.nasa.gov/pds4/pds/v1" xmlns:pds="http://pds.nasa.gov/pds4/pds/v1"
        #  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        #  xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1 https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1B10.xsd">
        xmlns_tokens = 'xmlns="http://pds.nasa.gov/pds4/pds/v1" xmlns:pds="http://pds.nasa.gov/pds4/pds/v1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'

        for line in my_file:
            n_count += 1
            if file_type == 'bytes_file':
                decoded_line = line.decode("utf-8")
            else:
                decoded_line = line
            # Because there may be special character Control-M, we need to remove them.
            # We also want to remove the carriage return. 
            decoded_line = decoded_line.replace(CONTROL_M,'').replace('\n','')
            xmlText.append(decoded_line)

            #if 'Product_Bundle' in line or 'Product' in line:
            if file_type == 'text_file':
                if '<Product_Bundle' in line:
                    splitted_tokens = line.split('<Product_Bundle ')
                    # Rebuild the 'Product_Bundle' or 'Product' line
                    line = '<Product_Bundle' + ' ' + xmlns_tokens + ' ' + splitted_tokens[1]
            if file_type == 'bytes_file':
                xmlBytes = b"".join([xmlBytes,line]) 
            else:
                xmlBytes = b"".join([xmlBytes,line.encode()]) 

        logger.debug(f"len(xmlBytes) {len(xmlBytes)}")

        # For now, dump what we have just read to text file so the function ProcessIAD2ProductLabelMetadata() can parse it.
        FileName = 'dummy_FileName.txt'
        eachFile = 'dummy_eachFile.txt'
        #file1 = open(eachFile,"w") 
        #file1.write(str(' '.join(xmlText))) # Write the entire list as one long string.
        #file1.close()

        #file1 = open(eachFile+'2',"w") # Write a 2nd file with carriage return.
        #file1.write(str('\n'.join(xmlText))) # Write the entire list as one long string with carriage return after each line.
        #file1.close()
        #print(function_name,"early#exit#0003")
        #exit(0)

        #dict_fixedList = {'pds_uri':'http://pds.nasa.gov/pds4/pds/v1'}
        dict_ConditionData = {} # Start out as empty list will get filled in after call to ProcessIAD2ProductLabelMetadata function.

        # Parameters and their meaning of ProcessIAD2ProductLabelMetadata function:
        #
        #    fict_fixedList     = structure containg configuration values needed to parse PDS4 label.
        #    dict_ConditionData = structure containing the condition of the metadata if it has been 'Submitted' or 'Reserved'
        #    FileName           = The content of PDS4 label on disk if it was written.
        #    xmlBytes           = a long series of bytes representing the PDS4 label (If this is not None, the function ProcessIAD2ProductLabelMetadata will read from memory.


        # Uncomment to test how the function will handle if the file is not valid.
        FileName = 'zzz'
        eachFile = 'kkkkkk'  # This signal for the below function to use the passed in xmlBytes to traverse the tree.

        (dict_ConditionData, list_keyword_values) = self.process_iad2_product_label_metadata(dict_fixedList, dict_ConditionData, eachFile, FileName,xmlBytes)

        # This works.
        #print(function_name,"early#exit#0009")
        #exit(0)
        logger.debug(f"list_keyword_values {list_keyword_values}")

        key = FileName
        DOI_template_filepath = dict_configList.get("DOI_template")  # The DOI template file should come from the config file. 
        logger.info(f"DOI_template_filepath {DOI_template_filepath}")
        sInventoryName = "DOI_" + key
        DOI_directory_PathName = os.path.join('.');
        fileDestination = os.path.join(DOI_directory_PathName,sInventoryName)
        fileSource = DOI_template_filepath

        # DEVELOPER_NOTE: Not sure why this copy has to be made.
        # TODO: Figure out why the below line is done shutil.copy2(fileSource, fileDestination)
        #shutil.copy2(fileSource, fileDestination)
        DOI_filepath = fileDestination
        DOI_filepath = DOI_template_filepath

        # Add key 'DOI_dummy_FileName.txt' to dict_ConditionData so the function ProcessDOIMetadata() can find it.
        dict_ConditionData[sInventoryName] = dict_ConditionData[FileName]
        o_doi_label = self.process_doi_metadata(dict_configList, dict_fixedList, dict_ConditionData, key, list_keyword_values, DOI_filepath,publisher_value,contributor_value)

        logger.debug(f"o_doi_label {o_doi_label}")
        return(o_doi_label)

if __name__ == '__main__':
    global f_debug
    global debug_flag
    function_name = 'main:'
    #print(function_name,'entering')
    publisher_value = DOI_CORE_CONST_PUBLISHER_VALUE
    target_url = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'
    contributor_value = 'Cartography and Imaging Sciences Discipline' 
    doiPDS4LabelUtil = DOIPDS4LabelUtil()
    o_doi_label = doiPDS4LabelUtil.parse_pds4_label_via_uri(target_url,publisher_value,contributor_value)
    print(function_name,"o_doi_label",o_doi_label.decode())
    donotcare = doiPDS4LabelUtil.dump_tree(o_doi_label);
