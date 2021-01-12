#!/usr/bin/env python

import os
from os.path import abspath, dirname, join
import unittest
from unittest.mock import patch

import pds_doi_service.core.outputs.osti_web_client
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class MyTestCase(unittest.TestCase):
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
            logger.info(f"Removed test artifact database file {cls.db_name}")

        # Because validation has been added to each action, the force=True is
        # required as the command line is not parsed for unit test.
        cls._action = DOICoreActionRelease(db_name=cls.db_name)
        logger.info(f"Instantiated DOICoreActionRelease with database file {cls.db_name}")

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)
            logger.info(f"Removed test artifact database file {cls.db_name}")

    def webclient_submit_patch(self, payload, i_url=None,
                               i_username=None, i_password=None):
        """
        Patch for DOIOstiWebClient.webclient_submit_existing_content().

        Allows a no-review release to occur without actually submitting
        anything to the OSTI test server.
        """
        # Just return the parsed DOI's from the input label, along with the
        # input label itself
        dois, _ = DOIOstiWebParser().response_get_parse_osti_xml(payload)

        return dois, payload.decode('utf-8')

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

        dois, _ = DOIOstiWebParser().response_get_parse_osti_xml(
            bytes(o_doi_label, encoding='utf-8')
        )

        # Should get three DOI's back that have all been marked as ready for review
        self.assertEqual(len(dois), 3)
        self.assertTrue(all([doi.status == DoiStatus.Review for doi in dois]))

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

        dois, _ = DOIOstiWebParser().response_get_parse_osti_xml(
            bytes(o_doi_label, encoding='utf-8')
        )

        # Should get three DOI's back that have all been marked as pending
        # registration
        self.assertEqual(len(dois), 3)
        self.assertTrue(all([doi.status == DoiStatus.Pending for doi in dois]))

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

        dois, _ = DOIOstiWebParser().response_get_parse_osti_xml(
            bytes(o_doi_label, encoding='utf-8')
        )

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

        dois, _ = DOIOstiWebParser().response_get_parse_osti_xml(
            bytes(o_doi_label, encoding='utf-8')
        )

        # Should get one DOI back with status 'pending'
        self.assertEqual(len(dois), 1)
        self.assertEqual(dois[0].status, DoiStatus.Pending)

if __name__ == '__main__':
    unittest.main()
