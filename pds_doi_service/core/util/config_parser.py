#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
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
import logging
import os
import sys

from os.path import abspath, dirname, join
from pkg_resources import resource_filename

logging.basicConfig(level=logging.ERROR)


class DOIConfigUtil:

    @staticmethod
    def _resolve_relative_path(parser):
        # resolve relative path with sys.prefix base path
        for section in parser.sections():
            for (key, val) in parser.items(section):
                if key.endswith('_file') or key.endswith('_dir'):
                    parser[section][key] = os.path.abspath(os.path.join(sys.prefix, val))

        return parser

    def get_config(self):
        parser = configparser.ConfigParser()

        # default configuration
        conf_default = 'conf.ini.default'
        conf_default_path = resource_filename(__name__, conf_default)

        # user-specified configuration for production
        conf_user = 'pds_doi_service.ini'
        conf_user_prod_path = os.path.join(sys.prefix, conf_user)

        # user-specified configuration for development
        conf_user_dev_path = abspath(
            join(dirname(__file__), os.pardir, os.pardir, os.pardir, conf_user)
        )

        candidates_full_path = [conf_default_path, conf_user_prod_path, conf_user_dev_path]

        logging.info("Searching for configuration files in %s", candidates_full_path)
        found = parser.read(candidates_full_path)

        logging.info("Using the following configuration file: %s", found)
        parser = DOIConfigUtil._resolve_relative_path(parser)

        return parser
