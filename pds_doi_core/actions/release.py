#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.input.exceptions import UnknownNodeException, InputFormatException, DuplicatedTitleDOIException, \
    UnexpectedDOIActionException, TitleDoesNotMatchProductTypeException, SiteURNotExistException, IllegalDOIActionException, WarningDOIException, \
    CriticalDOIException
from pds_doi_core.input.osti_input_validator import OSTIInputValidator
from pds_doi_core.outputs.osti import DOIOutputOsti
from pds_doi_core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_core.util.doi_validator import DOIValidator
from pds_doi_core.input.node_util import NodeUtil


class DOICoreActionRelease(DOICoreAction):
    _name = 'release'
    _description = 'create or update a DOI on OSTI server'
    _order = 20
    _run_arguments = ('input', 'node', 'submitter', 'force')

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)

        self._input = None
        self._node = None
        self._submitter = None
        self._force = False

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name,
                                              description='register a new DOI or update an existing DOI on OSTI server')

        node_values = NodeUtil.get_permissible_values()
        action_parser.add_argument('-n', '--node',
                                   help='The pds discipline node in charge of the released DOI. '
                                        ' Authorized values are: ' + ','.join(node_values),
                                   required=True,
                                   metavar='"img"')
        action_parser.add_argument('-f', '--force',
                                   help='If provided the release action will succeed even if warning are raised: '
                                        'duplicated title or release a DOI which has already been previously released.',
                                   required=False, action='store_true')
        action_parser.add_argument('-i', '--input',
                                   help='A file containing a list of doi metadata to update/release'
                                        'in OSTI XML format (see https://www.osti.gov/iad2/docs#record-model)'
                                        'The input can be produced by reserve and draft subcommands',
                                   required=True,
                                   metavar='input/DOI_Update_GEO_200318.xml')
        action_parser.add_argument('-s', '--submitter',
                                   help='The email address of the user performing the release',
                                   required=True,
                                   metavar='"my.email@node.gov"')

    def _parse_input(self, input):
        if input.endswith('.xml'):
            with open(input, mode='rb') as f:
                o_doi_label = f.read()
        else:
            msg = f"Input file {input} type not supported yet."
            raise CriticalDOIException(msg)

        return o_doi_label

    def _collect_exception_classes_and_messages(self, single_exception, io_exception_classes, io_exception_messages):
        # Given a single exception, collect the exception class name and message.
        # The variables io_exception_classes and io_exception_messages are both input and output.

        actual_class_name = type(single_exception).__name__
        logger.debug(f"actual_class_name,type(actual_class_name)  {actual_class_name},{type(actual_class_name)}")

        io_exception_classes.append (actual_class_name)     # SiteURNotExistException
        io_exception_messages.append(str(single_exception)) # site_url http://mysite.example.com/link/to/my-dataset-id-25901.html not exist

        return io_exception_classes, io_exception_messages

    def _raise_warn_exceptions(self, exception_classes, exception_messages):
        # Raise a WarningDOIException with all the class names and messages.

        message_to_raise = '' 
        for ii in range(len(exception_classes)):
            if ii == 0:
                message_to_raise = message_to_raise +        exception_classes[ii] + ':' + exception_messages[ii]
            else:
                # Add a comma after every message.
                message_to_raise = message_to_raise + ', ' + exception_classes[ii] + ':' + exception_messages[ii]
        raise WarningDOIException(message_to_raise)

    def _validate_doi(self, doi_label, force=False):
        """
         Before submitting the user input, it has to be validated against the database so a Doi object need to be built.
         Since the format of o_doi_label is same as a response from OSTI, the same parser can be used.
        :param doi_label:
        :return:
        """
        exception_classes  = [] 
        exception_messages = [] 
        try:

            dois = DOIOstiWebParser().response_get_parse_osti_xml(doi_label)

            for doi in dois:
                try:
                    doi.status = 'Registered'  # Add 'status' field so the ranking in the workflow can be determined.
                    single_doi_label = DOIOutputOsti().create_osti_doi_release_record(doi)
                    if self._config.get('OTHER', 'release_validate_against_xsd_flag').lower() == 'true':
                        self._doi_validator.validate_against_xsd(single_doi_label)

                    self._doi_validator.validate_osti_submission(doi)

                except (DuplicatedTitleDOIException, UnexpectedDOIActionException,
                        TitleDoesNotMatchProductTypeException, SiteURNotExistException) as e:
                    (exception_classes, exception_messages) = \
                        self._collect_exception_classes_and_messages(e,
                                                                     exception_classes,
                                                                     exception_messages)
        except Exception as e:
            raise  # Re-raise all exceptions.

        # If there is at least one exception caught, raise a WarningDOIException with all the messages.
        if len(exception_classes) > 0:
            self._raise_warn_exceptions(exception_classes,exception_messages)

        return 1

    def run(self, **kwargs):
        """
        Function performs a release of a DOI that has been previously reserved.  The input is a
        XML text file contains previously return output from a 'reserve' or 'draft' action.  The only
        required field is 'id'.  Any other fields included will be considered a replace action.
        """
        self.parse_arguments(kwargs)

        try:
            try:
                contributor_value = NodeUtil().get_node_long_name(self._node)
                o_doi_label = self._parse_input(self._input)

                # Validate the input content against database for any step violation.
                self._validate_doi(o_doi_label)

                # Validate the input content against schematron for correctness.
                # If the input is correct no exception is thrown and code can proceed to next step.
                # Also note that the check against schematron is done after XSD above so any bad dates
                # would have been caught already.

                OSTIInputValidator().validate_from_file(self._input)

            # warnings
            except (DuplicatedTitleDOIException, UnexpectedDOIActionException,
                    TitleDoesNotMatchProductTypeException, SiteURNotExistException, WarningDOIException) as e:
                if not self._force:
                    # If the user did not use --force parameter, re-raise the exception.
                    raise WarningDOIException(str(e))
            # errors
            except (IllegalDOIActionException, UnknownNodeException, InputFormatException) as e:
                raise CriticalDOIException(str(e))

            # Submit the text containing the 'release' action and its associated DOIs and optional metadata.
            (dois, response_str) = DOIOstiWebClient().webclient_submit_existing_content(
                o_doi_label,
                i_url=self._config.get('OSTI', 'url'),
                i_username=self._config.get('OSTI','user'),
                i_password=self._config.get('OSTI','password'))
            logger.debug(f"o_release_result {dois}")

            self.m_transaction_builder.prepare_transaction(self._node,
                                                           self._submitter,
                                                           dois,
                                                           input_path=self._input,
                                                           output_content=response_str).log()
            return response_str

        except Exception as e:
            raise  # Re-raise all other exceptions.



# end class DOICoreActionRelease(DOICoreAction):
