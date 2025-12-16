#!/usr/bin/env python
import unittest
from datetime import datetime
from importlib import resources
from os.path import abspath
from os.path import join

from lxml import etree
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.input.pds4_util import DOIPDS4LabelUtil


class Pds4UtilTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = str(resources.files(__name__))
        self.input_dir = abspath(join(self.test_dir, "data"))

        self.expected_authors = [
            {"first_name": "R.", "last_name": "Deen", "affiliation": [], "name_type": "Personal"},
            {"first_name": "H.", "last_name": "Abarca", "affiliation": [], "name_type": "Personal"},
            {"first_name": "P.", "last_name": "Zamani", "affiliation": [], "name_type": "Personal"},
            {"first_name": "J.", "last_name": "Maki", "affiliation": [], "name_type": "Personal"},
        ]
        self.expected_editors = [
            {"first_name": "P.", "middle_name": "H.", "last_name": "Smith", "affiliation": [], "name_type": "Personal"},
            {"first_name": "M.", "last_name": "Lemmon", "affiliation": [], "name_type": "Personal"},
            {"first_name": "R.", "middle_name": "F.", "last_name": "Beebe", "affiliation": [], "name_type": "Personal"},
        ]
        self.expected_keywords = {
            "mars",
            "insight",
            "lander",
            "camera",
            "context",
            "raw",
            "science",
            "deployment",
        }

    def test_parse_dois_from_pds4_label(self):
        """Test the DOIPDS4LabelUtil.get_doi_fields_from_pds4() method"""
        pds4_label_util = DOIPDS4LabelUtil()

        # Test with a PDS4 label containing all the fields we support parsing
        # DOI metadata for
        i_filepath = join(self.input_dir, "pds4_bundle_with_doi_and_contributors.xml")

        # Check if the file is a reference to another file
        with open(i_filepath, "r") as infile:
            content = infile.read().strip()

        if content.startswith("../../../"):
            # It's a reference, read the actual file
            actual_filepath = join(self.input_dir, content)
            with open(actual_filepath, "r") as infile:
                xml_contents = infile.read()
        else:
            # It's the actual content
            xml_contents = content

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

    def test_multiple_list_author_elements(self):
        """Test parsing labels with multiple List_Author elements (issue #500)"""
        pds4_label_util = DOIPDS4LabelUtil()

        # Test with a PDS4 label containing multiple List_Author elements
        i_filepath = join(self.input_dir, "bundle_multiple_list_author.xml")

        with open(i_filepath, "r") as infile:
            xml_contents = infile.read()

        xml_tree = etree.fromstring(xml_contents.encode())

        self.assertTrue(pds4_label_util.is_pds4_label(xml_tree))

        # This should not raise an exception
        doi = pds4_label_util.get_doi_fields_from_pds4(xml_tree)

        # Verify both authors from multiple List_Author elements were parsed
        self.assertIsInstance(doi, Doi)
        self.assertEqual(len(doi.authors), 2)
        self.assertEqual(doi.authors[0]['first_name'], 'Scott')
        self.assertEqual(doi.authors[0]['last_name'], 'Murchie')
        self.assertEqual(doi.authors[1]['first_name'], 'Chris')
        self.assertEqual(doi.authors[1]['last_name'], 'Hash')


class GetNamesTestCase(unittest.TestCase):
    def test_names_parse_correctly(self):
        entity_names = [
            "A. Dunn",
            "Dunn, Alex",
            "Dunn, A.",
            "Dunn, A. E.",
            "Dunn, A. E. F. G.",
            "Dunn, Alexander E.",
            "Dunn, Alexander E. F. G.",
            "Jet Propulsion Laboratory",
            "JPL",
            "Google Inc.",
            "Suffixed Jr., James",
        ]
        parsed_entities = DOIPDS4LabelUtil().get_names(entity_names)
        # Modified code to not expect 'Affiliation' where "Organizational" test cases
        expected_parsed_entities = [
            {"first_name": "A.", "last_name": "Dunn", "affiliation": [], "name_type": "Personal"},
            {"first_name": "Alex", "last_name": "Dunn", "affiliation": [], "name_type": "Personal"},
            {"first_name": "A.", "last_name": "Dunn", "affiliation": [], "name_type": "Personal"},
            {"first_name": "A.", "middle_name": "E.", "last_name": "Dunn", "affiliation": [], "name_type": "Personal"},
            {
                "first_name": "A.",
                "middle_name": "E. F. G.",
                "last_name": "Dunn",
                "affiliation": [],
                "name_type": "Personal",
            },
            {
                "first_name": "Alexander",
                "middle_name": "E.",
                "last_name": "Dunn",
                "affiliation": [],
                "name_type": "Personal",
            },
            {
                "first_name": "Alexander",
                "middle_name": "E. F. G.",
                "last_name": "Dunn",
                "affiliation": [],
                "name_type": "Personal",
            },
            {"name": "Jet Propulsion Laboratory", "affiliation": [], "name_type": "Organizational"},
            {"name": "JPL", "affiliation": [], "name_type": "Organizational"},
            {"name": "Google Inc.", "affiliation": [], "name_type": "Organizational"},
            {"first_name": "James", "last_name": "Suffixed Jr.", "affiliation": [], "name_type": "Personal"},
        ]
        self.assertListEqual(expected_parsed_entities, parsed_entities)


if __name__ == "__main__":
    unittest.main()
