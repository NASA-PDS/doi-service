import base64
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from datetime import timedelta

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiRecord
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pkg_resources import resource_filename


class WeeklyRoundupNotificationBaseTestCase(unittest.TestCase):
    tests_dir = os.path.abspath(resource_filename(__name__, ""))
    resources_dir = os.path.join(tests_dir, "resources")

    temp_dir = tempfile.mkdtemp()
    db_filepath = os.path.join(temp_dir, "doi_temp.sqlite")

    _database_obj: DOIDataBase

    # Some reference datetimes that are referenced in SetUpClass and in tests
    _now = datetime.now()
    _last_week = _now - timedelta(days=4)
    _ages_ago = _now - timedelta(days=30)

    @classmethod
    def setUpClass(cls):
        cls._database_obj = DOIDataBase(cls.db_filepath)

        # Write some example DOIs to the test db
        doi_records = [
            cls.generate_doi_record(uid="11111", added_last_week=True, updated_last_week=True),
            cls.generate_doi_record(uid="22222", added_last_week=False, updated_last_week=True),
            cls.generate_doi_record(uid="33333", added_last_week=False, updated_last_week=False),
        ]

        for record in doi_records:
            cls._database_obj.write_doi_info_to_database(record)

    @classmethod
    def tearDownClass(cls):
        cls._database_obj.close_database()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    @classmethod
    def generate_doi_record(cls, uid: str, added_last_week: bool, updated_last_week: bool):
        if added_last_week:
            assert updated_last_week

        pds_id = f"urn:nasa:pds:product_{uid}::1.0"
        doi_id = f"10.17189/{uid}"

        return DoiRecord(
            identifier=pds_id,
            status=DoiStatus.Pending,
            date_added=cls._last_week if added_last_week else cls._ages_ago,
            date_updated=cls._last_week if updated_last_week else cls._ages_ago,
            submitter="img-submitter@jpl.nasa.gov",
            title="Laboratory Shocked Feldspars Bundle",
            type=ProductType.Collection,
            subtype="PDS4 Collection",
            node_id="img",
            doi=doi_id,
            transaction_key="./transaction_history/img/2020-06-15T18:42:45.653317",
            is_latest=True,
        )
