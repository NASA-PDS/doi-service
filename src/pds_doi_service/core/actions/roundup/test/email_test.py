import base64
import json
import os
import unittest
from datetime import timedelta
from email.message import Message

import jinja2
from pds_doi_service.core.actions.roundup.email import run as do_roundup
from pds_doi_service.core.actions.roundup.enumerate import get_start_of_local_week
from pds_doi_service.core.actions.roundup.test.base import WeeklyRoundupNotificationBaseTestCase
from pds_doi_service.core.actions.test.util.email import capture_email


@unittest.skipIf(os.environ.get("CI") == "true", "Test is currently broken in Github Actions workflow. See #361")
class WeeklyRoundupEmailNotificationTestCase(WeeklyRoundupNotificationBaseTestCase):
    _message: Message

    sender = "test_sender@jpl.nasa.gov"
    recipient = "test_recipient@jpl.nasa.gov"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._message = capture_email(lambda: do_roundup(cls._database_obj, cls.sender, cls.recipient))

    def test_roundup_email_sender_correct(self):
        self.assertEqual(self.sender, self._message["From"])

    def test_roundup_email_recipients_correct(self):
        self.assertEqual(self.recipient, self._message["To"])

    def test_html_content(self):
        template_dict = {
            "week_start": get_start_of_local_week().date() - timedelta(days=7),
            "week_end": get_start_of_local_week().date() - timedelta(days=1),
            "modifications_date": self._last_week.date(),
        }
        html_content = self._message.get_payload(0).get_payload()
        expected_content_filepath = os.path.join(self.resources_dir, "roundup_email_body.jinja2")
        with open(expected_content_filepath, "r") as infile:
            template = jinja2.Template(infile.read())
            expected_html_content = template.render(template_dict)
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


if __name__ == "__main__":
    unittest.main()
