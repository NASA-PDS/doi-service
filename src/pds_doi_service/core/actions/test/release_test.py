#!/usr/bin/env python
import os
import unittest
from os.path import abspath
from os.path import join
from unittest.mock import patch

import pds_doi_service.core.outputs.datacite.datacite_web_client
import pds_doi_service.core.outputs.osti.osti_web_client
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.exceptions import CriticalDOIException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST
from pds_doi_service.core.util.general_util import get_global_keywords
from pkg_resources import resource_filename


class ReleaseActionTestCase(unittest.TestCase):
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

        cls._release_action = DOICoreActionRelease(db_name=cls.db_name)
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

        self._release_action = DOICoreActionRelease(db_name=self.db_name)

    _doi_counter = 1

    def webclient_submit_patch(
        self, payload, url=None, username=None, password=None, method=WEB_METHOD_POST, content_type=CONTENT_TYPE_XML
    ):
        """
        Patch for DOIWebClient.submit_content().

        Allows a no-review release to occur without actually submitting
        anything to the service provider's test server.
        """
        # Parse the DOI's from the input label, assign a dummy DOI (if necessary)
        # and update the DOI status to create the output label
        dois, _ = ReleaseActionTestCase._web_parser.parse_dois_from_label(payload, content_type=CONTENT_TYPE_JSON)

        doi = dois[0]

        if not doi.doi:
            doi.doi = f"10.17189/{ReleaseActionTestCase._doi_counter}"
            ReleaseActionTestCase._doi_counter += 1

        doi.status = DoiStatus.Findable

        o_doi_label = ReleaseActionTestCase._record_service.create_doi_record(doi, content_type=CONTENT_TYPE_JSON)

        return doi, o_doi_label

    def run_release_test(self, release_args, expected_dois, expected_status):
        """
        Helper function to run the release action and check the expected number
        of DOI records and DOI status returned.

        Parameters
        ----------
        release_args - dict
            The keyword arguments to pass to the release action run method
        expected_dois - int
            The number of DOI records expected from the release action
        expected_status - DoiStatus
            The expected status of each returned record

        """
        o_doi_label = self._release_action.run(**release_args)

        dois, errors = self._web_parser.parse_dois_from_label(o_doi_label, content_type=CONTENT_TYPE_JSON)

        # Should get the expected number of parsed DOI's
        self.assertEqual(len(dois), expected_dois)

        # Shouldn't be any errors returned
        self.assertEqual(len(errors), 0)

        # Each DOI should have the expected status set
        for doi in dois:
            self.assertEqual(doi.status, expected_status)

            # There should always be a DOI assigned, for both review and full-release
            self.assertIsNotNone(doi.doi)

            # Make sure global keywords were assigned at some point in the process
            self.assertTrue(all(keyword in doi.keywords for keyword in get_global_keywords()))

    def test_reserve_release_to_review(self):
        """Test release to review status with a reserved DOI entry"""

        release_args = {
            "input": join(self.input_dir, "osti_record_reserved.xml"),
            "node": "img",
            "submitter": "img-submitter@jpl.nasa.gov",
            "force": True,
            "review": True,
        }

        self.run_release_test(release_args, expected_dois=1, expected_status=DoiStatus.Review)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_reserve_release_to_provider(self):
        """Test release directly to the service provider with a reserved DOI entry"""

        release_args = {
            "input": join(self.input_dir, "osti_record_reserved.xml"),
            "node": "img",
            "submitter": "img-submitter@jpl.nasa.gov",
            "force": True,
            "review": False,
        }

        self.run_release_test(release_args, expected_dois=1, expected_status=DoiStatus.Findable)

    def test_unreserved_release_to_review(self):
        """Test release to review status using a record that has not been reserved (no DOI assigned)"""

        release_args = {
            "input": join(self.input_dir, "pds4_bundle_with_contributors.xml"),
            "node": "img",
            "submitter": "img-submitter@jpl.nasa.gov",
            "force": True,
            "review": True,
        }

        # Submitting a record w/ no DOI assigned for Review should result in an
        # exception since we have no way to store the transaction without a DOI
        # of some kind
        with self.assertRaises(CriticalDOIException):
            self.run_release_test(release_args, expected_dois=1, expected_status=DoiStatus.Review)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_unreserved_release_to_provider(self):
        """Test release directly to the service provider using a record that has not been reserved (no DOI assigned)"""

        release_args = {
            "input": join(self.input_dir, "pds4_bundle_with_contributors.xml"),
            "node": "img",
            "submitter": "img-submitter@jpl.nasa.gov",
            "force": True,
            "review": False,
        }

        # Releasing a record with no DOI directly to the service provider should
        # be OK, since we'll have a DOI assigned to use with the transaction database
        # once the request goes through
        self.run_release_test(release_args, expected_dois=1, expected_status=DoiStatus.Findable)

    def test_review_release_to_review(self):
        """
        Test release to review status with a review DOI entry

        This is essentially a no-op, but it should work regardless
        """

        release_args = {
            "input": join(self.input_dir, "osti_record_review.xml"),
            "node": "img",
            "submitter": "img-submitter@jpl.nasa.gov",
            "force": True,
            "review": True,
        }

        self.run_release_test(release_args, expected_dois=1, expected_status=DoiStatus.Review)

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_review_release_to_osti(self):
        """Test release directly to the service provider with a review DOI entry"""

        release_args = {
            "input": join(self.input_dir, "osti_record_review.xml"),
            "node": "img",
            "submitter": "img-submitter@jpl.nasa.gov",
            "force": True,
            "review": False,
        }

        self.run_release_test(release_args, expected_dois=1, expected_status=DoiStatus.Findable)


if __name__ == "__main__":
    unittest.main()
