import os
import requests
from lxml import etree

from pds_doi_core.actions.action import DOICoreAction
from pds_doi_core.input.exeptions import InputFormatException, UnknownNodeException
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.actions.release import DOICoreActionRelease

logger = get_logger('pds_doi_core.actions.reserve')


class DOICoreActionReserve(DOICoreAction):
    _name = 'reserve'
    description = ' % pds-doi-cmd reserve -n img -s Qui.T.Chau@jpl.nasa.gov -i input/DOI_Reserved_GEO_200318.csv\n'

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
                                   help='A pds4 label local or on http, a xls spreadsheet, a database file'
                                        ' is also supported to reserve a list of doi',
                                   required=True,
                                   metavar='input/DOI_Reserved_GEO_200318.csv')
        action_parser.add_argument('-s', '--submitter-email',
                                   help='The email address of the user performing the action for these services',
                                   required=True,
                                   metavar='"my.email@node.gov"')


    def _process_reserve_action_pdf4(self, target_url):
        # parse input
        if not target_url.startswith('http'):
            xml_tree = etree.parse(target_url)
        else:
            response = requests.get(target_url)
            xml_tree = etree.fromstring(response.content)

        doi = self.m_doi_pds4_label.get_doi_fields_from_pds4(xml_tree)

        return [doi]

    def _process_reserve_action_xlsx(self, target_url):
        '''Function process a reserve action based on .xlsx ending.'''

        doi_directory_pathname = os.path.join('.', 'output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        try:
            dois = self.m_doi_input_util.parse_sxls_file(target_url)

            # Do a sanity check on content of dict_condition_data.
            if len(dois) == 0:
                raise InputFormatException("Length of dict_condition_data['dois'] is zero, target_url " + target_url)

            return dois
        except InputFormatException as e:
            logger.error(e)
            exit(1)

    def _process_reserve_action_csv(self, target_url):
        '''Function process a reserve action based on .csv ending.'''

        doi_directory_pathname = os.path.join('.', 'output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        try:
            dois = self.m_doi_input_util.parse_csv_file(target_url)

            # Do a sanity check on content of dict_condition_data.
            if len(dois) == 0:
                raise InputFormatException("Length of dict_condition_data['dois'] is zero, target_url " + target_url)

            return dois
        except InputFormatException as e:
            logger.error(e)
            exit(1)

    def run(self, input=None, node=None, submitter=None,
            submit_label_flag=True):
        """
        Function receives a URI containing either XML, SXLS or CSV and create one or many labels to disk and submit these label(s) to OSTI.
        :param target_url:
        :param node_id:
        :param submitter_email:
        :return:
        """

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

        action_type = 'reserve_osti_label'
        publisher_value = self._config.get('OTHER', 'doi_publisher')

        logger.debug(f"target_url,action_type {input} {action_type}")

        if input.endswith('.xml'):
            dois = self._process_reserve_action_pds4(input)

        elif input.endswith('.xlsx'):
            dois = self._process_reserve_action_xlsx(input)

        elif input.endswith('.csv'):
            dois = self._process_reserve_action_csv(input)
        # Check to see if the given file has an attempt to process.
        else:
            logger.error(f"File type has not been implemented:target_url {input}")
            exit(1)

        for doi in dois:
            doi.contributor = contributor_value
            doi.publisher = publisher_value

        o_doi_label = self.m_doi_output_osti.create_osti_doi_reserved_record(dois)

        logger.debug(f"submit_label_flag {submit_label_flag}")
        logger.debug(f"doi_fields {dois}")
        logger.debug(f"o_doi_label {o_doi_label}")
        logger.debug(f"submitter_email {submitter}")

        # We can submit the content to OSTI if we wish.
        if submit_label_flag:
            from pds_doi_core.outputs.osti_web_client import DOIOstiWebClient
            doi_web_client = DOIOstiWebClient()
            dois, output_str = doi_web_client.webclient_submit_existing_content(
                o_doi_label,
                i_url=self._config.get('OSTI', 'url'),
                i_username=self._config.get('OSTI', 'user'),
                i_password=self._config.get('OSTI', 'password'))

            logger.debug(f"doi_fields {dois},{len(dois)}")

            logger.debug(f"reserve_response {output_str}")
            logger.debug(f"type(reserve_response) {type(output_str)}")

        else:
            # This path is normally used by developer to test the parsing of CSV or XLSX input without submitting the DOI.
            # Write a transaction for the 'reserve' action.
            for doi in dois:
                doi.status = 'reserved_not_submitted'
            output_str = o_doi_label

        # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
        transaction_obj = self.m_transaction_builder.prepare_transaction(node,
                                                                         submitter,
                                                                         dois,
                                                                         input_path=input,
                                                                         output_content=output_str)
        # Write a transaction for the 'reserve' action.
        transaction_obj.log()

        return output_str
