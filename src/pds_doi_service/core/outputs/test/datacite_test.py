#!/usr/bin/env python
import json
import unittest
from datetime import datetime
from os.path import abspath
from os.path import join
from unittest.mock import patch

import requests
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.entities.exceptions import InputFormatException
from pds_doi_service.core.entities.exceptions import UnknownDoiException
from pds_doi_service.core.entities.exceptions import UnknownIdentifierException
from pds_doi_service.core.outputs.datacite import DOIDataCiteRecord
from pds_doi_service.core.outputs.datacite import DOIDataCiteValidator
from pds_doi_service.core.outputs.datacite import DOIDataCiteWebClient
from pds_doi_service.core.outputs.datacite import DOIDataCiteWebParser
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST
from pds_doi_service.core.outputs.web_client import WEB_METHOD_PUT
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pkg_resources import resource_filename
from requests.models import Response


class DOIDataCiteRecordTestCase(unittest.TestCase):
    """Unit tests for the datacite_record.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, "data"))

    def test_create_datacite_label_json(self):
        """Test creation of a DataCite JSON label from a Doi object"""
        # Parse sample input to obtain a Doi object
        input_json_file = join(self.input_dir, "datacite_record_draft.json")

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

        # Remove the identifier field from the Doi object to make sure they're
        # re-added by the label creator
        input_doi = input_dois[0]
        input_doi.identifiers.clear()

        output_json = DOIDataCiteRecord().create_doi_record(input_doi)
        output_dois, _ = DOIDataCiteWebParser.parse_dois_from_label(output_json)

        output_doi = output_dois[0]

        # Should have an identifier entry for the PDS ID
        identifiers = list(map(lambda identifier: identifier["identifier"], output_doi.identifiers))
        self.assertEqual(len(identifiers), 1)
        self.assertIn(input_doi.pds_identifier, identifiers)

    def test_update_datacite_label_json(self):
        """Test creation of a DataCite label for a DOI record where the identifier has been updated"""
        input_json_file = join(self.input_dir, "datacite_record_draft.json")

        with open(input_json_file, "r") as infile:
            input_json = infile.read()
            input_dois, _ = DOIDataCiteWebParser.parse_dois_from_label(input_json)
            input_doi = input_dois[0]

        # Assign a new PDS identifier to the parsed DOI as this is a common use case
        # for update requests
        input_doi.pds_identifier = "urn:nasa:pds:insight_cameras::2.0"

        # Now create an output label from the parsed Doi
        output_json = DOIDataCiteRecord().create_doi_record(input_doi)
        output_dois, _ = DOIDataCiteWebParser.parse_dois_from_label(output_json)
        output_doi = output_dois[0]

        # Check that both the new and old identifiers are in the "identifiers" section
        urn_identifiers = list(
            filter(lambda identifier: identifier["identifierType"] == "Site ID", output_doi.identifiers)
        )

        self.assertEqual(len(urn_identifiers), 2)
        identifier_values = [identifier["identifier"] for identifier in urn_identifiers]
        self.assertIn("urn:nasa:pds:insight_cameras::1.0", identifier_values)
        self.assertIn("urn:nasa:pds:insight_cameras::2.0", identifier_values)


def requests_valid_request_patch(method, url, **kwargs):
    response = Response()
    response.status_code = 200

    with open(join(DOIDataCiteWebClientTestCase.input_dir, "datacite_record_findable.json")) as infile:
        response._content = infile.read().encode()

    return response


def requests_valid_request_paginated_patch(method, url, **kwargs):
    response = Response()
    response.status_code = 200

    if url == "url_for_page_1":
        next_link = "url_for_page_2"
        data = ["data_entry_2"]
    elif url == "url_for_page_2":
        next_link = "N/A"
        data = ["data_entry_3", "data_entry_4"]
    else:
        next_link = "url_for_page_1"
        data = ["data_entry_0", "data_entry_1"]

    response_content = {"data": data, "links": {"next": next_link}, "meta": {"totalPages": 3}}

    response._content = json.dumps(response_content).encode()

    return response


class DOIDataCiteWebClientTestCase(unittest.TestCase):
    """Unit tests for the datacite_web_client.py module"""

    input_dir = None

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, "data"))

    @patch.object(requests, "request", requests_valid_request_patch)
    def test_submit_content(self):
        """Test the datacite_web_client.submit_content method"""
        test_doi = Doi(
            title="InSight Cameras Bundle",
            publication_date=datetime(2019, 1, 1, 0, 0),
            product_type=ProductType.Dataset,
            product_type_specific="PDS4 Refereed Data Bundle",
            pds_identifier="urn:nasa:pds:insight_cameras::1.0",
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
        self.assertEqual(test_doi.pds_identifier, response_doi.pds_identifier)
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

    @patch.object(requests, "request", requests_valid_request_paginated_patch)
    def test_query_doi_with_pagination(self):
        """Test the datacite_web_client.query_doi method's ability to handle a paginated request"""
        response_text = DOIDataCiteWebClient().query_doi({"id": "10.13143/yzw2-vz66"})

        response_json = json.loads(response_text)

        expected_data = ["data_entry_0", "data_entry_1", "data_entry_2", "data_entry_3", "data_entry_4"]

        self.assertIn("data", response_json)
        self.assertIsInstance(response_json["data"], list)
        self.assertEqual(len(response_json["data"]), 5)
        self.assertListEqual(response_json["data"], expected_data)

    def test_endpoint_for_doi(self):
        """Test the datacite_web_client.endpoint_for_doi method"""
        config = DOIConfigUtil.get_config()

        expected_url = config.get("DATACITE", "url")
        expected_prefix = config.get("DATACITE", "doi_prefix")
        expected_suffix = "123abc"

        # Correct endpoint method and url are dependent on both the action
        # being performed, and whether an outgoing request has a DOI associated
        # or not, so test with all cases
        test_doi = Doi(
            title="doi_title",
            publication_date=datetime.now(),
            product_type=ProductType.Collection,
            product_type_specific="Test collection",
            pds_identifier="urn:nasa:pds:test-collection::1.0",
        )

        # Test reserve with no DOI assigned
        method, url = DOIDataCiteWebClient().endpoint_for_doi(test_doi, action="reserve")

        self.assertEqual(method, WEB_METHOD_POST)
        self.assertEqual(url, expected_url)

        # Test release with no DOI assigned
        method, url = DOIDataCiteWebClient().endpoint_for_doi(test_doi, action="release")

        self.assertEqual(method, WEB_METHOD_POST)
        self.assertEqual(url, expected_url)

        # Test reserve with a DOI assigned (not a valid case, but endpoint_for_doi doesn't care)
        test_doi.doi = f"{expected_prefix}/{expected_suffix}"

        method, url = DOIDataCiteWebClient().endpoint_for_doi(test_doi, action="reserve")

        self.assertEqual(method, WEB_METHOD_POST)
        self.assertEqual(url, expected_url)

        # Test release with a DOI assigned
        method, url = DOIDataCiteWebClient().endpoint_for_doi(test_doi, action="release")

        self.assertEqual(method, WEB_METHOD_PUT)
        self.assertEqual(url, f"{expected_url}/{expected_prefix}/{expected_suffix}")

        # Test with an unknown action
        with self.assertRaises(ValueError):
            DOIDataCiteWebClient().endpoint_for_doi(test_doi, action="update")


