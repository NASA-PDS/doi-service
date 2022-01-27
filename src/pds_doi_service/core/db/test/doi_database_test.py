#!/usr/bin/env python
import datetime
import os
import unittest
from datetime import timedelta
from datetime import timezone
from os.path import exists

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiRecord
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.util.general_util import get_logger
from pkg_resources import resource_filename

logger = get_logger(__name__)


class DOIDatabaseTest(unittest.TestCase):
    """Unit tests for the doi_database.py module"""

    def setUp(self):
        self._db_name = resource_filename(__name__, "doi_temp.db")

        # Delete temporary db if it already exists, this can occur when tests
        # are terminated before completion (during debugging for example)
        if exists(self._db_name):
            os.remove(self._db_name)

        self._doi_database = DOIDataBase(self._db_name)

    def tearDown(self):
        if exists(self._db_name):
            os.remove(self._db_name)

    def test_select_latest_rows(self):
        """Test selecting of latest rows from the transaction database"""
        # Set up a sample db entry
        doi_record = DoiRecord(
            identifier="urn:nasa:pds:lab_shocked_feldspars::1.0",
            status=DoiStatus.Unknown,
            date_added=datetime.datetime.now(tz=timezone.utc),
            date_updated=datetime.datetime.now(tz=timezone.utc),
            submitter="img-submitter@jpl.nasa.gov",
            title="Laboratory Shocked Feldspars Bundle",
            type=ProductType.Collection,
            subtype="PDS4 Collection",
            node_id="img",
            doi="10.17189/21729",
            transaction_key="img/2020-06-15T18:42:45.653317",
            is_latest=True,
        )

        # Insert a row in the 'doi' table
        self._doi_database.write_doi_info_to_database(doi_record)

        # Select the row we just added
        # The type of o_query_result should be JSON and a list of 1
        o_query_result = self._doi_database.select_latest_rows(query_criterias={"doi": [doi_record.doi]})

        # Reformat results to a dictionary to test with
        query_result = dict(zip(o_query_result[0], o_query_result[1][0]))

        # Ensure we got back everything we just put in
        self.assertEqual(query_result["status"], doi_record.status)
        self.assertEqual(
            int(query_result["date_added"].timestamp()),
            int(doi_record.date_added.timestamp()),
        )
        self.assertEqual(
            int(query_result["date_updated"].timestamp()),
            int(doi_record.date_updated.timestamp()),
        )
        self.assertEqual(query_result["submitter"], doi_record.submitter)
        self.assertEqual(query_result["title"], doi_record.title)
        self.assertEqual(query_result["type"], doi_record.type)
        self.assertEqual(query_result["subtype"], doi_record.subtype)
        self.assertEqual(query_result["node_id"], doi_record.node_id)
        self.assertEqual(query_result["identifier"], doi_record.identifier)
        self.assertEqual(query_result["doi"], doi_record.doi)
        self.assertEqual(query_result["transaction_key"], doi_record.transaction_key)

        self.assertTrue(query_result["is_latest"])

        # Update some fields and write a new "latest" entry
        doi_record.status = DoiStatus.Draft
        doi_record.submitter = "eng-submitter@jpl.nasa.gov"
        doi_record.node_id = "eng"

        self._doi_database.write_doi_info_to_database(doi_record)

        # Query again and ensure we only get latest back
        o_query_result = self._doi_database.select_latest_rows(query_criterias={"doi": [doi_record.doi]})

        # Should only get the one row back
        self.assertEqual(len(o_query_result[-1]), 1)

        query_result = dict(zip(o_query_result[0], o_query_result[-1][0]))

        self.assertEqual(query_result["status"], doi_record.status)
        self.assertEqual(query_result["submitter"], doi_record.submitter)
        self.assertEqual(query_result["node_id"], doi_record.node_id)

        self.assertTrue(query_result["is_latest"])

        self._doi_database.close_database()

    def test_select_latest_rows_lid_only(self):
        """Test corner case where we select and update rows that only specify a LID"""
        # Set up a sample db entry
        doi_record = DoiRecord(
            identifier="urn:nasa:pds:insight_cameras",
            status=DoiStatus.Unknown,
            date_added=datetime.datetime.now(tz=timezone.utc),
            date_updated=datetime.datetime.now(tz=timezone.utc),
            submitter="eng-submitter@jpl.nasa.gov",
            title="Insight Cameras Bundle",
            type=ProductType.Collection,
            subtype="PDS4 Collection",
            node_id="eng",
            doi="10.17189/22000",
            transaction_key="img/2021-05-10T00:00:00.000000",
            is_latest=True,
        )

        # Insert a row in the 'doi' table
        self._doi_database.write_doi_info_to_database(doi_record)

        # Select the row we just added
        # The type of o_query_result should be JSON and a list of 1
        o_query_result = self._doi_database.select_latest_rows(query_criterias={"ids": [doi_record.identifier]})

        # Reformat results to a dictionary to test with
        query_result = dict(zip(o_query_result[0], o_query_result[1][0]))

        # Ensure we got back everything we just put in
        self.assertEqual(query_result["status"], doi_record.status)
        self.assertEqual(
            int(query_result["date_added"].timestamp()),
            int(doi_record.date_added.timestamp()),
        )
        self.assertEqual(
            int(query_result["date_updated"].timestamp()),
            int(doi_record.date_updated.timestamp()),
        )
        self.assertEqual(query_result["submitter"], doi_record.submitter)
        self.assertEqual(query_result["title"], doi_record.title)
        self.assertEqual(query_result["type"], doi_record.type)
        self.assertEqual(query_result["subtype"], doi_record.subtype)
        self.assertEqual(query_result["node_id"], doi_record.node_id)
        self.assertEqual(query_result["identifier"], doi_record.identifier)
        self.assertEqual(query_result["doi"], doi_record.doi)
        self.assertEqual(query_result["transaction_key"], doi_record.transaction_key)

        self.assertTrue(query_result["is_latest"])

        # Update some fields and write a new "latest" entry
        doi_record.status = DoiStatus.Pending
        doi_record.submitter = "img-submitter@jpl.nasa.gov"
        doi_record.node_id = "img"

        self._doi_database.write_doi_info_to_database(doi_record)

        # Query again and ensure we only get latest back
        o_query_result = self._doi_database.select_latest_rows(query_criterias={"ids": [doi_record.identifier]})

        # Should only get the one row back
        self.assertEqual(len(o_query_result[-1]), 1)

        query_result = dict(zip(o_query_result[0], o_query_result[-1][0]))

        self.assertEqual(query_result["status"], doi_record.status)
        self.assertEqual(query_result["submitter"], doi_record.submitter)
        self.assertEqual(query_result["node_id"], doi_record.node_id)

        self.assertTrue(query_result["is_latest"])

        self._doi_database.close_database()

    def test_query_by_wildcard(self):
        """
        Test selection of database rows using tokens with wildcards for the
        columns that support it
        """
        # Insert some sample rows with similar lidvids
        num_rows = 6

        for _id in range(1, 1 + num_rows):
            doi_record = DoiRecord(
                identifier=f"urn:nasa:pds:lab_shocked_feldspars::{_id}.0",
                status=DoiStatus.Draft,
                date_added=datetime.datetime.now(),
                date_updated=datetime.datetime.now(),
                submitter="img-submitter@jpl.nasa.gov",
                title=f"Laboratory Shocked Feldspars Bundle {_id}",
                type=ProductType.Collection,
                subtype="PDS4 Collection",
                node_id="img",
                doi=f"10.17189/2000{_id}",
                transaction_key=f"img/{_id}/2020-06-15T18:42:45.653317",
                is_latest=True,
            )

            self._doi_database.write_doi_info_to_database(doi_record)

        # Use a wildcard with lidvid column to select everything we just
        # inserted
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={"ids": ["urn:nasa:pds:lab_shocked_feldspars::*"]}
        )

        # Should get all rows back
        self.assertEqual(len(o_query_result[-1]), num_rows)

        # Try again using just the lid
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={"ids": ["urn:nasa:*:lab_shocked_feldspars::1.0"]}
        )

        self.assertEqual(len(o_query_result[-1]), 1)

        # Test with a combination of wildcards and full tokens
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={
                "ids": ["urn:nasa:pds:lab_shocked_feldspars::1.0", "urn:nasa:pds:lab_shocked_feldspars::2.*"]
            }
        )

        self.assertEqual(len(o_query_result[-1]), 2)

        # Test case-insensitive search of titles
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={"title": ["*shocked feldspars bundle ?"]}
        )

        # Should get all rows back
        self.assertEqual(len(o_query_result[-1]), num_rows)

        # Test combination of wildcard tokens on a DOI search
        o_query_result = self._doi_database.select_latest_rows(
            query_criterias={"doi": ["10.17189/?0001", "10.1718*/20003"]}
        )

        # Should only match two DOI's
        self.assertEqual(len(o_query_result[-1]), 2)


if __name__ == "__main__":
    unittest.main()
