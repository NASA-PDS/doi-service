#!/usr/bin/env python

import os
from os.path import abspath, dirname, join
import unittest
import tempfile

from pds_doi_service.core.actions.draft import DOICoreActionDraft
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser


class DraftActionTestCase(unittest.TestCase):
    # Because validation has been added to each action, the force=True is
    # required for each test as the command line is not parsed.

    def setUp(self):
        self.test_dir = abspath(dirname(__file__))
        self.input_dir = abspath(
            join(self.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, 'input')
        )
        self.db_name = join(self.test_dir, 'doi_temp.db')
        self._draft_action = DOICoreActionDraft(db_name=self.db_name)
        self._review_action = DOICoreActionRelease(db_name=self.db_name)

    def tearDown(self):
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)

    def test_local_dir_one_file(self):
        """Test draft request with local dir containing one file"""
        kwargs = {
            'input': join(self.input_dir, 'draft_dir_one_file'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        osti_doi = self._draft_action.run(**kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(osti_doi)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.contributors), 1)
        self.assertEqual(len(doi.keywords), 18)
        self.assertEqual(doi.related_identifier,
                         'urn:nasa:pds:insight_cameras::1.0')
        self.assertEqual(doi.status, DoiStatus.Pending)

    def test_local_dir_two_files(self):
        """Test draft request with local dir containing two files"""
        kwargs = {
            'input': join(self.input_dir, 'draft_dir_two_files'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        osti_doi = self._draft_action.run(**kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(osti_doi)

        self.assertEqual(len(dois), 2)
        self.assertEqual(len(errors), 0)

        for doi in dois:
            self.assertEqual(len(doi.authors), 4)
            self.assertEqual(len(doi.contributors), 1)
            self.assertEqual(len(doi.keywords), 18)
            self.assertEqual(doi.status, DoiStatus.Pending)

        self.assertEqual(dois[0].related_identifier,
                         'urn:nasa:pds:insight_cameras::1.1')
        self.assertEqual(dois[1].related_identifier,
                         'urn:nasa:pds:insight_cameras::1.0')

    def test_local_bundle(self):
        """Test draft request with a local bundle path"""
        kwargs = {
            'input': join(self.input_dir, 'bundle_in_with_contributors.xml'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        osti_doi = self._draft_action.run(**kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(osti_doi)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.contributors), 1)
        self.assertEqual(len(doi.keywords), 18)
        self.assertEqual(doi.related_identifier,
                         'urn:nasa:pds:insight_cameras::1.0')
        self.assertEqual(doi.status, DoiStatus.Pending)

    def test_remote_bundle(self):
        """Test draft request with a remote bundle URL"""
        kwargs = {
            'input': 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml',
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        osti_doi = self._draft_action.run(**kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(osti_doi)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.contributors), 1)
        self.assertEqual(len(doi.keywords), 18)
        self.assertEqual(doi.related_identifier,
                         'urn:nasa:pds:insight_cameras::1.0')
        self.assertEqual(doi.status, DoiStatus.Pending)

    def test_remote_collection(self):
        """Test draft request with a remote collection URL"""
        kwargs = {
            'input': 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml',
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        osti_doi = self._draft_action.run(**kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(osti_doi)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.contributors), 1)
        self.assertEqual(len(doi.keywords), 12)
        self.assertEqual(doi.related_identifier,
                         'urn:nasa:pds:insight_cameras:data::1.0')
        self.assertEqual(doi.status, DoiStatus.Pending)

    def test_remote_browse_collection(self):
        """Test draft request with a remote browse collection URL"""
        kwargs = {
            'input': 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml',
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        osti_doi = self._draft_action.run(**kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(osti_doi)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.contributors), 1)
        self.assertEqual(len(doi.keywords), 12)
        self.assertEqual(doi.related_identifier,
                         'urn:nasa:pds:insight_cameras:browse::1.0')
        self.assertEqual(doi.description,
                         'Collection of BROWSE products.')
        self.assertEqual(doi.status, DoiStatus.Pending)

    def test_remote_calibration_collection(self):
        """Test draft request with remote calibration collection URL"""
        kwargs = {
            'input': 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml',
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        osti_doi = self._draft_action.run(**kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(osti_doi)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.contributors), 1)
        self.assertEqual(len(doi.keywords), 14)
        self.assertEqual(doi.related_identifier,
                         'urn:nasa:pds:insight_cameras:calibration::1.0')
        self.assertEqual(doi.description,
                         'Collection of CALIBRATION files/products to include in the archive.')
        self.assertEqual(doi.status, DoiStatus.Pending)

    def test_remote_document_collection(self):
        """Test draft request with remote document collection URL"""
        kwargs = {
            'input': 'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml',
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        osti_doi = self._draft_action.run(**kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(osti_doi)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self.assertEqual(len(doi.authors), 4)
        self.assertEqual(len(doi.contributors), 1)
        self.assertEqual(len(doi.keywords), 12)
        self.assertEqual(doi.related_identifier,
                         'urn:nasa:pds:insight_cameras:document::1.0')
        self.assertEqual(doi.description,
                         'Collection of DOCUMENT products.')
        self.assertEqual(doi.status, DoiStatus.Pending)

    def test_move_lidvid_to_draft(self):
        """Test moving a review record back to draft via its lidvid"""
        # Start by drafting a PDS label
        draft_kwargs = {
            'input': join(self.input_dir, 'bundle_in_with_contributors.xml'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        draft_osti_doi = self._draft_action.run(**draft_kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(draft_osti_doi)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(dois[0].status, DoiStatus.Pending)

        # Move the draft to review
        with tempfile.NamedTemporaryFile(mode='w', dir=self.test_dir, suffix='.xml') as xml_file:
            xml_file.write(draft_osti_doi)
            xml_file.flush()

            review_kwargs = {
                'input': xml_file.name,
                'node': 'img',
                'submitter': 'my_user@my_node.gov',
                'force': True
            }

            review_osti_doi = self._review_action.run(**review_kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(
            bytes(review_osti_doi, encoding='utf-8')
        )

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]
        self.assertEqual(doi.status, DoiStatus.Review)

        # Finally, move the review record back to draft with the lidvid option
        draft_kwargs = {
            'lidvid': doi.related_identifier,
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        draft_osti_doi = self._draft_action.run(**draft_kwargs)

        dois, errors = DOIOstiWebParser.response_get_parse_osti_xml(
            bytes(draft_osti_doi, encoding='utf-8')
        )

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(dois[0].status, DoiStatus.Pending)


if __name__ == '__main__':
    unittest.main()
