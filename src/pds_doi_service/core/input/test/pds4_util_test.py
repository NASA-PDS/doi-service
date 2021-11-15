#!/usr/bin/env python
import unittest
from datetime import datetime
from os.path import abspath
from os.path import join

from lxml import etree
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.input.pds4_util import DOIPDS4LabelUtil
from pkg_resources import resource_filename


class Pds4UtilTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = resource_filename(__name__, "")
        self.input_dir = abspath(join(self.test_dir, "data"))

        self.expected_authors = [
            {"first_name": "R.", "last_name": "Deen", "affiliation": [], "name_type": "Personal"},
            {"first_name": "H.", "last_name": "Abarca", "affiliation": [], "name_type": "Personal"},
            {"first_name": "P.", "last_name": "Zamani", "affiliation": [], "name_type": "Personal"},
            {"first_name": "J.", "last_name": "Maki", "affiliation": [], "name_type": "Personal"},
        ]
        self.expected_editors = [
            {"first_name": "P. H.", "last_name": "Smith", "affiliation": [], "name_type": "Personal"},
            {"first_name": "M.", "last_name": "Lemmon", "affiliation": [], "name_type": "Personal"},
            {"first_name": "R. F.", "last_name": "Beebe", "affiliation": [], "name_type": "Personal"},
        ]
        self.expected_keywords = {
            "mars",
            "insight",
            "lander",
            "camera",
            "product",
            "context",
            "reduced",
            "experiment",
            "edr",
            "data",
            "raw",
            "science",
            "rdr",
            "deployment",
            "record",
        }

    def test_parse_dois_from_pds4_label(self):
        """Test the DOIPDS4LabelUtil.get_doi_fields_from_pds4() method"""
        pds4_label_util = DOIPDS4LabelUtil()

        # Test with a PDS4 label containing all the fields we support parsing
        # DOI metadata for
        i_filepath = join(self.input_dir, "pds4_bundle_with_doi_and_contributors.xml")

        with open(i_filepath, "r") as infile:
            xml_contents = infile.read().encode().decode("utf-8-sig")
            xml_tree = etree.fromstring(xml_contents.encode())

        self.assertTrue(pds4_label_util.is_pds4_label(xml_tree))

        doi = pds4_label_util.get_doi_fields_from_pds4(xml_tree)

        # Ensure all the DOI metadata fields were parsed as we expect
        self.assertIsInstance(doi, Doi)
        self.assertIsInstance(doi.status, DoiStatus)
        self.assertEqual(doi.status, DoiStatus.Unknown)
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras::1.0")
        self.assertEqual(doi.doi, "10.17189/29569")
        self.assertEqual(doi.title, "InSight Cameras Bundle")
        self.assertEqual(
            doi.site_url,
            "https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn%3Anasa%3Apds%3Ainsight_cameras&amp;version=1.0",
        )
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertEqual(doi.publication_date, datetime.strptime("2020-01-01", "%Y-%m-%d"))
        self.assertIsInstance(doi.product_type, ProductType)
        self.assertEqual(doi.product_type, ProductType.Bundle)
        self.assertEqual(doi.product_type_specific, "PDS4 Refereed Data Bundle")
        self.assertListEqual(doi.authors, self.expected_authors)
        self.assertListEqual(doi.editors, self.expected_editors)
        self.assertSetEqual(doi.keywords, self.expected_keywords)


if __name__ == "__main__":
    unittest.main()
