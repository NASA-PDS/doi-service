#!/usr/bin/env python
import os
import unittest
from datetime import datetime
from os.path import abspath
from os.path import join
from unittest.mock import patch

import pds_doi_service.core.outputs.datacite.datacite_web_client
import pds_doi_service.core.outputs.osti.osti_web_client
from pds_doi_service.core.actions.reserve import DOICoreActionReserve
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST
from pds_doi_service.core.util.general_util import get_global_keywords
from pkg_resources import resource_filename


class ReserveActionTestCase(unittest.TestCase):
    _record_service = None
    _web_parser = None
    db_name = "doi_temp.db"

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, "data"))

        # Remove db_name if exist to have a fresh start otherwise exception will be
        # raised about using existing lidvid.
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

        cls._reserve_action = DOICoreActionReserve(db_name=cls.db_name)
        cls._record_service = DOIServiceFactory.get_doi_record_service()
        cls._web_parser = DOIServiceFactory.get_web_parser_service()

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

    def setUp(self) -> None:
        """
        Remove previous transaction DB and reinitialize the release action so
        we don't have to worry about conflicts from reusing PDS ID's/DOI's between
        tests.
        """
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)

        self._reserve_action = DOICoreActionReserve(db_name=self.db_name)

    _doi_counter = 1

    def webclient_submit_patch(
        self, payload, url=None, username=None, password=None, method=WEB_METHOD_POST, content_type=CONTENT_TYPE_XML
    ):
        """
        Patch for DOIWebClient.submit_content().

        Allows a reserve to occur without actually submitting anything to the
        service provider's test server.
        """
        # Parse the DOI's from the input label, add a dummy DOI value,
        # and create the output label
        dois, _ = ReserveActionTestCase._web_parser.parse_dois_from_label(payload, content_type=CONTENT_TYPE_JSON)

        doi = dois[0]

        # Create a new dummy DOI value using the rolling counter
        doi.doi = f"10.17189/{ReserveActionTestCase._doi_counter}"
        ReserveActionTestCase._doi_counter += 1

        o_doi_label = ReserveActionTestCase._record_service.create_doi_record(doi, content_type=CONTENT_TYPE_JSON)

        return doi, o_doi_label

    def run_reserve_test(self, reserve_args, expected_dois, expected_status):
        """
        Helper function to run the release action and check the expected number
        of DOI records and DOI status returned.

        Parameters
        ----------
        reserve_args - dict
            The keyword arguments to pass to the reserve action run method
        expected_dois - int
            The number of DOI records expected from the reserve action
        expected_status - DoiStatus
            The expected status of each returned record

        """
        o_doi_label = self._reserve_action.run(**reserve_args)

        dois, errors = self._web_parser.parse_dois_from_label(o_doi_label, content_type=CONTENT_TYPE_JSON)

        # Should get the expected number of parsed DOI's
        self.assertEqual(len(dois), expected_dois)

        # Shouldn't be any errors returned
        self.assertEqual(len(errors), 0)

        # Each DOI should have a DOI assigned and the expected status set
        for doi in dois:
            self.assertIsNotNone(doi.doi)
            self.assertEqual(doi.status, expected_status)

        return dois

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_xlsx_and_submit(self):
        """
        Test Reserve action with a local excel spreadsheet, submitting the
        result to the service provider.
        """
        reserve_args = {
            "input": join(self.input_dir, "spreadsheet_with_pds4_identifiers.xlsx"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        self.run_reserve_test(reserve_args, expected_dois=3, expected_status=DoiStatus.Draft)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_csv_and_submit(self):
        """
        Test Reserve action with a local CSV file, submitting the result to the
        service provider.
        """
        reserve_args = {
            "input": join(self.input_dir, "spreadsheet_with_pds4_identifiers.csv"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        self.run_reserve_test(reserve_args, expected_dois=3, expected_status=DoiStatus.Draft)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_pds4_label_and_submit(self):
        """
        Test Reserve action with a local PDS4 XML file, submitting the result to
        the service provider.
        """
        input_file = join(self.input_dir, "pds4_bundle_with_contributors.xml")

        reserve_args = {
            "input": input_file,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        self.run_reserve_test(reserve_args, expected_dois=1, expected_status=DoiStatus.Draft)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_local_dir_one_file(self):
        """Test reserve request with local dir containing one file"""
        input_dir = join(self.input_dir, "input_dir_one_file")

        reserve_args = {
            "input": input_dir,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        dois = self.run_reserve_test(reserve_args, expected_dois=1, expected_status=DoiStatus.Draft)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.editors), 3)
        self.assertEqual(len(doi.keywords), 17)
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras::1.0")
        self.assertEqual(doi.product_type, ProductType.Collection)
        self.assertTrue(all(keyword in doi.keywords for keyword in get_global_keywords()))
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_local_dir_two_files(self):
        """Test reserve request with local dir containing two files"""
        input_dir = join(self.input_dir, "input_dir_two_files")

        reserve_args = {
            "input": input_dir,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        dois = self.run_reserve_test(reserve_args, expected_dois=2, expected_status=DoiStatus.Draft)

        for doi in dois:
            self.assertEqual(len(doi.authors), 4)
            self.assertEqual(len(doi.keywords), 17)
            self.assertEqual(doi.product_type, ProductType.Collection)
            self.assertIsInstance(doi.publication_date, datetime)
            self.assertIsInstance(doi.date_record_added, datetime)
            self.assertTrue(all(keyword in doi.keywords for keyword in get_global_keywords()))
            self.assertTrue(doi.pds_identifier.startswith("urn:nasa:pds:insight_cameras::1"))
            self.assertTrue(doi.title.startswith("InSight Cameras Bundle"))

            # Make sure for the "pds4_bundle_with_contributors.xml" file, we
            # parsed the editors
            if doi.pds_identifier == "urn:nasa:pds:insight_cameras::1.0":
                self.assertEqual(len(doi.editors), 3)
            # For "bundle_in.xml", there should be no editors
            else:
                self.assertEqual(len(doi.editors), 0)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_remote_pds4_bundle(self):
        """Test draft request with a remote bundle URL"""
        input_url = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml"

        reserve_args = {
            "input": input_url,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        dois = self.run_reserve_test(reserve_args, expected_dois=1, expected_status=DoiStatus.Draft)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.keywords), 17)
        self.assertTrue(all(keyword in doi.keywords for keyword in get_global_keywords()))
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras::1.0")
        self.assertEqual(doi.product_type, ProductType.Collection)
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_remote_collection(self):
        """Test reserve request with a remote collection URL"""
        input_url = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml"

        reserve_args = {
            "input": input_url,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        dois = self.run_reserve_test(reserve_args, expected_dois=1, expected_status=DoiStatus.Draft)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.keywords), 11)
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras:data::1.0")
        self.assertEqual(doi.product_type, ProductType.Collection)
        self.assertTrue(all(keyword in doi.keywords for keyword in get_global_keywords()))
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_remote_browse_collection(self):
        """Test draft request with a remote browse collection URL"""
        input_url = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml"

        reserve_args = {
            "input": input_url,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        dois = self.run_reserve_test(reserve_args, expected_dois=1, expected_status=DoiStatus.Draft)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.keywords), 11)
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras:browse::1.0")
        self.assertEqual(doi.description, "Collection of BROWSE products.")
        self.assertEqual(doi.product_type, ProductType.Collection)
        self.assertTrue(all(keyword in doi.keywords for keyword in get_global_keywords()))
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_remote_calibration_collection(self):
        """Test reserve request with remote calibration collection URL"""
        input_url = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml"

        reserve_args = {
            "input": input_url,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        dois = self.run_reserve_test(reserve_args, expected_dois=1, expected_status=DoiStatus.Draft)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.keywords), 13)
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras:calibration::1.0")
        self.assertEqual(doi.description, "Collection of CALIBRATION files/products to include in the archive.")
        self.assertEqual(doi.product_type, ProductType.Collection)
        self.assertTrue(all(keyword in doi.keywords for keyword in get_global_keywords()))
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_remote_document_collection(self):
        """Test reserve request a with remote document collection URL"""
        input_url = "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml"

        reserve_args = {
            "input": input_url,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        dois = self.run_reserve_test(reserve_args, expected_dois=1, expected_status=DoiStatus.Draft)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.keywords), 11)
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras:document::1.0")
        self.assertEqual(doi.description, "Collection of DOCUMENT products.")
        self.assertEqual(doi.product_type, ProductType.Collection)
        self.assertTrue(all(keyword in doi.keywords for keyword in get_global_keywords()))
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)


if __name__ == "__main__":
    unittest.main()
