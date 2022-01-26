#
#  Copyright 2021, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
=========
update.py
=========

Contains the definition for the Update action of the Core PDS DOI Service.
"""
from pds_doi_service.core.actions import DOICoreAction
from pds_doi_service.core.actions.list import DOICoreActionList
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.exceptions import collect_exception_classes_and_messages
from pds_doi_service.core.entities.exceptions import CriticalDOIException
from pds_doi_service.core.entities.exceptions import DuplicatedTitleDOIException
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


class DOICoreActionUpdate(DOICoreAction):
    _name = "update"
    _description = (
        "Update a record with or without submission to the service provider. "
        "Metadata updates are pulled from the provided input file for the corresponding "
        "DOI values."
    )
    _order = 10
    _run_arguments = ("input", "node", "submitter", "force")

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)
        self._input_util = DOIInputUtil()
        self._record_service = DOIServiceFactory.get_doi_record_service()
        self._validator_service = DOIServiceFactory.get_validator_service()
        self._web_client = DOIServiceFactory.get_web_client_service()
        self._web_parser = DOIServiceFactory.get_web_parser_service()

        self._list_action = DOICoreActionList(db_name=db_name)

        self._input = None
        self._node = None
        self._submitter = None
        self._force = False

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name, description="Update records with DOI's already assigned")

        node_values = NodeUtil.get_permissible_node_ids()
        action_parser.add_argument(
            "-i",
            "--input",
            required=True,
            metavar="INPUT",
            help="Path to an input XML/JSON label or CSV/XLS spreadsheet. May be "
            "a local path or an HTTP address resolving to a PDS4 label file. Each "
            "record parsed from the input MUST define a DOI value in order to be "
            "updated.",
        )
        action_parser.add_argument(
            "-N",
            "--node",
            required=False,
            default=None,
            metavar="NODE_ID",
            help="The PDS Discipline Node to assign to each updated record. If not provided,"
            "the node(s) currently assigned to each record are maintained. "
            "Authorized values are: " + ",".join(node_values),
        )
        action_parser.add_argument(
            "-s",
            "--submitter",
            required=False,
            default="pds-operator@jpl.nasa.gov",
            metavar="EMAIL",
            help="The email address to associate with the Update request. " "Defaults to pds-operator@jpl.nasa.gov",
        )
        action_parser.add_argument(
            "-f",
            "--force",
            required=False,
            action="store_true",
            help="If provided, forces the action to proceed even if warnings are "
            "encountered during submission of the updated record to the "
            "database. Without this flag, any warnings encountered are "
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

    @staticmethod
    def _meld_dois(existing_doi, new_doi):
        """
        Melds the fields from a new Doi object into an existing one, updating
        only those fields that are set on the new Doi and which are different
        from those in the existing.

        Parameters
        ----------
        existing_doi : Doi
            The existing Doi to update.
        new_doi : Doi
            The new Doi to meld into the existing.

        Returns
        -------
        updated_doi : Doi
            A new Doi object that represents the melding of the provided objects.

        """
        existing_doi_fields = existing_doi.__dict__.copy()
        new_doi_fields = new_doi.__dict__

        for key in existing_doi_fields:
            if new_doi_fields[key] and existing_doi_fields[key] != new_doi_fields[key]:
                # Don't overwrite the original date_record_added, if present in the existing record
                if key == "date_record_added" and existing_doi_fields["date_record_added"]:
                    continue

                # Don't overwrite existing status, we'll be saving it in previous_status later on
                if key == "status":
                    continue

                existing_doi_fields[key] = new_doi_fields[key]

        updated_doi = Doi(**existing_doi_fields)

        return updated_doi

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
            if self._node:
                doi.node_id = self._node
                doi.contributor = NodeUtil.get_node_long_name(self._node)

            doi.publisher = self._config.get("OTHER", "doi_publisher")

            # Store the previous status of this DOI
            doi.previous_status = doi.status

            # Make sure the global keywords from the config are included
            doi.keywords.update(get_global_keywords())

            # If this DOI has already been released (aka is findable or in review),
            # then move the status back to the Review step. Otherwise, the record
            # should still be in draft.
            if doi.previous_status in (DoiStatus.Findable, DoiStatus.Review):
                doi.status = DoiStatus.Review
            else:
                doi.status = DoiStatus.Draft

        return dois

    def _update_dois(self, dois):
        """
        Updates the local transaction database using the provided Doi objects.
        The updates are not pushed to the service provider.

        Parameters
        ----------
        dois : Iterable[Doi]
            The Dois to update.

        Returns
        -------
        updated_dois : list[Doi]
            The list of Dois reflecting their update state. This includes melding
            with any existing Doi object with the same DOI value.

        """
        updated_dois = []

        for updated_doi in dois:
            if not updated_doi.doi:
                raise RuntimeError(
                    f"Record provided for identifier {updated_doi.pds_identifier} does not have a DOI assigned.\n"
                    "Use the Reserve action to acquire a DOI for the record before attempting to update it."
                )

            # Get the record from the transaction database for the current DOI value
            transaction_record = self._list_action.transaction_for_doi(updated_doi.doi)

            # Get the last output label associated with the transaction.
            # This represents the latest version of the metadata for the DOI.
            output_label = self._list_action.output_label_for_transaction(transaction_record)

            # Output labels can contain multiple entries, so get only the one for
            # the current DOI value
            existing_doi_label, _ = self._web_parser.get_record_for_doi(output_label, updated_doi.doi)

            # Parse the existing Doi object, and meld it with the new one
            existing_dois, _ = self._web_parser.parse_dois_from_label(existing_doi_label)

            updated_doi = self._meld_dois(existing_dois[0], updated_doi)

            updated_dois.append(updated_doi)

        return updated_dois

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
            try:
                single_doi_label = self._record_service.create_doi_record(doi)

                # Validate the label representation of the DOI
                self._validator_service.validate(single_doi_label)

                # Validate the object representation of the DOI
                self._doi_validator.validate_update_request(doi)
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
        Receives a number of input label locations from which to create a
        draft Data Object Identifier (DOI). Each location may be a local directory
        or file path, or a remote HTTP address to the input XML PDS4 label file.

        Parameters
        ----------
        kwargs : dict
            Contains the arguments for the Draft action as parsed from the
            command-line.

        Raises
        ------
        ValueError
            If the provided arguments are invalid.

        """
        updated_dois = []

        self.parse_arguments(kwargs)

        try:
            dois = self._parse_input(self._input)
            dois = self._update_dois(dois)
            dois = self._complete_dois(dois)
            dois = self._validate_dois(dois)

            for doi in dois:
                transaction = self.m_transaction_builder.prepare_transaction(
                    self._submitter,
                    doi,
                    input_path=doi.input_source,
                    output_content_type=CONTENT_TYPE_JSON,
                )

                transaction.log()

                updated_dois.append(doi)
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
            return None
        # Convert all other errors into a CriticalDOIException to report back
        except Exception as err:
            raise CriticalDOIException(str(err))

        # Create the return output label containing records for all updated DOI's
        # Note this action always returns JSON format to ensure interoperability
        # between the potential service providers
        output_label = self._record_service.create_doi_record(updated_dois, content_type=CONTENT_TYPE_JSON)

        return output_label
