import base64
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from datetime import timedelta
from email.message import Message

from pds_doi_service.core.actions.roundup import run as do_roundup
from pds_doi_service.core.actions.test.util.email import capture_email
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiRecord
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pkg_resources import resource_filename


class WeeklyRoundupEmailNotificationTestCase(unittest.TestCase):
    tests_dir = os.path.abspath(resource_filename(__name__, ""))
    resources_dir = os.path.join(tests_dir, "data", "roundup")

    temp_dir = tempfile.mkdtemp()
    db_filepath = os.path.join(temp_dir, "doi_temp.sqlite")

    _database_obj: DOIDataBase
    _message: Message

    sender = "test_sender@jpl.nasa.gov"
    recipient = "test_recipient@jpl.nasa.gov"

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

        cls._message = capture_email(lambda: do_roundup(cls._database_obj, cls.sender, cls.recipient))

    @classmethod
    def tearDownClass(cls):
        cls._database_obj.close_database()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_roundup_email_sender_correct(self):
        self.assertEqual(self.sender, self._message["From"])

    def test_roundup_email_recipients_correct(self):
        self.assertEqual(self.recipient, self._message["To"])

    def test_html_content(self):
        html_content = self._message.get_payload(0).get_payload()
        expected_content_filepath = os.path.join(self.resources_dir, "roundup_email_body.html")
        with open(expected_content_filepath, "r") as infile:
            expected_html_content = infile.read()
        self.assertEqual(expected_html_content.replace(" ", "").strip(), html_content.replace(" ", "").strip())

    def test_attachment_content(self):
        attachment_content = self._message.get_payload(1).get_payload()
        attachment_data = json.loads(base64.b64decode(attachment_content))
        expected_content_filepath = os.path.join(self.resources_dir, "roundup_email_attachment.json")
        with open(expected_content_filepath, "r") as infile:
            expected_data = json.load(infile)

        # Remove fields whose values are non-deterministic after confirming that they exist
        for k in ["date_added", "date_updated"]:
            for results in [attachment_data, expected_data]:
                for r in results:
                    self.assertIn(k, r.keys())
                    r.pop(k)

        self.assertEqual(expected_data, attachment_data)

    @staticmethod
    def generate_doi_record(uid: str, added_last_week: bool, updated_last_week: bool):
        if added_last_week:
            assert updated_last_week
        now = datetime.now()
        last_week = now - timedelta(days=4)
        ages_ago = now - timedelta(days=30)

        pds_id = f"urn:nasa:pds:product_{uid}::1.0"
        doi_id = f"10.17189/{uid}"

        return DoiRecord(
            identifier=pds_id,
            status=DoiStatus.Pending,
            date_added=last_week if added_last_week else ages_ago,
            date_updated=last_week if updated_last_week else ages_ago,
            submitter="img-submitter@jpl.nasa.gov",
            title="Laboratory Shocked Feldspars Bundle",
            type=ProductType.Collection,
            subtype="PDS4 Collection",
            node_id="img",
            doi=doi_id,
            transaction_key="./transaction_history/img/2020-06-15T18:42:45.653317",
            is_latest=True,
        )


if __name__ == "__main__":
    unittest.main()
