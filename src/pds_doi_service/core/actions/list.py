#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
=======
list.py
=======

Contains the definition for the List action of the Core PDS DOI Service.
"""

import json

from dateutil.parser import isoparse

from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.input.exceptions import UnknownLIDVIDException
from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOICoreActionList(DOICoreAction):
    _name = 'list'
    _description = ('List DOI entries within the transaction database that match '
                    'the provided search criteria')
    _order = 40
    _run_arguments = ('format', 'doi', 'ids', 'node', 'status',
                      'start_update', 'end_update', 'submitter')

    def __init__(self, db_name=None):
        super().__init__(db_name=None)
        # Object self._config is already instantiated from the previous
        # super().__init__() command, no need to do it again.
        if db_name:
            # If database name is specified from user, use it.
            self.m_default_db_file = db_name
        else:
            # Default name of the database.
            self.m_default_db_file = self._config.get('OTHER', 'db_file')

        self._database_obj = DOIDataBase(self.m_default_db_file)

        self._query_criterias = {}
        self._format = 'JSON'

    def parse_arguments_from_cmd(self, arguments):
        criteria = {}

        for k, v in arguments._get_kwargs():
            if k != 'subcommand':
                criteria[k] = v

        self.parse_criteria(**criteria)

    def parse_criteria(self, format='JSON', doi=None, ids=None, node=None,
                       status=None, start_update=None, end_update=None,
                       submitter=None):

        self._format = format

        if doi:
            self._query_criterias['doi'] = doi.split(',')

        if ids:
            self._query_criterias['ids'] = ids.split(',')

        if submitter:
            self._query_criterias['submitter'] = submitter.split(',')

        if node:
            self._query_criterias['node'] = node.strip().split(',')

        if status:
            self._query_criterias['status'] = status.strip().split(',')

        if start_update:
            self._query_criterias['start_update'] = isoparse(start_update)

        if end_update:
            self._query_criterias['end_update'] = isoparse(end_update)

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(
            cls._name, description='Extracts the submitted DOI from the local '
                                   'transaction database using the following '
                                   'selection criteria.'
        )

        node_values = NodeUtil.get_permissible_values()
        status_values = [status for status in DoiStatus]

        action_parser.add_argument(
            '-n', '--node', required=False, metavar='"img,eng"',
            help='A list of comma-separated node names to filter the available '
                 'DOI entries by. Valid values are: ' + ','.join(node_values)
        )
        action_parser.add_argument(
            '-status', '--status', required=False, metavar="draft,review",
            help='A list of comma-separated submission status values to filter '
                 'the database query results by. Valid status values are: '
                 '{}'.format(', '.join(status_values))
        )
        action_parser.add_argument(
            '-f', '--format',  default='JSON', required=False, metavar='JSON',
            help='The format of the output from the database query. Currently, '
                 'only JSON format is supported.'
        )
        action_parser.add_argument(
            '-doi', '--doi', required=False, metavar='10.17189/21734',
            help='A list of comma-delimited DOI values to use as filters with the '
                 'database query.'
        )
        action_parser.add_argument(
            '-i', '--ids', required=False,
            metavar='urn:nasa:pds:lab_shocked_feldspars',
            help='A list of comma-delimited PDS identifiers to use as filters with '
                 'the database query. Each ID may contain one or more wildcards '
                 '(*) to pattern match against.'
        )
        action_parser.add_argument(
            '-start', '--start-update', required=False,
            metavar='2020-01-01T19:02:15.000000',
            help='The start time of the record update to use as a filter with the '
                 'database query. Should conform to a valid isoformat date string.'
        )
        action_parser.add_argument(
            '-end', '--end-update', required=False,
            metavar='2020-12-311T23:59:00.000000',
            help='The end time for record update time to use as a filter with the '
                 'database query. Should conform to a valid isoformat date string.'
        )
        action_parser.add_argument(
            '-s', '--submitter', required=False, metavar='"my.email@node.gov"',
            help='A list of comma-separated email addresses to use as a filter '
                 'with the database query. Only entries containing the one of '
                 'the provided addresses as the submitter will be returned.'
        )

    def transaction_for_identifier(self, identifier):
        """
        Returns the latest transaction record for the provided PDS identifier.

        Parameters
        ----------
        identifier : str
            The PDS identifier to search for.

        Returns
        -------
        record : dict
            Latest transaction database record for the given identifier.

        Raises
        ------
        UnknownLIDVIDException
            If no entry can be found in the transaction database for the
            provided identifier.

        """
        list_kwargs = {'ids': identifier}
        list_results = json.loads(self.run(**list_kwargs))

        if not list_results:
            raise UnknownLIDVIDException(
                f'No record(s) could be found for identifier {identifier}.'
            )

        # Extract the latest record from all those returned
        record = next(filter(lambda list_result: list_result['is_latest'],
                             list_results))

        return record

    def run(self, **kwargs):
        """
        Lists all the latest records in the named database, returning the
        the results in JSON format.

        """
        self.parse_criteria(**kwargs)

        columns, rows = self._database_obj.select_latest_rows(self._query_criterias)

        # generate output
        if self._format == 'JSON':
            result_json = []

            for row in rows:
                # Convert the datetime objects to iso8601 strings
                for time_col in ('date_added', 'date_updated'):
                    row[columns.index(time_col)] = row[columns.index(time_col)].isoformat()

                result_json.append(dict(zip(columns, row)))

            o_query_result = json.dumps(result_json)
            logger.debug("o_select_result: %s", o_query_result)
        else:
            raise ValueError(f"Output format type {self._format} is not supported.")

        return o_query_result
