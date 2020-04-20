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

import os                                                                                                                       
import shutil                                                                                                                   
import sys                                                                                                                      

from xml.etree import ElementTree                                                                                               
from lxml import etree
from lxml import html
import logging

import urllib.request
import urllib.parse
import urllib.error

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# For now, check to see which version we are running.
# setenv DOI_ENV_PYTHON3_FLAG true
#if os.getenv('DOI_ENV_PYTHON3_FLAG','') == 'true':
#    import urllib.request
#    import urllib.parse
#    import urllib.error
#else:
#    import requests
#    from urllib2 import urlopen, URLError

from bs4 import BeautifulSoup

from datetime import datetime                                                                                                   
from optparse import OptionParser                                                                                               
from time import gmtime,strftime                                                                                                
import xlrd

from const import *;

class DOICoreServices:

    global m_debug_mode;
    global f_debug
    global debug_flag
    m_debug_mode = False;
    f_debug   = None                                                                                    
    debug_flag= False
    #m_debug_mode = True;
    #m_debug_mode = False;
    #------------------------------
    #------------------------------
    def GetConfigFileMetaData(self,filename):
    #------------------------------
    #------------------------------
        function_name = 'GetConfigFileMetaData:'

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

    #      for eachElement in dict_fixedList:
    #         print "dict_fixedList." + eachElement + " == '" + dict_fixedList.get(eachElement) + "'"

        return(dict_configList, dict_fixedList);

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def PopulateDOIXMLWithValues(self,dict_fixedList, xmlText, attr_xpath, value):                                      
        function_name = 'PopulateDOIXMLWithValues:';
        global m_debug_mode;
        if m_debug_mode:
            print(function_name,"Append","PopulateDOIXMLWithValues.xmlText: ",xmlText,)                                
            print(function_name,"Append","PopulateDOIXMLWithValues.attr_xpath: " + attr_xpath + "\n")
            print(function_name,"INSPECT_VARIABLE:Append","PopulateDOIXMLWithValues.value: ",value)
            print(function_name,"xmltext",len(xmlText),xmlText);
            print(function_name,"INSPECT_VARIABLE:len(xmltext)",len(xmlText));
            print(function_name,"dict_fixedList",dict_fixedList);
            print(function_name,"dict_fixedList",len(dict_fixedList));

        #------------------------------                                                                                             
        # Populate the xml attribute with the specified value                                                                       
        #------------------------------                                                                                             
        from lxml import etree
        if m_debug_mode:
            print(function_name,"type(xmlText)",type(xmlText));
            print(function_name,"type(xmlText)",type(xmlText));
        if isinstance(xmlText,bytes):
            doc = etree.fromstring(xmlText);
        else:
            doc = etree.fromstring(xmlText.encode()); # Have to change the text to bytes then encode it to get it to work.

        if m_debug_mode:
            print(function_name,"INSPECT_VARIABLE:attr_xpath",attr_xpath);
            print(function_name,"type(attr_xpath)",type(attr_xpath));
            print(function_name,"len(attr_xpath)",len(attr_xpath));
            print(function_name,"INSPECT_VARIABLE:doc.xpath(attr_xpath)[",doc.xpath(attr_xpath));
        if len(doc.xpath(attr_xpath)) == 0:
            if m_debug_mode:
                print(function_name,"INSPECT_VARIABLE:EXPATH_BAD:doc.xpath(attr_xpath)",doc.xpath(attr_xpath));
                print(function_name,"ERROR:LEN_XPATH_IS_ZERO:len(doc.xpath(attr_xpath)) == 0");
                print(function_name,"ERROR:attr_xpath",attr_xpath);
        #exit(0);
        else:
            if m_debug_mode:
                print(function_name,"INSPECT_VARIABLE:EXPATH_GOOD:doc.xpath(attr_xpath)[0].text",doc.xpath(attr_xpath)[0].text);
                print(function_name,"INSPECT_VARIABLE:value",value);
            elm = doc.xpath(attr_xpath)[0]                                                              
            elm.text = value                                                                                                            

        sOutText = etree.tostring(doc)                                                                                              

        #------------------------------                                                                                             
        # Return the buffer                                                                                                         
        #------------------------------                                                                                             
        return sOutText                                                                                                             

    #------------------------------
    #------------------------------
    def ReturnDOIDate(self,f_debug, debug_flag, prodDate):
    #------------------------------
    # 20171207 -- prodDate -- date in: <modification_date>2015-07-14</modification_date>
    #              doiDate -- date formatted as: 'yyyy-mm-dd'
    #------------------------------

        doiDate = datetime.strptime(prodDate, '%Y-%m-%d').strftime('%m/%d/%Y');
        return(doiDate);

    def DecodeBytesToString(self,xmlContent):
        o_string = None;
        o_xmlContent_as_string = xmlContent
        if isinstance(xmlContent,bytes):
            o_xmlContent_as_string = xmlContent.decode();
     
        return(o_xmlContent_as_string);

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
        
        function_name = 'ReturnNameSpaceDictionary:'
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
            xmlContent_as_string = self.DecodeBytesToString(xmlContent);
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
        function_name = 'ReturnRelativePathAndFileName:'

        RelPath  = "";
        FileName = "";

        #------------------------------                                                                                             
        # establish the path for the working directory                                                                              
        #  -- C:\\test\test.xml                                                                                                     
        #------------------------------                                                                                             
        #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.rootPath: " + rootPath + "\n")                          
        print(function_name,"rootPath: " + rootPath);
        print(function_name,"pathName: " + pathName);

        #------------------------------                                                                                             
        # Remove the working directory from the Path&FileName                                                                       
        #   --- residual is either just a filename or child subdirectories and a filename                                           
        #------------------------------                                                                                             
        a = pathName.replace(rootPath, "")                                                                                          
        #util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.a: " + a + "\n")                                        
        print(function_name,"a: " + a);

        #------------------------------                                                                                             
        # Check is there are 1 or more child directories                                                                            
        #------------------------------                                                                                             
        chr_92 = os.path.sep;
        print(function_name,"chr_92 in a",chr_92 in a);
        if (chr_92 in a):                                                                                                          
            fields = a.split(chr_92)                                                                                               

            iFields = len(fields)                                                                                                   
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
        print(function_name,"RelPath",RelPath);
        print(function_name,"FileName",FileName);

        return RelPath, FileName                                                                                                    

    #------------------------------                                                                                                 
    def ProcessIAD2ProductLabelMetadata(self,dict_fixedList, dict_ConditionData, eachFile, FileName, xmlContent=None):
        function_name = 'ProcessIAD2ProductLabelMetadata:'
        global m_debug_mode
        global f_debug,debug_flag

        pds_uri    = dict_fixedList.get("pds_uri")
        pds_uri_string = "{" + pds_uri + "}"

        #m_debug_mode = True;
        if m_debug_mode:
            print(function_name,"pds_uri_string",pds_uri_string);
            print(function_name,"xmlContent",xmlContent);
        if xmlContent is not None:
            if m_debug_mode:
                print(function_name,"len(xmlContent),xmlContent[0:20]",len(xmlContent),xmlContent[0:20]);
        #print(function_name,"early#exit#0001");
        #exit(0);

        #------------------------------
        # Read the IM Test_Case manifest file
        #   -- for each <test_case>; get dictionary of metadata
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

        #util.WriteDebugInfo(f_debug,debug_flag,"Append","MAIN.ProcessIAD2ProductLabelMetadata\n")                                         
        if m_debug_mode:
            print(function_name,"MAIN.ProcessIAD2ProductLabelMetadata\n")
            print(function_name," -- processing Product label file: " + eachFile);
        
        #------------------------------
        # Read the XML label
        #   -- generate a DICT of the identified namespaces in the XML preamble
        #         -- etree XML parser errors if encounters 'Null' namespace; so delete from DICT
        #------------------------------
        global dict_namespaces
        dict_namespaces = self.ReturnNameSpaceDictionary(f_debug, debug_flag, eachFile,xmlContent)
        if m_debug_mode:
            print(function_name,"dict_namespaces",dict_namespaces);
        
        #------------------------------
        # Open the XML label 
        #   --  ElementTree supports 'findall' using dict_namespaces and designation of instances
        #   -- etree doesn't support designation of instances
        #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
        #------------------------------
        try:  
            if os.path.isfile(eachFile):
                tree = etree.parse(eachFile)
                xmlProd_root = tree.getroot()
            else:
                    # If the actual content of the XML to be parsed is already in memory, we use it.
                if xmlContent is not None:
                    #jprint(function_name,"PARSE_FROM_MEMORY:len(xmlContent)",len(xmlContent));
                    #print(function_name,"PARSE_FROM_MEMORY:xmlContent[0:20])",xmlContent[0:20]);
                    # If we are reading from string, the value of tree should be set to None.
                    tree = None;
                    xmlProd_root = etree.fromstring(xmlContent);
                    #print(function_name,"PARSE_FROM_MEMORY:xmlProd_roottree",type(xmlProd_root),xmlProd_root);
                else:
                    print(function_name,"ERROR: xmlContent is None and os.path.isfile(eachFile) is false",eachFile);
                    exit(0); 
        
        except etree.ParseError as err:
            print(function_name,"ERROR: Parse error:err",err);
            exit(0);
            sString = "  -- ABORT: the xml 'Product label; file (%s) could not be parsed\n" % (eachFile)                
            f_inventory.write(sString)
            sString = "      -- %s\n" % (err)
            f_inventory.write(sString)
            sys.exit()
        
        else:                      
            if m_debug_mode:
                print(function_name,"ERROR:ELSE_PART_2:tree",tree);
                print(function_name,"ERROR:ELSE_PART_2:xmlProd_root",xmlProd_root);

            #------------------------------
            #------------------------------
            # Iterate over each <test_case> specified in the TC Manifest file
            #    -- for each <test_case>; use the metadata to:
            #         -- create a PDS4 XML label 
            #         -- modify the 'template' using the xpath and value_settings
            #         -- create the XML output label file
            #
            # Each TestCase consists of the following metadata:
            #   -- test_case name: unique identifier of the <test_case>
            #   -- state: isValid | notValid; indicates if values in test-case are either valid or not
            #   -- <conditions>; values must be paired:
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
            element_count = 0;
            string_to_walk = eachFile;
            # If the file is a valid file, walk through it.
            if os.path.isfile(eachFile):
                context = etree.iterparse(string_to_walk, events=("start", "end"));
            else:
                # If the value of eachFile is not a valid file, check to see if it has been read into memory already.
                if xmlContent is not None:
                    from io import StringIO; # for Python 3
                    string_to_walk = self.DecodeBytesToString(xmlContent);   # The content may be a bunch of bytes.
                    string_to_walk = StringIO(string_to_walk);          # Convert the bytes to string so we can walk through.
                #context = ElementTree.iterparse(string_to_walk, events=["start", "end"]);
                    context = ElementTree.iterparse(string_to_walk, events=("start", "end"));
                #context = etree.iterparse(string_to_walk, events=("start", "end"));
                else:
                    print(function_name,"ERROR: xmlContent is None and os.path.isfile(eachFile) is false",eachFile);
                    exit(0); 

            # Old method:
            #    for event, element in etree.iterparse(eachFile, events=("start", "end")):
            # A new way to walk.  If the xml content has already been read into memory, we can walk it.

            parentNode = None;  # Added this to we know to look for parent using alternate method.
            for event, element in context:
                #parentNode = None;  # Added this to we know to look for parent using alternate method.
                element_count += 1;
                if m_debug_mode:
                    print(function_name,"%5s, %4s, %s" % (event, element.tag, element.text))
                    print(function_name,"INSPECT_VARIABLE:ELEMENT_COUNT,EVENT,TAG,TEXT",element_count,event,element.tag,element.text);

                #------------------------------
                # <Identification_Area>
                #------------------------------
                if (element.tag == objIdentArea_uri):
                    if (event == "start"):
                        inIdentArea = True
                        parentNode = element; # Remember who your parent is for objIdentArea_uri tag.
                    if (event == 'end'):
                        parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value.

                # We have to remember the parent for each tag found below.

                parentNode = self.ProcessParentNode(parentNode,pds_uri_string,element,event);
                       
                #------------------------------
                # <logical_identifier>
                #------------------------------
                if m_debug_mode:
                    print(function_name,"INSPECT_VARIABLE:ELEMENT_COUNT,EVENT,TAG,TEXT,ELEMENT_TAG,OBJLID_URI",element_count,event,element.tag,element.text,'ELEMENT_TAG',element.tag,'OBJLID_URI',objLID_uri);
                    print(function_name,"INSPECT_VARIABLE:ELEMENT_COUNT,ELEMENT_TAG",element_count,element.tag);
                    print(function_name,"INSPECT_VARIABLE:ELEMENT_COUNT,OBJLID_URI",element_count,objLID_uri);
                if (element.tag == objLID_uri):
                    if (event == "start"):
                        LID_value = element.text
            
                    #------------------------------                                                                                     
                    # Convert LID to URL for <site_url>                                                                                       
                    #------------------------------                                                                                     
                    LID_url_value = LID_value.replace(":", "%3A")
                    if m_debug_mode:
                        print(function_name,"INSPECT_VARIABLE:ELEMENT_COUNT,EVENT,TAG,TEXT,LID_url_value",element_count,event,element.tag,element.text,LID_url_value);

                #------------------------------
                # <version_id> -- <product_nos>
                #  -- use <version_id> in <Identification_Area>
                #  -- DO NOT use <version_id> in <Modification_Detail>
                #------------------------------
                if (element.tag == objVID_uri):
                    if (event == "start"):
                        #print(function_name,"INSPECT_VARIABLE:event,element.tag,element,element.text",event,element.tag,element,element.text);
                        #print(function_name,"INSPECT_VARIABLE:element.keys()",element.keys());
                        if (parentNode is not None):
                            pass;
                    #print(function_name,"INSPECT_VARIABLE:parentNode,parentNode.text,parentNode.tag",parentNode,parentNode.text,parentNode.tag)
                    #print(function_name,"INSPECT_VARIABLE:objIdentArea_uri",objIdentArea_uri);
                    #print(function_name,"INSPECT_VARIABLE:etree.tostring(element)",etree.tostring(element));
                    #print(function_name,"INSPECT_VARIABLE:element.itersiblings",element.itersiblings());
                    #print(function_name,"INSPECT_VARIABLE:element.getroottree()",element.getroottree());
                    #print(function_name,"INSPECT_VARIABLE:element.getparent()",element.getparent());
                    #print(function_name,"INSPECT_VARIABLE:element.getparent().tag,element.getparent().text",element.getparent().tag,element.getparent().text);
                        # For some strange reason, if reading in the XML from memory, the following lines does not work
                        # and complains about "AttributeError: 'xml.etree.ElementTree.Element' object has no attribute 'iterancestors'"
                        # So the solution is to comment it out and put a try and catch and use something else.
                        #parentNode = next(element.iterancestors())
                        if parentNode is None:
                            print(function_name,"INSPECT_VARIABLE:element,element.tag,element.text",element,element.tag,element.text);
                            parentNode = next(element.iterancestors())
                    
                    if (parentNode.tag == objIdentArea_uri):
                        VID_value = element.text                    
                    
                        # Not sure why the below was commented out.  Uncomment it out.
                        dict_ConditionData[FileName]["product_nos"] = LID_value + "::" + VID_value
                        dict_ConditionData[FileName]["accession_number"]  = LID_value + "::" + VID_value                                                
                        dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"]  = LID_value + "::" + VID_value
                    #print(function_name,"FOUND_PRODUCT_NOS:FileName,dict_ConditionData[FileName]",FileName,dict_ConditionData[FileName]);
                    #exit(0);
                    #parentNode = None; # Reset parentNode to None to force the next event to set it to valid value.
                    
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
                    #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&amp;version=" + VID_value
                            url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&version=" + VID_value

                            dict_ConditionData[FileName]["product_type"] = "Collection"
                            dict_ConditionData[FileName]["product_type_specific"] = "PDS4 Bundle"
                            dict_ConditionData[FileName]["site_url"] = url_value
                            if m_debug_mode:
                                print(function_name,'FOUND_BUNDLE',dict_ConditionData[FileName]);
                            #print(function_name,'FOUND_BUNDLE',dict_ConditionData[FileName]);
                            #exit(0);
                    
                        elif ("Collection" in ProdClass_value):                        
                            isCollection = True
                    #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&amp;version=" + VID_value
                            url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&version=" + VID_value

                            dict_ConditionData[FileName]["product_type"] = "Dataset"
                            dict_ConditionData[FileName]["product_type_specific"] = "PDS4 Collection"
                            dict_ConditionData[FileName]["site_url"] = url_value

                        elif ("Document" in ProdClass_value):                        
                            print("<product_class> in Product XML label is Document (which is not yet supported): " + ProdClass_value);
                            sys.exit()

                        else:
                            print("<product_class> in Product XML label not Collection or Bundle: " + ProdClass_value);
                            sys.exit()
                                        
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
                        dict_ConditionData[FileName]["publication_date"]  = self.ReturnDOIDate(f_debug,debug_flag,PubDate_value); # Conver to DOI format
                        dict_ConditionData[FileName]["date_record_added"] = self.ReturnDOIDate(f_debug,debug_flag,PubDate_value); # Conver to DOI format
                        #print(function_name,"FileName,dict_ConditionData[FileName]",FileName,dict_ConditionData[FileName]);
                        #print(function_name,"self.ReturnDOIDate(PubDate_value)",self.ReturnDOIDate(f_debug,debug_flag,PubDate_value));
                        #exit(0);
                    
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
                        #parentNode = None; # Reset parentNode to None to force the next event to set it to valid value.

                #------------------------------
                # <author_list> -- <Identification_Area/Citation_Information/author_list>
                #                      -- <Identification_Area/Citation_Information/editor_list>
                #------------------------------
                if (element.tag == objAuthList_uri) or (element.tag == objEditorList_uri):
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
                        #  -- split author by ';' then split by ',' to get <author_last_name> & <author_first_name>
                        #
                        #  <author_list>French, R. G.; McGhee-French, C. A.; Gordon, M. K.</author_list>
                        #------------------------------                                
                        if (parentNode.tag == objCitationInfo_uri):                   
                            author_list = element.text
                     
                            items = author_list.split(";")
                            items2 = items[0].split(",")

                        dict_ConditionData[FileName]["authors/author/last_name"] =  items2[0]
                        dict_ConditionData[FileName]["authors/author/first_name"]  =  items2[1]

                        # NOTE_FROM_QUI: <author_list>R. Deen, H. Abarca, P. Zamani, J.Maki</author_list>
                        # Handle special case when the names are delimited using command instead of ;
                        #ProcessIAD2ProductLabelMetadata: len(items),items 1 ['R. Deen, H. Abarca, P. Zamani, J.Maki']
                        #ProcessIAD2ProductLabelMetadata: len(items2),items2 4 ['R. Deen', ' H. Abarca', ' P. Zamani', ' J.Maki']
                        #ProcessIAD2ProductLabelMetadata: element.text R. Deen, H. Abarca, P. Zamani, J.Maki
                        if len(items) == 1:
                            items3 = items[0].split(',');  # Split 'R. Deen, H. Abarca, P. Zamani, J.Maki' into ['R. Deen','H. Abarca','P. Zamani','J.Maki'
                            #print(function_name,"len(items3),items3",len(items3),items3);
                            last_names_list  = [];
                            first_names_list = [];
                            for ii in range(0,len(items3)):
                                #print(function_name,"ii,items3[ii])",ii,items3[ii]);
                                items4 = items3[ii].split('.');  # Split 'R. Deen' into ['R.''Deen']
                                #print(function_name,"ii,len(items4),items4",len(items4),items4);
                                #print(function_name,"ii,items4[0],items4[0]",len(items4[0]),items4[0]);
                                first_names_list.append(items4[0] + '.');  # Collect the first name to first_names_list.  Add the '.' back to first name.
                                last_names_list.append (items4[1]);        # Collect the last name to last_names_list.
                            dict_ConditionData[FileName]["authors/author/last_name"]   =  last_names_list;
                            dict_ConditionData[FileName]["authors/author/first_name"]  =  first_names_list;
                            #print(function_name,"len(items3),items3",len(items3),items3);
                            #print(function_name,"len(items4),items4",len(items4),items4);

                            # Add to creators field.
                            dict_ConditionData[FileName]["creators"] = author_list; 
                            #dict_ConditionData[FileName]["accession_number"] = ""

                        #print(function_name,"len(items),items",len(items),items);
                        #print(function_name,"len(items2),items2",len(items2),items2);


                    #print(function_name,"element.text",element.text);
                    #print(function_name,"parentNode.tag,objCitationInfo_uri",parentNode.tag,objCitationInfo_uri);
                    #print(function_name,'FOUND_AUTHOR_LIST',dict_ConditionData[FileName]);
                    #parentNode = None; # Reset parentNode to None to force the next event to set it to valid value.
                    #exit(0);
                    
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
    def ProcessDOIMetadata(self,dict_configList, dict_fixedList, dict_ConditionData, FileName, list_keyword_values, DOI_filepath,publisher_value=None,contributor_value=None):
        function_name = 'ProcessDOIMetadata:'
        global m_debug_mode;
        #m_debug_mode = True;
        if m_debug_mode:
            print(function_name,"publisher_value,contributor_value",publisher_value,contributor_value);
        #print(function_name,"early#exit#0045");
        #exit(0);

        try:
            f_DOI_file = open(DOI_filepath, mode='r+');
            xmlDOI_Text = f_DOI_file.read();
            f_DOI_file.close()
        except:
            print(function_name,"DOI file (%s) not found for edit\n" % (DOI_filepath));
            sys.exit();
        
        #------------------------------                                                                                                 
        # Begin replacing the metadata in the DOI file with that in Product Label                                                                                 
        #------------------------------
        parent_xpath = "/records/record/"
        
        #------------------------------                                                                                                 
        # For each key/value in dictionary (that contains the values for the DOI label)
        #------------------------------  
        dict_value = dict_ConditionData.get(FileName)
        if m_debug_mode:
            print(function_name,"INSPECT_VARIABLE:FileName,dict_value",FileName,dict_value);
        #print(function_name,"early#exit#0099");
        #exit(0);
        
        for key, value in dict_value.items():
            attr_xpath = parent_xpath + key
            if m_debug_mode:
                print(function_name,'key,value,attr_xpath',key,value,attr_xpath);
                print(function_name,'INSPECT_VARIABLE:value[',value,']');
            xmlDOI_Text = self.PopulateDOIXMLWithValues(dict_fixedList, xmlDOI_Text, attr_xpath, value)                          

        #------------------------------                                                                                                 
        # Add the <publisher> metadata defined in the Config file
        #    -- <keywords> using the items in list_keyword_values
        #  -- each value must be separated by semi-colon
        #------------------------------   

        # The value of publisher should come from the commmand line or config file.
        # If we got to there, the value of publisher_value is valid.

        attr_xpath = "/records/record/publisher"
        if m_debug_mode:
            print(function_name,'key,value,attr_xpath','publisher',publisher_value,attr_xpath);
        
        xmlDOI_Text = self.PopulateDOIXMLWithValues(dict_fixedList, xmlDOI_Text, attr_xpath, publisher_value)
        if m_debug_mode:
            print(function_name,"Append","ProcessDOIMetadata.xmlText: ",xmlDOI_Text);

        #------------------------------                                                                                                 
        # Add the <contributor> metadata as input from user.
        #------------------------------                                                                                                 
        # If we got to there, the value of contributor_value is valid.

        attr_xpath = "/records/record/contributors/contributor/full_name"
        if m_debug_mode:
            print(function_name,'key,value,attr_xpath','contributor',contributor_value,attr_xpath);
        #print(function_name,"early#exit#0001");
        #exit(0);

        contributor_value = 'PDS ' + contributor_value + ' Node';  # Prepend 'PDS' and append 'Node' to input contributor value.
        xmlDOI_Text = self.PopulateDOIXMLWithValues(dict_fixedList, xmlDOI_Text, attr_xpath, contributor_value)

        if m_debug_mode:
            print(function_name,"Append","ProcessDOIMetadata.xmlText: ",xmlDOI_Text);
        #print(function_name,"early#exit#0001");
        #exit(0);

        #------------------------------                                                                                                 
        # Add the global keyword values in the Config file to those scraped from the Product label
        #    -- <keywords> using the items in list_keyword_values
        #  -- each value must be separated by semi-colon
        #------------------------------   
        keyword_values = self.ReturnKeywordValues(dict_configList, list_keyword_values);
        #print(function_name,"keyword_values",keyword_values);
        if 'None; ' in keyword_values:
            keyword_values = keyword_values.replace('None; ','');  # Remove the 'None; ' value since it doesn't make sense.

        if m_debug_mode:
            print(function_name,"keyword_values",keyword_values);
            print(function_name,"early#exit#0060");

        attr_xpath = "/records/record/keywords"
        
        xmlDOI_Text = self.PopulateDOIXMLWithValues(dict_fixedList, xmlDOI_Text, attr_xpath, keyword_values)                          
        #util.WriteDebugInfo(f_debug,debug_flag,"Append","ProcessDOIMetadata.xmlText: " + xmlDOI_Text + "\n")                                                   
        if m_debug_mode:
            print(function_name,"xmlText:(normal) ",xmlDOI_Text);
            print(function_name,"xmlText:(decode)");
            print(xmlDOI_Text.decode());
            print(function_name,"type(xmlText): ",type(xmlDOI_Text));
            print(function_name,"DOI_filepath",DOI_filepath);
            print(function_name,"xmlDOI_Text",xmlDOI_Text);
        #print(function_name,"early#exit#0060");
        #exit(0);
        return(xmlDOI_Text);

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def ReturnKeywordValues(self,dict_configList, list_keyword_values):                                              
    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
        function_name = 'ReturnKeywordValues:';
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

    def GetPermissibleValues(self,json_value_1,json_key_1):
            # Function returns the PerrmissibleValueList for attributeDictionary where one element matches with PDS_NODE_IDENTIFIER.
            function_name = 'GetPermissibleValues:'
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

    def ValidateContributorValue(self,target_url,i_contributor):
        function_name = 'ValidateContributorValue:';
        import urllib;
        from urllib.request import urlopen
        import json;
        PDS_NODE_IDENTIFIER = '0001_NASA_PDS_1.pds.Node.pds.name'

        o_found_dict = None;
        o_contributor_is_valid_flag = False;
        o_permissible_contributor_list = [];

        # Read from URL if starts with 'http' otherwise read from local file.
        if target_url.startswith('http'):
            #print(function_name,'READ_AS_URI',target_url);
            response = urlopen(target_url)
            web_data  = response.read().decode('utf-8');
            #print(function_name,'type(web_data))',type(web_data));
            #print(function_name,'len(web_data))',len(web_data));
            json_data = json.loads(web_data);
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

                o_permissible_value_list = self.GetPermissibleValues(json_value_1,json_key_1);

                if len(o_permissible_value_list) > 0 and not o_contributor_is_valid_flag:
                    num_permissible_names_matched = 0;
                    for mmm in range(0,len(o_permissible_value_list)):
                        #print(function_name,"mmm,o_permissible_value_list[mmm]publisher,",mmm,o_permissible_value_list[mmm],i_contributor);
                        o_permissible_contributor_list.append(o_permissible_value_list[mmm]['PermissibleValue']['value']);
                        if o_permissible_value_list[mmm]['PermissibleValue']['value'] in i_contributor:
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

    def ProcessParentNode(self,previous_parent,pds_uri_string,element,event):
        function_name = 'ProcessParentNode:';
        processed_flag = False;
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

        o_parentNode = previous_parent;

        if (element.tag == objIdentArea_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;

        if (element.tag == objProductBundle_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objBundle_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;

        if (element.tag == objProductCollection_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objCollection_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;

        if (element.tag == objModification_History_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;

        if (element.tag == objField_Delimited):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;




        if (element.tag == objCitationInfo_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objDiscpName):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objDomain_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objFacet1):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objFacet2):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objInvestigArea_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objObsSysCompArea_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objPrimResSumArea_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;
        if (element.tag == objTargetIdentArea_uri):
            if (event == 'start'):
                o_parentNode = element; # Remember who your parent is
            if (event == 'end'):
                o_parentNode = None;    # Reset parentNode to None to force the next event to set it to valid value
            processed_flag = True;

        if (not processed_flag):
            pass;
        #print(function_name,"WARN: Cannot process tag:",element.tag);
        #print(function_name,"WARN: Need to add tag to this function",element.tag);
        #print(function_name,"SOURCE:["+element.tag+"]");
        #print(function_name,"DESTIN:["+objProductBundle_uri + "]");
        #print(function_name,"DESTIN:["+objBundle_uri + "]");
        #print(function_name,"event",event);
        #print(function_name,"objProductBundle_uri",objProductBundle_uri);
        #print(function_name,"objBundle_uri",objBundle_uri);
        #exit(0);
        return(o_parentNode);

    def ParsePDS4LabelViaURI(self,target_url,publisher_value,contributor_value):
        function_name = 'ParsePDS4LabelViaURI:';
        CONTROL_M = chr(13)
        global m_debug_mode
        o_doi_label = None;

        if m_debug_mode:
            print(function_name,"target_url",target_url);

        # Get the default configuration from external file.  Location may have to be absolute.
        xmlConfigFile = '.' + os.path.sep + 'config' + os.path.sep + 'default_config.xml';
        dict_configList = {}                                                                                                            
        dict_fixedList  = {}
        (dict_configList, dict_fixedList) = self.GetConfigFileMetaData(xmlConfigFile)

        if m_debug_mode:
            print(function_name,"dict_configList",dict_configList);
            print(function_name,"dict_fixedList",dict_fixedList);

        logger.info(f"Getting pds4 label from url {target_url}")
        my_file = urllib.request.urlopen(target_url)
        n_count = 0;

        # For now, read one line at a time and process it.
        xmlText = [];
        #xmlBytes = [];
        xmlBytes = b"";
        for line in my_file:
            n_count += 1;
            decoded_line = line.decode("utf-8");
            # Because there may be special character Control-M, we need to remove them.
            # We also want to remove the carriage return. 
            decoded_line = decoded_line.replace(CONTROL_M,'').replace('\n','');
            if m_debug_mode:
                print(function_name,"INSPECT_VARIABLE:DECODED_LINE:",n_count,len(decoded_line),decoded_line);
            xmlText.append(decoded_line);
            if m_debug_mode:
                print(function_name,"INSPECT_VARIABLE:NORMAL_LINE:",n_count,len(line),type(line),line);
            xmlBytes = b"".join([xmlBytes,line]); 
        #print(function_name,"len(xmlBytes)",len(xmlBytes));

        # For now, dump what we have just read to text file so the function ProcessIAD2ProductLabelMetadata() can parse it.
        FileName = 'dummy_FileName.txt';
        eachFile = 'dummy_eachFile.txt';
        #file1 = open(eachFile,"w") 
        #file1.write(str(' '.join(xmlText))); # Write the entire list as one long string.
        #file1.close();

        #file1 = open(eachFile+'2',"w"); # Write a 2nd file with carriage return.
        #file1.write(str('\n'.join(xmlText))); # Write the entire list as one long string with carriage return after each line.
        #file1.close();

        #dict_fixedList = {'pds_uri':'http://pds.nasa.gov/pds4/pds/v1'}
        dict_ConditionData = {}; # Start out as empty list will get filled in after call to ProcessIAD2ProductLabelMetadata function.
        # Parameters and their meaning:
        #    fict_fixedList = structure containg configuration values needed to parse PDS4 label.
        #    dict_ConditionData = structure containing the condition of the metadata if it has been 'Submitted' or 'Reserved'
        #    FileName = The content of PDS4 label on disk.
        #    xmlBytes = a long series of bytes representing the PDS4 label.


        # Uncomment to test how the function will handle if the file is not valid.
        FileName = 'zzz';
        eachFile = 'kkkkkk';  # This signal for the below function to use the passed in xmlBytes to traverse the tree.

        (dict_ConditionData, list_keyword_values) = self.ProcessIAD2ProductLabelMetadata(dict_fixedList, dict_ConditionData, eachFile, FileName,xmlBytes);

        if m_debug_mode:
            print(function_name,"dict_ConditionData",dict_ConditionData);
            print(function_name,"list_keyword_values",list_keyword_values);
        # This works.
        #print(function_name,"early#exit#0009");
        #exit(0);

        key = FileName;
        #DOI_template_filepath = '/home/qchau/Download/DOI_LIDVID_is_Registered_20171120/aaaDOI_templateFiles/DOI_template_20171211.xml'
        DOI_template_filepath = '/home/qchau/sandbox/pds-doi-service/config/DOI_template_20171211.xml'
        DOI_template_filepath = '/home/qchau/sandbox/pds-doi-service/config/DOI_template_20200407.xml'
        DOI_template_filepath = dict_configList.get("DOI_template");
        if m_debug_mode:
            print(function_name,"DOI_template_filepath",DOI_template_filepath);
        #print(function_name,"early#exit#0009");
        #exit(0);
        sInventoryName = "DOI_" + key
        DOI_directory_PathName = '.' + os.path.sep;
        fileDestination = os.path.join(DOI_directory_PathName,sInventoryName)
        fileSource = DOI_template_filepath

        if m_debug_mode:
            print(function_name,"sInventoryName",sInventoryName);
            print(function_name,"fileSource",fileSource);
            print(function_name,"fileDestination",fileDestination);

        shutil.copy2(fileSource, fileDestination)
        DOI_filepath = fileDestination;
        #dict_configList = {}  Don't set to empty list.
        if m_debug_mode:
            print(function_name,"dict_configList",dict_configList);
            print(function_name,"dict_fixedList",dict_fixedList);

        # Add key 'DOI_dummy_FileName.txt' to dict_ConditionData so the function ProcessDOIMetadata() can find it.
        dict_ConditionData[sInventoryName] = dict_ConditionData[FileName]

        if m_debug_mode:
            print(function_name,"dict_ConditionData",dict_ConditionData);

        o_doi_label = self.ProcessDOIMetadata(dict_configList, dict_fixedList, dict_ConditionData, key, list_keyword_values, DOI_filepath,publisher_value,contributor_value)

        if m_debug_mode:
            print(function_name,"o_doi_label",o_doi_label);
        #print(function_name,"early#exit#0008");
        #exit(0);

        return(o_doi_label);

        # Some encoding is necessary if we are dealing with string.
        if isinstance(xmlText,bytes):
            root = etree.fromstring(xmlText);
        else:
            root = etree.fromstring(str(' '.join(xmlText)).encode()); # Have to change the text to bytes then encode it to get it to work.

        if m_debug_mode:
            print(function_name,'root.tag = ' + root.tag + " => " + root.text); 

        # Inspect all the children elements in the tree.
        for appt in root.getchildren():
            if m_debug_mode:
                print(function_name,'appt.tag = ' + appt.tag + " => " + appt.text); 
            # Inspect Level 1 children.
            for elem1 in appt.getchildren():
                if not elem1.text:
                    text = 'None'
                else:
                    text = elem1.text ;
                if m_debug_mode:
                    print(function_name,'elem1.tag = ' + elem1.tag + " => " + text); 
                # Inspect Level 2 children.
                for elem2 in elem1.getchildren():


                    if not elem2.text:
                        text = 'None'
                    else:
                        text = elem2.text ;
                    if m_debug_mode:
                        print(function_name,'elem2.tag = ' + elem2.tag + " => " + text);
                # end for elem2 in elem1.getchildren():
     


        # end for elem1 in appt.getchildren():
        # end for appt in root.getchildren():
        return(1);

    def CreateDOILabel(self,target_url,contributor_value):
        function_name = 'CreateDOILabel:';
        global m_debug_mode
        o_doi_label = None;

        action_type = 'create_osti_label';
        publisher_value = DOI_CORE_CONST_PUBLISHER_VALUE;
        o_contributor_is_valid_flag = False;

        (o_contributor_is_valid_flag,o_permissible_contributor_list) = self.ValidateContributorValue(DOI_CORE_CONST_PUBLISHER_URL,contributor_value);
        if (not o_contributor_is_valid_flag):
            print(function_name,"ERROR: The value of given contributor is not valid:",contributor_value);
            print(function_name,"permissible_contributor_list",o_permissible_contributor_list);
            exit(0);

        #exit(0);
        type_is_valid = False;
        o_doi_label = 'invalid action type:action_type ' + action_type;

        if action_type == 'create_osti_label':
            #print(function_name,"target_url.startswith('http')",target_url.startswith('http'));
            if target_url.startswith('http'):
                o_doi_label = self.ParsePDS4LabelViaURI(target_url,publisher_value,contributor_value);
                type_is_valid = True;

        if not type_is_valid:
            print(function_name,"ERROR:",o_doi_label);
            print(function_name,"action_type",action_type);
            print(function_name,"target_url",target_url);
            exit(0);

        if m_debug_mode:
           print(function_name,"o_doi_label",o_doi_label.decode());
           print(function_name,"target_url,DOI_OBJECT_CREATED_SUCCESSFULLY",target_index,target_url);

        return(o_doi_label);
        
#------------------------------
#------------------------------
#  MAIN
#------------------------------
#------------------------------
#
if __name__ == '__main__':
    global f_debug
    global debug_flag
    global f_log   
    global m_debug_mode
    function_name = 'main';
    #print(function_name,'entering');

    default_run_dir     = '.' + os.path.sep 
    default_action_type = 'create_osti_label'
    default_target_url  = 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml';

    #default_publisher_url  = 'https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_JSON_1D00.JSON';
    run_dir     = default_run_dir;

    f_debug   = None                                                                                    
    debug_flag= False
    m_debug_mode = True;
    m_debug_mode = False;

    publisher_value = DOI_CORE_CONST_PUBLISHER_VALUE;

    if (len(sys.argv) > 1):
        action_type       = sys.argv[1];
        contributor_value = sys.argv[2];
        target_url        = sys.argv[3];
    else:
        # If not specified, set to default values for testing.
        print(function_name,"ERROR: Must provide contributor and target_url");
        exit(0);

    if m_debug_mode:
        print(function_name,"run_dir",run_dir);
        print(function_name,"publisher_value",publisher_value);
        print(function_name,"target_url",target_url);
        print(function_name,"contributor_value",contributor_value);

    doiCoreServices = DOICoreServices();
    o_doi_label = doiCoreServices.CreateDOILabel(target_url,contributor_value);
    print(o_doi_label.decode());
    exit(0);
    #return(1);

    #prodDate = '2019-01-01';
    #doi_date = ReturnDOIDate(f_debug, debug_flag, prodDate);
    #print(function_name,"doi_date",doi_date);
    #exit(0);

    #(o_contributor_is_valid_flag,o_permissible_contributor_list) = validate_publisher_value(DOI_CORE_CONST_PUBLISHER_URL,publisher_value);
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


    if action_type == 'create_osti_label':
        #print(function_name,"target_url.startswith('http')",target_url.startswith('http'));
        if target_url.startswith('http'):
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
       print(function_name,"target_url,DOI_OBJECT_CREATED_SUCCESSFULLY",target_index,target_url);
       print(function_name,'leaving');

    print(o_doi_label.decode());
    exit(0)

    # The code below should be in the unit test in another file.
    target_urls_list = ["https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml",
                   "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml",
                   "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml",
                   "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml",
                   "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml"]
    print(function_name,"target_urls_list:",target_urls_list);

    # Loop through each target and create a DOI object.
    for target_index,target_url in enumerate(target_urls_list):
        print(function_name,"target_index,target_url:",target_index,target_url);
        type_is_valid = False;
        o_doi_label = 'invalid action type:action_type ' + action_type;
        if action_type == 'create_osti_label':
            #print(function_name,"target_url.startswith('http')",target_url.startswith('http'));
            if target_url.startswith('http'):
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

        print(function_name,"o_doi_label",o_doi_label.decode());
        print(function_name,"target_index,target_url,DOI_OBJECT_CREATED_SUCCESSFULLY",target_index,target_url);
        exit(0)

        #print(function_name,"o_doi_label")
        print(o_doi_label.decode());

    exit(0);

    #status = main()
    #status = DOI_IAD2_label_creation();
    #sys.exit(status)


# First time:
# cd ~/sandbox/pds-doi-service
# pip install virtualenv
# python3 -m venv venv
# source venv/bin/activate
# python3 doi_core.py "./" -f aaaConfig_IAD2_IMG_InSight_20191216.xml
# python3 doi_core.py create_osti_label ./ 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml' 

# Second time:
# python3 DOICoreServices.py create_osti_label 'PDS Cartography and Imaging Sciences Discipline (IMG) Node' 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml'
# python3 DOICoreServices.py create_osti_label 'PDS Cartography and Imaging Sciences Discipline (IMG) Node' 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml'

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


