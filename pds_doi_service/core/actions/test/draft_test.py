#!/usr/bin/env python

import os
from os.path import abspath, dirname, join
import unittest

from pds_doi_service.core.actions.draft import DOICoreActionDraft
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser


class DraftActionTestCase(unittest.TestCase):
    # Because validation has been added to each action, the force=True is
    # required for each test as the command line is not parsed.

    @classmethod
    def setUpClass(cls):
        cls.test_dir = abspath(dirname(__file__))
        cls.input_dir = abspath(
            join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, 'input')
        )
        cls.db_name = 'doi_temp.db'
        cls._action = DOICoreActionDraft(db_name=cls.db_name)

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

    def test_local_dir_one_file(self):
        """Test draft request with local dir containing one file"""
        kwargs = {
            'input': join(self.input_dir, 'draft_dir_one_file'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        osti_doi = self._action.run(**kwargs)

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

        osti_doi = self._action.run(**kwargs)

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

        osti_doi = self._action.run(**kwargs)

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

        osti_doi = self._action.run(**kwargs)

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

        osti_doi = self._action.run(**kwargs)

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

        osti_doi = self._action.run(**kwargs)

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

        osti_doi = self._action.run(**kwargs)

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

        osti_doi = self._action.run(**kwargs)

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


if __name__ == '__main__':
    unittest.main()
