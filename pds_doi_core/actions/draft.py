import os
import copy
import requests
from lxml import etree

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.references.contributors import DOIContributorUtil



class DOICoreActionDraft(DOICoreAction):
    _name = 'draft'
    description = ' % pds-doi-cmd draft -n img -s Qui.T.Chau@jpl.nasa.gov -i input/bundle_in_with_contributors.xml\n'

    def parse_arguments_from_cmd(self,arguments):
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

    def _resolve_input_into_list_of_names(self, input):
        """Function receives an input which can be one name or a list of names separated by a comma or a directory.  Function will return a list of names.
        """
        o_list_of_names = []

        # Split the input using a comma, then inspect each token to check if it is a directory, a filename or a URL.
        split_tokens = input.split(',')
        for token in split_tokens:
            # Only save the file name if it is not an empty string as in the case of a comma being the last character:
            #    -i https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml,
            # or no name provided with just a comma:
            #    -i ,
            if len(token) > 0:
                if os.path.isdir(token):
                    # Get all file names in a directory.
                    # Note that the top level directory needs to precede the file name in the for loop.
                    list_of_names_from_token = [os.path.join(token,f) for f in os.listdir(token) if os.path.isfile(os.path.join(token, f))]

                    o_list_of_names.extend(list_of_names_from_token)
                elif os.path.isfile(token):
                    # The token is the name of a file, add it.
                    o_list_of_names.append(token)
                else:
                    # The token is a URL, add it.
                    o_list_of_names.append(token)

        return o_list_of_names

    def _transform_pds4_label_into_osti_record(self, input_file, node, submitter, contributor_value):
        """Function receives an XML input file and transform it into an OSTI record.
        """

        o_transformed_label = etree.Element("records")  # If the file cannot be transformed, an XML text of an empty tree will be returned.

        # parse input_file
        if not input_file.startswith('http'):
            # Only process .xml files and print WARNING for any other files, then continue.
            if input_file.endswith('.xml'):
               xml_tree = etree.parse(input_file)
            else:
                logger.warn(f"Expecting .xml files only, encountering {input_file}")
                return etree.tostring(o_transformed_label).decode()
        else:
            # A URL gets read into memory.
            response = requests.get(input_file)
            xml_tree = etree.fromstring(response.content)

        doi = self.m_doi_pds4_label.get_doi_fields_from_pds4(xml_tree)
        doi.publisher = self._config.get('OTHER', 'doi_publisher')
        doi.contributor = contributor_value

        # generate output
        o_doi_label = self.m_doi_output_osti.create_osti_doi_draft_record(doi)

        # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
        doi.status = 'draft'
        transaction_obj = self.m_transaction_builder.prepare_transaction(node,
                                                                         submitter,
                                                                         [doi],
                                                                         output_content=o_transformed_label)
        # Write a transaction for the 'draft' action.
        transaction_obj.log()

        return o_doi_label

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

        # The value of input can be a list of names, or a directory.  Resolve that to a list of names.
        list_of_names = self._resolve_input_into_list_of_names(input)

        # Create an empty tree with 'records' as the root tag.
        # An element will be added from the output of each file parsed.
        o_doi_labels = etree.Element("records") # OSTI uses 'records' as the root tag.

        # Batch processing logic:
        # For each name found, transform the PDS4 label to an OSTI record, then concatenate that record to o_doi_label to return.

        for input_file in list_of_names:

            # Transform the PDS4 label to an OSTI record.
            doi_label = self._transform_pds4_label_into_osti_record(input_file,node,submitter,contributor_value)

            # Concatenate each label to o_doi_labels to return.
            doc = etree.fromstring(doi_label.encode())
            for element in doc.iter():
                if element.tag == 'record':  # OSTI uses 'record' tag for each record.
                    o_doi_labels.append(copy.copy(element))  # Add the 'record' element to an empty tree the first time.

        # end for input_file in list_of_names:

        etree.indent(o_doi_labels)  # Make the output nice by indenting it.

        return etree.tostring(o_doi_labels,pretty_print=True).decode()

