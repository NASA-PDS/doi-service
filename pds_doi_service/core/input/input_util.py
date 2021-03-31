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

import os
import urllib.parse
import tempfile
from os.path import basename

from xmlschema import XMLSchemaValidationError

import pandas as pd
import requests
from lxml import etree

from pds_doi_service.core.entities.doi import Doi, DoiStatus, ProductType
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.doi_validator import DOIValidator
from pds_doi_service.core.util.general_util import get_logger

# Get the common logger
logger = get_logger('pds_doi_service.core.input.input_util')


class DOIInputUtil:

    EXPECTED_NUM_COLUMNS = 7
    """Expected number of columns in an input CSV file."""

    MANDATORY_COLUMNS = ['status', 'title', 'publication_date',
                         'product_type_specific', 'author_last_name',
                         'author_first_name', 'related_resource']
    """The names of the expected columns within a CSV file."""

    EXPECTED_PUBLICATION_DATE_LEN = 10
    """Expected minimum length of a parsed publication date."""

    DEFAULT_VALID_EXTENSIONS = ['.xml', '.csv', '.xlsx', '.xls', '.json']
    """The default list of valid input file extensions this module can read."""

    def __init__(self, valid_extensions=None):
        """
        Creates a new DOIInputUtil instance.

        Parameters
        ----------
        valid_extensions : iterable, optional
            A listing of the extensions this input util instance should
            support. Must be a subset of the default extensions supported
            by this module. If not provided, all the default extensions are
            allowed.

        Raises
        ------
        ValueError
            If one or more unsupported extensions is provided.

        """
        self._config = DOIConfigUtil().get_config()
        self._label_util = DOIPDS4LabelUtil(
            landing_page_template=self._config.get('LANDING_PAGES', 'url')
        )
        self._valid_extensions = valid_extensions or self.DEFAULT_VALID_EXTENSIONS

        if not isinstance(self._valid_extensions, (list, tuple, set)):
            self._valid_extensions = [self._valid_extensions]

        # Set up the mapping of supported extensions to the corresponding read
        # function pointers
        self._parser_map = {
            '.xml': self.parse_xml_file,
            '.xls': self.parse_sxls_file,
            '.xlsx': self.parse_sxls_file,
            '.csv': self.parse_csv_file,
            '.json': self.parse_json_file
        }

        if not all([extension in self._parser_map
                    for extension in self._valid_extensions]):
            raise ValueError('One or more the provided extensions are not '
                             'supported by the DOIInputUtil class.')

    def parse_xml_file(self, xml_path):
        """
        Parses DOIs from a file with an .xml extension. The file is expected
        to conform either to the PDS4 label or OSTI output label schema.

        """
        dois = []

        # First read the contents of the file
        with open(xml_path, 'r') as infile:
            xml_contents = infile.read()

        xml_tree = etree.fromstring(xml_contents.encode())

        # Check if we were handed a PSD4 label
        if self._label_util.is_pds4_label(xml_tree):
            logger.info(f'Parsing xml file {basename(xml_path)} as a PSD4 label')

            try:
                dois.append(self._label_util.get_doi_fields_from_pds4(xml_tree))
            except Exception as err:
                raise InputFormatException(
                    'Could not parse the provided xml file as a PDS4 label.\n'
                    f'Reason: {err}'
                )
        # Otherwise, assume OSTI format
        else:
            logger.info(f'Parsing xml file {basename(xml_path)} as an OSTI label')

            try:
                DOIValidator().validate_against_xsd(
                    xml_contents, use_alternate_validation_method=True
                )

                dois, _ = DOIOstiWebParser.parse_osti_response_xml(xml_contents)
            except XMLSchemaValidationError as err:
                raise InputFormatException(
                    'Could not parse the provided xml file as an OSTI label.\n'
                    f'Reason: {err.reason}'
                )

        return dois

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
            # Parse 3rd column (1-indexed) as a pd.Timestamp, can't use
            # name of column since it hasn't been standardized yet
            parse_dates=[3]
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

            doi = Doi(status=DoiStatus(row['status'].lower()),
                      title=row['title'],
                      publication_date=row['publication_date'],
                      product_type=ProductType.Collection,
                      product_type_specific=row['product_type_specific'],
                      related_identifier=row['related_resource'],
                      authors=[{'first_name': row['author_first_name'],
                                'last_name': row['author_last_name']}])

            logger.debug(f'getting doi metadata {doi.__dict__}')
            doi_records.append(doi)

        return doi_records

    def parse_csv_file(self, csv_filepath):
        """
        Receives a URI containing CSV format and create one external file per
        row to output directory.
        """
        # Read the CSV file into memory
        csv_sheet = pd.read_csv(
            csv_filepath,
            parse_dates=["publication_date"]
        )

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
            logger.error("csv_filepath " + csv_filepath)
            logger.error("data columns " + str(list(csv_sheet.columns)))
            raise InputFormatException(msg)
        else:
            dois = self._parse_rows_to_doi_meta(csv_sheet)
            logger.info("FILE_WRITE_SUMMARY: num_rows " + str(num_rows))

        return dois

    def parse_json_file(self, json_filepath):
        """
        Parses DOIs from a file with a .json extension. The file is expected
        to conform to the OSTI output JSON schema.

        """
        dois = []

        # First read the contents of the file
        with open(json_filepath, 'r') as infile:
            json_contents = infile.read()

        # We only support the OSTI json format currently, so attempt to
        # parse Dois with the DOIOStiWebParser class. If it fails we'll return
        # an empty list of Dois.
        try:
            dois, _ = DOIOstiWebParser.parse_osti_response_json(json_contents)
        except InputFormatException:
            logger.warning('Unable to parse any Doi objects from provided '
                           f'json file "{json_filepath}"')

        return dois

    def _read_from_path(self, path):
        """
        Parses Doi's from the file or files referenced by the provided path.
        If the path points to a single file, only that file is parsed. Otherwise,
        directories are walked for any files contained within. Any files with
        unsupported extensions are ignored.

        Parameters
        ----------
        path : str
            Path to the location to read. May be a single file or directory.

        Returns
        -------
        InputFormatException
            If an error is encountered while reading a local file.

        """
        dois = []

        if os.path.isfile(path):
            logger.info(f'Reading local file path {path}')

            extension = os.path.splitext(path)[-1]

            if extension in self._valid_extensions:
                # Select the appropriate read function based on the extension
                read_function = self._parser_map[extension]

                try:
                    dois = read_function(path)
                except OSError as err:
                    msg = f'Error reading file {path}, reason: {str(err)}'

                    logger.error(msg)
                    raise InputFormatException(msg)
            else:
                logger.info(f'File {path} has unsupported extension, ignoring')
        else:
            logger.info(f'Reading files within directory {path}')

            for sub_path in os.listdir(path):
                dois.extend(self._read_from_path(os.path.join(path, sub_path)))

        return dois

    def _read_from_remote(self, input_url):
        """
        Reads a remote file from the provided URL into a local temporary file,
        then parses and returns any Dois from it. The local temp file is
        deleted once this function returns.

        Parameters
        ----------
        input_url : str
            The URL to the file to download locally.

        Returns
        -------
        dois : list of Doi
            The Doi's parsed from the remote file.

        Raises
        ------
        InputFormatException
            If the URL points to a file with an unsupported extension.

        """
        parsed_url = urllib.parse.urlparse(input_url)

        # Check for valid extension before attempting to read from remote
        extension = os.path.splitext(parsed_url.path)[-1]

        if extension not in self._valid_extensions:
            raise InputFormatException(
                f'File extension type "{extension}" is not supported for this, '
                f'operation, must be one of {",".join(self._valid_extensions)}'
            )

        response = requests.get(input_url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            raise InputFormatException(
                f'Could not read remote file {input_url}, reason: {str(http_err)}'
            )

        with tempfile.NamedTemporaryFile(suffix=basename(parsed_url.path)) as temp_file:
            temp_file.write(response.content)
            temp_file.seek(0)

            return self._read_from_path(temp_file.name)

    def parse_dois_from_input_file(self, input_file):
        """
        Parses one or more Doi objects from the provided input file location.
        The location may be a path to a local file or directory, or a remote
        URL to the desired file.

        Parameters
        ----------
        input_file : str
            The location of the input to parse Doi's from. If a local directory,
            the location will be walked for input files. If a remote URL,
            the file will be read into a local temporary file, then processed
            like a local path.

        Returns
        -------
        dois : list of Doi
            The list of Doi objects parsed from the input location.

        Raises
        ------
        InputFormatException
            If the input location does not correspond to a URL (starting with
            http), or a local path, or if no Doi objects can be parsed from
            the file (because it is an unsupported exception).

        """
        # See if we were handed a URL
        if input_file.startswith('http'):
            dois = self._read_from_remote(input_file)
        # Otherwise see if its a local file
        elif os.path.exists(input_file):
            dois = self._read_from_path(input_file)
        else:
            raise InputFormatException(
                f"Error reading file {input_file}, path does not correspond to "
                f"a remote URL or a local file path."
            )

        # Make sure we got back at least one Doi
        if not dois:
            raise InputFormatException(
                f"Unable to parse DOI's from input location {input_file}\n"
                f"Please ensure the input is of the following type(s): "
                f"{', '.join(self._valid_extensions)}"
            )

        return dois
