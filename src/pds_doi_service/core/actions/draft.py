#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
========
draft.py
========

Contains the definition for the Draft action of the Core PDS DOI Service.
"""
import glob
from os.path import exists
from os.path import join

from pds_doi_service.core.actions import DOICoreAction
from pds_doi_service.core.actions.list import DOICoreActionList
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.input.exceptions import collect_exception_classes_and_messages
from pds_doi_service.core.input.exceptions import CriticalDOIException
from pds_doi_service.core.input.exceptions import DuplicatedTitleDOIException
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.exceptions import InvalidIdentifierException
from pds_doi_service.core.input.exceptions import NoTransactionHistoryForIdentifierException
from pds_doi_service.core.input.exceptions import raise_or_warn_exceptions
from pds_doi_service.core.input.exceptions import TitleDoesNotMatchProductTypeException
from pds_doi_service.core.input.exceptions import UnexpectedDOIActionException
from pds_doi_service.core.input.input_util import DOIInputUtil
from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_validator import DOIValidator
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOICoreActionDraft(DOICoreAction):
    _name = "draft"
    _description = "Prepare a draft DOI record created from PDS4 labels."
    _order = 10
    _run_arguments = ("input", "node", "submitter", "lidvid", "force", "keywords")

    DEFAULT_KEYWORDS = ["PDS", "PDS4"]
    """Default keywords added to each new draft request."""

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)
        self._record_service = DOIServiceFactory.get_doi_record_service()
        self._validator_service = DOIServiceFactory.get_validator_service()
        self._web_parser = DOIServiceFactory.get_web_parser_service()

        self._list_obj = DOICoreActionList(db_name=db_name)

        self._input = None
        self._node = None
        self._submitter = None
        self._lidvid = None
        self._force = False
        self._target = None
        self._keywords = ""

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(
            cls._name, description="Create a draft DOI record from existing PDS4 or DOI " "labels."
        )

        node_values = NodeUtil.get_permissible_values()
        action_parser.add_argument(
            "-i",
            "--input",
            required=False,
            metavar="input/bundle_in_with_contributors.xml",
            help="An input PDS4/DOI label. May be a local path or an HTTP address "
            "resolving to a label file. Multiple inputs may be provided "
            "via comma-delimited list. Must be provided if --lidvid is not "
            "specified.",
        )
        action_parser.add_argument(
            "-n",
            "--node",
            required=True,
            metavar='"img"',
            help="The PDS Discipline Node in charge of the DOI. Authorized " "values are: " + ",".join(node_values),
        )
        action_parser.add_argument(
            "-s",
            "--submitter",
            required=True,
            metavar='"my.email@node.gov"',
            help="The email address to associate with the Draft record.",
        )
        action_parser.add_argument(
            "-l",
            "--lidvid",
            required=False,
            metavar="urn:nasa:pds:lab_shocked_feldspars::1.0",
            help="A LIDVID for an existing DOI record to move back to draft "
            "status. Must be provided if --input is not specified.",
        )
        action_parser.add_argument(
            "-f",
            "--force",
            required=False,
            action="store_true",
            help="If provided, forces the action to proceed even if warnings are "
            "encountered during submission of the draft record to the "
            "database. Without this flag, any warnings encountered are "
            "treated as fatal exceptions.",
        )
        action_parser.add_argument(
            "-k",
            "--keywords",
            required=False,
            metavar='"Image"',
            default="",
            help="Extra keywords to associate with the Draft record. Multiple "
            'keywords must be separated by ",". Ignored when used with the '
            "--lidvid option.",
        )

    def _add_extra_keywords(self, keywords, io_doi):
        """
        Adds any extra keywords to the already produced DOI object.

        Parameters
        ----------
        keywords : str
            Comma-delimited string of additional keywords to associate to the
            provided DOI object.
        io_doi : Doi
            DOI object to assign keywords to.

        Returns
        -------
        io_doi : Doi
            The provided DOI object with additional keywords added.

        """
        # Add in the default set of keywords.
        io_doi.keywords |= set(self.DEFAULT_KEYWORDS)

        # Add the node long name (contributor) as a keyword as well.
        io_doi.keywords.add(io_doi.contributor.lower())

        # The keywords are comma separated. The io_doi.keywords field is a set.
        if keywords:
            keyword_tokens = set(map(str.strip, keywords.split(",")))

            io_doi.keywords |= keyword_tokens

        return io_doi

    def _transform_label_into_doi_objects(self, input_file, keywords):
        """
        Parses and returns a number of in-memory DOI objects from the provided
        input file.

        Parameters
        ----------
        input_file : str
            Path to the input file to parse DOI objects from.
        keywords : str
            Comma-delimited string of keywords to associate to each DOI object
            parsed from the input file.

        Returns
        -------
        o_dois : list of Doi
            The list of DOI objects parsed from the input file. If the file
            contains only a single DOI, a list of length 1 is returned.

        """
        input_util = DOIInputUtil(valid_extensions=[".json", ".xml"])

        o_dois = input_util.parse_dois_from_input_file(input_file)

        for o_doi in o_dois:
            o_doi.publisher = self._config.get("OTHER", "doi_publisher")
            o_doi.contributor = NodeUtil().get_node_long_name(self._node)

            # Add 'status' field so the ranking in the workflow can be determined.
            o_doi.status = DoiStatus.Draft

            # Add any default keywords or extra keywords provided by the user.
            self._add_extra_keywords(keywords, o_doi)

        # Return the list of all individual DOI's parsed.
        return o_dois

    def _run_single_file(self, input_file, node, submitter, force_flag, keywords):
        """
        Processes a single input file into one or more in-memory DOI objects
        set to the draft state. Each parsed DOI is then committed to the local
        transaction database in the draft state.

        Parameters
        ----------
        input_file : str
            Path to the input file to parse DOI objects from.
        node : str
            PDS node identifier associated with the draft request.
        submitter : str
            Email address associated with the submitter of the draft request.
        force_flag : bool
            If true, bypasses certain warnings raised from the validation of
            parsed DOI objects. Warnings will instead by printed to the output
            log.
        keywords : str
            Comma-delimited string of keywords to associate with each parsed
            DOI object.

        Returns
        -------
        dois : list of Doi
            The DOI objects parsed from the provided input file.

        """
        logger.info("Drafting input file %s", input_file)
        logger.debug("node,submitter,force_flag,keywords: %s,%s,%s,%s", node, submitter, force_flag, keywords)

        exception_classes = []
        exception_messages = []

        # Transform the input label to a list of Doi objects,
        # then validate each accordingly
        dois = self._transform_label_into_doi_objects(input_file, keywords)

        for doi in dois:
            try:
                self._doi_validator.validate(doi)
            # Collect any exceptions/warnings for now and decide whether to
            # raise or log them later on
            except (
                DuplicatedTitleDOIException,
                InvalidIdentifierException,
                UnexpectedDOIActionException,
                TitleDoesNotMatchProductTypeException,
            ) as err:
                (exception_classes, exception_messages) = collect_exception_classes_and_messages(
                    err, exception_classes, exception_messages
                )
            # Propagate input format exceptions, force flag should not affect
            # these being raised and certain callers (such as the API) look
            # for this exception specifically
            except InputFormatException as err:
                raise err
            # Catch all other exceptions as errors
            except Exception as err:
                raise CriticalDOIException(err)

        # If there is at least one exception caught, either raise a
        # WarningDOIException or log a warning with all the messages,
        # depending on the the state of the force flag
        if len(exception_classes) > 0:
            raise_or_warn_exceptions(exception_classes, exception_messages, log=force_flag)

        for doi in dois:
            # Use TransactionBuilder to prepare all things related to writing to
            # the local transaction database.
            transaction = self.m_transaction_builder.prepare_transaction(
                node, submitter, doi, input_path=input_file, output_content_type=CONTENT_TYPE_JSON
            )

            # Commit the transaction to the database
            transaction.log()

        return dois

    def _draft_input_files(self, inputs):
        """
        Creates a draft record from the provided list of input files.

        Parameters
        ----------
        inputs : str
            Comma-delimited listing of the inputs to produce draft records for.
            These may be local paths to a file or directory, or remote URLs.

        Returns
        -------
        o_doi_label : str
            Text body of the DOI label containing the draft records for
            requested inputs. Format of the label is dependent on the service
            provided configured by the INI config (OSTI, DataCite, etc.)

        Raises
        ------
        CriticalDOIException
            If any errors occur during creation of the draft record.

        """
        dois = []

        # The value of input can be a list of names, or a directory.
        # Split them up and let the input util library handle determination
        # of each type
        list_of_inputs = inputs.split(",")

        # Filter out any empty strings from trailing commas
        list_of_inputs = list(filter(lambda input_file: len(input_file), list_of_inputs))

        # For each input file, transform the input into a list of in-memory
        # DOI objects, then concatenate to the master list of DOIs.
        for input_file in list_of_inputs:
            dois.extend(self._run_single_file(input_file, self._node, self._submitter, self._force, self._keywords))

        if dois:
            # Create a single label containing records for each draft DOI
            o_doi_label = self._record_service.create_doi_record(dois)

            # Make sure were returning a valid label
            self._validator_service.validate(o_doi_label)
        else:
            logger.warning("No DOI objects could be parsed from the provided " "list of inputs: %s", list_of_inputs)
            o_doi_label = ""

        return o_doi_label

    def _set_lidvid_to_draft(self, lidvid):
        """
        Sets the status of the transaction record corresponding to the provided
        LIDVID back draft. This can be typical for records that do not advance
        past the review step.

        Parameters
        ----------
        lidvid : str
            The LIDVID associated to the record to set to draft.

        Returns
        -------
        doi_label : str
            The label for the provided LIDVID reflecting its draft status.
            Label format is dependent on the DOI service provider configured
            in the INI.

        Raises
        ------
        NoTransactionHistoryForIdentifierException
            If an entry for the provided LIDVID exists in the transaction
            database, but no local transaction history can be found.

        """
        # Get the output label produced from the last transaction
        # with this LIDVID
        transaction_record = self._list_obj.transaction_for_identifier(lidvid)

        # Make sure we can locate the output label associated with this
        # transaction
        transaction_location = transaction_record["transaction_key"]
        label_files = glob.glob(join(transaction_location, "output.*"))

        if not label_files or not exists(label_files[0]):
            raise NoTransactionHistoryForIdentifierException(
                f"Could not find a DOI label associated with LIDVID {lidvid}. "
                "The database and transaction history location may be out of sync. "
                "Please try resubmitting the record in reserve or draft."
            )

        label_file = label_files[0]

        # Label could contain entries for multiple LIDVIDs, so extract
        # just the one we care about
        (lidvid_record, content_type) = self._web_parser.get_record_for_identifier(label_file, lidvid)

        # Format label into an in-memory DOI object
        dois, _ = self._web_parser.parse_dois_from_label(lidvid_record, content_type)

        # Should only ever get one object back
        doi = dois[0]

        # Update the status back to draft while noting the previous status
        doi.previous_status = doi.status
        doi.status = DoiStatus.Draft

        # Update the contributor
        doi.contributor = NodeUtil().get_node_long_name(self._node)

        # Re-commit transaction to official roll DOI back to draft status
        transaction = self.m_transaction_builder.prepare_transaction(
            self._node, self._submitter, doi, input_path=label_file, output_content_type=content_type
        )

        # Commit the transaction to the database
        transaction.log()

        # Return up-to-date output label
        return transaction.output_content

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
        self.parse_arguments(kwargs)

        # Make sure we've been given something to work with
        if self._input is None and self._lidvid is None:
            raise ValueError("A value must be provided for either --input or " "--lidvid when using the Draft action.")

        if self._lidvid:
            return self._set_lidvid_to_draft(self._lidvid)

        if self._input:
            return self._draft_input_files(self._input)
