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
import tempfile
import urllib.parse
from datetime import datetime
from os.path import basename

import pandas as pd
import requests
from lxml import etree
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.osti.osti_validator import DOIOstiValidator
from pds_doi_service.core.outputs.osti.osti_web_parser import DOIOstiXmlWebParser
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.service import SERVICE_TYPE_DATACITE
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger
from xmlschema import XMLSchemaValidationError  # type: ignore

# Get the common logger
logger = get_logger(__name__)


class DOIInputUtil:

    EXPECTED_NUM_COLUMNS = 7
    """Expected number of columns in an input CSV file."""

    MANDATORY_COLUMNS = [
        "status",
        "title",
        "publication_date",
        "product_type_specific",
        "author_last_name",
        "author_first_name",
        "related_resource",
    ]
    """The names of the expected columns within a CSV file."""

    EXPECTED_PUBLICATION_DATE_LEN = 10
    """Expected minimum length of a parsed publication date."""

    DEFAULT_VALID_EXTENSIONS = [".xml", ".csv", ".xlsx", ".xls", ".json"]
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
        self._label_util = DOIPDS4LabelUtil(landing_page_template=self._config.get("LANDING_PAGES", "url"))
        self._valid_extensions = valid_extensions or self.DEFAULT_VALID_EXTENSIONS

        if not isinstance(self._valid_extensions, (list, tuple, set)):
            self._valid_extensions = [self._valid_extensions]

        # Set up the mapping of supported extensions to the corresponding read
        # function pointers
        self._parser_map = {
            ".xml": self.parse_xml_file,
            ".xls": self.parse_xls_file,
            ".xlsx": self.parse_xls_file,
            ".csv": self.parse_csv_file,
            ".json": self.parse_json_file,
        }

        if not all([extension in self._parser_map for extension in self._valid_extensions]):
            raise ValueError("One or more the provided extensions are not " "supported by the DOIInputUtil class.")

    def parse_xml_file(self, xml_path):
        """
        Parses DOIs from a file with an .xml extension. The file is expected
        to conform either to a PDS4 label or the OSTI XML label schema.

        Parameters
        ----------
        xml_path : str
            Path to the XML file to parse.

        Returns
        -------
        dois : List of Doi
            DOI objects parsed from the provided XML file.

        Raises
        ------
        InputFormatException
            If the provided XML file cannot be parsed as a PDS4 label or
            OSTI XML label.

        """
        dois = []

        # First read the contents of the file
        with open(xml_path, "r") as infile:
            xml_contents = infile.read()

        xml_tree = etree.fromstring(xml_contents.encode())

        # Check if we were handed a PSD4 label
        if self._label_util.is_pds4_label(xml_tree):
            logger.info("Parsing xml file %s as a PSD4 label", basename(xml_path))

            try:
                dois.append(self._label_util.get_doi_fields_from_pds4(xml_tree))
            except Exception as err:
                raise InputFormatException("Could not parse the provided xml file as a PDS4 label.\n" f"Reason: {err}")
        # Otherwise, assume OSTI format
        else:
            logger.info("Parsing xml file %s as an OSTI label", basename(xml_path))

            try:
                DOIOstiValidator()._validate_against_xsd(xml_tree)

                dois, _ = DOIOstiXmlWebParser.parse_dois_from_label(xml_contents)
            except XMLSchemaValidationError as err:
                raise InputFormatException(
                    "Could not parse the provided xml file as an OSTI label.\n" f"Reason: {err.reason}"
                )

        return dois

    def parse_xls_file(self, xls_path):
        """
        Parses DOIs from an Excel file with an .xls or .xlsx extension.
        Each row within the spreadsheet is parsed into a distinct DOI object.

        Parameters
        ----------
        xls_path : str
            Path to the Excel file to parse.

        Returns
        -------
        dois : List of Doi
            DOI objects parsed from the provided Excel file.

        Raises
        ------
        InputFormatException
            If the provided Excel file contains less than the expected number
            of columns.

        """
        logger.info("Parsing xls file %s", basename(xls_path))

        xl_wb = pd.ExcelFile(xls_path, engine="openpyxl")

        # We only want the first sheet.
        actual_sheet_name = xl_wb.sheet_names[0]
        xl_sheet = pd.read_excel(
            xls_path,
            actual_sheet_name,
            # Parse 3rd column (1-indexed) as a pd.Timestamp, can't use
            # name of column since it hasn't been standardized yet
            parse_dates=[3],
            # Remove automatic replacement of empty columns with NaN
            na_filter=False,
        )

        num_cols = len(xl_sheet.columns)
        num_rows = len(xl_sheet.index)

        logger.debug("num_cols: %d", num_cols)
        logger.debug("num_rows: %d", num_rows)
        logger.debug("data columns: %s", str(list(xl_sheet.columns)))

        # rename columns in a simpler way
        xl_sheet = xl_sheet.rename(
            columns={
                "publication_date (yyyy-mm-dd)": "publication_date",
                "product_type_specific\n(PDS4 Bundle | PDS4 Collection | PDS4 Document)": "product_type_specific",
                "related_resource\nLIDVID": "related_resource",
            }
        )

        if num_cols < self.EXPECTED_NUM_COLUMNS:
            msg = (
                f"Expected {self.EXPECTED_NUM_COLUMNS} columns in the "
                f"provided XLS file, but only found {num_cols} column(s)."
            )

            logger.error(msg)
            raise InputFormatException(msg)

        dois = self._parse_rows_to_dois(xl_sheet)

        return dois

    def _parse_rows_to_dois(self, xl_sheet):
        """
        Given an in-memory Excel spreadsheet, parse each row and return a list
        of DOI objects.

        Parameters
        ----------
        xl_sheet : pandas.DataFrame
            The in-memory spreadsheet to parse.

        Returns
        -------
        dois : list of Doi
            The DOI objects parsed from the Excel spreadsheet.

        """
        dois = []
        timestamp = datetime.now()

        for index, row in xl_sheet.iterrows():
            logger.debug(f"row {row}")

            doi = Doi(
                status=DoiStatus(row["status"].lower()),
                title=row["title"],
                publication_date=row["publication_date"],
                product_type=self._parse_product_type(row["product_type_specific"]),
                product_type_specific=row["product_type_specific"],
                related_identifier=row["related_resource"],
                authors=[{"first_name": row["author_first_name"], "last_name": row["author_last_name"]}],
                date_record_added=timestamp,
                date_record_updated=timestamp,
            )

            logger.debug("Parsed Doi: %r", doi.__dict__)
            dois.append(doi)

        return dois

    @staticmethod
    def _parse_product_type(product_type_specific):
        """
        Attempt to parse a ProductType enum value from the "product_type_specific"
        field of a parsed Doi.

        Parameters
        ----------
        product_type_specific : str
            The product_type_specific field from a parsed Doi.

        Returns
        -------
        product_type : ProductType
            The product type parsed from the product_type_specific field,
            if present. Otherwise, defaults to ProductType.Text.

        """
        product_type_specific_suffix = product_type_specific.split()[-1]

        try:
            product_type = ProductType(product_type_specific_suffix.capitalize())
            logger.debug("Parsed %s from %s", product_type, product_type_specific)
        except ValueError:
            product_type = ProductType.Collection
            logger.debug("Could not parsed product type from %s, defaulting to %s", product_type_specific, product_type)

        return product_type

    def parse_csv_file(self, csv_path):
        """
        Parses DOIs from a file with a .csv extension.
        Each row within the CSV is parsed into a distinct DOI object.

        Parameters
        ----------
        csv_path : str
            Path to the CSV file to parse.

        Returns
        -------
        dois : List of Doi
            DOI objects parsed from the provided CSV file.

        Raises
        ------
        InputFormatException
            If the provided CSV file contains less than the expected number
            of columns.

        """
        logger.info("Parsing csv file %s", basename(csv_path))

        # Read the CSV file into memory
        csv_sheet = pd.read_csv(
            csv_path,
            # Have pandas auto-parse publication_date column as a datetime
            parse_dates=["publication_date"],
            # Remove automatic replacement of empty columns with NaN
            na_filter=False,
        )

        num_cols = len(csv_sheet.columns)
        num_rows = len(csv_sheet.index)

        logger.debug("csv_sheet.head(): %s", str(csv_sheet.head()))
        logger.debug("num_cols: %d", num_cols)
        logger.debug("num_rows: %d", num_rows)
        logger.debug("data columns: %s", str(list(csv_sheet.columns)))

        if num_cols < self.EXPECTED_NUM_COLUMNS:
            msg = (
                f"Expecting {self.EXPECTED_NUM_COLUMNS} columns in the provided "
                f"CSV file, but only found {num_cols} column(s)."
            )

            logger.error(msg)
            raise InputFormatException(msg)

        dois = self._parse_rows_to_dois(csv_sheet)

        return dois

    def parse_json_file(self, json_path):
        """
        Parses DOI's from a file with a .json extension. The file is expected
        to conform to the JSON schema associated to the service provider in use.

        Parameters
        ----------
        json_path : str
            Path to the JSON file to parse.

        Returns
        -------
        dois : List of Doi
            DOI objects parsed from the provided JSON file.

        """
        logger.info("Parsing json file %s", basename(json_path))

        dois = []
        web_parser = DOIServiceFactory.get_web_parser_service()
        validator = DOIServiceFactory.get_validator_service()

        # First read the contents of the file
        with open(json_path, "r") as infile:
            json_contents = infile.read()

        # Validate and parse the provide JSON label based on the service provider
        # configured within the INI. If there's a mismatch, the validation step
        # should catch it.
        try:
            if DOIServiceFactory.get_service_type() == SERVICE_TYPE_DATACITE:
                validator.validate(json_contents)

            dois, _ = web_parser.parse_dois_from_label(json_contents, content_type=CONTENT_TYPE_JSON)
        except InputFormatException as err:
            logger.warning(
                "Unable to parse DOI objects from provided " 'json file "%s"\nReason: %s', json_path, str(err)
            )

        return dois

    def _read_from_path(self, path):
        """
        Parses DOI's from the file or files referenced by the provided path.
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
            logger.info("Reading local file path %s", path)

            extension = os.path.splitext(path)[-1]

            if extension in self._valid_extensions:
                # Select the appropriate read function based on the extension
                read_function = self._parser_map[extension]

                try:
                    dois = read_function(path)
                except OSError as err:
                    msg = f"Error reading file {path}, reason: {str(err)}"

                    logger.error(msg)
                    raise InputFormatException(msg)
            else:
                logger.info("File %s has unsupported extension, ignoring", path)
        else:
            logger.info("Reading files within directory %s", path)

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
            raise InputFormatException(f"Could not read remote file {input_url}, reason: {str(http_err)}")

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
        if input_file.startswith("http"):
            dois = self._read_from_remote(input_file)
        # Otherwise see if its a local file
        elif os.path.exists(input_file):
            dois = self._read_from_path(input_file)
        else:
            raise InputFormatException(
                f"Error reading file {input_file}, path does not correspond to " f"a remote URL or a local file path."
            )

        # Make sure we got back at least one Doi
        if not dois:
            raise InputFormatException(
                f"Unable to parse DOI's from input location {input_file}\n"
                f"Please ensure the input is of the following type(s): "
                f"{', '.join(self._valid_extensions)}"
            )

        return dois
