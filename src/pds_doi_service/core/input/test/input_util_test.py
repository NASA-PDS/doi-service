#!/usr/bin/env python
import datetime
import os
import unittest
from os.path import abspath
from os.path import join

from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.input_util import DOIInputUtil
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.service import SERVICE_TYPE_OSTI
from pkg_resources import resource_filename


class InputUtilTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = resource_filename(__name__, "")
        self.input_dir = abspath(join(self.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))

    def test_parse_dois_from_input_file(self):
        """Test the DOIInputUtil.parse_dois_from_input_file() method"""
        doi_input_util = DOIInputUtil(valid_extensions=".xml")

        # Test with local file
        i_filepath = join(self.input_dir, "bundle_in_with_contributors.xml")
        dois = doi_input_util.parse_dois_from_input_file(i_filepath)

        self.assertEqual(len(dois), 1)

        # Test with remote file
        i_filepath = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml"
        dois = doi_input_util.parse_dois_from_input_file(i_filepath)

        self.assertEqual(len(dois), 1)

        # Test with local directory
        i_filepath = join(self.input_dir, "draft_dir_two_files")
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
        i_filepath = join(self.input_dir, "DOI_Reserved_GEO_200318.xlsx")
        with self.assertRaises(InputFormatException):
            doi_input_util.parse_dois_from_input_file(i_filepath)

        # Test remote file with invalid extension
        doi_input_util = DOIInputUtil(valid_extensions=".csv")
        i_filepath = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml"
        with self.assertRaises(InputFormatException):
            doi_input_util.parse_dois_from_input_file(i_filepath)

    def test_read_xls(self):
        """Test the DOIInputUtil.parse_sxls_file() method"""
        doi_input_util = DOIInputUtil()

        # Test single entry spreadsheet
        i_filepath = join(self.input_dir, "DOI_Reserved_GEO_200318.xlsx")
        dois = doi_input_util.parse_xls_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)
        self.assertEqual(doi.title, "Laboratory Shocked Feldspars Bundle")
        self.assertEqual(doi.status, DoiStatus.Reserved)
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:lab_shocked_feldspars")
        self.assertEqual(len(doi.authors), 1)
        self.assertEqual(doi.product_type, ProductType.Collection)
        self.assertEqual(doi.product_type_specific, "PDS4 Collection")
        self.assertIsInstance(doi.publication_date, datetime.datetime)

        # Test multi entry spreadsheet
        i_filepath = join(self.input_dir, "DOI_Reserved_GEO_200318_with_corrected_identifier.xlsx")

        dois = doi_input_util.parse_xls_file(i_filepath)

        self.assertEqual(len(dois), 3)
        self.assertTrue(all([doi.title.startswith("Laboratory Shocked Feldspars") for doi in dois]))
        self.assertTrue(all([doi.status == DoiStatus.Reserved for doi in dois]))
        self.assertTrue(all([doi.related_identifier.startswith("urn:nasa:pds:lab_shocked_feldspars") for doi in dois]))
        self.assertTrue(all([len(doi.authors) == 1 for doi in dois]))
        self.assertTrue(
            all([doi.product_type == doi_input_util._parse_product_type(doi.product_type_specific) for doi in dois])
        )
        self.assertTrue(all([isinstance(doi.publication_date, datetime.datetime) for doi in dois]))

    def test_read_csv(self):
        """Test the DOIInputUtil.parse_csv_file() method"""
        doi_input_util = DOIInputUtil()

        i_filepath = join(self.input_dir, "DOI_Reserved_GEO_200318.csv")
        dois = doi_input_util.parse_csv_file(i_filepath)

        self.assertEqual(len(dois), 3)
        self.assertTrue(all([doi.title.startswith("Laboratory Shocked Feldspars") for doi in dois]))
        self.assertTrue(all([doi.status == DoiStatus.Reserved for doi in dois]))
        self.assertTrue(all([doi.related_identifier.startswith("urn:nasa:pds:lab_shocked_feldspars") for doi in dois]))
        self.assertTrue(all([len(doi.authors) == 1 for doi in dois]))
        self.assertTrue(all([doi.product_type == ProductType.Collection for doi in dois]))
        self.assertTrue(all([isinstance(doi.publication_date, datetime.datetime) for doi in dois]))

        # Test on a CSV containing a PD3 style identifier
        i_filepath = join(self.input_dir, "DOI_Reserved_PDS3.csv")
        dois = doi_input_util.parse_csv_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        # Make sure the PDS3 identifier was saved off as expected
        self.assertEqual(doi.related_identifier, "LRO-L-MRFLRO-2/3/5-BISTATIC-V3.0")

    def test_read_xml(self):
        """Test the DOIInputUtil.parse_xml_file() method"""
        doi_input_util = DOIInputUtil()

        # Test with a PDS4 label
        i_filepath = join(self.input_dir, "bundle_in_with_contributors.xml")
        dois = doi_input_util.parse_xml_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)

        # Test with an OSTI output label
        i_filepath = join(self.input_dir, "DOI_Release_20200727_from_reserve.xml")
        dois = doi_input_util.parse_xml_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)

        # Test with an OSTI label containing a PDS3 identifier
        i_filepath = join(self.input_dir, "DOI_Release_PDS3.xml")
        dois = doi_input_util.parse_xml_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)

        # Make sure the PDS3 identifier was saved off as expected
        self.assertEqual(doi.related_identifier, "LRO-L-MRFLRO-2/3/5-BISTATIC-V3.0")

    def test_read_json(self):
        """Test the DOIInputUtil.parse_json_file() method"""
        doi_input_util = DOIInputUtil()

        # Test with the appropriate JSON label for the current service
        if DOIServiceFactory.get_service_type() == SERVICE_TYPE_OSTI:
            i_filepath = join(self.input_dir, "DOI_Release_20210216_from_reserve.json")
        else:
            i_filepath = join(self.input_dir, "DOI_Release_20210615_from_reserve.json")

        dois = doi_input_util.parse_json_file(i_filepath)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertIsInstance(doi, Doi)


if __name__ == "__main__":
    unittest.main()
