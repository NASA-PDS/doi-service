# coding: utf-8

from __future__ import absolute_import

import os
from os.path import abspath, dirname, exists, join

from pds_doi_api.models.doi_record import DoiRecord
from pds_doi_api.models.doi_summary import DoiSummary
from pds_doi_api.test import BaseTestCase


class TestDoisController(BaseTestCase):
    """DoisController integration test stubs"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = abspath(dirname(__file__))
        cls.test_data_dir = join(cls.test_dir, 'data')

    def setUp(self):
        # Set testing mode to True so endpoints know to look for a custom
        # database instance to work with
        self.app.config['TESTING'] = True

    def test_get_dois(self):
        """Test case for get_dois"""
        test_db = join(self.test_data_dir, 'test.db')

        # Start with a empty query to fetch all available records
        query_string = [('db_name', test_db)]

        response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                    method='GET',
                                    query_string=query_string)

        self.assert200(
            response,
            'Response body is : ' + response.data.decode('utf-8')
        )

        records = response.json

        # Test database should contain 2 records (matching those that are
        # submitted in test_post_dois)
        self.assertEqual(len(records), 2)

        # Now use a query string to ensure we can get specific records back
        query_string = [('node', 'eng'),
                        ('db_name', test_db)]

        response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                    method='GET',
                                    query_string=query_string)

        self.assert200(
            response,
            'Response body is : ' + response.data.decode('utf-8')
        )

        # Should only get one of the records back
        records = response.json
        self.assertEqual(len(records), 1)

        # Reformat JSON result into a DoiSummary object so we can check fields
        summary = DoiSummary.from_dict(records[0])

        self.assertEqual(summary.submitter, 'eng-submitter@jpl.nasa.gov')
        self.assertEqual(summary.lid, 'urn:nasa:pds:insight_cameras')
        self.assertEqual(summary.vid, '1.1')
        self.assertEqual(summary.status, 'Draft')

    def test_post_dois(self):
        """Test case for post_dois"""
        # Use a non-existing database so a new one is created from scratch
        test_db = join(self.test_data_dir, 'new.db')

        # We can use a file system path since were working with a local server
        input_bundle = join(self.test_data_dir, 'bundle_in.xml')

        try:
            # Start by submitting a draft request
            query_string = [('action', 'draft'),
                            ('submitter', 'eng-submitter@jpl.nasa.gov'),
                            ('node', 'eng'),
                            ('url', input_bundle),
                            ('db_name', test_db)]

            draft_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                              method='POST',
                                              query_string=query_string)

            self.assert200(
                draft_response,
                'Response body is : ' + draft_response.data.decode('utf-8')
            )

            # Recreate a DoiRecord from the response JSON and examine the
            # fields
            draft_record = DoiRecord.from_dict(draft_response.json[0])

            self.assertEqual(draft_record.submitter, 'eng-submitter@jpl.nasa.gov')
            self.assertEqual(draft_record.lid, 'urn:nasa:pds:insight_cameras')
            self.assertEqual(draft_record.vid, '1.1')
            # Note we get Pending back from the parsed label, however
            # the object sent to transaction database has 'Draft' status
            self.assertEqual(draft_record.status, 'Pending')

            # Try to move draft status to reserve_not_submitted, without the
            # force flag this should return an Invalid Argument code
            query_string = [('action', 'reserve'),
                            ('submitter', 'eng-submitter@jpl.nasa.gov'),
                            ('node', 'eng'),
                            ('url', input_bundle),
                            ('db_name', test_db)]

            draft_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                              method='POST',
                                              query_string=query_string)

            self.assert400(
                draft_response,
                'Response body is : ' + draft_response.data.decode('utf-8')
            )

            input_bundle = join(self.test_data_dir, 'bundle_in_with_contributors.xml')

            # Submit a new bundle in reserve (not submitted) status
            query_string = [('action', 'reserve'),
                            ('submitter', 'img-submitter@jpl.nasa.gov'),
                            ('node', 'img'),
                            ('url', input_bundle),
                            ('db_name', test_db)]

            reserve_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                                method='POST',
                                                query_string=query_string)

            self.assert200(
                reserve_response,
                'Response body is : ' + draft_response.data.decode('utf-8')
            )

            # Recreate a DoiRecord from the response JSON and examine the
            # fields
            reserve_record = DoiRecord.from_dict(reserve_response.json[0])

            self.assertEqual(reserve_record.submitter, 'img-submitter@jpl.nasa.gov')
            self.assertEqual(reserve_record.lid, 'urn:nasa:pds:insight_cameras')
            self.assertEqual(reserve_record.vid, '1.0')
            self.assertEqual(reserve_record.status, 'reserved_not_submitted')

            # Now test with an unknown action, should get Invalid Argument
            query_string = [('action', 'unknown'),
                            ('submitter', 'img-submitter@jpl.nasa.gov'),
                            ('node', 'img'),
                            ('url', input_bundle),
                            ('db_name', test_db)]

            error_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                              method='POST',
                                              query_string=query_string)

            self.assert400(
                error_response,
                'Response body is : ' + draft_response.data.decode('utf-8')
            )
        finally:
            # Remove test DB so a new one is created each time
            if exists(test_db):
                os.unlink(test_db)

    def test_get_doi_from_id(self):
        """Test case for get_doi_from_id"""
        response = self.client.open(
            '/PDS_APIs/pds_doi_api/0.1/dois/{doi_prefix}/{doi_suffix}'
            .format(doi_prefix='doi_prefix_example', doi_suffix='doi_suffix_example'),
            method='GET'
        )
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_post_release_doi(self):
        """Test case for post_release_doi"""
        response = self.client.open(
            '/PDS_APIs/pds_doi_api/0.1/dois/{doi_prefix}/{doi_suffix}/release'
            .format(doi_prefix='doi_prefix_example', doi_suffix='doi_suffix_example'),
            method='POST')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_doi_from_id(self):
        """Test case for put_doi_from_id"""
        query_string = [('submitter', 'submitter_example'),
                        ('node', 'node_example'),
                        ('url', 'url_example')]
        response = self.client.open(
            '/PDS_APIs/pds_doi_api/0.1/dois/{doi_prefix}/{doi_suffix}'
            .format(doi_prefix='doi_prefix_example', doi_suffix='doi_suffix_example'),
            method='PUT',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
