#!/usr/bin/env python
import os
import unittest
from os.path import abspath
from os.path import join
from unittest.mock import patch

import pds_doi_service.core.outputs.datacite.datacite_web_client
import pds_doi_service.core.outputs.osti.osti_web_client
from pds_doi_service.core.actions.reserve import DOICoreActionReserve
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.service import SERVICE_TYPE_OSTI
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST
from pkg_resources import resource_filename


class ReserveActionTestCase(unittest.TestCase):
    _record_service = None
    _web_parser = None

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))
        cls.db_name = "doi_temp.db"

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

    def webclient_submit_patch(
        self, payload, url=None, username=None, password=None, method=WEB_METHOD_POST, content_type=CONTENT_TYPE_XML
    ):
        """
        Patch for DOIWebClient.submit_content().

        Allows a non dry-run reserve to occur without actually submitting
        anything to the service provider's test server.
        """
        # Parse the DOI's from the input label, update status to 'reserved',
        # and create the output label
        dois, _ = ReserveActionTestCase._web_parser.parse_dois_from_label(payload, content_type=CONTENT_TYPE_JSON)

        doi = dois[0]

        doi.status = DoiStatus.Reserved

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

        # Each DOI should have the expected status set
        for doi in dois:
            self.assertEqual(doi.status, expected_status)

    def test_reserve_xlsx_dry_run(self):
        """
        Test Reserve action with a local excel spreadsheet, using the
        dry run flag to avoid submission.
        """
        reserve_args = {
            "input": join(self.input_dir, "DOI_Reserved_GEO_200318_with_corrected_identifier.xlsx"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "dry_run": True,
            "force": True,
        }

        self.run_reserve_test(reserve_args, expected_dois=3, expected_status=DoiStatus.Reserved_not_submitted)

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
            "input": join(self.input_dir, "DOI_Reserved_GEO_200318_with_corrected_identifier.xlsx"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "dry_run": False,
            "force": True,
        }

        self.run_reserve_test(reserve_args, expected_dois=3, expected_status=DoiStatus.Reserved)

    def test_reserve_csv_dry_run(self):
        """
        Test Reserve action with a local CSV file, using the dry run flag
        to avoid submission to the service provider.
        """
        reserve_args = {
            "input": join(self.input_dir, "DOI_Reserved_GEO_200318.csv"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "dry_run": True,
            "force": True,
        }

        self.run_reserve_test(reserve_args, expected_dois=3, expected_status=DoiStatus.Reserved_not_submitted)

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
            "input": join(self.input_dir, "DOI_Reserved_GEO_200318.csv"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "dry_run": False,
            "force": True,
        }

        self.run_reserve_test(reserve_args, expected_dois=3, expected_status=DoiStatus.Reserved)

    def test_reserve_json_dry_run(self):
        """
        Test Reserve action with a local JSON file, using the dry run flag
        to avoid submission.
        """
        # Select the appropriate JSON format based on the currently configured
        # service
        if DOIServiceFactory.get_service_type() == SERVICE_TYPE_OSTI:
            input_file = join(self.input_dir, "DOI_Release_20210216_from_reserve.json")
        else:
            input_file = join(self.input_dir, "DOI_Release_20210615_from_reserve.json")

        reserve_args = {
            "input": input_file,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "dry_run": True,
            "force": True,
        }

        self.run_reserve_test(reserve_args, expected_dois=1, expected_status=DoiStatus.Reserved_not_submitted)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_json_and_submit(self):
        """
        Test Reserve action with a local JSON file, submitting the result to
        the service provider.
        """
        # Select the appropriate JSON format based on the currently configured
        # service
        if DOIServiceFactory.get_service_type() == SERVICE_TYPE_OSTI:
            input_file = join(self.input_dir, "DOI_Release_20210216_from_reserve.json")
        else:
            input_file = join(self.input_dir, "DOI_Release_20210615_from_reserve.json")

        reserve_args = {
            "input": input_file,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "dry_run": False,
            "force": True,
        }

        self.run_reserve_test(reserve_args, expected_dois=1, expected_status=DoiStatus.Reserved)


if __name__ == "__main__":
    unittest.main()
