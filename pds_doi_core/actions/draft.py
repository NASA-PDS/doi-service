import requests
from lxml import etree
import argparse

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.references.contributors import DOIContributorUtil


class DOICoreActionDraft(DOICoreAction):
    _name = 'draft'
    description = ' % pds-doi-cmd draft -n img -s Qui.T.Chau@jpl.nasa.gov -i input/bundle_in_with_contributors.xml\n'

    def __init__(self):
        super().__init__()
        self._parse_arguments_from_cmd() # Parse arguments from command line if there are any.

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
                                   help='A pds4 label local or on http, a xls spreadsheet, a database file'
                                        ' is also supported to reserve a list of doi',
                                   required=True,
                                   metavar='input/bundle_in_with_contributors.xml')
        action_parser.add_argument('-s', '--submitter-email',
                                   help='The email address of the user performing the action for these services',
                                   required=True,
                                   metavar='"my.email@node.gov"')
        action_parser.add_argument('-t', '--target',
                                   help='the system target to mint the DOI',
                                   required=False,
                                   default='osti',
                                   metavar='osti')

    def run(self,
            input = None,
            node = None,
            submitter = None):
        """
        Function receives a URI containing either XML or a local file and draft a Data Object Identifier (DOI).
        :param target_url:
        :param node:
        :param submitter_email:
        :return: o_doi_label:
        """
        if input is None:
            input = self._input_location

        if node is None:
            node = self._node_id

        if submitter is None:
            submitter = self._submitter



        try:
            contributor_value = self.m_node_util.get_node_long_name(node)
            logger.info(f"contributor_value['{contributor_value}']")
        except UnknownNodeException as e:
            raise e

        # check contributor
        doi_contributor_util = DOIContributorUtil(self._config.get('PDS4_DICTIONARY', 'url'),
                                                  self._config.get('PDS4_DICTIONARY', 'pds_node_identifier'))
        o_permissible_contributor_list = doi_contributor_util.get_permissible_values()
        if contributor_value not in o_permissible_contributor_list:
            logger.error(f"The value of given contributor is not valid: {contributor_value}")
            logger.info(f"permissible_contributor_list {o_permissible_contributor_list}")
            exit(1)

        # parse input
        if not input.startswith('http'):
            xml_tree = etree.parse(input)
        else:
            response = requests.get(input)
            xml_tree = etree.fromstring(response.content)

        doi_fields = self.m_doi_pds4_label.get_doi_fields_from_pds4(xml_tree)
        doi_fields['publisher'] = self._config.get('OTHER', 'doi_publisher')
        doi_fields['contributor'] = contributor_value

        # generate output
        o_doi_label = self.m_doi_output_osti.create_osti_doi_draft_record(doi_fields)

        # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
        transaction_obj = self.m_transaction_builder.prepare_transaction(input,
                                                                         node,
                                                                         submitter,
                                                                         [doi_fields],
                                                                         output_content=o_doi_label)

        # Write a transaction for the 'reserve' action.
        transaction_obj.log()

        return o_doi_label
