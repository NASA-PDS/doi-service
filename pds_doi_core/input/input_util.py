import os
import pandas as pd
from datetime import datetime

from pds_doi_core.outputs.output_util import DOIOutputUtil
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.input.exeptions import InputFormatException

# Get the common logger and set the level for this file if desire.
import logging
logger = get_logger('pds_doi_core.input.input_util')

class DOIInputUtil:

    m_doi_output_util = DOIOutputUtil()

    m_EXPECTED_NUM_COLUMNS = 7

    def parse_sxls_file(self, i_filepath):
        """Function receives a URI containing SXLS format and create one external file per row to output directory."""

        logger.info("i_filepath" + " " + i_filepath)

        doi_directory_pathname = os.path.join('.','output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        xl_wb = pd.ExcelFile(i_filepath)
        actual_sheet_name = xl_wb.sheet_names[0] # We only want the first sheet.
        xl_sheet = pd.read_excel(i_filepath,actual_sheet_name)
        num_cols = len(xl_sheet.columns)
        num_rows = len(xl_sheet.index)

        logger.info("num_cols" + " " + str(num_cols))
        logger.info("num_rows" + " " + str(num_rows))
        logger.debug("data columns " + " " + str(list(xl_sheet.columns)))

        # rename columns in a more simple way
        xl_sheet = xl_sheet.rename(columns={'publication_date (yyyy-mm-dd)': 'publication_date',
                                'product_type_specific\n(PDS4 Bundle | PDS4 Collection | PDS4 Document)': 'product_type_specific',
                                'related_resource\nLIDVID': 'related_resource'})

        if (num_cols < self.m_EXPECTED_NUM_COLUMNS):
            logger.error("expecting" + " " + str(self.m_EXPECTED_NUM_COLUMNS) + " columns in XLS file has %i columns." % (num_cols))
            logger.error("i_filepath" + " " + i_filepath)
            logger.error("columns " + " " + str(list(xl_sheet.columns)))
            raise InputFormatException("columns " + " " + str(list(xl_sheet.columns)))
        else:
            dict_condition_data = self._parse_rows_to_doi_meta(xl_sheet)
            logger.info("FILE_WRITE_SUMMARY:num_rows" + " " + str(num_rows))



        return dict_condition_data

    def _parse_rows_to_doi_meta(self, xl_sheet):
        """Given all rows in input file, parse each row and return the aggregated XML of all records in OSTI format"""

        doi_records = []

        for index, row in xl_sheet.iterrows():
            doi_record = {}
            doi_record['title'] = row['title']
            doi_record['authors'] = [{'first_name': row['author_first_name'],
                                     'last_name': row['author_last_name']}]
            doi_record['publication_date'] = row['publication_date']
            doi_record['product_type'] = 'Collection'
            doi_record['product_type_specific'] = row['product_type_specific']
            doi_record['related_identifier'] = row['related_resource']
            logger.debug(f'getting doi metadata {doi_record}')
            doi_records.append(doi_record)

        return doi_records


    def parse_csv_file(self, i_filepath):
        """Function receives a URI containing CSV format and create one external file per row to output directory."""

        logger.info("i_filepath" + " " + i_filepath)

        doi_directory_pathname = os.path.join('.','output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        # Read the CSV file into memory.

        xl_sheet = pd.read_csv(i_filepath,
                               parse_dates=['publication_date'],
                               date_parser=lambda d: datetime.strptime(d, '%Y-%m-%d'))
        num_cols = len(xl_sheet.columns)
        num_rows = len(xl_sheet.index)

        logger.debug("xl_sheet.head() " + " " + str(xl_sheet.head()))
        logger.info("num_cols" + " " + str(num_cols))
        logger.info("num_rows" + " " + str(num_rows))
        logger.debug("data columns" + str(list(xl_sheet.columns)))

        if num_cols < self.m_EXPECTED_NUM_COLUMNS:
            logger.error("expecting" + " " + str(self.m_EXPECTED_NUM_COLUMNS) + " columns in CSV file has %i columns." % (num_cols))
            logger.error("i_filepath" + " " + i_filepath)
            logger.error("data columns " + " " + str(list(xl_sheet.columns)))
            raise InputFormatException("columns " + " " + str(list(xl_sheet.columns)))
        else:

            dict_condition_data = self._parse_rows_to_doi_meta(xl_sheet)

            logger.info("FILE_WRITE_SUMMARY:num_rows" + " " + str(num_rows))

        return dict_condition_data
