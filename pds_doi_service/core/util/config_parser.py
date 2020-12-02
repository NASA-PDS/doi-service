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
        return parser

