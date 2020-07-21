#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import os

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.input.osti_input_validator import OSTIInputValidator
from pds_doi_core.input.osti_input_util import OSTIInputUtil
from pds_doi_core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_core.references.contributors import DOIContributorUtil
from pds_doi_core.util.config_parser import DOIConfigUtil

class DOICoreActionRelease(DOICoreAction):
    _name = 'release'
    description = ' % pds-doi-cmd release -n img -s Qui.T.Chau@jpl.nasa.gov -i input/DOI_Release_20200714.xml \n'
    # Examples:
    #
    # python3 pds_doi_core/cmd/pds_doi_cmd.py release -n img -s Qui.T.Chau@jpl.nasa.gov -i my_release_doc.xml

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        # Object self._config is already instantiated from the previous super().__init__() command, no need to do it again.
        self._parse_arguments_from_cmd() # Parse arguments from command line if there are any.
        self._doi_web_client = DOIOstiWebClient()
        self._web_parser = DOIOstiWebParser()
        self._validator = OSTIInputValidator()
        self._input_util = OSTIInputUtil()

    def _parse_arguments_from_cmd(self):
        parser = DOICoreAction.create_cmd_parser()
        self._arguments = parser.parse_args()
        self._input_location = None
        self._node_id        = None
        self._submitter      = None

        if self._arguments:
            if hasattr(self._arguments, 'input'):
                self._input_location = self._arguments.input
            if hasattr(self._arguments, 'node_id'):
                self._node_id = self._arguments.node_id
            if hasattr(self._arguments, 'submitter_email'):
                self._submitter       = self._arguments.submitter_email

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

    def _build_release_osti_xml_payload(self,osti_dict):
        o_xml_pay_load = "<records><record><id>"            + str(osti_dict['id'])       + \
                                          "</id><site_url>" + str(osti_dict['site_url']) + \
                                                "</site_url></record></records>"

        return o_xml_pay_load

    def _transform_xml_to_release_format(self,input):
        """
        Function transform the input XML file into a XML string in preparation for submitting to OSTI.
        """
        # Read the input file into a string.
        f_DOI_file = open(input, mode='r')
        xml_DOI_text = f_DOI_file.read()
        f_DOI_file.close()

        # Parse the string into fields in dictionary.
        o_doi_fields = self._input_util.read_osti_xml(xml_DOI_text)

        logger.debug(f"xml_DOI_text {xml_DOI_text}")
        logger.debug(f"o_doi_fields {o_doi_fields}")

        return o_doi_fields

    def _transform_csv_to_release_format(self,input):
        return 1

    def run(self, input=None, node=None, submitter=None,
            submit_label_flag=True):
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
        (validation_result,default_schematron,validation_report) = self._validator.validate_release_input(input)
        logger.debug(f"validation_result {validation_result}")
        # Exit if cannot validate the input file via schematron.
        if validation_result.lower() != 'true':
            logger.error(f"Validation failed for {input} using schematron {default_schematron}, with report {validation_report}")
            exit(1)


        # The type of doi_fields is a dictionary of fields extracted (parsed) from input file.
        # The type of o_doi_label is a string that can be used to submit to OSTI.
        if input.endswith('.xml'):
            doi_fields  = self._transform_xml_to_release_format(input)
            o_doi_label = self.m_doi_output_osti.create_osti_doi_release_record(doi_fields)
        elif input.endswith('.xlsx'):
            logger.error(f"Input file {input} type not supported yet.")
            exit(0)
        elif input.endswith('.csv'):
            logger.error(f"Input file {input} type not supported yet.")
            exit(0)

        logger.debug(f"doi_fields {doi_fields} {type(doi_fields)}")
        logger.debug(f"o_doi_label {o_doi_label} {type(o_doi_label)}")
        #exit(0)

        # Submit the text containing the 'release' action and its associated DOIs and optional metadata.
        (o_status_dict, osti_response_str) = self._doi_web_client.webclient_submit_existing_content(o_doi_label,
                                                                                                    i_url=self._config.get('OSTI', 'url'),
                                                                                                    i_username=self._config.get('OSTI', 'user'),
                                                                                                    i_password=self._config.get('OSTI', 'password'))
        logger.debug(f"o_status_dict {o_status_dict}")
        output_str = osti_response_str

        # At this point, the response from the OSTI server contains the latest metadata of all the DOIs.
        # Parse the response and get a new list of dictionaries doi_fields in preparation for writing a transaction.
        doi_fields = self._web_parser.response_get_parse_osti_xml_multiple_records(osti_response_str)
        logger.debug(f"osti_response_str {osti_response_str}")
        logger.debug(f"doi_fields {doi_fields}")

        # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
        transaction_obj = self.m_transaction_builder.prepare_transaction(input,
                                                                         node,
                                                                         submitter,
                                                                         doi_fields,
                                                                         output_content=output_str)
        # Write a transaction for the 'release' action.
        transaction_obj.log()

        # Return a list of status DOIs released and their status.  List can be empty.
        o_release_result = o_status_dict
        return o_release_result

# end class DOICoreActionRelease(DOICoreAction):
