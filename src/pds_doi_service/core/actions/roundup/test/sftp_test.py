import json
import os
import tempfile
import unittest

from pds_doi_service.core.actions.roundup.enumerate import get_previous_week_metadata
from pds_doi_service.core.actions.roundup.output import prepare_doi_record_for_ads_sftp
from pds_doi_service.core.actions.roundup.test.base import WeeklyRoundupNotificationBaseTestCase


class WeeklyRoundupAdsSftpNotificationTestCase(WeeklyRoundupNotificationBaseTestCase):
    _temp_file_path: str

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        metadata = get_previous_week_metadata(cls._database_obj)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as fp:
            output = metadata.to_json(doi_record_mapper=prepare_doi_record_for_ads_sftp)
            json.dump(output, fp)
            fp.flush()
            cls._temp_file_path = os.path.join(tempfile.gettempdir(), fp.name)

    def test_file_content(self):
        comparison_filepath = os.path.join(self.resources_dir, "roundup_ads_sftp_dump.json")
        with open(self._temp_file_path) as outfile, open(comparison_filepath) as cmpfile:
            test_data = json.load(outfile)
            expected_data = json.load(cmpfile)

            # Remove root-object fields whose values are non-deterministic after confirming that they exist
            for k in ["first_date", "last_date"]:
                for output_obj in [test_data, expected_data]:
                    self.assertIn(k, output_obj.keys())
                    output_obj.pop(k)

            # Remove per-record fields whose values are non-deterministic after confirming that they exist
            for k in [
                "last_modified",
            ]:
                for dataset in [test_data, expected_data]:
                    for r in dataset["modified_doi_records"]:
                        self.assertIn(k, r.keys())
                        r.pop(k)

            self.assertEqual(expected_data, test_data)


if __name__ == "__main__":
    unittest.main()
