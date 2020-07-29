#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.input.osti_input_validator import OSTIInputValidator
from pds_doi_core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_core.outputs.osti_web_parser import DOIOstiWebParser

class DOICoreActionRelease(DOICoreAction):
    _name = 'release'
    description = ' % pds-doi-cmd release -n img -s Qui.T.Chau@jpl.nasa.gov -i input/DOI_Release_20200723.xml \n'
    # Examples:
    #
    # python3 pds_doi_core/cmd/pds_doi_cmd.py release -n img -s Qui.T.Chau@jpl.nasa.gov -i my_release_doc.xml
    # python3 pds_doi_core/cmd/pds_doi_cmd.py release -n img -s Qui.T.Chau@jpl.nasa.gov -i input/DOI_Release_20200727_from_reserve.xml
    # python3 pds_doi_core/cmd/pds_doi_cmd.py release -n img -s Qui.T.Chau@jpl.nasa.gov -i input/DOI_Release_20200727_from_draft.xml

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        # Object self._config is already instantiated from the previous super().__init__() command, no need to do it again.
        self._doi_web_client = DOIOstiWebClient()
        self._web_parser = DOIOstiWebParser()
        self._validator = OSTIInputValidator()


    def parse_arguments_from_cmd(self, arguments):
        self._input_location = None
        self._node_id        = None
        self._submitter      = None

        if arguments:
            if hasattr(arguments, 'input'):
                self._input_location = arguments.input
            if hasattr(arguments, 'node_id'):
                self._node_id = arguments.node_id
            if hasattr(arguments, 'submitter_email'):
                self._submitter       = arguments.submitter_email

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name)

        action_parser.add_argument('-n', '--node-id',
                                   help='The pds discipline node in charge of the submission of the DOI',
                                   required=True,
                                   metavar='"img"')
        action_parser.add_argument('-i', '--input',
                                   help='A file containing a list of doi metadata to update/release',
                                   required=True,
                                   metavar='input/DOI_Update_GEO_200318.xml')
        action_parser.add_argument('-s', '--submitter-email',
                                   help='The email address of the user performing the action for these services',
                                   required=True,
                                   metavar='"my.email@node.gov"')

    def run(self, input=None, node=None, submitter=None):
        """
        Function performs a release of a DOI that has been previously reserved.  The input is a
        XML text file contains previously return output from a 'reserved' action.  The only
        required field is 'id'.  Any other fields included will be considered a replace action.
        :param input:
        :param node:
        :param submitter:
        :return:
        """

        o_release_result = []

        if input is None:
            input = self._input_location

        if node is None:
            node = self._node_id

        if submitter is None:
            submitter = self._submitter

        try:
            contributor_value = self.m_node_util.get_node_long_name(node)
        except UnknownNodeException as e:
            raise e

        logger.debug(f"input {input}")
        logger.debug(f"node {node}")
        logger.debug(f"submitter {submitter}")

        # Validate the input to 'release' action.
        (validation_result,default_schematron,validation_report) = self._validator.validate(input)
        logger.debug(f"validation_result {validation_result}")
        # Exit if cannot validate the input file via schematron.
        if validation_result.lower() != 'true':
            logger.error(f"Validation failed for {input} using schematron {default_schematron}, with report {validation_report}")
            exit(1)

        if input.endswith('.xml'):
            with open(input, mode='rb') as f:
                o_doi_label = f.read()
        else:
            logger.error(f"Input file {input} type not supported yet.")
            exit(1)

        logger.debug(f"o_doi_label {o_doi_label} {type(o_doi_label)}")

        # Submit the text containing the 'release' action and its associated DOIs and optional metadata.
        (o_release_result, osti_response_str) = self._doi_web_client.webclient_submit_existing_content(o_doi_label,
                                                                                                    i_url=self._config.get('OSTI', 'url'),
                                                                                                    i_username=self._config.get('OSTI', 'user'),
                                                                                                    i_password=self._config.get('OSTI', 'password'))
        logger.debug(f"o_release_result {o_release_result}")

        # At this point, the response from the OSTI server contains the latest metadata of all the DOIs.
        # Parse the response and get a new list of dictionaries doi_fields in preparation for writing a transaction.
        dois = self._web_parser.response_get_parse_osti_xml(osti_response_str)
        logger.debug(f"osti_response_str {osti_response_str}")
        logger.debug(f"doi_fields {dois}")

        # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
        transaction_obj = self.m_transaction_builder.prepare_transaction(node,
                                                                         submitter,
                                                                         dois,
                                                                         input_path=input,
                                                                         output_content=osti_response_str)
        # Write a transaction for the 'release' action.
        transaction_obj.log()

        # Return a list of status DOIs released and their status.  List can be empty.

        return o_release_result

# end class DOICoreActionRelease(DOICoreAction):
