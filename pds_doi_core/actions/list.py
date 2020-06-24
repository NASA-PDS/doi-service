#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import datetime
import json

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.db.doi_database import DOIDataBase
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.references.contributors import DOIContributorUtil

class DOICoreActionList(DOICoreAction):
    _name = 'list'
    description = ' % pds-doi-cmd list -n img -s Qui.T.Chau@jpl.nasa.gov -f JSON -doi 10.17189/21857 -start 2020-01-01T19:02:15.000000 -end 2020-12-13T23:59:59.000000 -lid urn:nasa:pds:lab_shocked_feldspars -lidvid urn:nasa:pds:lab_shocked_feldspars::1.0,urn:nasa:pds:lab_shocked_feldspars_2::1.0,urn:nasa:pds:lab_shocked_feldspars_3::1.0 \n'

    def __init__(self, arguments=None):
        super().__init__(arguments=arguments)
        # Object self._config is already instantiated from the previous super().__init__() command, no need to do it again.
        self.m_default_db_file    = self._config.get('OTHER','db_file')   # Default name of the database.
        self._database_obj = DOIDataBase(self.m_default_db_file)

        if self._arguments:
            self._input_doi_token = self._arguments.doi
            self._output_format = self._arguments.format_output
            self._start_update  = self._arguments.start_update
            self._end_update    = self._arguments.end_update
            self._lid           = self._arguments.lid
            self._lidvid        = self._arguments.lidvid

        self._query_criterias = {}

        if self._input_doi_token:
            self._query_criterias['doi'] = self._input_doi_token.split(',')
        if self._lid:
            self._query_criterias['lid'] = self._lid.split(',')
        if self._lidvid:
            self._query_criterias['lidvid'] = self._lidvid.split(',')
        if self._submitter:
            self._query_criterias['submitter'] = self._submitter.split(',')
        if self._node_id:
            self._query_criterias['node'] = self._node_id.lstrip().rstrip().split(',')
        if self._start_update:
            self._query_criterias['start_update'] = datetime.datetime.strptime(self._start_update,'%Y-%m-%dT%H:%M:%S.%f');
        if self._end_update:
            self._query_criterias['end_update']   = datetime.datetime.strptime(self._end_update,'%Y-%m-%dT%H:%M:%S.%f');

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name)
        action_parser.add_argument('-n', '--node-id',
                                   help='A list of node names comma separated to pass as input to the database query.',
                                   required=False,
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
        action_parser.add_argument('-s', '--submitter-email',
                                   help='A list of email addresses comma seprated to pass as input to the database query',
                                   required=False,
                                   metavar='"my.email@node.gov"')

    def run(self):
        """
        Function list all the latest records in the named database and return the object either in JSON or XML.
        :param submitter_email:
        :param output_format:
        :param query_criterias:
        :return: o_list_result:
        """

        # For a list operation, the 'node' field is just a series of tokens to pass into database query.
        # We do a verification by converting each to a long name.
        if (len(self._query_criterias) > 0) and 'node' in self._query_criterias:
            for ii in range(0,len(self._query_criterias['node'])):
                try:
                    contributor_value = self.m_node_util.get_node_long_name(self._query_criterias['node'][ii])
                    logger.info(f"contributor_value['{contributor_value}']")
                except UnknownNodeException as e:
                    raise e

        # No need to check contributor since the short names will be used in data base query.

        # Perform the database query and convert a dict object to JSON for returning.
        columns, rows = self._database_obj.select_latest_rows(self._query_criterias)
        # generate output

        if self._output_format == 'JSON':
            result_json = []
            for row in rows:
                result_json.append({columns[i]:row[i] for i in range(len(columns))})
            o_query_result = json.dumps(result_json)
            logger.debug(f"o_select_result {o_query_result} {type(o_query_result)}")
        else:
            logger.error(f"Output format type {self._output_format} not supported yet")
            exit(1)
        return o_query_result
