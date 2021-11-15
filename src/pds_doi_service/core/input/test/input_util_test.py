#!/usr/bin/env python
import datetime
import unittest
from os.path import abspath
from os.path import join

import pandas as pd
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.entities.exceptions import InputFormatException
from pds_doi_service.core.input.input_util import DOIInputUtil
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.service import SERVICE_TYPE_OSTI
from pkg_resources import resource_filename


class InputUtilTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = resource_filename(__name__, "")
        self.input_dir = abspath(join(self.test_dir, "data"))

    def test_parse_dois_from_input_file(self):
        """Test the DOIInputUtil.parse_dois_from_input_file() method"""
        doi_input_util = DOIInputUtil(valid_extensions=".xml")

        # Test with local file
        i_filepath = join(self.input_dir, "pds4_bundle_with_contributors.xml")
        dois = doi_input_util.parse_dois_from_input_file(i_filepath)

        self.assertEqual(len(dois), 1)

        # Test with remote file
        i_filepath = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml"
        dois = doi_input_util.parse_dois_from_input_file(i_filepath)

        self.assertEqual(len(dois), 1)

        # Test with local directory
        i_filepath = join(self.input_dir, "input_dir_two_files")
        dois = doi_input_util.parse_dois_from_input_file(i_filepath)

        self.assertEqual(len(dois), 2)

        # Test with invalid local file path (does not exist)
        i_filepath = "/dev/null/file/does/not/exist"
        with self.assertRaises(InputFormatException):
            doi_input_util.parse_dois_from_input_file(i_filepath)

        # Test with invalid remote file path (does not exist)
        i_filepath = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/fake_bundle.xml"
        with self.assertRaises(InputFormatException):
            doi_input_util.parse_dois_from_input_file(i_filepath)

        # Test local file with invalid extension
        i_filepath = join(self.input_dir, "spreadsheet_with_lid_only.xlsx")
        with self.assertRaises(InputFormatException):
            doi_input_util.parse_dois_from_input_file(i_filepath)

        # Test remote file with invalid extension
        doi_input_util = DOIInputUtil(valid_extensions=".csv")
        i_filepath = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml"
        with self.assertRaises(InputFormatException):
            doi_input_util.parse_dois_from_input_file(i_filepath)

    def test_read_xls(self):
        """Test the DOIInputUtil.parse_xls_file() method"""
        doi_input_util = DOIInputUtil()

        # Test single entry spreadsheet
        i_filepath = join(self.input_dir, "spreadsheet_with_lid_only.xlsx")
        dois = doi_input_util.parse_xls_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)
        self.assertEqual(doi.title, "Laboratory Shocked Feldspars Bundle")
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:lab_shocked_feldspars")
        self.assertEqual(len(doi.authors), 1)
        self.assertEqual(doi.product_type, ProductType.Collection)
        self.assertEqual(doi.product_type_specific, "PDS4 Collection")
        self.assertIsInstance(doi.publication_date, datetime.datetime)

        # Test multi entry spreadsheet
        i_filepath = join(self.input_dir, "spreadsheet_with_pds4_identifiers.xlsx")

        dois = doi_input_util.parse_xls_file(i_filepath)

        self.assertEqual(len(dois), 3)
        self.assertTrue(all([doi.title.startswith("Laboratory Shocked Feldspars") for doi in dois]))
        self.assertTrue(all([doi.pds_identifier.startswith("urn:nasa:pds:lab_shocked_feldspars") for doi in dois]))
        self.assertTrue(all([len(doi.authors) == 1 for doi in dois]))
        self.assertTrue(
            all([doi.product_type == doi_input_util._parse_product_type(doi.product_type_specific) for doi in dois])
        )
        self.assertTrue(all([isinstance(doi.publication_date, datetime.datetime) for doi in dois]))

        # Test with an invalid spreadsheet (insufficient columns)
        i_filepath = join(self.input_dir, "spreadsheet_with_missing_columns.xlsx")

        try:
            doi_input_util.parse_xls_file(i_filepath)
            self.fail()  # should never get here
        except Exception as err:
            self.assertIsInstance(err, InputFormatException)
            self.assertIn("only found 5 column(s)", str(err))

        # Test with an invalid spreadsheet (wrong column names)
        i_filepath = join(self.input_dir, "spreadsheet_with_invalid_column_names.xlsx")

        try:
            doi_input_util.parse_xls_file(i_filepath)
            self.fail()  # should never get here
        except Exception as err:
            self.assertIsInstance(err, InputFormatException)
            self.assertIn("Please assign the correct column names", str(err))

        # Test with a valid spreadsheet with malformed column names (that parser should correct)
        i_filepath = join(self.input_dir, "spreadsheet_with_malformed_column_names.xlsx")

        dois = doi_input_util.parse_xls_file(i_filepath)

        self.assertEqual(len(dois), 1)

        # Test with an invalid spreadsheet (multiple rows with errors)
        i_filepath = join(self.input_dir, "spreadsheet_with_invalid_rows.xlsx")

        try:
            doi_input_util.parse_xls_file(i_filepath)
            self.fail()  # should never get here
        except Exception as err:
            self.assertIsInstance(err, InputFormatException)
            self.assertIn("Failed to parse row 1", str(err))
            self.assertIn("Reason: No value provided for related_resource column", str(err))
            self.assertIn("Failed to parse row 2", str(err))
            self.assertIn("Reason: No value provided for title column", str(err))
            self.assertIn("Failed to parse row 3", str(err))
            self.assertIn("Incorrect publication_date format", str(err))

        # Test with a spreadsheet containing optional columns
        i_filepath = join(self.input_dir, "spreadsheet_with_optional_columns.xlsx")

        dois = doi_input_util.parse_xls_file(i_filepath)

        doi = dois[0]
        doi_fields = doi.__dict__

        for optional_column in doi_input_util.OPTIONAL_COLUMNS:
            self.assertIn(optional_column, doi_fields)
            self.assertIsNotNone(doi_fields[optional_column])

        # Test with a spreadsheet containing blank rows (parser should sanitize these)
        i_filepath = join(self.input_dir, "spreadsheet_with_blank_rows.xlsx")

        # Read the spreadsheet to get a total of rows w/ blanks
        xl_wb = pd.ExcelFile(i_filepath, engine="openpyxl")
        xl_sheet = pd.read_excel(i_filepath, xl_wb.sheet_names[0], na_filter=False)
        rows_with_blanks, _ = xl_sheet.shape

        # Now parse DOI's and confirm we get results back and that its less than
        # the number of rows originaly parsed
        dois = doi_input_util.parse_xls_file(i_filepath)

        self.assertTrue(len(dois) > 0)
        self.assertTrue(len(dois) < rows_with_blanks)

    def test_read_csv(self):
        """Test the DOIInputUtil.parse_csv_file() method"""
        doi_input_util = DOIInputUtil()

        i_filepath = join(self.input_dir, "spreadsheet_with_pds4_identifiers.csv")
        dois = doi_input_util.parse_csv_file(i_filepath)

        self.assertEqual(len(dois), 3)
        self.assertTrue(all([doi.title.startswith("Laboratory Shocked Feldspars") for doi in dois]))
        self.assertTrue(all([doi.pds_identifier.startswith("urn:nasa:pds:lab_shocked_feldspars") for doi in dois]))
        self.assertTrue(all([len(doi.authors) == 1 for doi in dois]))
        self.assertTrue(all([doi.product_type == ProductType.Collection for doi in dois]))
        self.assertTrue(all([isinstance(doi.publication_date, datetime.datetime) for doi in dois]))

        # Test on a CSV containing a PD3 style identifier
        i_filepath = join(self.input_dir, "spreadsheet_with_pds3_identifiers.csv")
        dois = doi_input_util.parse_csv_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        # Make sure the PDS3 identifier was saved off as expected
        self.assertEqual(doi.pds_identifier, "LRO-L-MRFLRO-2/3/5-BISTATIC-V3.0")

        # Test with an invalid spreadsheet (insufficient columns)
        i_filepath = join(self.input_dir, "spreadsheet_with_missing_columns.csv")

        try:
            doi_input_util.parse_csv_file(i_filepath)
            self.fail()  # should never get here
        except Exception as err:
            self.assertIsInstance(err, InputFormatException)
            self.assertIn("only found 5 column(s)", str(err))

        # Test with an invalid spreadsheet (wrong column names)
        i_filepath = join(self.input_dir, "spreadsheet_with_invalid_column_names.csv")

        try:
            doi_input_util.parse_csv_file(i_filepath)
            self.fail()  # should never get here
        except Exception as err:
            self.assertIsInstance(err, InputFormatException)
            self.assertIn("Please assign the correct column names", str(err))

        # Test with a valid spreadsheet with malformed column names (that parser should correct)
        i_filepath = join(self.input_dir, "spreadsheet_with_malformed_column_names.csv")

        dois = doi_input_util.parse_csv_file(i_filepath)

        self.assertEqual(len(dois), 1)

        # Test with an invalid spreadsheet (multiple rows with errors)
        i_filepath = join(self.input_dir, "spreadsheet_with_invalid_rows.csv")

        try:
            doi_input_util.parse_csv_file(i_filepath)
            self.fail()  # should never get here
        except Exception as err:
            self.assertIsInstance(err, InputFormatException)
            self.assertIn("Failed to parse row 1", str(err))
            self.assertIn("Reason: No value provided for related_resource column", str(err))
            self.assertIn("Failed to parse row 2", str(err))
            self.assertIn("Reason: No value provided for title column", str(err))
            self.assertIn("Failed to parse row 3", str(err))
            self.assertIn("Incorrect publication_date format", str(err))

        # Test with a spreadsheet containing optional columns
        i_filepath = join(self.input_dir, "spreadsheet_with_optional_columns.csv")

        dois = doi_input_util.parse_csv_file(i_filepath)

        doi = dois[0]
        doi_fields = doi.__dict__

        for optional_column in doi_input_util.OPTIONAL_COLUMNS:
            self.assertIn(optional_column, doi_fields)
            self.assertIsNotNone(doi_fields[optional_column])

        # Test with a spreadsheet containing blank rows (parser should sanitize these)
        i_filepath = join(self.input_dir, "spreadsheet_with_blank_rows.csv")

        # Read the spreadsheet to get a total of rows w/ blanks
        csv_sheet = pd.read_csv(i_filepath, na_filter=False)
        rows_with_blanks, _ = csv_sheet.shape

        # Now parse DOI's and confirm we get results back and that its less than
        # the number of rows originaly parsed
        dois = doi_input_util.parse_csv_file(i_filepath)

        self.assertTrue(len(dois) > 0)
        self.assertTrue(len(dois) < rows_with_blanks)

    def test_read_xml(self):
        """Test the DOIInputUtil.parse_xml_file() method"""
        doi_input_util = DOIInputUtil()

        # Test with a PDS4 label
        i_filepath = join(self.input_dir, "pds4_bundle_with_contributors.xml")
        dois = doi_input_util.parse_xml_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)

        # Test with an OSTI output label
        i_filepath = join(self.input_dir, "osti_record_reserved.xml")
        dois = doi_input_util.parse_xml_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)

        # Test with an OSTI label containing a PDS3 identifier
        i_filepath = join(self.input_dir, "osti_record_registered_with_pds3_identifier.xml")
        dois = doi_input_util.parse_xml_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)

        # Make sure the PDS3 identifier was saved off as expected
        self.assertEqual(doi.pds_identifier, "LRO-L-MRFLRO-2/3/5-BISTATIC-V3.0")

        # Test with a PDS4 label that contains a UTF-8 byte order marker
        i_filepath = join(self.input_dir, "pds4_bundle_with_utf-8-bom.xml")

        # Run a quick sanity check to ensure the input file starts with the BOM
        with open(i_filepath, "r") as infile:
            file_contents = infile.read()
            file_contents_bytes = file_contents.encode()
            self.assertTrue(file_contents_bytes.startswith(b"\xef\xbb\xbf"))

        # Parse the label and ensure we still get a Doi back
        dois = doi_input_util.parse_xml_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)

    def test_read_json(self):
        """Test the DOIInputUtil.parse_json_file() method"""
        doi_input_util = DOIInputUtil()

        # Test with the appropriate JSON label for the current service
        if DOIServiceFactory.get_service_type() == SERVICE_TYPE_OSTI:
            i_filepath = join(self.input_dir, "osti_record_reserved.json")
        else:
            i_filepath = join(self.input_dir, "datacite_record_draft.json")

        dois = doi_input_util.parse_json_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)

        # Test with a JSON label that contains a UTF-8 byte order marker
        if DOIServiceFactory.get_service_type() == SERVICE_TYPE_OSTI:
            i_filepath = join(self.input_dir, "osti_record_reserved_with_utf-8-bom.json")
        else:
            i_filepath = join(self.input_dir, "datacite_record_draft_with_utf-8-bom.json")

        # Run a quick sanity check to ensure the input file starts with the BOM
        with open(i_filepath, "r") as infile:
            file_contents = infile.read()
            file_contents_bytes = file_contents.encode()
            self.assertTrue(file_contents_bytes.startswith(b"\xef\xbb\xbf"))

        # Parse the label and ensure we still get a Doi back
        dois = doi_input_util.parse_json_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)


if __name__ == "__main__":
    unittest.main()
