import os
import requests
from lxml import etree

from pds_doi_core.actions.action import DOICoreAction
from pds_doi_core.input.exceptions import UnknownNodeException
from pds_doi_core.input.exceptions import DuplicatedTitleDOIException, TitleDoesNotMatchProductTypeException, \
    UnexpectedDOIActionException, InputFormatException, WarningDOIException, CriticalDOIException
from pds_doi_core.input.node_util import NodeUtil
from pds_doi_core.input.input_util import DOIInputUtil
from pds_doi_core.util.doi_validator import DOIValidator
from pds_doi_core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_core.outputs.osti import DOIOutputOsti
from pds_doi_core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.actions.reserve')


class DOICoreActionReserve(DOICoreAction):
    _name = 'reserve'
    _description = 'create or update a DOI before the data is published'
    _order = 0
    _run_arguments = ('input', 'node', 'submitter', 'dry_run', 'force')

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)
        self._input = None
        self._node = None
        self._submitter = None
        self._force = False
        self._dry_run = True

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name, description='create a DOI for a unpublished dataset.'
                                                                     ' The input is a spreadsheet or csv file')
        node_values = NodeUtil.get_permissible_values()
        action_parser.add_argument('-n', '--node',
                                   help='The pds discipline node in charge of the submission of the DOI. '
                                        ' Authorized values are: ' + ','.join(node_values),
                                   required=True,
                                   metavar='"img"')
        action_parser.add_argument('-f', '--force',
                                   help='If provided the reserve action will succeed even if warnings are raised',
                                   required=False, action='store_true')
        action_parser.add_argument('-i', '--input',
                                   help='A PDS4 label or a XLS spreadsheet or CSV file with the following columns: '
                                        + ','.join(DOIInputUtil.MANDATORY_COLUMNS),
                                   required=True,
                                   metavar='input/DOI_Reserved_GEO_200318.csv')
        action_parser.add_argument('-s', '--submitter-email',
                                   help='The email address of the user reserving the DOIs',
                                   required=True,
                                   metavar='"my.email@node.gov"')
        action_parser.add_argument('-d', '--dry-run',
                                   help="Does not submit the record to OSTI, "
                                        "record stays in a status 'reserved_not_sbmitted'",
                                   required=False,
                                   action='store_true')

    def _process_reserve_action_pdf4(self, target_url):
        # parse input
        if not target_url.startswith('http'):
            xml_tree = etree.parse(target_url)
        else:
            response = requests.get(target_url)
            xml_tree = etree.fromstring(response.content)

        doi = DOIPDS4LabelUtil().get_doi_fields_from_pds4(xml_tree)

        return [doi]

    def _process_reserve_action_xlsx(self, target_url):
        '''Function process a reserve action based on .xlsx ending.'''

        doi_directory_pathname = os.path.join('.', 'output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        try:
            dois = DOIInputUtil().parse_sxls_file(target_url)

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
            dois = DOIInputUtil().parse_csv_file(target_url)

            # Do a sanity check on content of dict_condition_data.
            if len(dois) == 0:
                raise InputFormatException("Length of dict_condition_data['dois'] is zero, target_url " + target_url)

            return dois
        except InputFormatException as e:
            logger.error(e)
            exit(1)

    def _parse_input(self, input):
        if input.endswith('.xml'):
            dois = self._process_reserve_action_pds4(input)

        elif input.endswith('.xlsx'):
            dois = self._process_reserve_action_xlsx(input)

        elif input.endswith('.csv'):
            dois = self._process_reserve_action_csv(input)
        # Check to see if the given file has an attempt to process.
        else:
            msg = f"File type has not been implemented:target_url {input}"
            logger.error(msg)
            raise InputFormatException(msg)

        return dois

    def complete_and_validate_dois(self, dois, contributor, publisher, dry_run):
        try:
            dois_out = []
            for doi in dois:
                doi.contributor = contributor
                doi.publisher = publisher
                # Note that the mustache file must have the double quotes around the status value: <record status="{{status}}">
                # as it is an attribute of a field.
                doi.status = "reserved_not_submitted" if dry_run else "reserved"  # Add 'status' field so the ranking in the workflow can be determined.

                # Validate the label to ensure that no rules are violated against using the same title if a DOI has been minted
                # or the same lidvid has been used if a DOI has been minted.
                self._doi_validator.validate(doi)

                dois_out.append(doi)

            return dois_out

        except Exception as e:
            raise

    def run(self, **kwargs):

        logger.info('run reserve')
        self.parse_arguments(kwargs)

        try:
            try:

                dois = self._parse_input(self._input)
                dois = self.complete_and_validate_dois(dois,
                                                       NodeUtil().get_node_long_name(self._node),
                                                       self._config.get('OTHER', 'doi_publisher'),
                                                       self._dry_run)

            # warnings
            except (DuplicatedTitleDOIException, UnexpectedDOIActionException,
                    TitleDoesNotMatchProductTypeException) as e:
                if not self._force:
                    raise WarningDOIException(e)
            # errors
            except (UnknownNodeException, InputFormatException) as e:
                raise CriticalDOIException(e)

            o_doi_label = DOIOutputOsti().create_osti_doi_reserved_record(dois)
            if not self._dry_run:
                dois, o_doi_label = DOIOstiWebClient().webclient_submit_existing_content(
                    o_doi_label,
                    i_url=self._config.get('OSTI', 'url'),
                    i_username=self._config.get('OSTI', 'user'),
                    i_password=self._config.get('OSTI', 'password'))

                self.m_transaction_builder.prepare_transaction(self._node,
                                                               self._submitter,
                                                               dois,
                                                               input_path=self._input,
                                                               output_content=o_doi_label).log()

            logger.debug(f"reserve_response {o_doi_label}")
            return o_doi_label

        except Exception as e:
            raise
