#!/usr/bin/env python

import datetime
import os
from os.path import exists
import unittest

from pkg_resources import resource_filename

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiStatus, ProductType
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOIDatabaseTest(unittest.TestCase):
    """Unit tests for the doi_database.py module"""

    def setUp(self):
        self._db_name = resource_filename(__name__, 'doi_temp.db')

        # Delete temporary db if it already exists, this can occur when tests
        # are terminated before completion (during debugging for example)
        if exists(self._db_name):
            os.remove(self._db_name)

        self._doi_database = DOIDataBase('doi_temp.db')

    def tearDown(self):
        if exists(self._db_name):
            os.remove(self._db_name)

    def test_select_latest_rows(self):
        """Test selecting of latest rows from the transaction database"""
        # Set up a sample db entry
        lid = 'urn:nasa:pds:lab_shocked_feldspars'
        vid = '1.0'
        transaction_key = 'img/2020-06-15T18:42:45.653317'
        doi = '10.17189/21729'
        transaction_date = datetime.datetime.now()
        status = DoiStatus.Unknown
        title = 'Laboratory Shocked Feldspars Bundle'
        product_type = ProductType.Collection
        product_type_specific = 'PDS4 Collection'
        submitter = 'img-submitter@jpl.nasa.gov'
        discipline_node = 'img'

        # Insert a row in the 'doi' table
        self._doi_database.write_doi_info_to_database(
            lid, vid, transaction_key, doi, transaction_date, status,
            title, product_type, product_type_specific, submitter, discipline_node
        )

        # Select the row we just added
        # The type of o_query_result should be JSON and a list of 1
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={'doi': [doi]}
        )

        # Reformat results to a dictionary to test with
        query_result = dict(zip(o_query_result[0], o_query_result[1][0]))

        # Ensure we got back everything we just put in
        self.assertEqual(query_result['status'], status)
        self.assertEqual(int(query_result['update_date']),
                         int(transaction_date.replace(tzinfo=datetime.timezone.utc).timestamp()))
        self.assertEqual(query_result['submitter'], submitter)
        self.assertEqual(query_result['title'], title)
        self.assertEqual(query_result['type'], product_type)
        self.assertEqual(query_result['subtype'], product_type_specific)
        self.assertEqual(query_result['node_id'], discipline_node)
        self.assertEqual(query_result['lid'], lid)
        self.assertEqual(query_result['vid'], vid)
        self.assertEqual(query_result['doi'], doi)
        self.assertEqual(query_result['transaction_key'], transaction_key)

        self.assertTrue(query_result['is_latest'])

        # Update some fields and write a new "latest" entry
        status = DoiStatus.Draft
        submitter = 'eng-submitter@jpl.nasa.gov'
        discipline_node = 'eng'

        self._doi_database.write_doi_info_to_database(
            lid, vid, transaction_key, doi, transaction_date, status,
            title, product_type, product_type_specific, submitter, discipline_node
        )

        # Query again and ensure we only get latest back
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={'doi': [doi]}
        )

        # Should only get the one row back
        self.assertEqual(len(o_query_result[-1]), 1)

        query_result = dict(zip(o_query_result[0], o_query_result[-1][0]))

        self.assertEqual(query_result['status'], status)
        self.assertEqual(query_result['submitter'], submitter)
        self.assertEqual(query_result['node_id'], discipline_node)

        self.assertTrue(query_result['is_latest'])

        self._doi_database.close_database()

    def test_query_by_wildcard(self):
        """
        Test selection of database rows using tokens with wildcards for the
        columns that support it
        """
        # Insert some sample rows with similar lidvids
        num_rows = 6

        for _id in range(1, 1 + num_rows):
            lid = 'urn:nasa:pds:lab_shocked_feldspars'
            vid = f'{_id}.0'
            transaction_key = f'img/{_id}/2020-06-15T18:42:45.653317'
            doi = f'10.17189/2000{_id}'
            transaction_date = datetime.datetime.now()
            status = DoiStatus.Draft
            title = f'Laboratory Shocked Feldspars Bundle {_id}'
            product_type = ProductType.Collection
            product_type_specific = 'PDS4 Collection'
            submitter = 'img-submitter@jpl.nasa.gov'
            discipline_node = 'img'

            self._doi_database.write_doi_info_to_database(
                lid, vid, transaction_key, doi, transaction_date, status,
                title, product_type, product_type_specific, submitter, discipline_node
            )

        # Use a wildcard with lidvid column to select everything we just
        # inserted
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={'lidvid': ['urn:nasa:pds:lab_shocked_feldspars::*']}
        )

        # Should get all rows back
        self.assertEqual(len(o_query_result[-1]), num_rows)

        # Try again using just the lid column
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={'lid': ['urn:nasa:*:lab_shocked_feldspars']}
        )

        self.assertEqual(len(o_query_result[-1]), num_rows)

        # Test with a combination of wildcards and full tokens
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={'lidvid': ['urn:nasa:pds:lab_shocked_feldspars::1.0',
                                        'urn:nasa:pds:lab_shocked_feldspars::2.*']}
        )

        self.assertEqual(len(o_query_result[-1]), 2)


if __name__ == '__main__':
    unittest.main()
