#!/usr/bin/env python
import os
import sys
import unittest

from pds_doi_service.core.util import config_parser
from pds_doi_service.core.util.config_parser import DOIConfigParser
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pkg_resources import resource_filename


class ConfigParserTest(unittest.TestCase):
    def test_add_absolute_path(self):
        """
        Test that DOIConfigUtil._resolve_relative_path() prepends the
        system prefix to file or directory locations.
        """
        parser = DOIConfigUtil().get_config()

        self.assertEqual(parser["OTHER"]["db_file"], os.path.join(sys.prefix, "doi.db"))
        self.assertEqual(parser["OTHER"]["transaction_dir"], os.path.join(sys.prefix, "transaction_history"))

    def test_doi_config_parser(self):
        """
        Test environment variable overrides for the the DOIConfigParser class.
        """
        parser = DOIConfigParser()

        # Populate our config parser with the default INI
        conf_file_path = resource_filename("pds_doi_service", "core/util/conf.default.ini")
        parser.read(conf_file_path)

        # Ensure we get values from the default INI to begin with
        self.assertIsNone(parser.get("OSTI", "user"))
        self.assertEqual(parser["PDS4_DICTIONARY"]["pds_node_identifier"], "0001_NASA_PDS_1.pds.Node.pds.name")
        self.assertEqual(parser["OTHER"]["db_file"], "doi.db")

        # Now provide some environment variables to override with
        osti_user_override = "actual_username"
        node_id_override = "123ABC"
        other_db_override = "/path/to/other/doi.db"

        os.environ["OSTI_USER"] = osti_user_override
        os.environ["PDS4_DICTIONARY_PDS_NODE_IDENTIFIER"] = node_id_override
        os.environ["OTHER_DB_FILE"] = other_db_override

        # Our config parser should prioritize the environment variables
        try:
            self.assertEqual(parser.get("OSTI", "user"), osti_user_override)
            self.assertEqual(parser.get("PDS4_DICTIONARY", "pds_node_identifier"), node_id_override)
            self.assertEqual(parser.get("OTHER", "db_file"), other_db_override)
        finally:
            os.environ.pop("OSTI_USER")
            os.environ.pop("PDS4_DICTIONARY_PDS_NODE_IDENTIFIER")
            os.environ.pop("OTHER_DB_FILE")


class DOIConfigUtilTest(unittest.TestCase):
    config_parser_module_dirpath = os.path.split(config_parser.__file__)[0]
    default_config_path = os.path.join(config_parser_module_dirpath, "conf.default.ini")
    user_config_path = os.path.join(sys.prefix, "pds_doi_service.ini")

    def setUp(self) -> None:
        self._remove_user_config()

    def tearDown(self) -> None:
        self._remove_user_config()

    def test_user_config_overrides_default(self):
        config = DOIConfigUtil._get_config()
        self.assertEqual("defaultValue", config.get("TEST", "noOverrideKey"))
        self.assertEqual("defaultValue", config.get("TEST", "overrideKey"))
        self.assertIsNone(config.get("TEST", "additionalUserKey"))

        self._write_user_config()

        config = DOIConfigUtil._get_config()
        self.assertEqual("defaultValue", config.get("TEST", "noOverrideKey"))
        self.assertEqual("userValue", config.get("TEST", "overrideKey"))
        self.assertEqual("userValue", config.get("TEST", "additionalUserKey"))

    def test_env_vars_override_user_config(self):
        config = DOIConfigUtil._get_config()
        self.assertEqual("defaultValue", config.get("TEST", "overrideKey"))

        self._write_user_config()
        config = DOIConfigUtil._get_config()
        self.assertEqual("userValue", config.get("TEST", "overrideKey"))

        os.environ["TEST_OVERRIDEKEY"] = "env_var_value"
        self.assertEqual("env_var_value", config.get("TEST", "overrideKey"))

        os.environ.pop("TEST_OVERRIDEKEY")

    def _write_user_config(self):
        with open(self.user_config_path, "w+") as outfile:
            lines = ["[TEST]\n", "overrideKey = userValue\n", "additionalUserKey = userValue\n"]
            outfile.writelines(lines)

    def _remove_user_config(self):
        try:
            os.remove(self.user_config_path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    unittest.main()
