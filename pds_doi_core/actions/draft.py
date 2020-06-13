import requests
from lxml import etree

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.references.contributors import DOIContributorUtil


class DOICoreActionDraft(DOICoreAction):
    def __init__(self):
        super().__init__()

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