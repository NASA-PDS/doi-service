#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
==========
reserve.py
==========

Contains the definition for the Reserve action of the Core PDS DOI Service.
"""

from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.input.exceptions import (CriticalDOIException,
                                                   DuplicatedTitleDOIException,
                                                   InputFormatException,
                                                   InvalidIdentifierException,
                                                   SiteURLNotExistException,
                                                   TitleDoesNotMatchProductTypeException,
                                                   UnexpectedDOIActionException,
                                                   collect_exception_classes_and_messages,
                                                   raise_or_warn_exceptions)
from pds_doi_service.core.input.input_util import DOIInputUtil
from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_validator import DOIValidator
from pds_doi_service.core.outputs.osti.osti_record import DOIOstiRecord
from pds_doi_service.core.outputs.osti.osti_validator import DOIOstiValidator
from pds_doi_service.core.outputs.osti.osti_web_client import DOIOstiWebClient
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOICoreActionReserve(DOICoreAction):
    _name = 'reserve'
    _description = 'Create or update a DOI before the data is published'
    _order = 0
    _run_arguments = ('input', 'node', 'submitter', 'dry_run', 'force')

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)
        self._osti_validator = DOIOstiValidator()
        self._input_util = DOIInputUtil()

        self._input = None
        self._node = None
        self._submitter = None
        self._force = False
        self._dry_run = True

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(
            cls._name, description='Create a DOI for one or more unpublished datasets. '
                                   'The input is a spreadsheet or CSV file '
                                   'containing records to reserve DOIs for.')

        node_values = NodeUtil.get_permissible_values()
        action_parser.add_argument(
            '-n', '--node', required=True, metavar='"img"',
            help="The PDS Discipline Node in charge of the submission of the DOI. "
                 "Authorized values are: " + ','.join(node_values)
        )
        action_parser.add_argument(
            '-f', '--force', required=False, action='store_true',
            help='If provided, forces the reserve action to proceed even if '
                 'warnings are encountered during submission of the reserve '
                 'request. Without this flag, any warnings encountered are '
                 'treated as fatal exceptions.'
        )
        action_parser.add_argument(
            '-i', '--input', required=True,
            metavar='input/DOI_Reserved_GEO_200318.csv',
            help='A PDS4 XML label, OSTI XML/JSON label or XLS/CSV '
                 'spreadsheet file with the following columns: ' +
                 ','.join(DOIInputUtil.MANDATORY_COLUMNS)
        )
        action_parser.add_argument(
            '-s', '--submitter', required=True, metavar='"my.email@node.gov"',
            help='The email address to associate with the Reserve request.'
        )
        action_parser.add_argument(
            '-dry-run', '--dry-run', required=False, action='store_true',
            help="Performs the Reserve request without submitting the record. "
                 "The record is logged to the local database with a status "
                 "of 'reserved_not_submitted'."
        )

    def _parse_input(self, input_file):
        return self._input_util.parse_dois_from_input_file(input_file)

    def _complete_dois(self, dois):
        """
        Ensures the list of Doi objects to reserve have the requisite fields,
        such as status or contributor, filled in prior to submission.

        Parameters
        ----------
        dois : list of Doi
            The list of Doi objects to complete

        Returns
        -------
        dois : list of Doi
            The completed list of Doi objects.

        """
        for doi in dois:
            # First set contributor, publisher at the beginning of the function
            # to ensure that they are set in case of an exception.
            doi.contributor = NodeUtil().get_node_long_name(self._node)
            doi.publisher = self._config.get('OTHER', 'doi_publisher')

            # Add 'status' field so the ranking in the workflow can be determined
            doi.status = DoiStatus.Reserved_not_submitted if self._dry_run else DoiStatus.Reserved

        return dois

    def _validate_dois(self, dois):
        """
        Validates the list of Doi objects prior to their submission.

        Depending on the configuration of the DOI service, Doi objects may
        be validated against the OSTI XSD, schematron, as well as the internal
        checks performed by the DOIValidator class.

        Any exceptions or warnings encountered during the checks are stored
        until all Doi's have been checked. Depending on the state of the
        force flag, these collected exceptions are either raised as a single
        exception, or simply logged.

        Parameters
        ----------
        dois : list of Doi
            The Doi objects to validate.

        Returns
        -------
        dois : list of Doi
            The validated list of Doi objects.

        """
        exception_classes = []
        exception_messages = []

        for doi in dois:
            try:
                single_doi_label = DOIOstiRecord().create_doi_record(doi)

                # Validate XML representation of the DOI
                self._osti_validator.validate(single_doi_label)

                # Validate the object representation of the DOI
                self._doi_validator.validate(doi)
            # Collect all warnings and exceptions so they can be combined into
            # a single WarningDOIException
            except (DuplicatedTitleDOIException,
                    InvalidIdentifierException,
                    UnexpectedDOIActionException,
                    TitleDoesNotMatchProductTypeException,
                    SiteURLNotExistException) as err:
                (exception_classes,
                 exception_messages) = collect_exception_classes_and_messages(
                    err, exception_classes, exception_messages
                )

        # If there is at least one exception caught, either raise a
        # WarningDOIException or log a warning with all the messages,
        # depending on the the state of the force flag
        if len(exception_classes) > 0:
            raise_or_warn_exceptions(exception_classes, exception_messages,
                                     log=self._force)

        return dois

    def run(self, **kwargs):
        """
        Performs a reserve of a new DOI.

        Parameters
        ----------
        kwargs : dict
            The parsed command-line arguments for the release action.

        Returns
        -------
        output_label : str
            The output label, in OSTI json format, reflecting the status of the
            reserved input DOI's.

        Raises
        ------
        CriticalDOIException
            If any unrecoverable errors are encountered during validation of
            the input DOI's.

        """
        output_dois = []

        self.parse_arguments(kwargs)

        try:
            # Parse, complete and validate the set of provided DOI's
            dois = self._parse_input(self._input)
            dois = self._complete_dois(dois)
            dois = self._validate_dois(dois)

            for doi in dois:
                # Create the JSON request label to send
                io_doi_label = DOIOstiRecord().create_doi_record(
                    doi, content_type=CONTENT_TYPE_JSON
                )

                # Submit the Reserve request if this isn't a dry run
                if not self._dry_run:
                    doi, o_doi_label = DOIOstiWebClient().submit_content(
                        payload=io_doi_label,
                        content_type=CONTENT_TYPE_JSON
                    )

                # Log the inputs and outputs of this transaction
                transaction = self.m_transaction_builder.prepare_transaction(
                    self._node, self._submitter, doi, input_path=self._input,
                    output_content_type=CONTENT_TYPE_JSON
                )

                # Commit the transaction to the local database
                transaction.log()

                # Append the latest version of the Doi object to return
                # as a label
                output_dois.append(doi)

        # Propagate input format exceptions, force flag should not affect
        # these being raised and certain callers (such as the API) look
        # for this exception specifically
        except InputFormatException as err:
            raise err
        # Convert all other errors into a CriticalDOIException to report back
        except Exception as err:
            raise CriticalDOIException(err)

        output_label = DOIOstiRecord().create_doi_record(
            output_dois, content_type=CONTENT_TYPE_JSON
        )

        return output_label
