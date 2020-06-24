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
        self._input_location = self._arguments.input

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

    def run(self, target_url,
            node_id, submitter_email):
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
        input_content = None
        if not target_url.startswith('http'):
            xml_tree = etree.parse(target_url)
        else:
            response = requests.get(target_url)
            xml_tree = etree.fromstring(response.content)

        doi_fields = self.m_doi_pds4_label.get_doi_fields_from_pds4(xml_tree)
        doi_fields['publisher'] = self._config.get('OTHER', 'doi_publisher')
        doi_fields['contributor'] = contributor_value

        # generate output
        o_doi_label = self.m_doi_output_osti.create_osti_doi_draft_record(doi_fields)

        # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
        transaction_obj = self.m_transaction_builder.prepare_transaction(target_url,
                                                                         node_id,
                                                                         submitter_email,
                                                                         [doi_fields],
                                                                         output_content=o_doi_label)

        # Write a transaction for the 'reserve' action.
        transaction_obj.log()

        return o_doi_label
