# coding: utf-8
from __future__ import absolute_import

import json
import os
import unittest
from datetime import datetime
from os.path import abspath
from os.path import exists
from os.path import join
from unittest.mock import patch

import pds_doi_service.api.controllers.dois_controller
import pds_doi_service.core.outputs.osti.osti_web_client
import pds_doi_service.core.outputs.transaction
from pds_doi_service.api.encoder import JSONEncoder
from pds_doi_service.api.models import DoiRecord
from pds_doi_service.api.models import DoiSummary
from pds_doi_service.api.models import LabelPayload
from pds_doi_service.api.models import LabelsPayload
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.service import SERVICE_TYPE_DATACITE
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pkg_resources import resource_filename

from ._base import BaseTestCase


class TestDoisController(BaseTestCase):
    """DoisController integration test stubs"""

    # These attributes are defined at class level so it may be accessed
    # by patched methods
    test_data_dir = None
    input_dir = None
    service_type = None

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.test_data_dir = join(cls.test_dir, "data")
        cls.input_dir = abspath(join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))
        cls.service_type = DOIServiceFactory.get_service_type()

        # Path to a temporary database to re-instantiate for every test
        cls.temp_db = join(cls.test_data_dir, "temp.db")

    def setUp(self):
        # Set testing mode to True so endpoints know to look for a custom
        # database instance to work with
        self.app.config["TESTING"] = True

        # Make sure valid referrers is set as tests expect
        config = DOIConfigUtil.get_config()
        config.set("OTHER", "api_valid_referrers", "localhost,0.0.0.0")

    def tearDown(self):
        # Remove the temp DB so a new one is created before each test
        if exists(self.temp_db):
            os.unlink(self.temp_db)

    def list_action_run_patch(self, **kwargs):
        """
        Patch for DOICoreActionList.run()

        Returns a JSON string corresponding to a successful search.
        The transaction_key is modified to point to the local test data
        directory appropriate for the current service.
        """
        return json.dumps(
            [
                {
                    "status": DoiStatus.Draft,
                    "date_added": "2020-10-20T14:04:12.560568-07:00",
                    "date_updated": "2020-10-20T14:04:12.560568-07:00",
                    "submitter": "eng-submitter@jpl.nasa.gov",
                    "title": "InSight Cameras Bundle 1.1",
                    "type": "Dataset",
                    "subtype": "PDS4 Refereed Data Bundle",
                    "node_id": "eng",
                    "identifier": "urn:nasa:pds:insight_cameras::1.1",
                    "doi": "10.17189/28957",
                    "transaction_key": join(TestDoisController.test_data_dir, TestDoisController.service_type),
                    "is_latest": 1,
                }
            ]
        )

    def list_action_run_patch_missing(self, **kwargs):
        """
        Patch for DOICoreActionList.run()

        Returns a result corresponding to an unsuccessful search.
        """
        return "[]"

    def draft_action_run_patch(self, **kwargs):
        """
        Patch for DOICoreActionDraft.run()

        Returns body of a label corresponding to a successful draft
        request.
        """
        draft_record_file = join(TestDoisController.test_data_dir, TestDoisController.service_type, "draft_record")
        with open(draft_record_file, "r") as infile:
            return infile.read()

    def reserve_action_run_patch(self, **kwargs):
        """
        Patch for DOICoreActionReserve.run()

        Returns body of a label corresponding to a successful reserve
        (dry-run) request.
        """
        draft_record_file = join(TestDoisController.test_data_dir, TestDoisController.service_type, "reserve_record")
        with open(draft_record_file, "r") as infile:
            return infile.read()

    def release_action_run_patch(self, **kwargs):
        """
        Patch for DOICoreActionRelease.run()

        Returns body of a label corresponding to a successful release
        request.
        """
        draft_record_file = join(TestDoisController.test_data_dir, TestDoisController.service_type, "release_record")
        with open(draft_record_file, "r") as infile:
            return infile.read()

    def release_action_run_w_error_patch(self, **kwargs):
        """
        Patch for DOICoreActionRelease.run()

        Returns body of a label corresponding to errors returned
        from the DOI service provider.
        """
        draft_record_file = join(TestDoisController.test_data_dir, TestDoisController.service_type, "error_record")
        with open(draft_record_file, "r") as infile:
            return infile.read()

    def transaction_log_patch(self):
        """No-op patch for Transaction.log() to avoid modifying our test DB"""
        return

    def webclient_query_patch(self, query=None, content_type=CONTENT_TYPE_XML):
        """
        Patch for DOIOstiWebClient.webclient_query_doi().

        Allows a pending check to occur without actually having to communicate
        with the OSTI test server.
        """
        # Return dummy xml results containing the statuses we expect
        # Released
        if query["doi"] == "10.17189/28957":
            xml_file = "DOI_Release_20200727_from_register.xml"
        # Pending
        elif query["doi"] == "10.17189/29348":
            xml_file = "DOI_Release_20200727_from_release.xml"
        # Error
        else:
            xml_file = "DOI_Release_20200727_from_error.xml"

        with open(join(TestDoisController.input_dir, xml_file), "r") as infile:
            xml_contents = infile.read()

        return xml_contents

    def test_get_dois(self):
        """Test case for get_dois"""
        # For these tests, use a pre-existing database with some canned
        # entries to query for
        test_db = join(self.test_data_dir, "test.db")

        # Start with a empty query to fetch all available records
        query_string = [("db_name", test_db)]

        # Ensure fetch-all endpoint works both with and without a trailing
        # slash
        endpoints = ["/PDS_APIs/pds_doi_api/0.2/dois", "/PDS_APIs/pds_doi_api/0.2/dois/"]

        for endpoint in endpoints:
            response = self.client.open(
                endpoint, method="GET", query_string=query_string, headers={"Referer": "http://localhost"}
            )

            self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

            records = response.json

            # Test database should contain 3 records
            self.assertEqual(len(records), 3)

        # Now use a query string to ensure we can get specific records back
        query_string = [("node", "eng"), ("db_name", test_db)]

        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

        # Should only get one of the records back
        records = response.json
        self.assertEqual(len(records), 1)

        # Reformat JSON result into a DoiSummary object so we can check fields
        summary = DoiSummary.from_dict(records[0])

        self.assertEqual(summary.node, "eng")
        self.assertEqual(summary.title, "InSight Cameras Bundle 1.1")
        self.assertEqual(summary.submitter, "eng-submitter@jpl.nasa.gov")
        self.assertEqual(summary.identifier, "urn:nasa:pds:insight_cameras::1.1")
        self.assertEqual(summary.status, DoiStatus.Draft)

        # Test filtering by start/end date
        # Note: this test was originally developed on PDT, so its important
        #       to include the correct time zone offset as part of the query

        query_string = [
            ("start_date", "2020-10-20T21:04:13.000000+08:00"),
            ("end_date", "2020-10-20T21:04:14.000000+08:00"),
            ("db_name", test_db),
        ]

        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

        # Should only get one of the records back
        records = response.json
        self.assertEqual(len(records), 1)

        # Reformat JSON result into a DoiSummary object so we can check fields
        summary = DoiSummary.from_dict(records[0])

        self.assertEqual(summary.node, "img")
        self.assertEqual(summary.title, "InSight Cameras Bundle 1.0")
        self.assertEqual(summary.submitter, "img-submitter@jpl.nasa.gov")
        self.assertEqual(summary.identifier, "urn:nasa:pds:insight_cameras::1.0")
        self.assertEqual(summary.status, DoiStatus.Reserved_not_submitted)

        # Test fetching of a record that only has an LID (no VID) associated to it
        query_string = [("node", "img"), ("ids", "urn:nasa:pds:lab_shocked_feldspars"), ("db_name", test_db)]

        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

        # Should only get one of the records back
        records = response.json
        self.assertEqual(len(records), 1)

        # Reformat JSON result into a DoiSummary object so we can check fields
        summary = DoiSummary.from_dict(records[0])

        self.assertEqual(summary.node, "img")
        self.assertEqual(summary.title, "Laboratory Shocked Feldspars Bundle")
        self.assertEqual(summary.submitter, "img-submitter@jpl.nasa.gov")
        self.assertEqual(summary.identifier, "urn:nasa:pds:lab_shocked_feldspars")
        self.assertEqual(summary.status, DoiStatus.Reserved_not_submitted)

        # Now try filtering by workflow status
        query_string = [("status", DoiStatus.Reserved_not_submitted.value), ("db_name", test_db)]

        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

        # Should only get two of the records back
        records = response.json
        self.assertEqual(len(records), 2)

        # Finally, test with a malformed start/end date and ensure we
        # get "invalid argument" code back
        query_string = [
            ("start_date", "2020-10-20 14:04:13.000000"),
            ("end_date", "10-20-2020 14:04"),
            ("db_name", test_db),
        ]

        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert400(response, "Response body is : " + response.data.decode("utf-8"))

    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionList, "run", list_action_run_patch)
    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionDraft, "run", draft_action_run_patch)
    def test_post_dois_draft_w_url(self):
        """Test a draft POST with url input"""
        # We can use a file system path since were working with a local server
        input_bundle = join(self.test_data_dir, "bundle_in.xml")

        # Start by submitting a draft request
        query_string = [
            ("action", "draft"),
            ("submitter", "eng-submitter@jpl.nasa.gov"),
            ("node", "eng"),
            ("url", input_bundle),
            ("db_name", self.temp_db),
        ]

        draft_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(draft_response, "Response body is : " + draft_response.data.decode("utf-8"))

        # Recreate a DoiRecord from the response JSON and examine the
        # fields
        draft_record = DoiRecord.from_dict(draft_response.json[0])

        self.assertEqual(draft_record.node, "eng")
        self.assertEqual(draft_record.title, "InSight Cameras Bundle 1.1")
        self.assertEqual(draft_record.submitter, "eng-submitter@jpl.nasa.gov")
        self.assertEqual(draft_record.identifier, "urn:nasa:pds:insight_cameras::1.1")
        self.assertEqual(draft_record.doi, "10.17189/28957")
        self.assertEqual(draft_record.creation_date, datetime.fromisoformat("2020-10-20T14:04:12.560568-07:00"))
        self.assertEqual(draft_record.update_date, datetime.fromisoformat("2020-10-20T14:04:12.560568-07:00"))
        # Note we get Pending back from the parsed label, however
        # the object sent to transaction database has 'Draft' status
        self.assertEqual(draft_record.status, DoiStatus.Pending)

    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionList, "run", list_action_run_patch)
    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionDraft, "run", draft_action_run_patch)
    def test_post_dois_draft_w_payload(self):
        """Test a draft POST with requestBody input"""
        input_bundle = join(self.test_data_dir, "bundle_in.xml")

        with open(input_bundle, "rb") as infile:
            body = infile.read()

        query_string = [
            ("action", "draft"),
            ("submitter", "eng-submitter@jpl.nasa.gov"),
            ("node", "eng"),
            ("db_name", self.temp_db),
        ]

        draft_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="POST",
            data=body,
            content_type="application/xml",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(draft_response, "Response body is : " + draft_response.data.decode("utf-8"))

        # Recreate a DoiRecord from the response JSON and examine the
        # fields
        draft_record = DoiRecord.from_dict(draft_response.json[0])

        self.assertEqual(draft_record.node, "eng")
        self.assertEqual(draft_record.title, "InSight Cameras Bundle 1.1")
        self.assertEqual(draft_record.submitter, "eng-submitter@jpl.nasa.gov")
        self.assertEqual(draft_record.identifier, "urn:nasa:pds:insight_cameras::1.1")
        self.assertEqual(draft_record.doi, "10.17189/28957")
        self.assertEqual(draft_record.creation_date, datetime.fromisoformat("2020-10-20T14:04:12.560568-07:00"))
        self.assertEqual(draft_record.update_date, datetime.fromisoformat("2020-10-20T14:04:12.560568-07:00"))
        # Note we get Pending back from the parsed label, however
        # the object sent to transaction database has 'Draft' status
        self.assertEqual(draft_record.status, DoiStatus.Pending)

    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionList, "run", list_action_run_patch)
    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionReserve, "run", reserve_action_run_patch)
    def test_post_dois_reserve(self):
        """Test dry-run reserve POST"""
        # Submit a new bundle in reserve (not submitted) status
        body = LabelsPayload(
            [
                LabelPayload(
                    status=DoiStatus.Reserved,
                    title="Laboratory Shocked Feldspars Bundle",
                    publication_date=datetime.now(),
                    product_type_specific="PDS4 Bundle",
                    author_last_name="Johnson",
                    author_first_name="J. R.",
                    related_resource="urn:nasa:pds:lab_shocked_feldspars",
                )
            ]
        )

        query_string = [
            ("action", "reserve"),
            ("submitter", "img-submitter@jpl.nasa.gov"),
            ("node", "img"),
            ("db_name", self.temp_db),
        ]

        reserve_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="POST",
            data=JSONEncoder().encode(body),
            content_type="application/json",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(reserve_response, "Response body is : " + reserve_response.data.decode("utf-8"))

        # Recreate a DoiRecord from the response JSON and examine the
        # fields
        reserve_record = DoiRecord.from_dict(reserve_response.json[0])

        self.assertEqual(reserve_record.node, "img")
        self.assertEqual(reserve_record.title, "InSight Cameras Bundle")
        self.assertEqual(reserve_record.submitter, "img-submitter@jpl.nasa.gov")
        self.assertEqual(reserve_record.identifier, "urn:nasa:pds:insight_cameras::2.0")
        self.assertEqual(reserve_record.status, DoiStatus.Reserved_not_submitted)

    def test_post_dois_invalid_requests(self):
        """Test invalid POST requests"""

        # Test with an unknown action, should get Invalid Argument
        query_string = [
            ("action", "unknown"),
            ("submitter", "img-submitter@jpl.nasa.gov"),
            ("node", "img"),
            ("db_name", self.temp_db),
        ]

        error_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert400(error_response, "Response body is : " + error_response.data.decode("utf-8"))

        # Test draft action with no url or requestBody input
        query_string = [
            ("action", "draft"),
            ("submitter", "img-submitter@jpl.nasa.gov"),
            ("node", "img"),
            ("db_name", self.temp_db),
        ]

        error_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert400(error_response, "Response body is : " + error_response.data.decode("utf-8"))

        # Test reserve action with a url instead of a requestBody
        input_bundle = join(self.test_data_dir, "bundle_in.xml")

        query_string = [
            ("action", "reserve"),
            ("submitter", "eng-submitter@jpl.nasa.gov"),
            ("node", "eng"),
            ("url", input_bundle),
            ("db_name", self.temp_db),
        ]

        error_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert400(error_response, "Response body is : " + error_response.data.decode("utf-8"))

    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionList, "run", list_action_run_patch)
    def test_post_submit(self):
        """Test the submit endpoint"""
        query_string = [
            ("force", False),
            ("db_name", self.temp_db),
            ("identifier", "urn:nasa:pds:insight_cameras::1.1"),
        ]

        release_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/doi/submit",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(release_response, "Response body is : " + release_response.data.decode("utf-8"))

        # Recreate a DoiRecord from the response JSON and examine the
        # fields
        submit_record = DoiRecord.from_dict(release_response.json[0])

        self.assertEqual(submit_record.node, "eng")
        self.assertEqual(submit_record.title, "InSight Cameras Bundle 1.1")
        self.assertEqual(submit_record.submitter, "eng-submitter@jpl.nasa.gov")
        self.assertEqual(submit_record.identifier, "urn:nasa:pds:insight_cameras::1.1")
        self.assertEqual(submit_record.status, DoiStatus.Review)
        self.assertEqual(submit_record.doi, "10.17189/28957")

    def test_disabled_release_endpoint(self):
        """
        Test to ensure that the dois/{lidvid}/release is not reachable.

        Note that this test should be removed if the dois/{lidvid}/release
        endpoint is ever re-enabled, along with the @unittest.skip decorators
        for the corresponding unit tests.
        """
        query_string = [
            ("force", False),
            ("db_name", self.temp_db),
            ("identifier", "urn:nasa:pds:insight_cameras::1.1"),
        ]

        release_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois/release",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert404(release_response, "Response body is : " + release_response.data.decode("utf-8"))

    @unittest.skip("dois/release endpoint is disabled")
    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionRelease, "run", release_action_run_patch)
    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionList, "run", list_action_run_patch)
    def test_post_release(self):
        """Test the release endpoint"""
        query_string = [
            ("force", False),
            ("db_name", self.temp_db),
            ("identifier", "urn:nasa:pds:insight_cameras::1.1"),
        ]

        release_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois/release",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(release_response, "Response body is : " + release_response.data.decode("utf-8"))

        # Recreate a DoiRecord from the response JSON and examine the
        # fields
        release_record = DoiRecord.from_dict(release_response.json[0])

        self.assertEqual(release_record.node, "eng")
        self.assertEqual(release_record.title, "InSight Cameras Bundle 1.1")
        self.assertEqual(release_record.submitter, "eng-submitter@jpl.nasa.gov")
        self.assertEqual(release_record.identifier, "urn:nasa:pds:insight_cameras::1.1")
        self.assertEqual(release_record.status, DoiStatus.Pending)
        self.assertEqual(release_record.doi, "10.17189/21734")

        # Record field should match what we provided via patch method
        self.assertEqual(release_record.record, self.release_action_run_patch())

    @unittest.skip("dois/release endpoint is disabled")
    @patch.object(
        pds_doi_service.api.controllers.dois_controller.DOICoreActionRelease, "run", release_action_run_w_error_patch
    )
    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionList, "run", list_action_run_patch)
    def test_post_release_w_errors(self):
        """
        Test the release endpoint where errors are received back from the
        release action.
        """
        query_string = [
            ("force", False),
            ("db_name", self.temp_db),
            ("identifier", "urn:nasa:pds:insight_cameras::1.1"),
        ]

        error_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois/release",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert400(error_response, "Response body is : " + error_response.data.decode("utf-8"))

        # Check the error response and make sure it contains all the errors
        # provided from the original XML
        errors = error_response.json["errors"]

        self.assertEqual(errors[0]["name"], "WarningDOIException")
        self.assertIn("Title is required", errors[0]["message"])
        self.assertIn("A publication date is required", errors[0]["message"])
        self.assertIn("A site URL is required", errors[0]["message"])
        self.assertIn("A product type is required", errors[0]["message"])
        self.assertIn("A specific product type is required for non-dataset types", errors[0]["message"])

    @unittest.skip("dois/release endpoint is disabled")
    @patch.object(
        pds_doi_service.api.controllers.dois_controller.DOICoreActionList, "run", list_action_run_patch_missing
    )
    def test_post_release_missing_lid(self):
        """
        Test the release endpoint where no existing entry for the requested
        LID exists.
        """
        query_string = [
            ("force", False),
            ("db_name", self.temp_db),
            ("identifier", "urn:nasa:pds:insight_cameras::1.1"),
        ]

        error_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois/release",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert404(error_response, "Response body is : " + error_response.data.decode("utf-8"))

        # Check the error response and make sure it contains the expected
        # error message
        errors = error_response.json["errors"]

        self.assertEqual(errors[0]["name"], "UnknownLIDVIDException")
        self.assertIn(
            "No record(s) could be found for LIDVID " "urn:nasa:pds:insight_cameras::1.1", errors[0]["message"]
        )

    def list_action_run_patch_no_transaction_history(self, **kwargs):
        """
        Patch for DOICoreActionList.run()

        Returns a result corresponding to an entry where the listed
        transaction_key location no longer exists.
        """
        return json.dumps([{"transaction_key": "/dev/null", "is_latest": 1}])

    @unittest.skip("dois/release endpoint is disabled")
    @patch.object(
        pds_doi_service.api.controllers.dois_controller.DOICoreActionList,
        "run",
        list_action_run_patch_no_transaction_history,
    )
    def test_post_release_missing_transaction_history(self):
        """
        Test the release endpoint where the requested LID returns an entry
        with a missing transaction_key location.
        """
        query_string = [
            ("force", False),
            ("db_name", self.temp_db),
            ("identifier", "urn:nasa:pds:insight_cameras::1.1"),
        ]

        error_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois/release",
            method="POST",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert500(error_response, "Response body is : " + error_response.data.decode("utf-8"))

        # Check the error response and make sure it contains the expected
        # error message
        errors = error_response.json["errors"]

        self.assertEqual(errors[0]["name"], "NoTransactionHistoryForLIDVIDException")
        self.assertIn(
            "Could not find a DOI label associated with identifier " "urn:nasa:pds:insight_cameras::1.1",
            errors[0]["message"],
        )

    @patch.object(pds_doi_service.api.controllers.dois_controller.DOICoreActionList, "run", list_action_run_patch)
    def test_get_doi_from_id(self):
        """Test case for get_doi_from_id"""
        query_string = [("identifier", "urn:nasa:pds:insight_cameras::1.1")]

        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/doi",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

        # Recreate a DoiRecord from the response JSON and examine the
        # fields
        record = DoiRecord.from_dict(response.json)

        self.assertEqual(record.node, "eng")
        self.assertEqual(record.title, "InSight Cameras Bundle 1.1")
        self.assertEqual(record.submitter, "eng-submitter@jpl.nasa.gov")
        self.assertEqual(record.identifier, "urn:nasa:pds:insight_cameras::1.1")
        self.assertEqual(record.status, DoiStatus.Pending)

        # Make sure we only got one record back
        dois, _ = DOIServiceFactory.get_web_parser_service().parse_dois_from_label(record.record)

        self.assertEqual(len(dois), 1)

        # Test again with an LID only, should get the same result back
        query_string = [("identifier", "urn:nasa:pds:insight_cameras")]

        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/doi",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

        record = DoiRecord.from_dict(response.json)

        self.assertEqual(record.node, "eng")
        self.assertEqual(record.title, "InSight Cameras Bundle")
        self.assertEqual(record.submitter, "eng-submitter@jpl.nasa.gov")
        self.assertEqual(record.identifier, "urn:nasa:pds:insight_cameras")
        self.assertEqual(record.status, DoiStatus.Pending)

        # Make sure we only got one record back
        dois, _ = DOIServiceFactory.get_web_parser_service().parse_dois_from_label(record.record)

        self.assertEqual(len(dois), 1)

    @patch.object(
        pds_doi_service.api.controllers.dois_controller.DOICoreActionList, "run", list_action_run_patch_missing
    )
    def test_get_doi_missing_id(self):
        """Test get_doi_from_id where requested LIDVID is not found"""
        query_string = [("identifier", "urn:nasa:pds:insight_cameras::1.1")]

        error_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/doi",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert404(error_response, "Response body is : " + error_response.data.decode("utf-8"))

        # Check the error response and make sure it contains the expected
        # error message
        errors = error_response.json["errors"]

        self.assertEqual(errors[0]["name"], "UnknownIdentifierException")
        self.assertIn(
            "No record(s) could be found for identifier " "urn:nasa:pds:insight_cameras::1.1", errors[0]["message"]
        )

    @patch.object(
        pds_doi_service.api.controllers.dois_controller.DOICoreActionList,
        "run",
        list_action_run_patch_no_transaction_history,
    )
    def test_get_doi_missing_transaction_history(self):
        """
        Test get_doi_from_id where transaction history for LIDVID cannot be
        found
        """
        query_string = [("identifier", "urn:nasa:pds:insight_cameras::1.1")]

        error_response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/doi",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert500(error_response, "Response body is : " + error_response.data.decode("utf-8"))

        # Check the error response and make sure it contains the expected
        # error message
        errors = error_response.json["errors"]

        self.assertEqual(errors[0]["name"], "NoTransactionHistoryForIdentifierException")
        self.assertIn(
            "Could not find a DOI label associated with identifier " "urn:nasa:pds:insight_cameras::1.1",
            errors[0]["message"],
        )

    def test_put_doi_from_id(self):
        """Test case for put_doi_from_id"""
        query_string = [
            ("submitter", "img-submitter@jpl.nasa.gov"),
            ("node", "img"),
            ("identifier", "urn:nasa:pds:insight_cameras::1.1"),
            ("url", "http://fake.url.net"),
        ]

        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/doi",
            method="PUT",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        # Should return a Not Implemented code
        self.assertEqual(response.status_code, 501)

        errors = response.json["errors"]
        self.assertEqual(errors[0]["name"], "NotImplementedError")
        self.assertIn("Please use the POST /doi endpoint for record update", errors[0]["message"])

    @unittest.skipIf(
        DOIServiceFactory.get_service_type() == SERVICE_TYPE_DATACITE,
        "DataCite does not assign a pending state to release requests",
    )
    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "query_doi", webclient_query_patch
    )
    @patch.object(pds_doi_service.core.outputs.transaction.Transaction, "log", transaction_log_patch)
    def test_get_check_dois(self):
        """Test case for get_check_dois"""
        # TODO need datacite version
        test_db = join(self.test_data_dir, "pending_dois.db")

        query_string = [
            ("submitter", "doi-checker@jpl.nasa.gov"),
            ("email", False),
            ("attachment", False),
            ("db_name", test_db),
        ]

        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois/check",
            method="GET",
            query_string=query_string,
            headers={"Referer": "http://localhost"},
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

        records = response.json
        self.assertEqual(len(records), 3)

        # Check each record and ensure each DOI returned with the expected
        # status
        for record in records:
            self.assertEqual(record["submitter"], "doi-checker@jpl.nasa.gov")

            if record["doi"] == "10.17189/28957":
                self.assertEqual(record["status"], DoiStatus.Registered)

            if record["doi"] == "10.17189/29348":
                self.assertEqual(record["status"], DoiStatus.Pending)

            if record["doi"] == "10.17189/29527":
                self.assertEqual(record["status"], DoiStatus.Error)
                # Make sure we got a message back with the error
                self.assertIsNotNone(record["message"])

    def test_filter_by_referrers(self):
        """Test filtering of requests based on the referer header value"""

        # By default, the INI config should specify localhost and 0.0.0.0 as
        # valid hostnames, so attempting with any other referrer should
        # return a 403 "forbidden" error
        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois", method="GET", headers={"Referer": "http://www.zombo.com"}
        )

        self.assert403(response, "Response body is : " + response.data.decode("utf-8"))

        # Requests with no referrer provided should also fail with a 401
        # "unauthorized" error
        response = self.client.open("/PDS_APIs/pds_doi_api/0.2/dois", method="GET")

        self.assert401(response, "Response body is : " + response.data.decode("utf-8"))

        # Providing a valid referrer should make everything work again
        response = self.client.open(
            "/PDS_APIs/pds_doi_api/0.2/dois", method="GET", headers={"Referer": "http://0.0.0.0"}
        )

        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    import unittest

    unittest.main()
