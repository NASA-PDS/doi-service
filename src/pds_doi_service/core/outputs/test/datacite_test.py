#!/usr/bin/env python
import json
import os
import unittest
from datetime import datetime
from os.path import abspath
from os.path import join
from unittest.mock import patch

import requests
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.outputs.datacite import DOIDataCiteRecord
from pds_doi_service.core.outputs.datacite import DOIDataCiteValidator
from pds_doi_service.core.outputs.datacite import DOIDataCiteWebClient
from pds_doi_service.core.outputs.datacite import DOIDataCiteWebParser
from pkg_resources import resource_filename
from requests.models import Response


class DOIDataCiteRecordTestCase(unittest.TestCase):
    """Unit tests for the datacite_record.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))

    def test_create_datacite_label_json(self):
        """Test creation of a DataCite JSON label from a Doi object"""
        # Parse sample input to obtain a Doi object
        input_json_file = join(self.input_dir, "DOI_Release_20210615_from_reserve.json")

        with open(input_json_file, "r") as infile:
            input_json = infile.read()
            input_dois, _ = DOIDataCiteWebParser.parse_dois_from_label(input_json)

            # Now create an output label from the parsed Doi
            output_json = DOIDataCiteRecord().create_doi_record(input_dois[0])
            output_dois, _ = DOIDataCiteWebParser.parse_dois_from_label(output_json)

        # Massage the output a bit so we can do a direct comparison
        input_doi_fields = input_dois[0].__dict__
        output_doi_fields = output_dois[0].__dict__

        self.assertDictEqual(input_doi_fields, output_doi_fields)


def requests_valid_request_patch(method, url, **kwargs):
    response = Response()
    response.status_code = 200

    with open(join(DOIDataCiteWebClientTestCase.input_dir, "DOI_Release_20210615_from_release.json")) as infile:
        response._content = infile.read().encode()

    return response


class DOIDataCiteWebClientTestCase(unittest.TestCase):
    """Unit tests for the datacite_web_client.py module"""

    input_dir = None

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))

    @patch.object(requests, "request", requests_valid_request_patch)
    def test_submit_content(self):
        """Test the datacite_web_client.submit_content method"""
        test_doi = Doi(
            title="InSight Cameras Bundle",
            publication_date=datetime(2019, 1, 1, 0, 0),
            product_type=ProductType.Dataset,
            product_type_specific="PDS4 Refereed Data Bundle",
            related_identifier="urn:nasa:pds:insight_cameras::1.0",
            id="yzw2-vz66",
            doi="10.13143/yzw2-vz66",
            publisher="NASA Planetary Data System",
            contributor="Engineering",
            status=DoiStatus.Reserved,
        )

        test_payload = DOIDataCiteRecord().create_doi_record(test_doi)

        response_doi, response_text = DOIDataCiteWebClient().submit_content(test_payload)

        # Ensure the response DOI and text line up
        response_text_doi, _ = DOIDataCiteWebParser.parse_dois_from_label(response_text)
        self.assertEqual(response_doi, response_text_doi[0])

        # Ensure the DOI returned corresponds to the one we provided
        self.assertEqual(test_doi.title, response_doi.title)
        self.assertEqual(test_doi.related_identifier, response_doi.related_identifier)
        self.assertEqual(test_doi.doi, response_doi.doi)

        # Check that the status has been updated by the submission request
        self.assertEqual(response_doi.status, DoiStatus.Findable)

    @patch.object(requests, "request", requests_valid_request_patch)
    def test_query_doi(self):
        """Test the datacite_web_client.query_doi method"""
        # Test with a single query term and a query dictionary
        queries = ("PDS", {"id": "10.13143/yzw2-vz66"})

        for query in queries:
            response_text = DOIDataCiteWebClient().query_doi(query)

            response_dois, _ = DOIDataCiteWebParser.parse_dois_from_label(response_text)
            response_doi = response_dois[0]

            # Should get the same record back for both queries
            self.assertEqual(response_doi.doi, "10.13143/yzw2-vz66")


class DOIDataCiteWebParserTestCase(unittest.TestCase):
    """Unit tests for the datacite_web_parser.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))

        cls.expected_authors = [
            {"name": "R. Deen", "name_identifiers": [], "name_type": "Personal"},
            {"name": "H. Abarca", "name_identifiers": [], "name_type": "Personal"},
            {"name": "P. Zamani", "name_identifiers": [], "name_type": "Personal"},
            {"name": "J. Maki", "name_identifiers": [], "name_type": "Personal"},
        ]
        cls.expected_editors = [
            {"name": "P. H. Smith", "name_identifiers": []},
            {"name": "M. Lemmon", "name_identifiers": []},
            {"name": "R. F. Beebe", "name_identifiers": []},
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
        self.assertEqual(doi.contributor, "Engineering")
        self.assertIsInstance(doi.date_record_added, datetime)
        self.assertIsInstance(doi.date_record_updated, datetime)
        self.assertEqual(
            doi.description,
            "InSight Cameras Experiment Data Record (EDR) " "and Reduced Data Record (RDR) Data Products",
        )
        self.assertEqual(doi.doi, "10.13143/yzw2-vz66")
        self.assertListEqual(doi.editors, self.expected_editors)
        self.assertEqual(doi.id, "yzw2-vz66")
        self.assertSetEqual(doi.keywords, self.expected_keywords)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertEqual(doi.product_type_specific, "PDS4 Refereed Data Bundle")
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertEqual(doi.publisher, "NASA Planetary Data System")
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:insight_cameras::1.0")
        # Check that site url HTML was un-escaped as expected
        self.assertIn("&", doi.site_url)
        self.assertNotIn("&amp;", doi.site_url)
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.title, "InSight Cameras Bundle")

    def test_parse_osti_response_json(self):
        """Test parsing of an OSTI label in JSON format"""
        # Test with a nominal file containing most of the optional fields
        input_json_file = join(self.input_dir, "DOI_Release_20210615_from_reserve.json")

        with open(input_json_file, "r") as infile:
            input_json = infile.read()
            dois, errors = DOIDataCiteWebParser.parse_dois_from_label(input_json)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self._compare_doi_to_expected(doi)


class DOIDataCiteValidatorTestCast(unittest.TestCase):
    """Unit tests for the datacite_validator.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))

    def test_json_label_validation(self):
        """Test validation against a DataCite label created from a valid Doi object"""
        validator = DOIDataCiteValidator()

        # Parse sample input to obtain a Doi object
        input_json_file = join(self.input_dir, "DOI_Release_20210615_from_reserve.json")

        # Next, create a valid output DataCite label from the parsed Doi
        with open(input_json_file, "r") as infile:
            input_json = infile.read()
            input_dois, _ = DOIDataCiteWebParser.parse_dois_from_label(input_json)

            output_json = DOIDataCiteRecord().create_doi_record(input_dois[0])

        # Label created from template should pass schema validation
        validator.validate(output_json)

        # Now remove some required fields to ensure its caught by validation
        output_json = json.loads(output_json)
        output_json["data"]["attributes"].pop("publicationYear")
        output_json["data"]["attributes"].pop("schemaVersion")
        output_json = json.dumps(output_json)

        try:
            validator.validate(output_json)

            # Should never make it here
            self.fail("Invalid JSON was accepted by DOIDataCiteValidator")
        except InputFormatException as err:
            # Make sure the error details the reasons we expect
            self.assertIn("'publicationYear' is a required property", str(err))
            self.assertIn("'schemaVersion' is a required property", str(err))


if __name__ == "__main__":
    unittest.main()
