#!/usr/bin/env python
import os
import tempfile
import unittest
from datetime import datetime
from os.path import abspath
from os.path import join

from pds_doi_service.core.actions.draft import DOICoreActionDraft
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.entities.exceptions import InputFormatException
from pds_doi_service.core.entities.exceptions import WarningDOIException
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pkg_resources import resource_filename


class DraftActionTestCase(unittest.TestCase):
    # Because validation has been added to each action, the force=True is
    # required for each test as the command line is not parsed.

    def setUp(self):
        self.test_dir = resource_filename(__name__, "")
        self.input_dir = abspath(join(self.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))
        self.db_name = join(self.test_dir, "doi_temp.db")
        self._draft_action = DOICoreActionDraft(db_name=self.db_name)
        self._review_action = DOICoreActionRelease(db_name=self.db_name)

        self._record_service = DOIServiceFactory.get_doi_record_service()
        self._web_parser = DOIServiceFactory.get_web_parser_service()

    def tearDown(self):
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)

    def test_local_pds4_bundle(self):
        """Test draft request with a local bundle path"""
        kwargs = {
            "input": join(self.input_dir, "bundle_in_with_doi_and_contributors.xml"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        doi_label = self._draft_action.run(**kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(doi_label)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.editors), 3)
        self.assertEqual(len(doi.keywords), 18)
        self.assertEqual(doi.pds_identifier, "urn:nasa:pds:insight_cameras::1.0")
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.product_type, ProductType.Collection)
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    def test_local_osti_label(self):
        """Test draft action with a local OSTI label"""
        kwargs = {
            "input": join(self.input_dir, "DOI_Release_20200727_from_review.xml"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        doi_label = self._draft_action.run(**kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(doi_label)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(doi.status, DoiStatus.Draft)

    def test_local_unsupported_file(self):
        """Attempt a draft with a unsupported file types"""
        kwargs = {
            "input": join(self.input_dir, "DOI_Reserved_GEO_200318.csv"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        with self.assertRaises(InputFormatException):
            self._draft_action.run(**kwargs)

        kwargs = {
            "input": join(self.input_dir, "DOI_Reserved_GEO_200318.xlsx"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        with self.assertRaises(InputFormatException):
            self._draft_action.run(**kwargs)

    def test_move_lidvid_to_draft(self):
        """Test moving a review record back to draft via its lidvid"""
        # Start by drafting a PDS label
        draft_kwargs = {
            "input": join(self.input_dir, "bundle_in_with_doi_and_contributors.xml"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        draft_doi_label = self._draft_action.run(**draft_kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(draft_doi_label)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(dois[0].status, DoiStatus.Draft)

        # Move the draft to review
        json_doi_label = self._record_service.create_doi_record(dois, content_type="json")

        with tempfile.NamedTemporaryFile(mode="w", dir=self.test_dir, suffix=".json") as outfile:
            outfile.write(json_doi_label)
            outfile.flush()

            review_kwargs = {"input": outfile.name, "node": "img", "submitter": "my_user@my_node.gov", "force": True}

            review_doi_label = self._review_action.run(**review_kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(review_doi_label, content_type="json")

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]
        self.assertEqual(doi.status, DoiStatus.Review)

        # Finally, move the review record back to draft with the lidvid option
        draft_kwargs = {
            "lidvid": doi.pds_identifier,
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        draft_doi_label = self._draft_action.run(**draft_kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(draft_doi_label, content_type="json")

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(dois[0].status, DoiStatus.Draft)

    def test_force_flag(self):
        """
        Ensure the force flag allows bypass of warnings encountered while
        submitting a draft.
        """
        draft_kwargs = {
            "input": join(self.input_dir, "bundle_in_with_doi_and_contributors.xml"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        draft_doi_label = self._draft_action.run(**draft_kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(draft_doi_label)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(dois[0].status, DoiStatus.Draft)

        doi = dois[0]

        # Assign a new DOI and slightly modify the lidvid so we trigger the "duplicate title" warning
        doi.doi = "10.17189/abcdef"
        doi.id = "abcdef"
        doi.pds_identifier += ".1"
        doi.identifiers.clear()
        doi.related_identifiers.clear()

        modified_draft_label = self._record_service.create_doi_record(doi, content_type="json")

        with tempfile.NamedTemporaryFile(mode="w", dir=self.test_dir, suffix=".json") as outfile:
            outfile.write(modified_draft_label)
            outfile.flush()

            draft_kwargs = {"input": outfile.name, "node": "img", "submitter": "my_user@my_node.gov", "force": False}

            # Should get a warning exception containing the duplicate title finding
            with self.assertRaises(WarningDOIException):
                self._draft_action.run(**draft_kwargs)

            # Now try again with the force flag set and we should bypass the
            # warning
            draft_kwargs = {"input": outfile.name, "node": "img", "submitter": "my_user@my_node.gov", "force": True}

            try:
                self._draft_action.run(**draft_kwargs)
            except WarningDOIException:
                self.fail()


if __name__ == "__main__":
    unittest.main()
