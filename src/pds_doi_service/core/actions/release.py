#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
==========
release.py
==========

Contains the definition for the Release action of the Core PDS DOI Service.
"""
from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.entities.doi import DoiEvent
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.input.exceptions import collect_exception_classes_and_messages
from pds_doi_service.core.input.exceptions import CriticalDOIException
from pds_doi_service.core.input.exceptions import DuplicatedTitleDOIException
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.exceptions import InvalidIdentifierException
from pds_doi_service.core.input.exceptions import raise_or_warn_exceptions
from pds_doi_service.core.input.exceptions import SiteURLNotExistException
from pds_doi_service.core.input.exceptions import TitleDoesNotMatchProductTypeException
from pds_doi_service.core.input.exceptions import UnexpectedDOIActionException
from pds_doi_service.core.input.input_util import DOIInputUtil
from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_validator import DOIValidator
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.service import SERVICE_TYPE_DATACITE
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST
from pds_doi_service.core.outputs.web_client import WEB_METHOD_PUT
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOICoreActionRelease(DOICoreAction):
    _name = "release"
    _description = "Move a reserved DOI to review, or submit a DOI for " "release to the service provider."
    _order = 20
    _run_arguments = ("input", "node", "submitter", "force", "no_review")

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)
        self._input_util = DOIInputUtil(valid_extensions=[".xml", ".json"])
        self._record_service = DOIServiceFactory.get_doi_record_service()
        self._validator_service = DOIServiceFactory.get_validator_service()
        self._web_client = DOIServiceFactory.get_web_client_service()

        self._input = None
        self._node = None
        self._submitter = None
        self._force = False
        self._no_review = False

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(
            cls._name,
            description="Release a DOI, in draft or reserve status, for review. "
            "A DOI may also be released to the DOI service provider "
            "directly.",
        )
        action_parser.add_argument(
            "-n",
            "--node",
            required=True,
            metavar='"img"',
            help="The PDS Discipline Node in charge of the released DOI. "
            "Authorized values are: {}".format(",".join(NodeUtil.get_permissible_values())),
        )
        action_parser.add_argument(
            "-f",
            "--force",
            required=False,
            action="store_true",
            help="If provided, forces the release action to proceed even if "
            "warning are encountered during submission of the release "
            "request. Without this flag, any warnings encountered are "
            "treated as fatal exceptions.",
        )
        action_parser.add_argument(
            "-i",
            "--input",
            required=True,
            metavar="input/DOI_Update_GEO_200318.xml",
            help="A file containing a list of DOI metadata to update/release "
            "in OSTI JSON/XML format (see https://www.osti.gov/iad2/docs#record-model)."
            "The input is produced by the Reserve and Draft actions, and "
            "can be retrieved for a DOI with the List action.",
        )
        action_parser.add_argument(
            "-s",
            "--submitter",
            required=True,
            metavar='"my.email@node.gov"',
            help="The email address to associate with the Release request.",
        )
        action_parser.add_argument(
            "--no-review",
            required=False,
            action="store_true",
            help="If provided, the requested DOI will be released directly to "
            "the DOI service provider for registration. Use to override the "
            'default behavior of releasing a DOI to "review" status.',
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
            The list of Doi objects to complete

        Returns
        -------
        dois : list of Doi
            The completed list of Doi objects.

        """
        for doi in dois:
            # Make sure correct contributor and publisher fields are set
            doi.contributor = NodeUtil().get_node_long_name(self._node)
            doi.publisher = self._config.get("OTHER", "doi_publisher")

            # Add 'status' field so the ranking in the workflow can be determined.
            doi.status = DoiStatus.Pending if self._no_review else DoiStatus.Review

            if self._no_review:
                # Add the event field to instruct DataCite to publish DOI to
                # findable state (should have no effect for other providers)
                doi.event = DoiEvent.Publish

        return dois

    def _validate_dois(self, dois):
        """
        Validates the list of DOI objects prior to their submission.

        Depending on the configuration of the PDS DOI service, DOI objects may
        be validated against a schema as well as internal checks performed by
        the validator class.

        Any exceptions or warnings encountered during the checks are stored
        until all DOI's have been checked. Depending on the state of the
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
                single_doi_label = self._record_service.create_doi_record(doi)

                # Validate the label representation of the DOI
                self._validator_service.validate(single_doi_label)

                # Validate the object representation of the DOI
                self._doi_validator.validate(doi)
            except (
                DuplicatedTitleDOIException,
                InvalidIdentifierException,
                UnexpectedDOIActionException,
                TitleDoesNotMatchProductTypeException,
                SiteURLNotExistException,
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
        Performs a release of a DOI that has been previously reserved.

        A reserved DOI can be "released" either to the review step, or
        released directly to the DOI service provider for immediate registration.

        The input is a path to a text file containing the previously returned
        output of a 'reserve' or 'draft' action.

        Parameters
        ----------
        kwargs : dict
            The parsed command-line arguments for the release action.

        Returns
        -------
        output_label : str
            The output label text body reflecting the status of the released
            DOI(s).

        Raises
        ------
        CriticalDOIException
            If any unrecoverable errors are encountered during validation of
            the input DOI's.

        """
        output_dois = []

        self.parse_arguments(kwargs)

        try:
            # Parse, complete and validate the input dois prior to their
            # submission
            dois = self._parse_input(self._input)
            dois = self._complete_dois(dois)
            dois = self._validate_dois(dois)

            for doi in dois:
                # Create a JSON format label to send to the service provider
                io_doi_label = self._record_service.create_doi_record(doi, content_type=CONTENT_TYPE_JSON)

                # If the next step is to release, submit to the service provider and
                # use the response label for the local transaction database entry
                if self._no_review:
                    service_type = DOIServiceFactory.get_service_type()

                    # For OSTI, all submissions use the POST method
                    # for DataCite, releasing a reserved DOI requires the PUT method
                    method = WEB_METHOD_PUT if service_type == SERVICE_TYPE_DATACITE else WEB_METHOD_POST

                    # For DataCite, need to append the assigned DOI to the url
                    # for the PUT request. For OSTI, can just default to the
                    # url within the INI.
                    if service_type == SERVICE_TYPE_DATACITE:
                        url = "{url}/{doi}".format(url=self._config.get("DATACITE", "url"), doi=doi.doi)
                    else:
                        url = self._config.get("OSTI", "url")

                    doi, o_doi_label = self._web_client.submit_content(
                        url=url, method=method, payload=io_doi_label, content_type=CONTENT_TYPE_JSON
                    )

                # Otherwise, if the next step is review, the label we've already
                # created has marked all the Doi's as being the "review" step
                # so its ready to be submitted to the local transaction history
                transaction = self.m_transaction_builder.prepare_transaction(
                    self._node, self._submitter, doi, input_path=self._input, output_content_type=CONTENT_TYPE_JSON
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
            raise CriticalDOIException(str(err))

        # Create the return output label containing records for all submitted DOI's
        # Note this action always returns JSON format to ensure interoperability
        # between the potential service providers
        output_label = self._record_service.create_doi_record(output_dois, content_type=CONTENT_TYPE_JSON)

        return output_label
