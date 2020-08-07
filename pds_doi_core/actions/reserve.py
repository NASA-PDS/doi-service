import os
import requests
from lxml import etree

from pds_doi_core.actions.action import DOICoreAction
from pds_doi_core.input.exeptions import InputFormatException, UnknownNodeException
from pds_doi_core.input.exeptions import DuplicatedTitleDOIException, InvalidDOIException, IllegalDOIActionException, UnexpectedDOIActionException
from pds_doi_core.util.doi_validator import DOIValidator
from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.actions.reserve')


class DOICoreActionReserve(DOICoreAction):
    _name = 'reserve'
    description = ' % pds-doi-cmd reserve -n img -s Qui.T.Chau@jpl.nasa.gov -i input/DOI_Reserved_GEO_200318.csv\n'

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)

    def parse_arguments_from_cmd(self, arguments):

        self._input_location = None
        self._node_id        = None
        self._submitter      = None
        self._force_flag     = False

        if arguments:
            if hasattr(arguments, 'input'):
                self._input_location = arguments.input
            if hasattr(arguments, 'node_id'):
                self._node_id = arguments.node_id
            if hasattr(arguments, 'submitter_email'):
                self._submitter       = arguments.submitter_email
            if hasattr(arguments, 'force'):
                self._force_flag      = arguments.force

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name)
        action_parser.add_argument('-n', '--node-id',
                                   help='The pds discipline node in charge of the submission of the DOI',
                                   required=True,
                                   metavar='"img"')
        action_parser.add_argument('-f', '--force',
                                   help= 'If provided the reserve action will succeed even if warnings are raised: duplicated title or reserve a DOI which has already been previously reserve',
                                   required=False, action='store_true')
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
            submit_label_flag=True, force_flag=None):
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
        if force_flag is None:
            force_flag = self._force_flag

        logger.info(f"force_flag {force_flag}")

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

        counter = 0
        for doi in dois:
            doi.contributor = contributor_value
            doi.publisher = publisher_value
            # Note that the mustache file must have the double quotes around the status value: <record status="{{status}}">
            # as it is an attribute of a field.
            doi.status = "Reserved" # Add 'status' field so the ranking in the workflow can be determined.

            # Save the field 'publication_date' in 'original_publication_date' in case it is needed later if the label is not submitted.
            # The type of 'publication_date' field is a timestamp.
            doi.original_publication_date = doi.publication_date

            # Wrap the validate() in a try/except to allow the processing of specific error in this run() function.
            # Validate the label to ensure that no rules are violated against using the same title if a DOI has been minted.
            # The IllegalDOIActionException can also occur if an existing DOI has been minted using the same lidvid value.

            #doi.title = 'some other title counter_' + str(counter)
            try:
                # Validate the label to ensure that no rules are violated against using the same title if a DOI has been minted
                # or the same lidvid has been used if a DOI has been minted.
                self._doi_validator.validate(doi,self._name)
            except DuplicatedTitleDOIException as e:
                if not force_flag:
                    # If the user did not use force_flag, re-raise the DuplicatedTitleDOIException exception.
                    raise
                else:
                    logger.debug(e)
                    logger.debug(f"Exception DuplicatedTitleDOIException encountered but force_flag is true, will continue.")
            except IllegalDOIActionException as e:
                if not force_flag:
                    # If the user did not use force_flag, re-raise the IllegalDOIActionException exception.
                    raise
                else:
                    logger.debug(e)
                    logger.debug(f"Exception IllegalDOIActionException encountered but force_flag is true, will continue.")
            except Exception as e:
                raise # Re-raise all other exceptions.

            # Note that if an individual row in the input file has an error, this loop will stop prematurely to allow
            # the user to make correction.

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
                # Fetch the 'original_publication_date' field (a timestamp) and save to 'publication_date' field.
                # otherwise the function create_osti_doi_reserved_record will fail because it is expecting 'publication_date' to be a timestamp.
                doi.publication_date = doi.original_publication_date
            o_doi_label = self.m_doi_output_osti.create_osti_doi_reserved_record(dois)
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
