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

from datetime import datetime, timezone, timedelta
import json

from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.input.exceptions import UnknownLIDVIDException
from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOICoreActionList(DOICoreAction):
    _name = 'list'
    _description = 'extract doi descriptions with criteria'
    _order = 40
    _run_arguments = ('format', 'doi', 'lid', 'lidvid', 'node', 'status',
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

    def parse_criteria(self, format='JSON', doi=None, lid=None, lidvid=None,
                       node=None, status=None, start_update=None,
                       end_update=None, submitter=None):

        self._format = format

        if doi:
            self._query_criterias['doi'] = doi.split(',')

        if lid:
            self._query_criterias['lid'] = lid.split(',')

        if lidvid:
            self._query_criterias['lidvid'] = lidvid.split(',')

        if submitter:
            self._query_criterias['submitter'] = submitter.split(',')

        if node:
            self._query_criterias['node'] = node.strip().split(',')

        if status:
            self._query_criterias['status'] = status.strip().split(',')

        if start_update:
            self._query_criterias['start_update'] = datetime.fromisoformat(start_update)

        if end_update:
            self._query_criterias['end_update'] = datetime.fromisoformat(end_update)

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
            help='A list of node names comma separated to return the matching '
                 'DOI. Authorized values are: ' + ','.join(node_values)
        )
        action_parser.add_argument(
            '-status', '--status', required=False, metavar="draft,review",
            help='A list of comma-separated submission status values to pass '
                 'as input to the database query. Valid status values are: '
                 '{}'.format(', '.join(status_values))
        )
        action_parser.add_argument(
            '-f', '--format',  default='JSON', required=False, metavar='JSON',
            help='The format of the output from the database query. Currently, '
                 'only JSON format is supported.'
        )
        action_parser.add_argument(
            '-doi', '--doi', required=False, metavar='10.17189/21734',
            help='A list of comma-delimited DOIs to pass as input to the '
                 'database query.'
        )
        action_parser.add_argument(
            '-lid', '--lid', required=False,
            metavar='urn:nasa:pds:lab_shocked_feldspars',
            help='A list of comma-delimited LIDs to pass as input to the '
                 'database query. Each LID may contain one or more wildcards '
                 '(*) to pattern match against.'
        )
        action_parser.add_argument(
            '-lidvid', '--lidvid', required=False,
            metavar='urn:nasa:pds:lab_shocked_feldspars::1.0',
            help='A list of comma-delimited LIDVIDs to pass as input to the '
                 'database query. Each LIDVID may contain one or more wildcards '
                 '(*) to pattern match against.'
        )
        action_parser.add_argument(
            '-start', '--start-update', required=False,
            metavar='2020-01-01T19:02:15.000000',
            help='The start time of the record update to pass as input to the '
                 'database query.'
        )
        action_parser.add_argument(
            '-end', '--end-update', required=False,
            metavar='2020-12-311T23:59:00.000000',
            help='The end time for record update time to pass as input to the '
                 'database query.'
        )
        action_parser.add_argument(
            '-s', '--submitter', required=False, metavar='"my.email@node.gov"',
            help='A list of email addresses comma separated to pass as input to '
                 'the database query.'
        )

    def transaction_for_lidvid(self, lidvid):
        """
        Returns the latest transaction record for the provided LIDVID.

        Parameters
        ----------
        lidvid : str
            The LIDVID to search for.

        Returns
        -------
        record : dict
            Latest Transaction Database record for the given LIDVID.

        Raises
        ------
        UnknownLIDVIDException
            If no entry can be found in the transaction database for the
            provided LIDVID.

        """
        list_kwargs = {'lidvid': lidvid}
        list_results = json.loads(self.run(**list_kwargs))

        if not list_results:
            raise UnknownLIDVIDException(
                f'No record(s) could be found for LIDVID {lidvid}.'
            )

        # Extract the latest record from all those returned
        record = next(filter(lambda list_result: list_result['is_latest'],
                             list_results))

        return record

    def run(self, **kwargs):
        """
        Lists all the latest records in the named database, returning the
        the results in JSON format.

        :param kwargs:
        :return: o_list_result:
        """
        self.parse_criteria(**kwargs)

        columns, rows = self._database_obj.select_latest_rows(self._query_criterias)

        # generate output
        if self._format == 'JSON':
            result_json = []

            for row in rows:
                # Convert the update time from Unix epoch to iso8601 including tz
                row = list(row)
                update_date = row[columns.index('update_date')]
                update_date = (datetime.fromtimestamp(update_date, tz=timezone.utc)
                               .replace(tzinfo=timezone(timedelta(hours=--8.0)))
                               .isoformat())
                row[columns.index('update_date')] = update_date

                # Convert status back to an Enum, force to lowercase
                # to handle any legacy uppercase status values
                row[columns.index('status')] = DoiStatus(row[columns.index('status')].lower())

                result_json.append({columns[i]: row[i]
                                    for i in range(len(columns))})

            o_query_result = json.dumps(result_json)
            logger.debug("o_select_result: %s", o_query_result)
        else:
            raise ValueError(f"Output format type {self._format} is not supported.")

        return o_query_result
