#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
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
import glob
import json
from os.path import exists
from os.path import join

from dateutil.parser import isoparse
from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.exceptions import NoTransactionHistoryForIdentifierException
from pds_doi_service.core.entities.exceptions import UnknownDoiException
from pds_doi_service.core.entities.exceptions import UnknownIdentifierException
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.util.node_util import NodeUtil

logger = get_logger(__name__)

FORMAT_RECORD = "record"
FORMAT_LABEL = "label"
VALID_FORMATS = [FORMAT_RECORD, FORMAT_LABEL]


class DOICoreActionList(DOICoreAction):
    _name = "list"
    _description = "List DOI entries within the transaction database that match the provided search criteria"
    _order = 40
    _run_arguments = ("format", "doi", "ids", "node", "status", "start_update", "end_update", "submitter")

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)

        if db_name:
            # If database name is specified from user, use it.
            self.m_default_db_file = db_name
        else:
            # Default name of the database.
            self.m_default_db_file = self._config.get("OTHER", "db_file")

        self._database_obj = DOIDataBase(self.m_default_db_file)
        self._record_service = DOIServiceFactory.get_doi_record_service()
        self._web_parser = DOIServiceFactory.get_web_parser_service()

        self._format = None
        self._doi = None
        self._ids = None
        self._node = None
        self._status = None
        self._start_update = None
        self._end_update = None
        self._submitter = None

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(
            cls._name,
            description="Extracts the submitted DOI from the local transaction database using "
            "the following selection criteria. Output is returned in JSON format.",
        )

        node_values = NodeUtil.get_permissible_node_ids()
        status_values = [status for status in DoiStatus]

        action_parser.add_argument(
            "-f",
            "--format",
            required=False,
            default=FORMAT_RECORD,
            choices=VALID_FORMATS,
            help="Specify the format of the results returned by the list query. "
            'Valid options are "record" for a list of transaction records, or '
            '"label" for an output JSON label containing entries for all '
            'DOI records that match the query. Defaults to "record".',
        )
        action_parser.add_argument(
            "-N",
            "--node",
            required=False,
            metavar="NODE_ID[,NODE_ID]...",
            help="A list of comma-separated node names to filter the available "
            "DOI entries by. Valid values are: " + ",".join(node_values),
        )
        action_parser.add_argument(
            "-status",
            "--status",
            required=False,
            metavar="STATUS[,STATUS]...",
            help="A list of comma-separated submission status values to filter "
            "the database query results by. Valid status values are: {}".format(", ".join(status_values)),
        )
        action_parser.add_argument(
            "-doi",
            "--doi",
            required=False,
            metavar="DOI[,DOI]...",
            help="A list of comma-delimited DOI values to use as filters with the database query. "
            "Each DOI may contain one or more wildcards (*) to pattern match against.",
        )
        action_parser.add_argument(
            "-i",
            "--ids",
            required=False,
            metavar="ID[,ID]...",
            help="A list of comma-delimited PDS identifiers to use as filters with "
            "the database query. Each ID may contain one or more wildcards "
            "(*) to pattern match against.",
        )
        action_parser.add_argument(
            "-start",
            "--start-update",
            required=False,
            metavar="YYYY-MM-DD[THH:mm:ss.ssssss[Z]]",
            help="The start time of the record update to use as a filter with the "
            "database query. Should conform to a valid isoformat date string. By "
            "default, the local time zone is assumed. To provide a time in UTC, "
            "append a 'Z' to the time portion of the provided date-time.",
        )
        action_parser.add_argument(
            "-end",
            "--end-update",
            required=False,
            metavar="YYYY-MM-DD[THH:mm:ss.ssssss[Z]]",
            help="The end time for record update time to use as a filter with the "
            "database query. Should conform to a valid isoformat date string. By "
            "default, the local time zone is assumed. To provide a time in UTC, "
            "append a 'Z' to the time portion of the provided date-time.",
        )
        action_parser.add_argument(
            "-s",
            "--submitter",
            required=False,
            metavar="EMAIL",
            help="A list of comma-separated email addresses to use as a filter "
            "with the database query. Only entries containing the one of "
            "the provided addresses as the submitter will be returned.",
        )

    def parse_criteria(self, kwargs):
        """
        Parse the command-line criteria into a dictionary format suitable
        for use to query the the local transaction database.

        Note that this method takes the place of DOICoreAction.parse_arguments.

        Parameters
        ----------
        kwargs : dict
            The command-line arguments as parsed by argparse.

        Returns
        -------
        query_criteria : dict
            Dictionary mapping each criteria type to the list of values to
            filter by.

        """
        super(DOICoreActionList, self).parse_arguments(kwargs)

        query_criteria = {}

        if self._doi:
            query_criteria["doi"] = self._doi.split(",")

        if self._ids:
            query_criteria["ids"] = self._ids.split(",")

        if self._submitter:
            query_criteria["submitter"] = self._submitter.split(",")

        if self._node:
            query_criteria["node"] = self._node.strip().split(",")

        if self._status:
            query_criteria["status"] = self._status.strip().split(",")

        if self._start_update:
            query_criteria["start_update"] = isoparse(self._start_update)

        if self._end_update:
            query_criteria["end_update"] = isoparse(self._end_update)

        return query_criteria

    @staticmethod
    def output_label_for_transaction(transaction_record):
        """
        Returns a path to the output label associated to the provided transaction
        record.

        Parameters
        ----------
        transaction_record : dict
            Details of a transaction as returned from a list request.

        Returns
        -------
        label_file : str
            Path to the output label associated to the provided transaction record.

        Raises
        ------
        NoTransactionHistoryForIdentifierException
            If the output label associated to the transaction cannot be found
            on local disk.

        """
        # Make sure we can locate the output label associated with this
        # transaction
        transaction_location = transaction_record["transaction_key"]
        label_files = glob.glob(join(transaction_location, "output.*"))

        if not label_files or not exists(label_files[0]):
            raise NoTransactionHistoryForIdentifierException(
                f"Could not find a DOI label associated with identifier {transaction_record['identifier']}. "
                "The database and transaction history location may be out of sync."
            )

        label_file = label_files[0]

        return label_file

    def transaction_for_doi(self, doi):
        """
        Returns the latest transaction record for the provided DOI.

        Parameters
        ----------
        doi : str
            The DOI to search for.

        Returns
        -------
        record : dict
            Latest transaction database record for the given identifier.

        Raises
        ------
        UnknownDoiException
            If no entry can be found in the transaction database for the
            provided identifier.

        """
        list_kwargs = {"doi": doi}
        list_results = json.loads(self.run(**list_kwargs))

        if not list_results:
            raise UnknownDoiException(f"No record(s) could be found for DOI {doi}.")

        # Latest record should be the only one returned
        record = list_results[0]

        return record

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
        UnknownIdentifierException
            If no entry can be found in the transaction database for the
            provided identifier.

        """
        list_kwargs = {"ids": identifier}
        list_results = json.loads(self.run(**list_kwargs))

        if not list_results:
            raise UnknownIdentifierException(f"No record(s) could be found for identifier {identifier}.")

        # Latest record should be the only one returned
        record = list_results[0]

        return record

    def run(self, **kwargs):
        """
        Lists all the latest records in the named database, returning the
        the results in JSON format.

        Parameters
        ----------
        kwargs : dict
            Dictionary containing the list action argument names mapped
            to the criteria to filter results by.

        Returns
        -------
        o_query_result : str
            JSON formatted results from the list action query filtered by the
            provided criteria dictionary.

        """
        query_criteria = self.parse_criteria(kwargs)

        columns, rows = self._database_obj.select_latest_rows(query_criteria)

        transaction_records = []

        for row in rows:
            # Convert the datetime objects to iso8601 strings
            for time_col in ("date_added", "date_updated"):
                row[columns.index(time_col)] = row[columns.index(time_col)].isoformat()

            transaction_records.append(dict(zip(columns, row)))

        # For label format we need to obtain the output label for each transaction,
        # parse Doi objects from them, then reform all parsed Dois into the return label
        if self._format == FORMAT_LABEL:
            queried_dois = []

            for transaction_record in transaction_records:
                label_file = self.output_label_for_transaction(transaction_record)

                with open(label_file, "r") as infile:
                    label_contents = infile.read()
                    dois, _ = self._web_parser.parse_dois_from_label(label_contents)
                    queried_dois.extend(dois)

            if queried_dois:
                o_query_result = self._record_service.create_doi_record(queried_dois)
            else:
                o_query_result = ""
        # If output format is records, just need to dump transaction dictionary to a JSON string
        else:
            o_query_result = json.dumps(transaction_records)
            logger.debug("o_select_result: %s", o_query_result)

        return o_query_result
