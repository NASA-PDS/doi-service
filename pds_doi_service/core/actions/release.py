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

from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.input.exceptions import (UnknownNodeException,
                                                   InputFormatException,
                                                   DuplicatedTitleDOIException,
                                                   UnexpectedDOIActionException,
                                                   TitleDoesNotMatchProductTypeException,
                                                   SiteURLNotExistException,
                                                   IllegalDOIActionException,
                                                   CriticalDOIException,
                                                   collect_exception_classes_and_messages,
                                                   raise_warn_exceptions)
from pds_doi_service.core.input.osti_input_validator import OSTIInputValidator
from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.outputs.osti import DOIOutputOsti
from pds_doi_service.core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.util.doi_validator import DOIValidator
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_core.actions.release')


class DOICoreActionRelease(DOICoreAction):
    _name = 'release'
    _description = 'create or update a DOI on OSTI server'
    _order = 20
    _run_arguments = ('input', 'node', 'submitter', 'force', 'no_review')

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)

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
                 'in OSTI XML format (see https://www.osti.gov/iad2/docs#record-model).'
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
        if input_file.endswith('.xml'):
            with open(input_file, mode='rb') as f:
                o_doi_label = f.read()
        else:
            msg = f"Input file {input_file} type not supported yet."
            raise CriticalDOIException(msg)

        return o_doi_label

    def _validate_dois(self, doi_label):
        """
        Before submitting the user input, it has to be validated against the
        database so a Doi object can be built.

        Since the format of o_doi_label is same as a response from OSTI, the
        same parser can be used.

        Parameters
        ----------
        doi_label : str or bytes
            Contents of the DOI XML label file to validate.

        Returns
        -------
        dois : list of Doi
            The parsed, validated DOI's with the appropriate workflow status
            assigned.

        Raises
        ------
        WarningDOIException
            Rolls up any encountered warnings or errors were encountered during
            validation.

        """
        exception_classes = []
        exception_messages = []

        dois, _ = DOIOstiWebParser().response_get_parse_osti_xml(doi_label)

        for doi in dois:
            try:
                # Add 'status' field so the ranking in the workflow can be determined.
                doi.status = DoiStatus.Pending if self._no_review else DoiStatus.Review

                single_doi_label = DOIOutputOsti().create_osti_doi_release_record(doi)

                if self._config.get('OTHER', 'release_validate_against_xsd_flag').lower() == 'true':
                    self._doi_validator.validate_against_xsd(single_doi_label)

                self._doi_validator.validate_osti_submission(doi)
            except (DuplicatedTitleDOIException, UnexpectedDOIActionException,
                    TitleDoesNotMatchProductTypeException, SiteURLNotExistException) as err:
                (exception_classes,
                 exception_messages) = collect_exception_classes_and_messages(
                    err, exception_classes, exception_messages
                )

        # If there is at least one exception caught, raise a WarningDOIException
        # with all the messages, provided the force flag is not set
        if len(exception_classes) > 0 and not self._force:
            raise_warn_exceptions(exception_classes, exception_messages)

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
            i_doi_label = self._parse_input(self._input)

            # Validate the input content against database for any step violation.
            dois = self._validate_dois(i_doi_label)

            # Validate the input content against schematron for correctness.
            # If the input is correct no exception is thrown and the code can
            # proceed to next step.
            # Also note that the check against schematron is done after XSD
            # above so any bad dates would have been caught already.
            OSTIInputValidator().validate_from_file(self._input)

            # If the next step is to release to OSTI, submit to the server
            # and use response label for the local transaction database entry
            if self._no_review:
                # Submit the text containing the 'release' action and its associated
                # DOIs and optional metadata.
                (dois, o_doi_label) = DOIOstiWebClient().webclient_submit_existing_content(
                    i_doi_label,
                    i_url=self._config.get('OSTI', 'url'),
                    i_username=self._config.get('OSTI', 'user'),
                    i_password=self._config.get('OSTI', 'password')
                )
                logger.debug(f"o_release_result {dois}")
            # Otherwise, if the next step is review, recreate an OSTI label
            # from the parsed DOI's that have the "review" status assigned.
            # This becomes the label associated with the transaction database entry.
            else:
                o_doi_label = DOIOutputOsti().create_osti_doi_review_record(dois)
                logger.debug(f"o_review_result {o_doi_label}")

            transaction = self.m_transaction_builder.prepare_transaction(
                self._node, self._submitter, dois, input_path=self._input,
                output_content=o_doi_label
            )

            # Commit the transaction to the local database
            transaction.log()

            return o_doi_label
        # Convert errors into a CriticalDOIException to report back
        except (IllegalDOIActionException, UnknownNodeException,
                InputFormatException) as err:
            raise CriticalDOIException(str(err))

# end class DOICoreActionRelease(DOICoreAction):
