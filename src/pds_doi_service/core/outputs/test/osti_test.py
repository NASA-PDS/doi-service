#!/usr/bin/env python
import json
import os
import unittest
from datetime import datetime
from os.path import abspath
from os.path import join

from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.osti.osti_record import DOIOstiRecord
from pds_doi_service.core.outputs.osti.osti_web_parser import DOIOstiJsonWebParser
from pds_doi_service.core.outputs.osti.osti_web_parser import DOIOstiXmlWebParser
from pkg_resources import resource_filename


class DOIOstiRecordTestCase(unittest.TestCase):
    """Unit tests for the osti_record.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        # FIXME: moving this code from PACKAGE-DIR to PACKAGE-DIR/src (and, when we add
        # namepsace packages, to PACKAGE-DIR/src/pds) shouldn't necessitate re-jiggering
        # all the parent directories:
        cls.input_dir = abspath(join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))

    def test_create_osti_label_xml(self):
        """Test creation of an OSTI XML label from a Doi object"""
        # Parse sample input to obtain a Doi object
        input_xml_file = join(self.input_dir, "DOI_Release_20200727_from_release.xml")

        with open(input_xml_file, "r") as infile:
            input_xml = infile.read()
            input_dois, _ = DOIOstiXmlWebParser.parse_dois_from_label(input_xml)

            # Now create an output label from the parsed Doi
            output_xml = DOIOstiRecord().create_doi_record(input_dois[0], content_type=CONTENT_TYPE_XML)
            output_dois, _ = DOIOstiXmlWebParser.parse_dois_from_label(output_xml)

        # Massage the output a bit so we can do a straight dict comparison
        input_doi_fields = input_dois[0].__dict__
        output_doi_fields = output_dois[0].__dict__

        # Added/updated dates are always overwritten when parsing Doi objects
        # from input labels, so remove these key/values from the comparison
        for date_key in ("date_record_added", "date_record_updated"):
            input_doi_fields.pop(date_key, None)
            output_doi_fields.pop(date_key, None)

        self.assertDictEqual(input_doi_fields, output_doi_fields)

    def test_create_osti_label_json(self):
        """Test creation of an OSTI JSON label from Doi objects"""
        # Parse sample input to obtain a Doi object
        input_json_file = join(self.input_dir, "DOI_Release_20210216_from_release.json")

        with open(input_json_file, "r") as infile:
            input_json = infile.read()
            dois, _ = DOIOstiJsonWebParser.parse_dois_from_label(input_json)

            # Now create an output label from the parsed Doi
            output_json = DOIOstiRecord().create_doi_record(dois[0], content_type=CONTENT_TYPE_JSON)

        # Massage the output a bit so we can do a straight dict comparison
        input_json = json.loads(input_json)[0]
        output_json = json.loads(output_json)[0]

        # Add/update dates are always overwritten when parsing Doi objects
        # from input labels, so remove these key/values from the comparison
        for date_key in ("date_record_added", "date_record_updated"):
            input_json.pop(date_key, None)
            output_json.pop(date_key, None)

        self.assertDictEqual(input_json, output_json)


class DOIOstiWebParserTestCase(unittest.TestCase):
    """Unit tests for the osti_web_parser.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        # FIXME: moving this code from PACKAGE-DIR to PACKAGE-DIR/src (and, when we add
        # namepsace packages, to PACKAGE-DIR/src/pds) shouldn't necessitate re-jiggering
        # all the parent directories:
        cls.input_dir = abspath(join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))

        cls.expected_authors = [
            {"first_name": "R.", "last_name": "Deen"},
            {"first_name": "H.", "last_name": "Abarca"},
            {"first_name": "P.", "last_name": "Zamani"},
            {"first_name": "J.", "last_name": "Maki"},
        ]
        cls.expected_editors = [
            {"first_name": "P. H.", "last_name": "Smith"},
            {"first_name": "M.", "last_name": "Lemmon"},
            {"first_name": "R. F.", "last_name": "Beebe"},
        ]
        cls.expected_keywords = {
            "data",
            "rdr",
            "product",
            "experiment",
            "lander",
            "context",
            "PDS",
            "raw",
            "mars",
            "record",
            "reduced",
            "science",
            "edr",
            "PDS4",
            "camera",
            "deployment",
            "insight",
            "engineering",
        }

    def _compare_doi_to_expected(self, doi):
        """
        Helper method to test that both mandatory and optional fields from
        a parsed Doi match the expected values and/or formats.
        """
        self.assertListEqual(doi.authors, self.expected_authors)
        self.assertEqual(doi.availability, "NASA Planetary Data System")
        self.assertEqual(doi.contributor, "Engineering")
        self.assertEqual(doi.country, "US")
        self.assertIsInstance(doi.date_record_added, datetime)
        self.assertEqual(
            doi.description,
            "InSight Cameras Experiment Data Record (EDR) " "and Reduced Data Record (RDR) Data Products",
        )
        self.assertEqual(doi.doi, "10.17189/29569")
        self.assertListEqual(doi.editors, self.expected_editors)
        self.assertEqual(doi.id, "29569")
        self.assertSetEqual(doi.keywords, self.expected_keywords)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertEqual(doi.product_type_specific, "PDS4 Refereed Data Bundle")
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertEqual(doi.publisher, "NASA Planetary Data System")
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:insight_cameras::1.0")
        # Check that site url HTML was un-escaped as expected
        self.assertIn("&", doi.site_url)
        self.assertNotIn("&amp;", doi.site_url)
        self.assertEqual(doi.sponsoring_organization, "National Aeronautics and Space Administration (NASA)")
        self.assertEqual(doi.status, DoiStatus.Pending)
        self.assertEqual(doi.title, "InSight Cameras Bundle")

    def test_parse_osti_response_xml(self):
        """Test parsing of an OSTI label in XML format"""
        # Test with a nominal file containing most of the optional fields
        input_xml_file = join(self.input_dir, "DOI_Release_20200727_from_release.xml")

        with open(input_xml_file, "r") as infile:
            input_xml = infile.read()
            dois, errors = DOIOstiXmlWebParser.parse_dois_from_label(input_xml)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self._compare_doi_to_expected(doi)

        # Test with an erroneous file to ensure errors are parsed as we expect
        input_xml_file = join(self.input_dir, "DOI_Release_20200727_from_error.xml")

        with open(input_xml_file, "r") as infile:
            input_xml = infile.read()
            dois, errors = DOIOstiXmlWebParser.parse_dois_from_label(input_xml)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 1)

    def test_parse_osti_response_json(self):
        """Test parsing of an OSTI label in JSON format"""
        # Test with a nominal file containing most of the optional fields
        input_json_file = join(self.input_dir, "DOI_Release_20210216_from_release.json")

        with open(input_json_file, "r") as infile:
            input_json = infile.read()
            dois, errors = DOIOstiJsonWebParser.parse_dois_from_label(input_json)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self._compare_doi_to_expected(doi)

        # Test with an erroneous file to ensure errors are parsed as we expect
        input_json_file = join(self.input_dir, "DOI_Release_20210216_from_error.json")

        with open(input_json_file, "r") as infile:
            input_json = infile.read()
            dois, errors = DOIOstiJsonWebParser.parse_dois_from_label(input_json)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main()
