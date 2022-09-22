#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
================
config_parser.py
================

Classes and functions for locating and parsing the configuration file for the
core DOI service.
"""
import configparser
import functools
import os
import sys
from os.path import abspath
from os.path import dirname
from os.path import join

from pds_doi_service.core.util.logging import get_logger
from pkg_resources import resource_filename

logger = get_logger()


class DOIConfigParser(configparser.ConfigParser):
    """
    Specialized version of ConfigParser which prioritizes environment variables
    when searching for the requested configuration section/option.

    """

    @property
    def config_defaults_filepath(self) -> str:
        return DOIConfigUtil.get_config_defaults_filepath()

    @property
    def user_config_filepath(self) -> str:
        return DOIConfigUtil.get_user_config_filepath()

    def get(self, section, option, *, raw=False, vars=None, fallback=None):
        """
        Overloaded version of ConfigParser.get() which searches the
        current environment for potential configuration values before checking
        values from the parsed INI. This allows manipulation of the DOI service
        configuration from external contexts such as Docker.

        The key used to search the local environment is determined from the
        section and option names passed to this function. The values are
        concatenated with an underscore and converted to upper-case, for
        example::

            DOIConfigParser.get('OSTI', 'user') -> os.environ['OSTI_USER']
            DOIConfigParser.get('OTHER', 'db_file') -> os.environ['OTHER_DB_FILE']

        If the key is not present in os.environ, then the result from the
        default ConfigParser.get() is returned.

        """
        env_var_key = "_".join([section, option]).upper()

        if env_var_key in os.environ:
            return os.environ[env_var_key]

        return super().get(section, option, raw=raw, vars=vars, fallback=fallback)


class DOIConfigUtil:
    @staticmethod
    def get_user_config_filepath():
        """Return the expected path of the user-specified configuration"""
        return os.path.join(sys.prefix, "pds_doi_service.ini")

    @staticmethod
    def get_config_defaults_filepath():
        """Return the expected path of the user-specified configuration"""
        return resource_filename(__name__, "conf.default.ini")

    @staticmethod
    def _resolve_relative_path(parser):
        # resolve relative path with sys.prefix base path
        for section in parser.sections():
            for (key, val) in parser.items(section):
                if key.endswith("_file") or key.endswith("_dir"):
                    parser[section][key] = os.path.abspath(os.path.join(sys.prefix, val))

        return parser

    @staticmethod
    @functools.lru_cache()
    def get_config():
        return DOIConfigUtil._get_config()

    @staticmethod
    def _get_config():
        """Non-cached version, for improved testability"""

        # Parsed in order, with subsequent config values overwriting values provided in preceding configs
        config_candidate_filepaths = [
            DOIConfigUtil.get_config_defaults_filepath(),
            DOIConfigUtil.get_user_config_filepath(),
        ]

        logger.info("Searching for configuration files from candidates %s", config_candidate_filepaths)

        parser = DOIConfigParser()
        found = parser.read(config_candidate_filepaths)

        if not found:
            raise RuntimeError(
                "Could not find an INI configuration file to "
                f"parse from the following candidates: {config_candidate_filepaths}"
            )

        # When providing multiple configs they are parsed in successive order,
        # and any previously parsed values are overwritten. So the config
        # we use should correspond to the last file in the list returned
        # from ConfigParser.read()
        logger.info("Using configs (with later files overwriting previous files' values): %s", found)
        parser = DOIConfigUtil._resolve_relative_path(parser)

        return parser
