#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
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
from pds_doi_service.core.entities.doi import DoiEvent
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.exceptions import collect_exception_classes_and_messages
from pds_doi_service.core.entities.exceptions import CriticalDOIException
from pds_doi_service.core.entities.exceptions import DuplicatedTitleDOIException
from pds_doi_service.core.entities.exceptions import IllegalDOIActionException
from pds_doi_service.core.entities.exceptions import InputFormatException
from pds_doi_service.core.entities.exceptions import InvalidIdentifierException
from pds_doi_service.core.entities.exceptions import raise_or_warn_exceptions
from pds_doi_service.core.entities.exceptions import TitleDoesNotMatchProductTypeException
from pds_doi_service.core.entities.exceptions import UnexpectedDOIActionException
from pds_doi_service.core.entities.exceptions import WarningDOIException
from pds_doi_service.core.input.input_util import DOIInputUtil
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_validator import DOIValidator
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.util.general_util import get_global_keywords
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.util.node_util import NodeUtil

logger = get_logger(__name__)


class DOICoreActionReserve(DOICoreAction):
    _name = "reserve"
    _description = (
        "Submit a request to reserve a DOI prior to public release. "
        "Reserved DOI's may be released after via the release action"
    )
    _order = 0
    _run_arguments = ("input", "node", "submitter", "force")

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)
        self._input_util = DOIInputUtil(valid_extensions=[".xml", ".csv", ".xlsx", ".xls"])
        self._record_service = DOIServiceFactory.get_doi_record_service()
        self._validator_service = DOIServiceFactory.get_validator_service()
        self._web_client = DOIServiceFactory.get_web_client_service()

        self._input = None
        self._node = None
        self._submitter = None
        self._force = False

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(
            cls._name,
            description="Reserve DOI's for one or more unpublished datasets. "
            "DOI's will be assigned by the provider, but will not be "
            "publicly findable. To create findable records, utilize "
            "the Release action with the labels returned by this action.",
        )
        action_parser.add_argument(
            "-i",
            "--input",
            required=True,
            help="Path to a PDS4 XML label or XLS/CSV "
            "spreadsheet file with the following columns: " + ",".join(DOIInputUtil.MANDATORY_COLUMNS),
        )
        action_parser.add_argument(
            "-N",
            "--node",
            required=True,
            metavar="NODE_ID",
            help="The PDS Discipline Node in charge of the submission of the DOI(s). "
            "Authorized values are: {}".format(",".join(NodeUtil.get_permissible_node_ids())),
        )
        action_parser.add_argument(
            "-s",
            "--submitter",
            required=False,
            default="pds-operator@jpl.nasa.gov",
            metavar="EMAIL",
            help="The email address to associate with the Reserve request. Defaults to pds-operator@jpl.nasa.gov",
        )
        action_parser.add_argument(
            "-f",
            "--force",
            required=False,
            action="store_true",
            help="If provided, forces the reserve action to proceed even if "
            "warnings are encountered during submission of the Reserve "
            "request. Without this flag, any warnings encountered are "
            "treated as fatal exceptions.",
        )

    def _parse_input(self, input_file):
        """
        Parses the provided input file to one or more DOI objects.

        Parameters
        ----------
        input_file : str
            Path to the input file location to parse.

        Returns
        -------
        dois : list of Doi
            The DOI objects parsed from the input file.

        """
        return self._input_util.parse_dois_from_input_file(input_file)

    def _complete_dois(self, dois):
        """
        Ensures the list of DOI objects to reserve have the requisite fields,
        such as status or contributor, filled in prior to submission.

        Parameters
        ----------
        dois : list of Doi
            The list of DOI objects to complete

        Returns
        -------
        dois : list of Doi
            The completed list of DOI objects.

        """
        for doi in dois:
            # First set node, contributor, and publisher at the beginning of the function
            # to ensure that they are set in case of an exception.
            doi.node_id = self._node
            doi.contributor = NodeUtil.get_node_long_name(self._node)
            doi.publisher = self._config.get("OTHER", "doi_publisher")

            # Add 'status' field so the ranking in the workflow can be determined
            doi.status = DoiStatus.Draft

            # Make sure the global keywords from the config are included
            doi.keywords.update(get_global_keywords())

            # Add the event field to instruct DataCite to make this entry
            # hidden so it can be modified (should have no effect for other
            # providers)
            doi.event = DoiEvent.Hide

        return dois

    def _validate_dois(self, dois):
        """
        Validates the list of DOI objects prior to their submission.

        Depending on the configuration of the DOI service, DOI objects may
        be validated against a schema as well as the internal checks performed
        by the validator class.

        Any exceptions or warnings encountered during the checks are stored
        until all DOI's have been checked. Depending on the state of the
        force flag, these collected exceptions are either raised as a single
        exception, or simply logged.

        Parameters
        ----------
        dois : list of Doi
            The DOI objects to validate.

        Returns
        -------
        dois : list of Doi
            The validated list of DOI objects.

        """
        exception_classes = []
        exception_messages = []

        for doi in dois:
            if doi.doi:
                raise IllegalDOIActionException(
                    f"Provided record with identifier {doi.pds_identifier} already has a DOI ({doi.doi}) assigned.\n"
                    f"Please use the Update action to modify records with existing DOI."
                )

            try:
                # Validate the object representation of the DOI
                self._doi_validator.validate_reserve_request(doi)
            # Collect all warnings and exceptions so they can be combined into
            # a single WarningDOIException
            except (
                DuplicatedTitleDOIException,
                InvalidIdentifierException,
                UnexpectedDOIActionException,
                TitleDoesNotMatchProductTypeException,
            ) as err:
                (exception_classes, exception_messages) = collect_exception_classes_and_messages(
                    err, exception_classes, exception_messages
                )

        # If there is at least one exception caught, either raise a
        # WarningDOIException or log a warning with all the messages,
        # depending on the the state of the force flag
        if len(exception_classes) > 0:
            raise_or_warn_exceptions(exception_classes, exception_messages, log=self._force)

        return dois

    def run(self, **kwargs):
        """
        Performs a reserve of a new DOI.

        Parameters
        ----------
        kwargs : dict
            The parsed command-line arguments for the reserve action.

        Returns
        -------
        output_label : str
            The output label, in JSON format, reflecting the status of the
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

            for input_doi in dois:
                # Create the JSON request label to send
                io_doi_label = self._record_service.create_doi_record(input_doi, content_type=CONTENT_TYPE_JSON)

                # Submit the Reserve request
                # Determine the correct HTTP verb and URL for submission of this DOI
                method, url = self._web_client.endpoint_for_doi(input_doi, self._name)

                output_doi, o_doi_label = self._web_client.submit_content(
                    method=method, url=url, payload=io_doi_label, content_type=CONTENT_TYPE_JSON
                )

                # Log the inputs and outputs of this transaction
                transaction = self.m_transaction_builder.prepare_transaction(
                    self._submitter,
                    output_doi,
                    input_path=input_doi.input_source,
                    output_content_type=CONTENT_TYPE_JSON,
                )

                # Commit the transaction to the local database
                transaction.log()

                # Append the latest version of the Doi object to return as a label
                output_dois.append(output_doi)

        # Propagate input format exceptions, force flag should not affect
        # these being raised and certain callers (such as the API) look
        # for this exception specifically
        except InputFormatException as err:
            raise err
        # If we catch this exception, it means validation produced a warning
        # and the --force flag is not set, so log the error and exit without
        # producing an output label
        except WarningDOIException as err:
            logger.error(str(err))
            raise err
        # Convert all other errors into a CriticalDOIException to report back
        except Exception as err:
            error_message = str(err)
            bad_credentials_error_substr = "reason: 404 Client Error"
            if bad_credentials_error_substr in error_message:
                explanatory_message = "This error may also be indicative of bad credentials when returned by DataCite."
                raise CriticalDOIException(f"{error_message}.  {explanatory_message}")

            raise CriticalDOIException(err)

        # Create the return output label containing records for all submitted DOI's
        # Note this action always returns JSON format to ensure interoperability
        # between the potential service providers
        output_label = self._record_service.create_doi_record(output_dois, content_type=CONTENT_TYPE_JSON)

        return output_label
