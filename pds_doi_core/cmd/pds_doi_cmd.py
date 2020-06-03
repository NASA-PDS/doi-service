#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------
import os
from lxml import etree
import requests

from pds_doi_core.util.cmd_parser import create_cmd_parser
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.input.input_util import DOIInputUtil
from pds_doi_core.input.node_util import NodeUtil
from pds_doi_core.input.exeptions import InputFormatException, UnknownNodeException
from pds_doi_core.references.contributors import DOIContributorUtil
from pds_doi_core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_core.outputs.osti import DOIOutputOsti
from pds_doi_core.outputs.output_util import DOIOutputUtil
from pds_doi_core.outputs.transaction import Transaction
from pds_doi_core.outputs.transaction_logger import TransactionLogger

# Get the common logger and set the level for this file.
logger = get_logger('pds_doi_core.cmd.pds_doi_cmd')

class DOICoreServices:
    m_doi_config_util = DOIConfigUtil()
    m_doi_input_util = DOIInputUtil()
    m_doi_output_util = DOIOutputUtil()
    m_doi_pds4_label = DOIPDS4LabelUtil()
    m_doi_output_osti = DOIOutputOsti()
    m_transaction_logger = TransactionLogger()
    m_node_util = NodeUtil()

    def __init__(self):
        self._config = self.m_doi_config_util.get_config()

    def _get_default_configurations(self):
        '''Function returns two dictionaries containing the default configuration from conf.ini.default or conf.ini files'''

        dict_configlist = {}
        dict_configlist['global_keyword_values'] = self._config.get('OTHER','global_keyword_values')
        dict_configlist['DOI_template'         ] = self._config.get('OTHER','DOI_template')
        dict_configlist['DOI_reserve_template' ] = self._config.get('OTHER','DOI_reserve_template')

        dict_fixedlist = {}

        dict_fixedlist['pds_uri'] =  self._config.get('OTHER','pds_uri')

        return (dict_configlist,dict_fixedlist)


    def _process_reserve_action_xlsx(self, target_url):
        '''Function process a reserve action based on .xlsx ending.'''

        # It is much more preferable to get the default configurations from conf.ini.default or conf.ini
        (dict_configlist,dict_fixedlist) = self._get_default_configurations()

        logger.debug(f"dict_configlist {dict_configlist}")
        logger.debug(f"dict_fixedlist  {dict_fixedlist}")

        doi_directory_pathname = os.path.join('.','output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        try:
            dict_condition_data = self.m_doi_input_util.parse_sxls_file(target_url)
            return self.m_doi_output_osti.create_osti_doi_reserved_record(dict_condition_data)
        except InputFormatException as e:
            logger.error(e)
            exit(1)


    def _process_reserve_action_csv(self, target_url):
        '''Function process a reserve action based on .csv ending.'''

        # It is much more preferable to get the default configurations from conf.ini.default or conf.ini
        (dict_configlist,dict_fixedlist) = self._get_default_configurations()

        doi_directory_pathname = os.path.join('.','output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        try:
            dict_condition_data = self.m_doi_input_util.parse_csv_file(target_url)
            return self.m_doi_output_osti.create_osti_doi_reserved_record(dict_condition_data)
        except InputFormatException as e:
            logger.error(e)
            exit(1)

    def reserve_doi_label(self,
                          target_url,
                          node_id,
                          submitter_email,
                          submit_label_flag=True):
        """
        Function receives a URI containing either XML, SXLS or CSV and create one or many labels to disk and submit these label(s) to OSTI.
        :param target_url:
        :param node_id:
        :param submitter_email:
        :return:
        """

        try:
            contributor_value = self.m_node_util.get_node_long_name(node_id)
        except UnknownNodeException as e:
            raise(e)


        action_type = 'reserve_osti_label'
        o_doi_label = 'invalid action type:action_type ' + action_type
        publisher_value = self._config.get('OTHER', 'doi_publisher')

        logger.debug(f"target_url,action_type {target_url} {action_type}")

        if target_url.endswith('.xml'):
            o_doi_label = self.m_doi_pds4_label.parse_pds4_label_via_uri(target_url, publisher_value, contributor_value)

        elif target_url.endswith('.xlsx'):
            o_doi_label = self._process_reserve_action_xlsx(target_url)

        elif target_url.endswith('.csv'):
            o_doi_label = self._process_reserve_action_csv(target_url)

        # Check to see if the given file has an attempt to process.
        else:
            logger.error(f"File type has not been implemented:target_url {target_url}")
            exit(1)

        # Build a transaction so we write a transaction.
        doi_transaction = Transaction(target_url, node_id, 'reserve', submitter_email)
        doi_transaction.add_field('status','Reserved'.lower())

        # We can submit the content to OSTI if we wish.

        logger.debug(f"submit_label_flag {submit_label_flag}")

        if submit_label_flag:
            from pds_doi_core.outputs.osti_web_client import DOIOstiWebClient
            doi_web_client = DOIOstiWebClient()
            doi_web_client.webclient_submit_existing_content(o_doi_label,
                                                             i_url=self._config.get('OSTI', 'url'),
                                                             i_username=self._config.get('OSTI', 'user'),
                                                             i_password=self._config.get('OSTI', 'password'))
            (o_reserved_flag, o_out_text) = doi_web_client._verify_osti_reserved_status(o_doi_label)

             # Write a transaction for the 'reserve' action.
            doi_transaction.add_field('output_content',o_out_text)
            self.m_transaction_logger.log_transaction(doi_transaction)

            return o_out_text
        else:
            # Write a transaction for the 'reserve' action.
            doi_transaction.add_field('output_content',o_doi_label)
            self.m_transaction_logger.log_transaction(doi_transaction)

            return o_doi_label

    def create_doi_label(self, target_url, node_id, submitter_email):
        """
        Function receives a URI containing either XML or a local file and draft a Data Object Identifier (DOI).  
        :param target_url:
        :param node_id:
        :param submitter_email:
        :return: o_doi_label:
        """

        try:
            contributor_value = self.m_node_util.get_node_long_name(node_id)
            logger.info(f"contributor_value['{contributor_value}']")
        except UnknownNodeException as e:
            raise(e)



        # check contributor
        doi_contributor_util = DOIContributorUtil(self._config.get('PDS4_DICTIONARY', 'url'),
                                                  self._config.get('PDS4_DICTIONARY', 'pds_node_identifier'))
        o_permissible_contributor_list = doi_contributor_util.get_permissible_values()
        if contributor_value not in o_permissible_contributor_list:
            logger.error(f"The value of given contributor is not valid: {contributor_value}")
            logger.info(f"permissible_contributor_list {o_permissible_contributor_list}")
            exit(1)

        # parse input
        input_content = None
        if not target_url.startswith('http'):
            xml_tree = etree.parse(target_url)
            input_content = etree.tostring(xml_tree)
        else:
            response = requests.get(target_url)
            xml_tree = etree.fromstring(response.content)
            input_content = response.content 

        doi_fields = self.m_doi_pds4_label.get_doi_fields_from_pds4(xml_tree)
        doi_fields['publisher'] = self._config.get('OTHER', 'doi_publisher')
        doi_fields['contributor'] = contributor_value

        # Build a dictionary so we write a transaction.
        doi_transaction = Transaction(target_url, node_id, 'draft', submitter_email, input_content.decode())
        doi_transaction.add_field('status','Pending'.lower())

        # generate output
        o_doi_label = self.m_doi_output_osti.create_osti_doi_draft_record(doi_fields)

        # Write a transaction for the 'reserve' action.
        doi_transaction.add_field('output_content',o_doi_label)

        self.m_transaction_logger.log_transaction(doi_transaction)

        return o_doi_label 


def main():
    parser = create_cmd_parser()
    arguments = parser.parse_args()
    action_type = arguments.action
    submitter_email = arguments.submitter_email
    node_id = arguments.node_id.lstrip().rstrip()  # Remove any leading and trailing blanks.
    input_location = arguments.input

    logger.info(f"run_dir {os.getcwd()}")
    logger.info(f"input_location {input_location}")
    logger.info(f"node_id ['{node_id}']")

    try:
        doi_core_services = DOICoreServices()

        if action_type == 'draft':
            o_doi_label = doi_core_services.create_doi_label(input_location, node_id, submitter_email)
            logger.info(o_doi_label)

        elif action_type == 'reserve':
            o_doi_label = doi_core_services.reserve_doi_label(input_location,
                                                              node_id, submitter_email,
                                                              submit_label_flag=True)
            # By default, submit_label_flag=True if not specified.
            # By default, write_to_file_flag=True if not specified.
            logger.info(o_doi_label.decode())
        else:
            logger.error(f"Action {action_type} is not supported yet.")
            exit(1)
    except UnknownNodeException as e:
        logger.error(e)
        exit(1)



if __name__ == '__main__':
    main()
