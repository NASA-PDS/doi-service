#!/usr/bin/env python

import os
from os.path import abspath, join
import unittest
from unittest.mock import patch

from pkg_resources import resource_filename

import pds_doi_service.core.outputs.osti.osti_web_client
from pds_doi_service.core.actions.reserve import DOICoreActionReserve
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.osti.osti_record import DOIOstiRecord
from pds_doi_service.core.outputs.osti.osti_web_parser import DOIOstiJsonWebParser
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML, CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST


class ReserveActionTestCase(unittest.TestCase):

    def setUp(self):
        # This setUp() function is called for every test.
        self.db_name = 'doi_temp.db'
        self._action = DOICoreActionReserve(db_name=self.db_name)
        self.test_dir = resource_filename(__name__, '')
        self.input_dir = abspath(
            join(self.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, 'input')
        )

    def tearDown(self):
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)

    def webclient_submit_patch(self, payload, url=None, username=None,
                               password=None, method=WEB_METHOD_POST,
                               content_type=CONTENT_TYPE_XML):
        """
        Patch for DOIOstiWebClient.submit_content().

        Allows a non dry-run reserve to occur without actually submitting
        anything to the OSTI test server.
        """
        # Parse the DOI's from the input label, update status to 'reserved',
        # and create the output label
        dois, _ = DOIOstiJsonWebParser.parse_dois_from_label(payload)

        doi = dois[0]

        doi.status = DoiStatus.Reserved

        o_doi_label = DOIOstiRecord().create_doi_record(
            doi, content_type=CONTENT_TYPE_JSON
        )

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
        o_doi_label = self._action.run(**reserve_args)

        dois, errors = DOIOstiJsonWebParser.parse_dois_from_label(o_doi_label)

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
        dry run flag to avoid submission to OSTI.
        """
        reserve_args = {
            'input': join(self.input_dir,
                          'DOI_Reserved_GEO_200318_with_corrected_identifier.xlsx'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'dry_run': True,
            'force': True
        }

        self.run_reserve_test(
            reserve_args, expected_dois=3, expected_status=DoiStatus.Reserved_not_submitted
        )

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient,
        'submit_content', webclient_submit_patch)
    def test_reserve_xlsx_and_submit(self):
        """
        Test Reserve action with a local excel spreadsheet, submitting the
        result to OSTI.
        """
        reserve_args = {
            'input': join(self.input_dir,
                          'DOI_Reserved_GEO_200318_with_corrected_identifier.xlsx'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'dry_run': False,
            'force': True
        }

        self.run_reserve_test(
            reserve_args, expected_dois=3, expected_status=DoiStatus.Reserved
        )

    def test_reserve_csv_dry_run(self):
        """
        Test Reserve action with a local CSV file, using the dry run flag
        to avoid submission to OSTI.
        """
        reserve_args = {
            'input': join(self.input_dir, 'DOI_Reserved_GEO_200318.csv'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'dry_run': True,
            'force': True
        }

        self.run_reserve_test(
            reserve_args, expected_dois=3, expected_status=DoiStatus.Reserved_not_submitted
        )

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient,
        'submit_content', webclient_submit_patch)
    def test_reserve_csv_and_submit(self):
        """
        Test Reserve action with a local CSV file, submitting the result to OSTI.
        """
        reserve_args = {
            'input': join(self.input_dir, 'DOI_Reserved_GEO_200318.csv'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'dry_run': False,
            'force': True
        }

        self.run_reserve_test(
            reserve_args, expected_dois=3, expected_status=DoiStatus.Reserved
        )

    def test_reserve_json_dry_run(self):
        """
        Test Reserve action with a local JSON file, using the dry run flag
        to avoid submission to OSTI.
        """
        reserve_args = {
            'input': join(self.input_dir, 'DOI_Release_20210216_from_reserve.json'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'dry_run': True,
            'force': True
        }

        self.run_reserve_test(
            reserve_args, expected_dois=1, expected_status=DoiStatus.Reserved_not_submitted
        )

    @patch.object(
        pds_doi_service.core.outputs.osti.DOIOstiWebClient,
        'submit_content', webclient_submit_patch)
    def test_reserve_json_and_submit(self):
        """
        Test Reserve action with a local JSON file, submitting the result to OSTI.
        """
        reserve_args = {
            'input': join(self.input_dir, 'DOI_Release_20210216_from_reserve.json'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'dry_run': False,
            'force': True
        }

        self.run_reserve_test(
            reserve_args, expected_dois=1, expected_status=DoiStatus.Reserved
        )


if __name__ == '__main__':
    unittest.main()
