#!/usr/bin/env python

import os
from os.path import abspath, dirname, join
import unittest
from unittest.mock import patch

import pds_doi_service.core.outputs.osti_web_client
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.osti import DOIOutputOsti, CONTENT_TYPE_JSON, CONTENT_TYPE_XML
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser


class ReleaseActionTestCase(unittest.TestCase):
    # As of 07/13/2020, OSTI has the below ID records (['22831','22832','22833'])
    # in their test server so this test will work to demonstrate that they have
    # new status of 'Pending' or 'Registered'. If for some reason the server has
    # been wiped clean, this unit test will still run but won't show any status
    # changed to 'Registered'.

    @classmethod
    def setUpClass(cls):
        cls.test_dir = abspath(dirname(__file__))
        cls.input_dir = abspath(
            join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, 'input')
        )
        cls.db_name = 'doi_temp.db'

        # Remove db_name if exist to have a fresh start otherwise exception will be
        # raised about using existing lidvid.
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

        # Because validation has been added to each action, the force=True is
        # required as the command line is not parsed for unit test.
        cls._action = DOICoreActionRelease(db_name=cls.db_name)

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

    def webclient_submit_patch(self, payload, i_url=None,
                               i_username=None, i_password=None,
                               content_type=CONTENT_TYPE_XML):
        """
        Patch for DOIOstiWebClient.webclient_submit_existing_content().

        Allows a no-review release to occur without actually submitting
        anything to the OSTI test server.
        """
        # Parse the DOI's from the input label, update status to 'pending',
        # and create the output label
        dois, _ = DOIOstiWebParser().parse_osti_response_json(payload)

        for doi in dois:
            doi.status = DoiStatus.Pending

        o_doi_label = DOIOutputOsti().create_osti_doi_record(
            dois, content_type=CONTENT_TYPE_JSON
        )

        return dois, o_doi_label

    def test_reserve_release_to_review(self):
        """Test release to review status with a reserved DOI entry"""

        release_args = {
            'input': join(self.input_dir, 'DOI_Release_20200727_from_reserve.xml'),
            'node': 'img',
            'submitter': 'img-submitter@jpl.nasa.gov',
            'force': True,
            'no_review': False
        }

        o_doi_label = self._action.run(**release_args)

        dois, _ = DOIOstiWebParser().parse_osti_response_json(o_doi_label)

        # Should get one DOI back that has been marked as ready for review
        self.assertEqual(len(dois), 1)
        self.assertTrue(dois[0].status == DoiStatus.Review)

    @patch.object(
        pds_doi_service.core.outputs.osti_web_client.DOIOstiWebClient,
        'webclient_submit_existing_content', webclient_submit_patch)
    def test_reserve_release_to_osti(self):
        """Test release directly to OSTI with a reserved DOI entry"""

        release_args = {
            'input': join(self.input_dir, 'DOI_Release_20200727_from_reserve.xml'),
            'node': 'img',
            'submitter': 'Qui.T.Chau@jpl.nasa.gov',
            'force': True,
            'no_review': True
        }

        o_doi_label = self._action.run(**release_args)

        dois, _ = DOIOstiWebParser().parse_osti_response_json(o_doi_label)

        # Should get one DOI back that has been marked as pending registration
        self.assertEqual(len(dois), 1)
        self.assertTrue(dois[0].status == DoiStatus.Pending)

    def test_draft_release_to_review(self):
        """Test release to review status with a draft DOI entry"""

        release_args = {
            'input': join(self.input_dir, 'DOI_Release_20200727_from_draft.xml'),
            'node': 'img',
            'submitter': 'img-submitter@jpl.nasa.gov',
            'force': True,
            'no_review': False
        }

        o_doi_label = self._action.run(**release_args)

        dois, _ = DOIOstiWebParser().parse_osti_response_json(o_doi_label)

        # Should get one DOI back with status 'review'
        self.assertEqual(len(dois), 1)
        self.assertEqual(dois[0].status, DoiStatus.Review)

    @patch.object(
        pds_doi_service.core.outputs.osti_web_client.DOIOstiWebClient,
        'webclient_submit_existing_content', webclient_submit_patch)
    def test_draft_release_to_osti(self):
        """Test release directly to OSTI with a draft DOI entry"""

        release_args = {
            'input': join(self.input_dir, 'DOI_Release_20200727_from_draft.xml'),
            'node': 'img',
            'submitter': 'Qui.T.Chau@jpl.nasa.gov',
            'force': True,
            'no_review': True
        }

        o_doi_label = self._action.run(**release_args)

        dois, _ = DOIOstiWebParser().parse_osti_response_json(o_doi_label)

        # Should get one DOI back with status 'pending'
        self.assertEqual(len(dois), 1)
        self.assertEqual(dois[0].status, DoiStatus.Pending)

    def test_review_release_to_review(self):
        """
        Test release to review status with a review DOI entry

        This is essentially a no-op, but it should work regardless
        """

        release_args = {
            'input': join(self.input_dir, 'DOI_Release_20200727_from_review.xml'),
            'node': 'img',
            'submitter': 'img-submitter@jpl.nasa.gov',
            'force': True,
            'no_review': False
        }

        o_doi_label = self._action.run(**release_args)

        dois, _ = DOIOstiWebParser().parse_osti_response_json(o_doi_label)

        # Should get one DOI back with status 'review'
        self.assertEqual(len(dois), 1)
        self.assertEqual(dois[0].status, DoiStatus.Review)

    @patch.object(
        pds_doi_service.core.outputs.osti_web_client.DOIOstiWebClient,
        'webclient_submit_existing_content', webclient_submit_patch)
    def test_review_release_to_osti(self):
        """Test release directly to OSTI with a review DOI entry"""

        release_args = {
            'input': join(self.input_dir, 'DOI_Release_20200727_from_review.xml'),
            'node': 'img',
            'submitter': 'img-submitter@jpl.nasa.gov',
            'force': True,
            'no_review': True
        }

        o_doi_label = self._action.run(**release_args)

        dois, _ = DOIOstiWebParser().parse_osti_response_json(o_doi_label)

        # Should get one DOI back with status 'pending'
        self.assertEqual(len(dois), 1)
        self.assertEqual(dois[0].status, DoiStatus.Pending)


if __name__ == '__main__':
    unittest.main()
