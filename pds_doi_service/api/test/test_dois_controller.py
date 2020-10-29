# coding: utf-8

from __future__ import absolute_import

from datetime import datetime
import os
from os.path import abspath, dirname, exists, join

from pds_doi_service.api.encoder import JSONEncoder
from pds_doi_service.api.models import (DoiRecord, DoiSummary,
                                        LabelsPayload, LabelPayload)
from pds_doi_service.api.test import BaseTestCase


class TestDoisController(BaseTestCase):
    """DoisController integration test stubs"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = abspath(dirname(__file__))
        cls.test_data_dir = join(cls.test_dir, 'data')

        # Path to a temporary database to re-instantiate for every test
        cls.temp_db = join(cls.test_data_dir, 'temp.db')

    def setUp(self):
        # Set testing mode to True so endpoints know to look for a custom
        # database instance to work with
        self.app.config['TESTING'] = True

    def tearDown(self):
        # Remove the temp DB so a new one is created before each test
        if exists(self.temp_db):
            os.unlink(self.temp_db)

    def test_get_dois(self):
        """Test case for get_dois"""
        # For these tests, use a pre-existing database with some canned
        # entries to query for
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

    def test_post_dois_draft_w_url(self):
        """Test a draft POST with url input"""
        # We can use a file system path since were working with a local server
        input_bundle = join(self.test_data_dir, 'bundle_in.xml')

        # Start by submitting a draft request
        query_string = [('action', 'draft'),
                        ('submitter', 'eng-submitter@jpl.nasa.gov'),
                        ('node', 'eng'),
                        ('url', input_bundle),
                        ('db_name', self.temp_db)]

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

    def test_post_dois_draft_w_payload(self):
        """Test a draft POST with requestBody input"""
        input_bundle = join(self.test_data_dir, 'bundle_in.xml')

        with open(input_bundle, 'rb') as infile:
            body = infile.read()

        query_string = [('action', 'draft'),
                        ('submitter', 'eng-submitter@jpl.nasa.gov'),
                        ('node', 'eng'),
                        ('db_name', self.temp_db)]

        draft_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                          method='POST',
                                          data=body,
                                          content_type='application/xml',
                                          query_string=query_string)

        self.assert200(
            draft_response,
            'Response body is : ' + draft_response.data.decode('utf-8')
        )

        # Recreate a DoiRecord from the response JSON and examine the
        # fields
        draft_record = DoiRecord.from_dict(draft_response.json[0])

    def test_post_dois_reserve(self):
        """Test dry-run reserve POST"""
        # Submit a new bundle in reserve (not submitted) status
        body = LabelsPayload(
            [LabelPayload(status='Reserved',
                          title='Laboratory Shocked Feldspars Bundle',
                          publication_date=datetime.now(),
                          product_type_specific='PDS4 Bundle',
                          author_last_name='Johnson',
                          author_first_name='J. R.',
                          related_resource='urn:nasa:pds:lab_shocked_feldspars')]
        )

        query_string = [('action', 'reserve'),
                        ('submitter', 'img-submitter@jpl.nasa.gov'),
                        ('node', 'img'),
                        ('db_name', self.temp_db)]

        reserve_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                            method='POST',
                                            data=JSONEncoder().encode(body),
                                            content_type='application/json',
                                            query_string=query_string)

        self.assert200(
            reserve_response,
            'Response body is : ' + reserve_response.data.decode('utf-8')
        )

        # Recreate a DoiRecord from the response JSON and examine the
        # fields
        reserve_record = DoiRecord.from_dict(reserve_response.json[0])

        self.assertEqual(reserve_record.submitter, 'img-submitter@jpl.nasa.gov')
        self.assertEqual(reserve_record.lid, 'urn:nasa:pds:lab_shocked_feldspars')
        self.assertEqual(reserve_record.status, 'reserved_not_submitted')

    def test_post_dois_invalid_draft_to_reserve(self):
        # We can use a file system path since were working with a local server
        input_bundle = join(self.test_data_dir, 'bundle_in.xml')

        # Start by submitting a draft request
        query_string = [('action', 'draft'),
                        ('submitter', 'eng-submitter@jpl.nasa.gov'),
                        ('node', 'eng'),
                        ('url', input_bundle),
                        ('db_name', self.temp_db)]

        reserve_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                            method='POST',
                                            query_string=query_string)

        self.assert200(
            reserve_response,
            'Response body is : ' + reserve_response.data.decode('utf-8')
        )

        # Try to move draft status to reserve_not_submitted, without the
        # force flag this should return an Invalid Argument code
        body = LabelsPayload(
            [LabelPayload(status='Reserved',
                          title='Insight Cameras Bundle',
                          publication_date=datetime.now(),
                          product_type_specific='PDS4 Bundle',
                          author_last_name='Johnson',
                          author_first_name='J. R.',
                          related_resource='urn:nasa:pds:insight_cameras::1.1')]
        )

        query_string = [('action', 'reserve'),
                        ('submitter', 'eng-submitter@jpl.nasa.gov'),
                        ('node', 'eng'),
                        ('db_name', self.temp_db)]

        reserve_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                            method='POST',
                                            data=JSONEncoder().encode(body),
                                            content_type='application/json',
                                            query_string=query_string)

        self.assert400(
            reserve_response,
            'Response body is : ' + reserve_response.data.decode('utf-8')
        )

    def test_post_dois_invalid_requests(self):
        """Test invalid POST requests"""

        # Test with an unknown action, should get Invalid Argument
        query_string = [('action', 'unknown'),
                        ('submitter', 'img-submitter@jpl.nasa.gov'),
                        ('node', 'img'),
                        ('db_name', self.temp_db)]

        error_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                          method='POST',
                                          query_string=query_string)

        self.assert400(
            error_response,
            'Response body is : ' + error_response.data.decode('utf-8')
        )

        # Test draft action with no url or requestBody input
        query_string = [('action', 'draft'),
                        ('submitter', 'img-submitter@jpl.nasa.gov'),
                        ('node', 'img'),
                        ('db_name', self.temp_db)]

        error_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                          method='POST',
                                          query_string=query_string)

        self.assert400(
            error_response,
            'Response body is : ' + error_response.data.decode('utf-8')
        )

        # Test reserve action with a url instead of a requestBody
        input_bundle = join(self.test_data_dir, 'bundle_in.xml')

        query_string = [('action', 'reserve'),
                        ('submitter', 'eng-submitter@jpl.nasa.gov'),
                        ('node', 'eng'),
                        ('url', input_bundle),
                        ('db_name', self.temp_db)]

        error_response = self.client.open('/PDS_APIs/pds_doi_api/0.1/dois',
                                          method='POST',
                                          query_string=query_string)

        self.assert400(
            error_response,
            'Response body is : ' + error_response.data.decode('utf-8')
        )

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
