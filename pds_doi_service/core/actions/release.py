#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
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

from datetime import datetime
from distutils.util import strtobool

from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.input.exceptions import (InputFormatException,
                                                   DuplicatedTitleDOIException,
                                                   UnexpectedDOIActionException,
                                                   TitleDoesNotMatchProductTypeException,
                                                   SiteURLNotExistException,
                                                   CriticalDOIException,
                                                   collect_exception_classes_and_messages,
                                                   raise_or_warn_exceptions)
from pds_doi_service.core.input.input_util import DOIInputUtil
from pds_doi_service.core.input.osti_input_validator import OSTIInputValidator
from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.outputs.osti import DOIOutputOsti, CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_service.core.util.doi_validator import DOIValidator
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_service.core.actions.release')


class DOICoreActionRelease(DOICoreAction):
    _name = 'release'
    _description = 'create or update a DOI on OSTI server'
    _order = 20
    _run_arguments = ('input', 'node', 'submitter', 'force', 'no_review')

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)
        self._input_util = DOIInputUtil(valid_extensions=['.xml', '.json'])

        self._input = None
        self._node = None
        self._submitter = None
        self._force = False
        self._no_review = False

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(
            cls._name, description='Release a DOI, in draft or reserve status, '
                                   'for review. A DOI may also be released to '
                                   'the OSTI server directly.'
        )

        node_values = NodeUtil.get_permissible_values()
        action_parser.add_argument(
            '-n', '--node', required=True, metavar='"img"',
            help='The PDS Discipline Node in charge of the released DOI. '
                 'Authorized values are: ' + ','.join(node_values)
        )
        action_parser.add_argument(
            '-f', '--force', required=False, action='store_true',
            help='If provided, forces the release action to proceed even if '
                 'warning are encountered during submission of the release to '
                 'OSTI. Without this flag, any warnings encountered are '
                 'treated as fatal exceptions.'
        )
        action_parser.add_argument(
            '-i', '--input', required=True,
            metavar='input/DOI_Update_GEO_200318.xml',
            help='A file containing a list of DOI metadata to update/release '
                 'in OSTI JSON/XML format (see https://www.osti.gov/iad2/docs#record-model).'
                 'The input is produced by the Reserve and Draft actions, and '
                 'can be retrieved for a DOI with the List action.',
        )
        action_parser.add_argument(
            '-s', '--submitter', required=True, metavar='"my.email@node.gov"',
            help='The email address to associate with the Release request.'
        )

        action_parser.add_argument(
            '--no-review', required=False, action='store_true',
            help='If provided, the requested DOI will be released directly to '
                 'the OSTI server for registration. Use to override the default '
                 'behavior of releasing a DOI to "review" status.'
        )

    def _parse_input(self, input_file):
        return self._input_util.parse_dois_from_input_file(input_file)

    def _complete_dois(self, dois):
        """
        Ensures the list of Doi objects to reserve have the requisite fields,
        such as status or contributor, filled in prior to submission to OSTI.

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
            doi.publisher = self._config.get('OTHER', 'doi_publisher')

            # Add 'status' field so the ranking in the workflow can be determined.
            doi.status = DoiStatus.Pending if self._no_review else DoiStatus.Review

            # Add field 'date_record_added' because the XSD requires it.
            if doi.date_record_added is None:
                doi.date_record_added = datetime.now().strftime('%Y-%m-%d')
            # If date added is already present, mark the date of this update
            else:
                doi.date_record_updated = datetime.now().strftime('%Y-%m-%d')

        return dois

    def _validate_dois(self, dois):
        """
        Validates the list of Doi objects prior to their submission to OSTI.

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
                single_doi_label = DOIOutputOsti().create_osti_doi_record(doi)

                # Validate XML representation of the DOI against the OSTI XSD,
                # if requested
                if strtobool(self._config.get('OTHER', 'release_validate_against_xsd_flag')):
                    self._doi_validator.validate_against_xsd(
                        single_doi_label, use_alternate_validation_method=True
                    )

                # Validate the input content against schematron for correctness.
                OSTIInputValidator().validate(single_doi_label)

                self._doi_validator.validate_osti_submission(doi)
            except (DuplicatedTitleDOIException, UnexpectedDOIActionException,
                    TitleDoesNotMatchProductTypeException, SiteURLNotExistException) as err:
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
        Performs a release of a DOI that has been previously reserved.

        A reserved DOI can be "released" either to the review step, or
        released directly to OSTI for immediate registration.

        The input is an XML text file containing the previously returned output
        of a 'reserve' or 'draft' action. The only required field is 'id'.
        Any other fields included are considered a replace action.

        Parameters
        ----------
        kwargs : dict
            The parsed command-line arguments for the release action.

        Returns
        -------
        o_doi_label : str
            The output OSTI label, reflecting the status of the released
            input DOI's. A copy of this label is associated with the
            database transaction for this run.

        Raises
        ------
        CriticalDOIException
            If any unrecoverable errors are encountered during validation of
            the input DOI's.

        """
        self.parse_arguments(kwargs)

        try:
            # Parse, complete and validate the input dois prior to their
            # submission to OSTI
            dois = self._parse_input(self._input)
            dois = self._complete_dois(dois)
            dois = self._validate_dois(dois)

            # Create an JSON request label to send to OSTI
            io_doi_label = DOIOutputOsti().create_osti_doi_record(
                dois, content_type=CONTENT_TYPE_JSON
            )

            # If the next step is to release to OSTI, submit to the server
            # and use response label for the local transaction database entry
            if self._no_review:
                # Submit the text containing the 'release' action and its associated
                # DOIs and optional metadata.
                dois, o_doi_label = DOIOstiWebClient().webclient_submit_existing_content(
                    io_doi_label,
                    i_url=self._config.get('OSTI', 'url'),
                    i_username=self._config.get('OSTI', 'user'),
                    i_password=self._config.get('OSTI', 'password'),
                    content_type=CONTENT_TYPE_JSON
                )

                # The label returned from OSTI is of a slightly different
                # format than what we expect to pass validation, so reformat
                # using the valid template here
                io_doi_label = DOIOutputOsti().create_osti_doi_record(
                    dois, content_type=CONTENT_TYPE_JSON
                )

            # Otherwise, if the next step is review, the label we've already
            # created has marked all the Doi's as being the "review" step
            # so its ready to be submitted to the local transaction history
            transaction = self.m_transaction_builder.prepare_transaction(
                self._node, self._submitter, dois, input_path=self._input,
                output_content=io_doi_label, output_content_type=CONTENT_TYPE_JSON
            )

            # Commit the transaction to the local database
            transaction.log()

            return io_doi_label
        # Propagate input format exceptions, force flag should not affect
        # these being raised and certain callers (such as the API) look
        # for this exception specifically
        except InputFormatException as err:
            raise err
        # Convert all other errors into a CriticalDOIException to report back
        except Exception as err:
            raise CriticalDOIException(str(err))
