#
#  Copyright 2021, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
=============
input_util.py
=============

Contains classes for working with input label files, be they local or remote.
"""

import pandas as pd
from datetime import datetime

from pds_doi_service.core.entities.doi import Doi, ProductType
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.outputs.output_util import DOIOutputUtil
from pds_doi_service.core.util.general_util import get_logger

# Get the common logger
logger = get_logger('pds_doi_service.core.input.input_util')


class DOIInputUtil:
    m_doi_output_util = DOIOutputUtil()

    EXPECTED_NUM_COLUMNS = 7
    """Expected number of columns in an input CSV file."""

    MANDATORY_COLUMNS = ['status', 'title', 'publication_date',
                         'product_type_specific', 'author_last_name',
                         'author_first_name','related_resource']
    """The names of the expected columns within a CSV file."""

    EXPECTED_PUBLICATION_DATE_LEN = 10
    """Expected minimum length of a parsed publication date."""

    def parse_sxls_file(self, i_filepath):
        """
        Receives a URI containing SXLS format and writes one external file per
        row to an output directory.
        """
        logger.info("i_filepath " + i_filepath)

        xl_wb = pd.ExcelFile(i_filepath, engine='openpyxl')

        # We only want the first sheet.
        actual_sheet_name = xl_wb.sheet_names[0]
        xl_sheet = pd.read_excel(
            i_filepath, actual_sheet_name,
            converters={'publication_date': str,
                        'publication_date (yyyy-mm-dd)': str}
        )

        num_cols = len(xl_sheet.columns)
        num_rows = len(xl_sheet.index)

        logger.info("num_cols " + str(num_cols))
        logger.info("num_rows " + str(num_rows))
        logger.debug("data columns " + str(list(xl_sheet.columns)))

        # rename columns in a simpler way
        xl_sheet = xl_sheet.rename(
            columns={
                'publication_date (yyyy-mm-dd)': 'publication_date',
                'product_type_specific\n(PDS4 Bundle | PDS4 Collection | PDS4 Document)': 'product_type_specific',
                'related_resource\nLIDVID': 'related_resource'
            }
        )

        if num_cols < self.EXPECTED_NUM_COLUMNS:
            msg = (f"Expected {self.EXPECTED_NUM_COLUMNS} columns in the "
                   f"provided XLS file, but only found {num_cols} columns.")

            logger.error(msg)
            raise InputFormatException(msg)
        else:
            dois = self._parse_rows_to_doi_meta(xl_sheet)
            logger.info("FILE_WRITE_SUMMARY: num_rows " + str(num_rows))

        return dois

    def _parse_rows_to_doi_meta(self, xl_sheet):
        """
        Given all rows in input file, parse each row and return the aggregated
        XML of all records in OSTI format.
        """

        doi_records = []

        for index, row in xl_sheet.iterrows():
            logger.debug(f"row {row}")
            # It is possible that the length of row['publication_date'] is more
            # than needed, we only need to get the first 10 characters
            #   '2020-08-01' from '2020-08-01 00:00:00'
            if len(row['publication_date']) >= self.EXPECTED_PUBLICATION_DATE_LEN:
                # It is possible that the format provided is not expected,
                # put a try/except clause to catch that.
                try:
                    publication_date_value = datetime.strptime(
                        row['publication_date'][:self.EXPECTED_PUBLICATION_DATE_LEN],
                        '%Y-%m-%d'
                    )
                except Exception:
                    msg = (f"Expecting publication_date "
                           f"[{row['publication_date']}] with format YYYY-mm-dd")

                    logger.error(msg)
                    raise InputFormatException(msg)
            else:
                raise InputFormatException(
                    f"Expecting publication_date to be at least "
                    f"{self.EXPECTED_PUBLICATION_DATE_LEN} characters: "
                    f"[{row['publication_date']}]"
                )

            doi = Doi(title=row['title'],
                      publication_date=publication_date_value,
                      product_type=ProductType.Collection,
                      product_type_specific=row['product_type_specific'],
                      related_identifier=row['related_resource'],
                      authors=[{'first_name': row['author_first_name'],
                                'last_name': row['author_last_name']}])

            logger.debug(f'getting doi metadata {doi.__dict__}')
            doi_records.append(doi)

        return doi_records

    def parse_csv_file(self, i_filepath):
        """
        Receives a URI containing CSV format and create one external file per
        row to output directory.
        """
        logger.info("i_filepath " + i_filepath)

        # Read the CSV file into memory.
        csv_sheet = pd.read_csv(i_filepath)
        num_cols = len(csv_sheet.columns)
        num_rows = len(csv_sheet.index)

        logger.debug("csv_sheet.head() " + str(csv_sheet.head()))
        logger.info("num_cols " + str(num_cols))
        logger.info("num_rows " + str(num_rows))
        logger.debug("data columns " + str(list(csv_sheet.columns)))

        if num_cols < self.EXPECTED_NUM_COLUMNS:
            msg = (f"Expecting {self.EXPECTED_NUM_COLUMNS} columns in the provided "
                   f"CSV file, but only found {num_cols} columns.")

            logger.error(msg)
            logger.error("i_filepath " + i_filepath)
            logger.error("data columns " + str(list(csv_sheet.columns)))
            raise InputFormatException(msg)
        else:
            dois = self._parse_rows_to_doi_meta(csv_sheet)
            logger.info("FILE_WRITE_SUMMARY: num_rows " + str(num_rows))

        return dois
