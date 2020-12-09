#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------

import os
from os.path import abspath, dirname, join
import sys
import configparser
import logging

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
        conf_default_path = abspath(join(dirname(__file__), conf_default))
        conf_user = 'pds_doi_service.ini'
        conf_user_prod_path = os.path.join(sys.prefix, conf_user)
        conf_user_dev_path = abspath(join(dirname(__file__), os.pardir, os.pardir, os.pardir, conf_user))
        candidates_full_path = [conf_default_path, conf_user_prod_path, conf_user_dev_path]
        logging.info(f"search configuration files in {candidates_full_path}")
        found = parser.read(candidates_full_path)
        logging.info(f"used configuration following files {found}")
        parser = DOIConfigUtil._resolve_relative_path(parser)
        return parser

