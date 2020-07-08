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
    description = ' % pds-doi-cmd list \n'

    def __init__(self, db_name=None):
        super().__init__(db_name=None)
        # Object self._config is already instantiated from the previous super().__init__() command, no need to do it again.
        if db_name:
            self.m_default_db_file    = db_name # If database name is specified from user, use it.
        else:
            self.m_default_db_file    = self._config.get('OTHER','db_file')   # Default name of the database.
        self._database_obj = DOIDataBase(self.m_default_db_file)

        self._query_criterias = {}
        self._output_format = 'JSON'

    def parse_arguments_from_cmd(self, arguments):
        criteria = {}
        for k,v in arguments._get_kwargs():
            if k != 'action':
                criteria[k] = v

        self.set_criterias(**criteria)


    def set_criterias(self,
                       format_output='JSON',
                       doi=None,
                       lid=None,
                       lidvid=None,
                       node_id=None,
                       status=None,
                       start_update=None,
                       end_update=None,
                       submitter_email=None):

        self._output_format = format_output

        if doi:
            self._query_criterias['doi'] = doi.split(',')

        if lid:
            self._query_criterias['lid'] = lid.split(',')

        if lidvid:
            self._query_criterias['lidvid'] = lidvid.split(',')

        if submitter_email:
            self._query_criterias['submitter'] = submitter_email.split(',')

        if node_id:
            self._query_criterias['node'] = node_id.lstrip().rstrip().split(',')

        if status:
            self._query_criterias['status'] = status.lstrip().rstrip().split(',')

        if start_update:
            self._query_criterias['start_update'] = datetime.datetime.strptime(start_update,'%Y-%m-%dT%H:%M:%S.%f');

        if end_update:
            self._query_criterias['end_update']   = datetime.datetime.strptime(end_update,'%Y-%m-%dT%H:%M:%S.%f');


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
