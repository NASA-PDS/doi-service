#!/usr/bin/env python

import unittest
import sys
import os

from pkg_resources import resource_filename

from pds_doi_service.core.util.config_parser import DOIConfigParser, DOIConfigUtil


class ConfigParserTest(unittest.TestCase):

    def test_add_absolute_path(self):
        """
        Test that DOIConfigUtil._resolve_relative_path() prepends the
        system prefix to file or directory locations.
        """
        parser = DOIConfigUtil().get_config()

        self.assertEqual(parser['OTHER']['db_file'],
                         os.path.join(sys.prefix, 'doi.db'))
        self.assertEqual(parser['OTHER']['transaction_dir'],
                         os.path.join(sys.prefix, 'transaction_history'))

    def test_doi_config_parser(self):
        """
        Test environment variable overrides for the the DOIConfigParser class.
        """
        parser = DOIConfigParser()

        # Populate our config parser with the default INI
        conf_file_path = resource_filename('pds_doi_service', 'core/util/conf.ini.default')
        parser.read(conf_file_path)

        # Ensure we get values from the default INI to begin with
        self.assertEqual(parser['OSTI']['user'], 'username')
        self.assertEqual(parser['PDS4_DICTIONARY']['pds_node_identifier'],
                         '0001_NASA_PDS_1.pds.Node.pds.name')
        self.assertEqual(parser['LANDING_PAGES']['url'],
                         'https://pds.nasa.gov/ds-view/pds/view{}.jsp?identifier={}&version={}')
        self.assertEqual(parser['OTHER']['db_file'], 'doi.db')

        # Now provide some environment variables to override with
        os.environ['OSTI_USER'] = 'actual_username'
        os.environ['PDS4_DICTIONARY_PDS_NODE_IDENTIFIER'] = '123ABC'
        os.environ['LANDING_PAGES_URL'] = 'https://zombo.com'
        os.environ['OTHER_DB_FILE'] = '/path/to/other/doi.db'

        # Our config parser should prioritize the environment variables
        try:
            self.assertEqual(parser['OSTI']['user'], os.environ['OSTI_USER'])
            self.assertEqual(parser['PDS4_DICTIONARY']['pds_node_identifier'],
                             os.environ['PDS4_DICTIONARY_PDS_NODE_IDENTIFIER'])
            self.assertEqual(parser['LANDING_PAGES']['url'], os.environ['LANDING_PAGES_URL'])
            self.assertEqual(parser['OTHER']['db_file'], os.environ['OTHER_DB_FILE'])
        finally:
            os.environ.pop('OSTI_USER')
            os.environ.pop('PDS4_DICTIONARY_PDS_NODE_IDENTIFIER')
            os.environ.pop('LANDING_PAGES_URL')
            os.environ.pop('OTHER_DB_FILE')


if __name__ == '__main__':
    unittest.main()
