#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import requests
from lxml import etree

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.db.doi_database import DOIDataBase
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.references.contributors import DOIContributorUtil

class DOICoreActionList(DOICoreAction):

    def __init__(self):
        super().__init__()
        self.m_doi_config_util = DOIConfigUtil()
        self._config = self.m_doi_config_util.get_config()
        self.m_default_table_name = self._config.get('OTHER','db_table')  # Default name of table.
        self.m_default_db_file    = self._config.get('OTHER','db_file')   # Default name of the database.
        self._database_obj = DOIDataBase()

    def run(self,
            database_url, node_id, submitter_email):
        """
        Function list all the latest records in the named database and return the JSON object.
        :param database_url:
        :param node_id:
        :param submitter_email:
        :return: o_doi_label:
        """

        try:
            contributor_value = self.m_node_util.get_node_long_name(node_id)
            logger.info(f"contributor_value['{contributor_value}']")
        except UnknownNodeException as e:
            raise e

        # check contributor
        doi_contributor_util = DOIContributorUtil(self._config.get('PDS4_DICTIONARY', 'url'),
                                                  self._config.get('PDS4_DICTIONARY', 'pds_node_identifier'))
        o_permissible_contributor_list = doi_contributor_util.get_permissible_values()
        if contributor_value not in o_permissible_contributor_list:
            logger.error(f"The value of given contributor is not valid: {contributor_value}")
            logger.info(f"permissible_contributor_list {o_permissible_contributor_list}")
            exit(1)

        # If the database name is provided uses it otherwise use default.
        if database_url:
            db_name = database_url
        else:
            db_name = self.m_default_db_file 

        # generate output
        o_query_result = self._database_obj.select_latest_rows(db_name,self.m_default_table_name)
        print("o_query_result",o_query_result,type(o_query_result))

        return o_query_result
