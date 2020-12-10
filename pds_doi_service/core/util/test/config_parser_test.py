import unittest
import sys
import os
from pds_doi_service.core.util.config_parser import DOIConfigUtil

class ConfigParserTest(unittest.TestCase):
    def test_add_absolute_path(self):

        parser = DOIConfigUtil().get_config()
        self.assertEqual(parser['OTHER']['db_file'], os.path.join(sys.prefix, 'doi.db'))
        self.assertEqual(parser['OTHER']['transaction_dir'], os.path.join(sys.prefix, 'transaction_history'))


if __name__ == '__main__':
    unittest.main()
