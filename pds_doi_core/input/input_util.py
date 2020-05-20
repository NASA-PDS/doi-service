#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

from lxml import etree
import copy
import pandas as pd
import xlrd

from datetime import datetime

from pds_doi_core.util.const import *

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.outputs.output_util import DOIOutputUtil
from pds_doi_core.util.general_util import DOIGeneralUtil, get_logger

# Get the common logger and set the level for this file if desire.
import logging
logger = get_logger('pds_doi_core.input.input_util')

class DOIInputUtil:

    m_doi_config_util = DOIConfigUtil()
    m_doi_output_util = DOIOutputUtil()

    m_EXPECTED_NUM_COLUMNS = 7

    def parse_sxls_file(self,i_app_basepath,i_filepath,dict_fixedlist=None, dict_config_list=None, dict_condition_data=None):
        '''Function receives a URI containing SXLS format and create one external file per row to output directory.'''
        o_doi_label = None
        o_num_files_created = 0

        logger.info("i_app_basepath" + " " + i_app_basepath)
        logger.info("i_filepath" + " " + i_filepath)

        doi_directory_pathname = os.path.join('.','output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        #------------------------------
        # Open the DOI reserved XML label
        #   -- ElementTree supports 'findall' using dict_namespaces and designation of instances
        #   -- etree doesn't support designation of instances
        #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
        #------------------------------
        reserve_template_pathname = dict_config_list.get("DOI_reserve_template")
        logger.info("reserve_template_pathname" + " " + reserve_template_pathname)

        # Do a sanity check on the structure of the DOI template structure.
        self._validate_reserve_doi_template_structure(reserve_template_pathname)

        xl_wb    = pd.ExcelFile(i_filepath)
        actual_sheet_name = xl_wb.sheet_names[0] # We only want the first sheet.
        xl_wb    = pd.read_excel(i_filepath)
        xl_sheet = pd.read_excel(i_filepath,actual_sheet_name)
        num_cols = len(xl_sheet.columns)
        num_rows = len(xl_sheet.index)

        logger.info("num_cols" + " " + str(num_cols))
        logger.info("num_rows" + " " + str(num_rows))
        logger.debug("data columns " + " " + str(list(xl_sheet.columns)))

        if (num_cols < self.m_EXPECTED_NUM_COLUMNS):
            logger.error("expecting" + " " + str(self.m_EXPECTED_NUM_COLUMNS) + " columns in XLS file has %i columns." % (num_cols))
            logger.error("i_filepath" + " " + i_filepath)
            logger.error("columns " + " " + str(list(xl_sheet.columns)))
            sys.exit(1)
        else:
          (dict_condition_data,o_created_filelist,o_aggregated_tree) = self._parse_rows_to_osti_meta(doi_directory_pathname,xl_sheet,num_rows,reserve_template_pathname,dict_condition_data,dict_fixedlist)

          o_num_files_created = len(o_created_filelist)
          logger.info("FILE_WRITE_SUMMARY:o_num_files_created" + " " + str(o_num_files_created))
          logger.info("FILE_WRITE_SUMMARY:num_rows" + " " + str(num_rows))

          o_aggregated_DOI_content = self.m_doi_output_util.aggregate_reserve_osti_doi(doi_directory_pathname,o_created_filelist)

        return(o_num_files_created,o_aggregated_DOI_content)

    def _parse_rows_to_osti_meta(self,doi_directory_pathname,xl_sheet,num_rows,reserve_template_pathname,dict_condition_data,dict_fixedlist):
        '''Given all rows in input file, parse each row and return the aggregated XML of all records in OSTI format'''
        o_created_filelist = []
        aggregated_root = etree.XML('''<?xml version="1.0"?>
                                      <records>
                                      </records>''')
        o_aggregated_tree = etree.ElementTree(aggregated_root);

        parent_xpath = "/records/record/"

        start_row = 0 # Module pandas read in the column header differently, which make the row 0 the first actual data.

        for row_idx in range(start_row,num_rows):    # Iterate through rows ignore 1st row
            #------------------------------
            # extract metadata from Columns and populate row-content
            #  -- ignore 1st column 'state' which is used for validation
            #------------------------------
            #------------------------------
            # Generate the product_label_filename using the LIDVID
            #    -- remove "urn:nasa:pds"
            #     -- replace "::" with "-"
            #------------------------------

            # Extra processing if any fields starts with single or double quotes. 

            actual_index = row_idx - 1 # Because of how pandas data frame is structure, we subtract 1.
            related_resource = xl_sheet.iloc[actual_index,6]

            logger.debug("row_idx,related_resource" + " " + str(row_idx) + " " + str(related_resource))

            product_label_filename = related_resource.replace("urn:nasa:pds:", "")
            product_label_filename = product_label_filename.replace("::", "_")

            logger.info("related_resource,product_label_filename" + " " + related_resource + " " + product_label_filename)

            logger.info(" -- processing Product label file: " + product_label_filename)

            dict_condition_data[product_label_filename] = {}

            dict_condition_data[product_label_filename]["title"] = xl_sheet.iloc[actual_index, 1]
            #--
            # Eventhough cell is shown to be 'text / unicode' value is actually stored as datetime
            #    -- test for unicode else datetime
            #--
            type_date_column = str(type(xl_sheet.iloc[actual_index, 2]))

            logger.debug("type_date_column" + " " + type_date_column)
            if 'unicode' in type_date_column or 'str' in type_date_column:
                dict_condition_data[product_label_filename]["publication_date"] = xl_sheet.iloc[actual_index, 2]
            else:
                pb_int = xl_sheet.iloc[actual_index,2]
                pb_datetime = pb_int

            dict_condition_data[product_label_filename]["product_type"] ="Collection"
            dict_condition_data[product_label_filename]["product_type_specific"]     = xl_sheet.iloc[actual_index,3]
            dict_condition_data[product_label_filename]["authors/author/last_name"]  = xl_sheet.iloc[actual_index,4]
            dict_condition_data[product_label_filename]["authors/author/first_name"] = xl_sheet.iloc[actual_index,5]
            dict_condition_data[product_label_filename]["related_identifiers/related_identifier/identifier_value"] = xl_sheet.iloc[actual_index,6]
            #------------------------------
            #------------------------------
            # Begin replacing the metadata in the DOI template file with that in Product Label
            #------------------------------
            try:
                #f_doi_file = open(reserve_template_pathname, mode='r+')
                f_doi_file = open(reserve_template_pathname, mode='r')
                xml_doi_text = f_doi_file.read()
                f_doi_file.close()

            except:
                logger.error("DOI template file (%s) not found for edit\n" % (reserve_template_pathname))
                sys.exit(1)

            #------------------------------
            # For each key/value in dictionary (that contains the values for the DOI label)
            #------------------------------
            dict_value = dict_condition_data.get(product_label_filename)

            for key, value in dict_value.items():
                attr_xpath = parent_xpath + key

                xml_doi_text = self.m_doi_output_util.populate_doi_xml_with_values(dict_fixedlist, xml_doi_text, attr_xpath, value)

            # The type of xml_doi_text is bytes and content is of XML format.
            # Find the element with 'record' tag, extract it and insert it into our o_aggregated_tree to return.
            my_root = etree.fromstring(xml_doi_text);
            my_tree = etree.ElementTree(my_root);
            find_me = my_root.find('record')
            o_aggregated_tree.getroot().insert(0,find_me)

            # Write the replacement metadata to the DOI file

            doi_filepath = self.m_doi_output_util.write_replacement_osti_metadata(doi_directory_pathname,product_label_filename,xml_doi_text)

            # Add the new name created to so we can agggregate them all into one file.
            o_created_filelist.append(doi_filepath)

        # end for row_idx in range(start_row,num_rows):    # Iterate through rows ignore 1st row

        return (dict_condition_data,o_created_filelist,o_aggregated_tree)

    def _validate_reserve_doi_template_structure(self,reserve_template_pathname):
        # Do a sanity check on the structure of the DOI template structure.
        try:
            tree = etree.parse(reserve_template_pathname)
        except OSError as err:
            logger.error("ABORT: the xml 'Reserved template label file (%s) could not be read" % (reserve_template_pathname) )
            sys.exit(1)
        except etree.ParseError as err:
            logger.error("ABORT: the xml 'Reserved template label file (%s) could not be parsed" % (reserve_template_pathname) )
            sys.exit(1)
        else:
            pass

        return 1

    def parse_csv_file(self,i_app_basepath,i_filepath,dict_fixedlist=None, dict_config_list=None, dict_condition_data=None):
        '''Function receives a URI containing CSV format and create one external file per row to output directory.'''
        o_doi_label = None
        o_num_files_created = 0

        logger.info("i_app_basepath" + " " + i_app_basepath)
        logger.info("i_filepath" + " " + i_filepath)

        doi_directory_pathname = os.path.join('.','output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        #------------------------------
        # Open the DOI reserved XML label
        #   -- ElementTree supports 'findall' using dict_namespaces and designation of instances
        #   -- etree doesn't support designation of instances
        #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
        #------------------------------
        reserve_template_pathname = dict_config_list.get("DOI_reserve_template")
        logger.info("reserve_template_pathname" + " " + reserve_template_pathname)

        # Do a sanity check on the structure of the DOI template structure.
        self._validate_reserve_doi_template_structure(reserve_template_pathname)

        # Read the CSV file into memory.

        xl_sheet = pd.read_csv(i_filepath)
        num_cols = len(xl_sheet.columns)
        num_rows = len(xl_sheet.index)

        logger.debug("xl_sheet.head() " + " " + str(xl_sheet.head()))
        logger.info("num_cols" + " " + str(num_cols))
        logger.info("num_rows" + " " + str(num_rows))
        logger.debug("data columns" + str(list(xl_sheet.columns)))

        if (num_cols < self.m_EXPECTED_NUM_COLUMNS):
            logger.error("expecting" + " " + str(self.m_EXPECTED_NUM_COLUMNS) + " columns in CSV file has %i columns." % (num_cols))
            logger.error("i_filepath" + " " + i_filepath)
            logger.error("data columns " + " " + str(list(xl_sheet.columns)))
            sys.exit(1)
        else:

            (dict_condition_data,o_created_filelist,o_aggregated_tree) = self._parse_rows_to_osti_meta(doi_directory_pathname,xl_sheet,num_rows,reserve_template_pathname,dict_condition_data,dict_fixedlist)

            o_num_files_created = len(o_created_filelist)
            logger.info("FILE_WRITE_SUMMARY:o_num_files_created" + " " + str(o_num_files_created))
            logger.info("FILE_WRITE_SUMMARY:num_rows" + " " + str(num_rows))

            o_aggregated_DOI_content = self.m_doi_output_util.aggregate_reserve_osti_doi(doi_directory_pathname,o_created_filelist)
        #print("o_aggregated_DOI_content",o_aggregated_DOI_content,type(o_aggregated_DOI_content));
        #exit(0)

        return(o_num_files_created,dict_condition_data,o_aggregated_DOI_content,o_aggregated_tree)
