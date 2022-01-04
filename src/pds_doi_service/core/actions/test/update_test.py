#!/usr/bin/env python
import csv
import os
import tempfile
import unittest
from datetime import datetime
from os.path import abspath
from os.path import join
from unittest.mock import patch

import pds_doi_service.core.outputs.datacite.datacite_web_client
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.actions.reserve import DOICoreActionReserve
from pds_doi_service.core.actions.update import DOICoreActionUpdate
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.entities.exceptions import CriticalDOIException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST
from pds_doi_service.core.util.general_util import create_landing_page_url
from pds_doi_service.core.util.general_util import get_global_keywords
from pkg_resources import resource_filename


class UpdateActionTestCase(unittest.TestCase):
    _record_service = None
    _web_parser = None
    db_name = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, "data"))
        cls.db_name = join(cls.test_dir, "doi_temp.db")
        cls._update_action = DOICoreActionUpdate(db_name=cls.db_name)
        cls._reserve_action = DOICoreActionReserve(db_name=cls.db_name)
        cls._release_action = DOICoreActionRelease(db_name=cls.db_name)

        cls._record_service = DOIServiceFactory.get_doi_record_service()
        cls._web_parser = DOIServiceFactory.get_web_parser_service()

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

    def setUp(self) -> None:
        """
        Remove previous transaction DB and reinitialize the action objects so
        we don't have to worry about conflicts from reusing PDS ID's/DOI's between
        tests.
        """
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)

        self._update_action = DOICoreActionUpdate(db_name=self.db_name)
        self._reserve_action = DOICoreActionReserve(db_name=self.db_name)
        self._release_action = DOICoreActionRelease(db_name=self.db_name)

    _doi_counter = 1

    def webclient_submit_patch(
        self, payload, url=None, username=None, password=None, method=WEB_METHOD_POST, content_type=CONTENT_TYPE_XML
    ):
        """
        Patch for DOIWebClient.submit_content().

        Allows a request to occur without actually submitting anything to the
        service provider's test server.
        """
        # Parse the DOI's from the input label, add a dummy DOI value,
        # and create the output label
        dois, _ = UpdateActionTestCase._web_parser.parse_dois_from_label(payload, content_type=CONTENT_TYPE_JSON)

        doi = dois[0]

        # Create a new dummy DOI value using the rolling counter
        if not doi.doi:
            doi.doi = f"10.17189/{UpdateActionTestCase._doi_counter}"
            UpdateActionTestCase._doi_counter += 1

        # Assign the other necessary fields to emulate the request
        if method == WEB_METHOD_POST:
            doi.status = DoiStatus.Draft
        else:
            doi.status = DoiStatus.Findable

        doi.date_record_added = datetime.now()
        doi.date_record_updated = datetime.now()

        o_doi_label = UpdateActionTestCase._record_service.create_doi_record(doi, content_type=CONTENT_TYPE_JSON)

        return doi, o_doi_label

    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_update_reserved_doi(self):
        """Test an update of identifier fields on a previously reserved record"""

        # Submit a reserve request to get an entry w/ DOI to update
        kwargs = {
            "input": join(self.input_dir, "pds4_bundle_with_contributors.xml"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        doi_label = self._reserve_action.run(**kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(doi_label)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras::1.0")

        # Update the LIDVID for the record in memory, create a new JSON label,
        # and submit it with the update action
        doi.pds_identifier = "urn:nasa:pds:insight_cameras::2.0"
        doi.date_record_updated = datetime.now()
        json_doi_label = self._record_service.create_doi_record(doi, content_type=CONTENT_TYPE_JSON)

        with tempfile.NamedTemporaryFile(mode="w", dir=self.test_dir, suffix=".json") as outfile:
            outfile.write(json_doi_label)
            outfile.flush()

            update_kwargs = {"input": outfile.name, "node": "img", "submitter": "my_user@my_node.gov", "force": True}

            updated_doi_label = self._update_action.run(**update_kwargs)

        # Parse the updated label and ensure the correct fields were updated
        updated_dois, errors = self._web_parser.parse_dois_from_label(updated_doi_label)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        updated_doi = updated_dois[0]

        # LIDVID should be updated
        self.assertEqual(updated_doi.pds_identifier, "urn:nasa:pds:insight_cameras::2.0")

        # Status should remain "draft" since this DOI was never released
        self.assertEqual(updated_doi.status, DoiStatus.Draft)

        # date_record_added should have been carried over, but date_record_updated should have changed
        self.assertEqual(doi.date_record_added, updated_doi.date_record_added)
        self.assertNotEqual(doi.date_record_updated, updated_doi.date_record_updated)

        # Both new and old PDS identifiers should be present in identifiers section
        identifiers = list(map(lambda identifier: identifier["identifier"], updated_doi.identifiers))
        self.assertIn("urn:nasa:pds:insight_cameras::2.0", identifiers)
        self.assertIn("urn:nasa:pds:insight_cameras::1.0", identifiers)

        # Global keywords should have been assigned, if they weren't already
        self.assertTrue(all(keyword in updated_doi.keywords for keyword in get_global_keywords()))

    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_update_reserved_doi_with_spreadsheet(self):
        """Test an update of identifier fields on records via spreadsheet submission"""
        # Submit a reserve request to get an entry w/ DOI to update
        input_csv = join(self.input_dir, "spreadsheet_with_pds4_identifiers.csv")

        kwargs = {
            "input": input_csv,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        doi_label = self._reserve_action.run(**kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(doi_label)

        self.assertEqual(len(dois), 3)
        self.assertEqual(len(errors), 0)

        for doi in dois:
            self.assertIsNone(doi.site_url)

        # Map the DOI's assigned to the associated PDS identifier
        doi_map = {doi.pds_identifier: doi.doi for doi in dois}

        # Read the submitted CSV, add a DOI column with the DOI's assigned
        # and update the identifier associated with each row
        rows = []

        with open(input_csv, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            for row in reader:
                row["doi"] = doi_map[row["related_resource"]]
                # Add a minor ver to each VID
                row["related_resource"] += ".99"
                row["site_url"] = create_landing_page_url(row["related_resource"], product_type=ProductType.Collection)
                rows.append(row)

        fieldnames.extend(["doi", "site_url"])

        # Write out a new CSV file and submit it to the update action
        with tempfile.NamedTemporaryFile(mode="w", dir=self.test_dir, suffix=".csv") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

            csvfile.flush()

            update_kwargs = {"input": csvfile.name, "node": "img", "submitter": "my_user@my_node.gov", "force": True}

            updated_doi_label = self._update_action.run(**update_kwargs)

        # Parse the updated label and ensure the correct fields were updated
        updated_dois, errors = self._web_parser.parse_dois_from_label(updated_doi_label)

        self.assertEqual(len(dois), 3)
        self.assertEqual(len(errors), 0)

        # Make sure the identifiers were updated as expected, the site url is assigned, and global keywords were added
        for doi in updated_dois:
            self.assertTrue(doi.pds_identifier.endswith(".99"))
            self.assertIsNotNone(doi.site_url)
            self.assertTrue(all(keyword in doi.keywords for keyword in get_global_keywords()))

    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_update_released_doi(self):
        """Test an update of identifier fields on a previously released record"""
        # Submit a release request to get an entry w/ DOI to update
        kwargs = {
            "input": join(self.input_dir, "pds4_bundle_with_doi_and_contributors.xml"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        doi_label = self._release_action.run(**kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(doi_label)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras::1.0")

        # Update the LIDVID for the record in memory, create a new JSON label,
        # and submit it with the update action
        doi.pds_identifier = "urn:nasa:pds:insight_cameras::2.0"
        doi.date_record_updated = datetime.now()
        json_doi_label = self._record_service.create_doi_record(doi, content_type=CONTENT_TYPE_JSON)

        with tempfile.NamedTemporaryFile(mode="w", dir=self.test_dir, suffix=".json") as outfile:
            outfile.write(json_doi_label)
            outfile.flush()

            update_kwargs = {"input": outfile.name, "node": "img", "submitter": "my_user@my_node.gov", "force": False}

            updated_doi_label = self._update_action.run(**update_kwargs)

            # Since we're attempting to move a label from Findable back to Review,
            # we'll get a warning back from the service and no output label
            self.assertIsNone(updated_doi_label)

            # Enable the force flag and try again, should get a label back now
            update_kwargs["force"] = True

            updated_doi_label = self._update_action.run(**update_kwargs)

            self.assertIsNotNone(updated_doi_label)

        # Parse the updated label and ensure the correct fields were updated
        updated_dois, errors = self._web_parser.parse_dois_from_label(updated_doi_label)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        updated_doi = updated_dois[0]

        # LIDVID should be updated
        self.assertEqual(updated_doi.pds_identifier, "urn:nasa:pds:insight_cameras::2.0")

        # Status should have changed from Findable to Review since this DOI was released
        self.assertEqual(updated_doi.status, DoiStatus.Review)

        # date_record_added should have been carried over, but date_record_updated should have changed
        self.assertEqual(doi.date_record_added, updated_doi.date_record_added)
        self.assertNotEqual(doi.date_record_updated, updated_doi.date_record_updated)

        # Both new and old PDS identifiers should be present in identifiers section
        identifiers = list(map(lambda identifier: identifier["identifier"], updated_doi.identifiers))
        self.assertIn("urn:nasa:pds:insight_cameras::2.0", identifiers)
        self.assertIn("urn:nasa:pds:insight_cameras::1.0", identifiers)

        # Global keywords should have been assigned, if they weren't already
        self.assertTrue(all(keyword in updated_doi.keywords for keyword in get_global_keywords()))

    def test_invalid_update_requests(self):
        """Test invalid update requests to ensure exceptions are raised"""

        # Attempting to update a record with no DOI assigned should result in an exception
        update_kwargs = {
            "input": join(self.input_dir, "pds4_bundle_with_contributors.xml"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        with self.assertRaises(CriticalDOIException):
            self._update_action.run(**update_kwargs)

        # This should go for spreadsheet submissions as well
        update_kwargs["input"] = join(self.input_dir, "spreadsheet_with_pds3_identifiers.csv")

        with self.assertRaises(CriticalDOIException):
            self._update_action.run(**update_kwargs)


if __name__ == "__main__":
    unittest.main()
