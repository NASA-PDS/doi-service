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
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.exceptions import WarningDOIException
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

    def test_local_dir_one_file(self):
        """Test draft request with local dir containing one file"""
        kwargs = {
            "input": join(self.input_dir, "draft_dir_one_file"),
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
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:insight_cameras::1.0")
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    def test_local_dir_two_files(self):
        """Test draft request with local dir containing two files"""
        kwargs = {
            "input": join(self.input_dir, "draft_dir_two_files"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        doi_label = self._draft_action.run(**kwargs)

        dois, errors = self._web_parser.parse_dois_from_label(doi_label)

        self.assertEqual(len(dois), 2)
        self.assertEqual(len(errors), 0)

        for doi in dois:
            self.assertEqual(len(doi.authors), 4)
            self.assertEqual(len(doi.keywords), 18)
            self.assertEqual(doi.status, DoiStatus.Draft)
            self.assertEqual(doi.product_type, ProductType.Dataset)
            self.assertIsInstance(doi.publication_date, datetime)
            self.assertIsInstance(doi.date_record_added, datetime)
            self.assertTrue(doi.related_identifier.startswith("urn:nasa:pds:insight_cameras::1"))
            self.assertTrue(doi.title.startswith("InSight Cameras Bundle 1."))

            # Make sure for the "bundle_in_with_contributors.xml" file, we
            # parsed the editors
            if doi.related_identifier == "urn:nasa:pds:insight_cameras::1.0":
                self.assertEqual(len(doi.editors), 3)
            # For "bundle_in.xml", there should be no editors
            else:
                self.assertEqual(len(doi.editors), 0)

    def test_local_pds4_bundle(self):
        """Test draft request with a local bundle path"""
        kwargs = {
            "input": join(self.input_dir, "bundle_in_with_contributors.xml"),
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
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:insight_cameras::1.0")
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    def test_remote_pds4_bundle(self):
        """Test draft request with a remote bundle URL"""
        kwargs = {
            "input": "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml",
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
        self.assertEqual(len(doi.keywords), 18)
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:insight_cameras::1.0")
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.product_type, ProductType.Dataset)
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

    def test_remote_collection(self):
        """Test draft request with a remote collection URL"""
        kwargs = {
            "input": "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml",
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
        self.assertEqual(len(doi.keywords), 12)
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:insight_cameras:data::1.0")
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    def test_remote_browse_collection(self):
        """Test draft request with a remote browse collection URL"""
        kwargs = {
            "input": "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml",
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
        self.assertEqual(len(doi.keywords), 12)
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:insight_cameras:browse::1.0")
        self.assertEqual(doi.description, "Collection of BROWSE products.")
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    def test_remote_calibration_collection(self):
        """Test draft request with remote calibration collection URL"""
        kwargs = {
            "input": "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml",
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
        self.assertEqual(len(doi.keywords), 14)
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:insight_cameras:calibration::1.0")
        self.assertEqual(doi.description, "Collection of CALIBRATION files/products to include in the archive.")
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    def test_remote_document_collection(self):
        """Test draft request with remote document collection URL"""
        kwargs = {
            "input": "https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml",
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
        self.assertEqual(len(doi.keywords), 12)
        self.assertEqual(doi.related_identifier, "urn:nasa:pds:insight_cameras:document::1.0")
        self.assertEqual(doi.description, "Collection of DOCUMENT products.")
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertIsInstance(doi.date_record_added, datetime)

    def test_move_lidvid_to_draft(self):
        """Test moving a review record back to draft via its lidvid"""
        # Start by drafting a PDS label
        draft_kwargs = {
            "input": join(self.input_dir, "bundle_in_with_contributors.xml"),
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
            "lidvid": doi.related_identifier,
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
            "input": join(self.input_dir, "bundle_in_with_contributors.xml"),
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

        # Slightly modify the lidvid so we trigger the "duplicate title" warning
        doi.related_identifier += ".1"

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
