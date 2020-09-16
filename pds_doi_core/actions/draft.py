import os
import copy
import requests
from lxml import etree

from pds_doi_core.actions.action import DOICoreAction, logger
from pds_doi_core.input.exceptions import UnknownNodeException, DuplicatedTitleDOIException, \
    UnexpectedDOIActionException, TitleDoesNotMatchProductTypeException, InputFormatException, \
    WarningDOIException, CriticalDOIException
from pds_doi_core.input.osti_input_validator import OSTIInputValidator
from pds_doi_core.input.pds4_util import DOIPDS4LabelUtil
from pds_doi_core.outputs.osti import DOIOutputOsti
from pds_doi_core.input.node_util import NodeUtil


from pds_doi_core.util.doi_validator import DOIValidator


class DOICoreActionDraft(DOICoreAction):
    _name = 'draft'
    _description = 'prepare a OSTI record from a PDS4 labels'
    _order = 10
    _run_arguments = ('input', 'node', 'submitter', 'force', 'keyword')

    def __init__(self, db_name=None):
        super().__init__(db_name=db_name)
        self._doi_validator = DOIValidator(db_name=db_name)

        self._input = None
        self._node = None
        self._submitter = None
        self._force = False
        self._target = None
        self._keyword = None

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name, description='create a draft of OSTI records, from PDS4 label or list of PDS4 labels input')
        node_values = NodeUtil.get_permissible_values()
        action_parser.add_argument('-n', '--node',
                                   help='The pds discipline node in charge of the DOI.'
                                        ' Authorized values are: ' + ','.join(node_values),
                                   required=True,
                                   metavar='"img"')
        action_parser.add_argument('-f', '--force',
                                   help='If provided, will force an action to proceed even if the workflow step is less than in database',
                                   required=False, action='store_true')
        action_parser.add_argument('-i', '--input',
                                   help='A pds4 label local or on http, or a list of them separated by ","',
                                   required=True,
                                   metavar='input/bundle_in_with_contributors.xml')
        action_parser.add_argument('-k', '--keyword',
                                   help='Extra keywords separated by ","',
                                   required=False,
                                   metavar='"Image"')
        action_parser.add_argument('-s', '--submitter',
                                   help='The email address of the user creating the draft',
                                   required=True,
                                   metavar='"my.email@node.gov"')
        action_parser.add_argument('-t', '--target',
                                   help='The system target to mint the DOI (only OSTI supported)',
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
                    list_of_names_from_token = [os.path.join(token, f) for f in os.listdir(token) if
                                                os.path.isfile(os.path.join(token, f))]

                    o_list_of_names.extend(list_of_names_from_token)
                elif os.path.isfile(token):
                    # The token is the name of a file, add it.
                    o_list_of_names.append(token)
                else:
                    # The token is a URL, add it.
                    o_list_of_names.append(token)

        return o_list_of_names

    def _add_extra_keywords(self, keywords, io_doi):
        """Function add any extra keywords added to the already produced DOI object.
        """

        # The keywords are commma separated.  The io_doi.keywords field is a set.
        tokens = keywords.split(',')
        for one_keyword in tokens: 
            io_doi.keywords.add(one_keyword.lstrip().rstrip())

        return io_doi

    def _transform_pds4_label_into_osti_record(self, input_file, contributor_value, keywords):
        """Function receives an XML input file and transform it into an OSTI record.
        """

        o_transformed_label = etree.Element("records")  # If the file cannot be transformed, an XML text of an empty tree will be returned.
        o_doi = None  # Set to None to signify if finding a file that does not end with '.xml' extension. 

        # parse input_file
        if not input_file.startswith('http'):
            # Only process .xml files and print WARNING for any other files, then continue.
            if input_file.endswith('.xml'):
                try:
                   xml_tree = etree.parse(input_file)
                except OSError as e:
                    msg = f'Error reading file {input_file}'
                    logger.error(msg)
                    raise InputFormatException(msg)

            else:
                msg = f"File {input_file} is not processed, only .xml are parsed"
                logger.warning(msg)
                return None, o_doi

        else:
            # A URL gets read into memory.
            response = requests.get(input_file)
            xml_tree = etree.fromstring(response.content)

        o_doi = DOIPDS4LabelUtil(landing_page_template=self._config.get('LANDING_PAGES', 'url'))\
            .get_doi_fields_from_pds4(xml_tree)
        o_doi.publisher = self._config.get('OTHER', 'doi_publisher')
        o_doi.contributor = contributor_value
        o_doi.status = 'Draft'  # Add 'status' field so the ranking in the workflow can be determined.

        # Add any extra keywords provided by the user.
        if keywords:
            self._add_extra_keywords(keywords, o_doi)

        # Add the node long name (contributor) as a keyword as well.
        o_doi.keywords.add(contributor_value)

        # generate output
        o_doi_label = DOIOutputOsti().create_osti_doi_draft_record(o_doi)

        # Return the label (which is text) and a dictionary 'o_doi' representing all values parsed.
        return o_doi_label, o_doi

    def _run_single_file(self, input_file, node, submitter, contributor_value, force_flag, keywords=None):
        logger.info(f"input_file {input_file}")
        logger.debug(f"force_flag,input_file {force_flag,input_file}")
        try:

            # Transform the PDS4 label to an OSTI record.
            doi_label, doi_obj = self._transform_pds4_label_into_osti_record(input_file, contributor_value, keywords)

            if doi_label:
                # Validate the doi_label content against schematron for correctness.
                # If the input is correct no exception is thrown and code can proceed to database validation and then submission.
                OSTIInputValidator().validate(doi_label)

                if self._config.get('OTHER', 'draft_validate_against_xsd_flag').lower() == 'true':
                    self._doi_validator.validate_against_xsd(doi_label)
            if doi_obj:
                self._doi_validator.validate(doi_obj)

        # warnings
        except (DuplicatedTitleDOIException, UnexpectedDOIActionException,
                TitleDoesNotMatchProductTypeException) as e:
            if not force_flag:
                # If the user did not use force_flag, re-raise the exception.
                raise WarningDOIException(str(e))
        # errors
        except InputFormatException as e:
            raise CriticalDOIException(e)

        if not doi_obj:
            return None

        # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
        self.m_transaction_builder.prepare_transaction(node,
                                                       submitter,
                                                       [doi_obj],
                                                       input_path=input_file,
                                                       output_content=doi_label).log()

        return doi_label

    def run(self, **kwargs):
        """
        Function receives a URI containing either XML or a local file and draft a Data Object Identifier (DOI).
        :return: o_doi_label:
        """
        self.parse_arguments(kwargs)

        try:
            contributor_value = NodeUtil().get_node_long_name(self._node)

            # The value of input can be a list of names, or a directory.  Resolve that to a list of names.
            list_of_names = self._resolve_input_into_list_of_names(self._input)

            o_doi_labels = etree.Element("records")  # OSTI uses 'records' as the root tag.

            # For each name found, transform the PDS4 label to an OSTI record, then concatenate that record to o_doi_label to return.
            for input_file in list_of_names:
                doi_label = self._run_single_file(input_file, self._node, self._submitter, contributor_value, self._force, self._keyword)
                # It is possible that the value of doi_label is None if the file is not a valid label.
                if not doi_label:
                    continue

                # Concatenate each label to o_doi_labels to return.
                doc = etree.fromstring(doi_label.encode())
                for element in doc.iter():
                    if element.tag == 'record':  # OSTI uses 'record' tag for each record.
                        o_doi_labels.append(
                            copy.copy(element))  # Add the 'record' element to an empty tree the first time.

            etree.indent(o_doi_labels)  # Make the output nice by indenting it.

            return etree.tostring(o_doi_labels, pretty_print=True).decode()

        except UnknownNodeException as e:
            raise CriticalDOIException(str(e))
        except Exception as e:
            raise  # Re-raise any other exceptions.
