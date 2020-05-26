#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

import os
import sys
from lxml import etree

from pds_doi_core.util.general_util import get_logger

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.input.out_util')

class DOIOutputUtil:
    # This class DOIOutputUtil provide convenient functions to update a DOI object already in memory.
    # The structure of DOI object is a document tree.

    def write_replacement_osti_metadata(self,i_doi_directory_pathname,FileName,xmlDOI_Text):
        '''Write the replacement metadata to the DOI file.'''

        sString = "DOI_reserved_" + FileName + ".xml"
        sString = sString.replace(":", "_")
        DOI_filepath = os.path.join(i_doi_directory_pathname,sString)
        logger.info("sString,DOI_filepath" + " " + sString + " " + DOI_filepath)

        logger.info("FILE_WRITE" + " " + DOI_filepath);

        f_DOI_file = open(DOI_filepath, mode='w')
        f_DOI_file.write(xmlDOI_Text.decode())
        f_DOI_file.close()

        return DOI_filepath

    def aggregate_reserve_osti_doi_from_dict(self,dict_config_list,dict_fixedlist,i_doi_directory_pathname,dict_condition_data,write_to_file_flag=False):
        """
        Create a file that groups each DOI record into a single file -- that can singly be submitted

        <?xml version="1.0" encoding="UTF-8"?>
         <records>
           <record status="Reserved">
                  ...
            </record>
           <record status="Reserved">
                  ...
            </record>
        </records>
        """
        aggregated_root = etree.XML('''<?xml version="1.0"?>
                                      <records>
                                      </records>''')
        o_aggregated_tree = etree.ElementTree(aggregated_root);
        o_created_filelist = []
        o_doi_aggregate_filepath = '';

        doi_directory_pathname = os.path.join('.','output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        parent_xpath = "/records/record/"

        reserve_template_pathname = dict_config_list.get("DOI_reserve_template")
        logger.info("reserve_template_pathname" + " " + reserve_template_pathname)

        for product_label_filename, dict_value in dict_condition_data.items():
            try:
                f_doi_file = open(reserve_template_pathname, mode='r')
                xml_doi_text = f_doi_file.read()
                f_doi_file.close()
            except FileNotFoundError:
                logger.error("DOI template file (%s) not found for edit\n" % (reserve_template_pathname))
                sys.exit(1)

            for key, value in dict_value.items():
                attr_xpath = parent_xpath + key

                xml_doi_text = self.populate_doi_xml_with_values(dict_fixedlist, xml_doi_text, attr_xpath, value)

            # The type of xml_doi_text is bytes and content is of XML format.
            # Find the element with 'record' tag, extract it and insert it into our o_aggregated_tree to return.
            my_root = etree.fromstring(xml_doi_text);
            my_tree = etree.ElementTree(my_root);
            find_me = my_root.find('record')
            o_aggregated_tree.getroot().insert(0,find_me)

            # Write the replacement metadata to the DOI file

            if write_to_file_flag:
               doi_filepath = self.write_replacement_osti_metadata(doi_directory_pathname,product_label_filename,xml_doi_text)

               # Add the new name created to so we can agggregate them all into one file.
               o_created_filelist.append(doi_filepath)

        # Write the entire tree (the aggregated content) to file with nice format.
        if write_to_file_flag:
            aggregated_reserve_filename = "aaa_DOI_aggregate_reserved.xml"
            o_doi_aggregate_filepath = os.path.join(doi_directory_pathname,aggregated_reserve_filename)
            f = open(o_doi_aggregate_filepath, "w")
            f.write(etree.tostring(o_aggregated_tree).decode()) # Convert bytes to string before writing.
            f.close()

        return (o_aggregated_tree,o_doi_aggregate_filepath,o_created_filelist)

    def populate_doi_xml_with_values(self,dict_fixedlist, xml_text, attr_xpath, i_value):                                      
        '''Given an XML object xml_text, this function will update the attr_xpath in xml_text with the new input i_value.
           Since we don't know the type of xml_text (bytes or text), we may have to encode xml_text from string to bytes.'''
        elm = None # Set to None so the value can be checked before printing.

        logger.debug("len(xml_text) %s",len(xml_text))
        logger.debug("type(xml_text) %s",type(xml_text))

        #------------------------------                                                                                             
        # Populate the xml attribute with the specified value                                                                       
        #------------------------------                                                                                             

        if isinstance(xml_text,bytes):
            doc = etree.fromstring(xml_text)
        else:
            doc = etree.fromstring(xml_text.encode()) # Have to change the text to bytes then encode it to get it to work.

        #print(f"VARIABLE_CHECK: LEN_DOC_XPATH_ATTR_XPATH {len(doc.xpath(attr_xpath))} {attr_xpath} {i_value} {type(i_value)}")

        if len(doc.xpath(attr_xpath)) == 0:
            # This shouldn't happen where the attr_xpath is not found in document.
            logger.error(f"Expected len of {attr_xpath} to not be zero {len(doc.xpath(attr_xpath))}")
            exit(1)

        else:

            elm = doc.xpath(attr_xpath)[0]                                                              

            logger.info("VARIABLE_UPDATE: variable [%s] value [%s]" % (attr_xpath,str(i_value)))

            # Do a sanity check to make sure the list update is not 'last_name' or 'first_name' because it would of been
            # done with populate_list_values_with_values() function above.
            list_of_tags_to_not_process = ['first_name','last_name']
            if isinstance(i_value,list):
                if attr_xpath in list_of_tags_to_not_process:
                    logger.error("This function does not suppport this attr_xpath [%s] list_of_tags_to_not_process [%s]." % (attr_xpath,list_of_tags_to_not_process))
                    exit(1)
                if 'last_name' in attr_xpath:
                    logger.error("This function does not suppport this attr_xpath [%s]." % attr_xpath)
                    exit(1)
                if 'first_name' in attr_xpath:
                    logger.error("This function does not suppport this attr_xpath [%s]." % attr_xpath)
                    exit(1)
            else: 
                # Do a normal setting of value to text of element.
                elm.text = i_value

        etree.indent(doc,space="    ")  # Re-indent because we may have new levels added.
        sOutText = etree.tostring(doc,pretty_print=True)
        return(sOutText)
