#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import json
#import requests
from lxml import etree

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.db.doi_database import DOIDataBase
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.references.contributors import DOIContributorUtil

class DOICoreActionList(DOICoreAction):
    _name = 'list'
    description = ' % pds-doi-cmd list -c img -s Qui.T.Chau@jpl.nasa.gov -i doi.db -f JSON -doi 10.17189/21857 -start 2020-01-01T19:02:15.000000 -end 2020-12-13T23:59:59.000000 -lid urn:nasa:pds:lab_shocked_feldspars -lidvid urn:nasa:pds:lab_shocked_feldspars::1.0,urn:nasa:pds:lab_shocked_feldspars_2::1.0,urn:nasa:pds:lab_shocked_feldspars_3::1.0 \n'

    def __init__(self):
        super().__init__()
        # Object self._config is already instantiated from the previous super().__init__() command, no need to do it again.
        self.m_default_table_name = self._config.get('OTHER','db_table')  # Default name of table.
        self.m_default_db_file    = self._config.get('OTHER','db_file')   # Default name of the database.
        self._database_obj = DOIDataBase()

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name)
        action_parser.add_argument('-c', '--node-id',
                                   help='A list of node names comma separated to pass as input to the database query.',
                                   required=True,
                                   metavar='"img,eng"')
        action_parser.add_argument('-f', '--format-output',
                                   help='The format of the output from the database query.  Default is JSON if not specified',
                                   default='JSON',
                                   required=False,
                                   metavar='JSON')
        action_parser.add_argument('-doi', '--doi',
                                   help='A list of DOIs comma separated to pass as input to the database query.',
                                   required=False,
                                   metavar='10.17189/21734')
        action_parser.add_argument('-lid', '--lid',
                                   help='A list of LIDs comma separated to pass as input to the database query.',
                                   required=False,
                                   metavar='urn:nasa:pds:lab_shocked_feldspars')
        action_parser.add_argument('-lidvid', '--lidvid',
                                   help='A list of LIDVIDs comma separated to pass as input to the database query.',
                                   required=False,
                                   metavar='urn:nasa:pds:lab_shocked_feldspars::1.0')
        action_parser.add_argument('-start', '--start-update',
                                   help='The start time for record update to pass as input to the database query.',
                                   required=False,
                                   metavar='2020-01-01T19:02:15.000000')
        action_parser.add_argument('-end', '--end-update',
                                   help='The end time for record update time to pass as input to the database query.',
                                   required=False,
                                   metavar='2020-12-311T23:59:00.000000')
        action_parser.add_argument('-i', '--input',
                                   help='A file name of the database',
                                   required=True,
                                   metavar='doi.db')
        action_parser.add_argument('-s', '--submitter-email',
                                   help='A list of email addresses comma seprated to pass as input to the database query',
                                   required=False,
                                   metavar='"my.email@node.gov"')

    def run(self,
            database_url, output_format, query_criterias=[]):
        """
        Function list all the latest records in the named database and return the object either in JSON or XML.
        :param database_url:
        :param submitter_email:
        :param output_format:
        :param query_criterias:
        :return: o_list_result:
        """

        # Check for output format type.
        if output_format == 'JSON':
            pass
        else:
            logger.error(f"Output format type {output_format} not supported yet")
            exit(1)

        # For a list operation, the 'node' field is just a series of tokens to pass into database query.
        # We do a verification by converting each to a long name.
        if (len(query_criterias) > 0) and 'node' in query_criterias:
            for ii in range(0,len(query_criterias['node'])):
                try:
                    contributor_value = self.m_node_util.get_node_long_name(query_criterias['node'][ii])
                    logger.info(f"contributor_value['{contributor_value}']")
                except UnknownNodeException as e:
                    raise e

        # No need to check contributor since the short names will be used in data base query.

        # If the database name is provided uses it otherwise use default.
        if database_url:
            db_name = database_url
        else:
            db_name = self.m_default_db_file

        # Perform the database query and convert a dict object to JSON for returning.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)
        # generate output
        if output_format == 'JSON':
            result_json = []
            for row in rows:
                result_json.append({columns[i]:row[i] for i in range(len(columns))})
            o_query_result = json.dumps(result_json)
            logger.debug(f"o_select_result {o_query_result} {type(o_query_result)}")
        return o_query_result