class DOIDataCiteWebParserTestCase(unittest.TestCase):
    """Unit tests for the datacite_web_parser.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, "data"))

        cls.expected_authors = [
            {"name": "R. Deen", "name_identifiers": [], "name_type": "Personal", "affiliation": ["NASA PDS"]},
            {"name": "H. Abarca", "name_identifiers": [], "name_type": "Personal", "affiliation": ["NASA PDS"]},
            {"name": "P. Zamani", "name_identifiers": [], "name_type": "Personal", "affiliation": ["NASA PDS"]},
            {"name": "J. Maki", "name_identifiers": [], "name_type": "Personal", "affiliation": ["NASA PDS"]},
        ]
        cls.expected_editors = [
            {"name": "P. H. Smith", "name_identifiers": [], "affiliation": ["NASA PDS"]},
            {"name": "M. Lemmon", "name_identifiers": [], "affiliation": ["NASA PDS"]},
            {"name": "R. F. Beebe", "name_identifiers": [], "affiliation": ["NASA PDS"]},
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
            "InSight Cameras Experiment Data Record (EDR) and Reduced Data Record (RDR) Data Products",
        )
        self.assertEqual(doi.doi, "10.13143/yzw2-vz66")
        self.assertListEqual(doi.editors, self.expected_editors)
        self.assertEqual(doi.id, "yzw2-vz66")
        self.assertSetEqual(doi.keywords, self.expected_keywords)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertEqual(doi.product_type_specific, "PDS4 Refereed Data Bundle")
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertEqual(doi.publisher, "NASA Planetary Data System")
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras::1.0")
        # Check that site url HTML was un-escaped as expected
        self.assertIn("&", doi.site_url)
        self.assertNotIn("&amp;", doi.site_url)
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.title, "InSight Cameras Bundle")

    def test_parse_datacite_response_json(self):
        """Test parsing of an DataCite label in JSON format"""
        # Test with a nominal file containing most of the optional fields
        input_json_file = join(self.input_dir, "datacite_record_draft.json")

        with open(input_json_file, "r") as infile:
            input_json = infile.read()
            dois, errors = DOIDataCiteWebParser.parse_dois_from_label(input_json)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self._compare_doi_to_expected(doi)

    def test_parse_datacite_multi_id_json(self):
        """Test parsing of a DataCite label where a history of identifiers is present"""
        # This file provides a record where multiple LID's are specified with
        # different VID's to simulate an entry that has been updated over time.
        # Parser should assign the newest LIDVID as the primary PDS identifier
        input_file_json = join(self.input_dir, "datacite_record_multi_id.json")

        with open(input_file_json, "r") as infile:
            input_json = infile.read()
            dois, errors = DOIDataCiteWebParser.parse_dois_from_label(input_json)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        # Newest LIDVID should have been assigned
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras::2.0")

        # All other identifiers should be present
        identifiers = [identifier["identifier"] for identifier in doi.identifiers]
        self.assertIn("urn:nasa:pds:insight_cameras::2.0", identifiers)
        self.assertIn("urn:nasa:pds:insight_cameras::1.0", identifiers)
        self.assertIn("urn:nasa:pds:insight_cameras", identifiers)

    def test_get_record_for_identifier(self):
        """Test isolation of specific record based on PDS identifier"""
        input_json_file = join(self.input_dir, "datacite_record_multi_entry.json")

        # Test extraction of a single record from a multi-entry label, parse the
        # DOI from the result, and ensure we get the record back we expected
        record, content_type = DOIDataCiteWebParser.get_record_for_identifier(
            input_json_file, "urn:nasa:pds:ladee_nms:data_raw::1.0"
        )

        self.assertEqual(content_type, CONTENT_TYPE_JSON)

        dois, _ = DOIDataCiteWebParser.parse_dois_from_label(record)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:ladee_nms:data_raw::1.0")
        self.assertEqual(doi.doi, "10.17189/1408893")

        # Make sure we get an exception back for an identifier that is not present
        # in the file
        with self.assertRaises(UnknownIdentifierException):
            DOIDataCiteWebParser.get_record_for_identifier(input_json_file, "urn:nasa:pds:ladee_nms:data_raw::2.0")

    def test_get_record_for_doi(self):
        """Test isolation of a specific record based on DOI"""
        input_json_file = join(self.input_dir, "datacite_record_multi_entry.json")

        # Test extraction of a single record from a multi-entry label, parse the DOI
        # from the result, and ensure we got the record back we expected
        record, content_type = DOIDataCiteWebParser.get_record_for_doi(input_json_file, "10.17189/1408892")

        self.assertEqual(content_type, CONTENT_TYPE_JSON)

        dois, _ = DOIDataCiteWebParser.parse_dois_from_label(record)

        self.assertEqual(len(dois), 1)

        doi = dois[0]

        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:ladee_nms:data_calibrated::1.0")
        self.assertEqual(doi.doi, "10.17189/1408892")

        # Make sure we get an exception for a DOI that is not present in the file
        with self.assertRaises(UnknownDoiException):
            DOIDataCiteWebParser.get_record_for_doi(input_json_file, "10.17189/1408890")


class DOIDataCiteValidatorTestCase(unittest.TestCase):
    """Unit tests for the datacite_validator.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, "data"))

    def test_json_label_validation(self):
        """Test validation against a DataCite label created from a valid Doi object"""
        validator = DOIDataCiteValidator()

        # Parse sample input to obtain a Doi object
        input_json_file = join(self.input_dir, "datacite_record_draft.json")

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
