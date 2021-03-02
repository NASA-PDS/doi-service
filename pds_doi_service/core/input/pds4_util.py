#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
==========
pds4_util.py
==========

Contains functions and classes for parsing PDS4 XML labels.
"""

import requests
from datetime import datetime
from enum import Enum

from pds_doi_service.core.entities.doi import Doi, DoiStatus, ProductType
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.util.keyword_tokenizer import KeywordTokenizer

logger = get_logger('pds_doi_service.core.input.pds4_util')


class BestParserMethod(Enum):
    BY_COMMA = 1
    BY_SEMI_COLON = 2


class DOIPDS4LabelUtil:

    def __init__(self, landing_page_template):
        self._landing_page_template = landing_page_template

        self.xpath_dict = {
            'lid':
                '/*/pds4:Identification_Area/pds4:logical_identifier',
            'vid':
                '/*/pds4:Identification_Area/pds4:version_id',
            'title':
                '/*/pds4:Identification_Area/pds4:title',
            'publication_year':
                '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:publication_year',
            'modification_date':
                '/*/pds4:Identification_Area/pds4:Modification_History/pds4:Modification_Detail/pds4:modification_date',
            'description':
                '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:description',
            'product_class':
                '/*/pds4:Identification_Area/pds4:product_class',
            'authors':
                '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:author_list',
            'editors':
                '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:editor_list',
            'investigation_area':
                '/*/pds4:Context_Area/pds4:Investigation_Area/pds4:name',
            'observing_system_component':
                '/*/pds4:Context_Area/pds4:Observing_System/pds4:Observing_System_Component/pds4:name',
            'target_identification':
                '/*/pds4:Context_Area/pds4:Target_Identification/pds4:name',
            'primary_result_summary':
                '/pds4:Product_Bundle/pds4:Context_Area/pds4:Primary_Result_Summary/*',
            'doi':
                '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:doi'
        }

    def is_pds4_label(self, xml_tree):
        # If reading xpaths with the PSD4 namespace returns anything, it should
        # be safe to assume its a PDS4 label, additional validation can occur
        # downstream.
        if self.read_pds4(xml_tree):
            return True

        return False

    def get_doi_fields_from_pds4(self, xml_tree):
        pds4_fields = self.read_pds4(xml_tree)
        doi_fields = self.process_pds4_fields(pds4_fields)
        return doi_fields

    def read_pds4(self, xml_tree):
        """
        Reads values from a PDS4 XML Label into a local dictionary using the
        mapping of field names to xpath locations.

        Parameters
        ----------
        xml_tree : lxml.etree.Element
            The root of the parsed PDS4 label to read.

        Returns
        -------
        pds4_field_value_dict : dict
            The dictionary of values read from the parsed PDS4 label.
            The key names correspond to the keys of the xpath mapping
            stored by this class. If the provided XML tree does not
            correspond to a valid PSD4 label, then this will be an empty
            dictionary.

        """
        pds4_field_value_dict = {}

        pds4_namespace = {'pds4': 'http://pds.nasa.gov/pds4/pds/v1'}

        for key, xpath in self.xpath_dict.items():
            elements = xml_tree.xpath(xpath, namespaces=pds4_namespace)

            if elements:
                pds4_field_value_dict[key] = ' '.join(
                    [element.text.strip()
                     for element in elements if element.text]).strip()

        return pds4_field_value_dict

    def _check_for_possible_full_name(self, names_list):
        # Given a list of names:
        # Case 1: "R. Deen, H. Abarca, P. Zamani, J.Maki"
        # determine if each token can be potentially a person' name:
        #   "R. Deen", "H. Abarca", "J.Maki"
        # This happens very rarely but it does happen.
        # Case 4 :"VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team"
        o_list_contains_full_name_flag = False
        num_dots_found = 0
        num_person_names = 0

        for one_name in names_list:
            if '.' in one_name:
                num_dots_found += 1
                # Now that the dot is found, look to see the name contains at
                # least two tokens.
                if len(one_name.strip().split('.')) >= 2:
                    # 'R. Deen' split to ['R','Deen'], "J.Maki" split to ['J','Maki']
                    num_person_names += 1
            else:
                # The name does not contain a dot, split using spaces.
                # Case 4  --> Should be parsed by semi-colon
                #  "VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team"
                # A person's name should contain at least two tokens.
                if len(one_name.strip().split()) >= 2:
                    num_person_names += 1

        # If every name contains a dot, the list can potentially hold a person's
        # name. This does not work if the convention of having the dot
        # in each person's name is broken.
        if num_dots_found == len(names_list) or num_person_names == len(names_list):
            o_list_contains_full_name_flag = True

        logger.debug(f"num_dots_found,num_person_names,len(names_list),names_list "
                     f"{num_dots_found,num_person_names,len(names_list),names_list}")
        logger.debug(f"o_list_contains_full_name_flag "
                     f"{o_list_contains_full_name_flag,names_list,len(names_list)}")

        return o_list_contains_full_name_flag

    def _find_method_to_parse_authors(self, pds4_fields_authors):
        """
        This function makes a best guess as to which parsing method is correct
        for a given list of authors.

        Examples of cases:
            Case 1 --> Should be parsed by semi-colon
                pds4_fields_authors = "Lemmon, M."
            Case 2 --> Should be parsed by comma
                pds4_fields_authors = "R. Deen, H. Abarca, P. Zamani, J.Maki"
            Case 3 --> Should be parsed by semi-colon
                pds4_fields_authors = "Davies, A.; Veeder, G."
            Case 4  --> Should be parsed by semi-colon
                pds4_fields_authors = "VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team"
            Case 5 --> Should be parsed by semi-colon
                pds4_fields_authors = "MER Science Team"

        Parameters
        ----------
        pds4_fields_authors : str
            A listing of authors which may be delimited by comma or semi-colon

        Returns
        -------
        o_best_method : BestParserMethod
            The best method of parsing the list of authors.

        """
        # The 'authors' field from data providers can be inconsistent.
        # Sometimes a comma ',' is used to separate the names, sometimes its
        # semi-colons ';'
        authors_from_comma_split = pds4_fields_authors.split(',')
        authors_from_semi_colon_split = pds4_fields_authors.split(';')

        # Check from authors_from_comma_split to see if it possibly contains full name.
        # Mostly this case: "R. Deen, H. Abarca, P. Zamani, J.Maki"
        # When it is not obvious because it looks similarly to this case:
        # "VanBommel, S. J., Guinness, E., Stein, T., and the MER Science Team"
        comma_parsed_list_contains_full_name = self._check_for_possible_full_name(authors_from_comma_split)

        number_commas = pds4_fields_authors.count(',')
        number_semi_colons = pds4_fields_authors.count(';')

        if number_semi_colons == 0:
            if number_commas >= 1:
                if comma_parsed_list_contains_full_name:
                    # Case 2
                    o_best_method = BestParserMethod.BY_COMMA
                else:
                    # Case 1 or Case 4
                    o_best_method = BestParserMethod.BY_SEMI_COLON
            else:
                # Case 5
                o_best_method = BestParserMethod.BY_SEMI_COLON
        else:
            # Case 3
            o_best_method = BestParserMethod.BY_SEMI_COLON

        logger.debug(f"o_best_method,pds4_fields_authors "
                     f"{o_best_method,pds4_fields_authors} "
                     f"number_commas,number_semi_colons "
                     f"{number_commas,number_semi_colons}")
        logger.debug(f"len(authors_from_comma_split),len(authors_from_semi_colon_split) "
                     f"{len(authors_from_comma_split),len(authors_from_semi_colon_split)}")

        return o_best_method

    def process_pds4_fields(self, pds4_fields):
        try:
            product_class = pds4_fields['product_class']
            product_class_suffix = product_class.split('_')[1]

            if product_class == 'Product_Document':
                product_specific_type = 'technical documentation'
                product_type = ProductType.Text
            else:
                product_specific_type = 'PDS4 Refereed Data ' + product_class_suffix
                product_type = ProductType.Dataset

            site_url = self._landing_page_template.format(
                product_class_suffix, requests.utils.quote(pds4_fields['lid']),
                requests.utils.quote(pds4_fields['vid'])
            )

            editors = (self.get_editor_names(pds4_fields['editors'].split(';'))
                       if 'editors' in pds4_fields else None)

            # The 'authors' field is inconsistent on the use of separators.
            # Try to make a best guess on which method is better.
            o_best_method = self._find_method_to_parse_authors(pds4_fields['authors'])

            if o_best_method == BestParserMethod.BY_COMMA:
                authors_list = pds4_fields['authors'].split(',')
            elif o_best_method == BestParserMethod.BY_SEMI_COLON:
                authors_list = pds4_fields['authors'].split(';')
            else:
                logger.error(f"o_best_method,pds4_fields['authors'] "
                             f"{o_best_method,pds4_fields['authors']}")
                raise InputFormatException(
                    "Cannot split the authors using comma or semi-colon."
                )

            osti_id = None

            if 'doi' in pds4_fields:
                doi_prefix_suffix = pds4_fields['doi'].split('/')
                if len(doi_prefix_suffix) == 2:
                    osti_id = doi_prefix_suffix[1]

            doi = Doi(status=DoiStatus.Unknown,
                      title=pds4_fields['title'],
                      description=pds4_fields['description'],
                      publication_date=self.get_publication_date(pds4_fields),
                      product_type=product_type,
                      product_type_specific=product_specific_type,
                      related_identifier=pds4_fields['lid'] + '::' + pds4_fields['vid'],
                      site_url=site_url,
                      authors=self.get_author_names(authors_list),
                      editors=editors,
                      keywords=self.get_keywords(pds4_fields),
                      date_record_added=self.get_record_added_date(pds4_fields),
                      id=osti_id)
        except KeyError as key_err:
            missing_key = key_err.args[0]
            msg = (f"Could not find a value for an expected PS4 label field: {key_err}.\n"
                   f"Please ensure there is a value present in the label for the "
                   f"following xpath: {self.xpath_dict[missing_key]}")
            logger.error(msg)
            raise InputFormatException(msg)

        return doi

    def get_publication_date(self, pds4_fields):
        # The field 'modification_date' is favored first.
        # If it is present use it, otherwise use 'publication_year' field next.
        if 'modification_date' in pds4_fields:
            logger.debug(
                f"pds4_fields['modification_date'] "
                f"{pds4_fields['modification_date'], type(pds4_fields['modification_date'])}"
            )

            # Some PDS4 labels have more than one 'modification_date' field,
            # so sort in ascending and select the first date.
            latest_mod_date = sorted(pds4_fields['modification_date'].split(), reverse=False)[0]
            publication_date = datetime.strptime(latest_mod_date, '%Y-%m-%d')
        elif 'publication_year' in pds4_fields:
            publication_date = datetime.strptime(pds4_fields['publication_year'], '%Y')
        else:
            publication_date = datetime.now()

        return publication_date

    def get_record_added_date(self, pds4_fields):
        # TODO: have the creation date read from the transaction database if the
        #       record has been added earlier.
        return datetime.now()

    def get_keywords(self, pds4_fields):
        keyword_fields = {'investigation_area',
                          'observing_system_component',
                          'target_identification',
                          'primary_result_summary',
                          'description'}

        keyword_tokenizer = KeywordTokenizer()

        for keyword_src in keyword_fields:
            if keyword_src in pds4_fields.keys():
                keyword_tokenizer.process_text(pds4_fields[keyword_src])

        return keyword_tokenizer.get_keywords()

    @staticmethod
    def _smart_first_last_name_detector(split_fullname, default_order=(0, -1)):
        if len(split_fullname[0]) == 1 or split_fullname[0][-1] == '.':
            return 0, -1
        elif len(split_fullname[-1]) == 1 or split_fullname[-1][-1] == '.':
            return -1, 0
        else:
            return default_order

    @staticmethod
    def _get_name_components(full_name, first_last_name_order,
                             first_last_name_separators,
                             use_smart_first_name_detector=True):
        logger.debug(f"parse full_name {full_name}")

        full_name = full_name.strip()

        person = None

        for sep in first_last_name_separators:
            split_fullname = [name.strip() for name in full_name.split(sep)]

            if len(split_fullname) >= 2:
                # identify first/last name order
                if use_smart_first_name_detector:
                    first_i, last_i = DOIPDS4LabelUtil._smart_first_last_name_detector(
                        split_fullname, default_order=first_last_name_order
                    )
                else:
                    first_i, last_i = tuple(first_last_name_order)

                # re-add . if it has been removed as a separator
                first_name_suffix = '.' if sep == '.' else ''

                person = {
                    'first_name': split_fullname[first_i] + first_name_suffix,
                    'last_name': split_fullname[last_i]
                }

                if len(split_fullname) >= 3:
                    person['middle_name'] = split_fullname[1]

                break

        if not person:
            person = {'full_name': full_name}

        logger.debug(f'parsed person {person}')

        return person

    def get_names(self, name_list, first_last_name_order=(0, -1),
                  first_last_name_separator=(',', '.')):
        logger.debug(f"name_list {name_list}")
        logger.debug(f"first_last_name_order {first_last_name_order}")

        persons = []

        for full_name in name_list:
            persons.append(
                self._get_name_components(full_name, first_last_name_order,
                                          first_last_name_separator)
            )

        return persons

    def get_author_names(self, name_list):
        return self.get_names(name_list, first_last_name_order=(-1, 0))

    def get_editor_names(self, name_list):
        return self.get_names(name_list, first_last_name_separator=(',',))
