import requests
from datetime import datetime
from enum import Enum

from pds_doi_core.input.exceptions import InputFormatException
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.entities.doi import Doi
logger = get_logger('pds_doi_core.input.pds4_util')

class BestParserMethod(Enum):
    BY_COMMA      = 1
    BY_SEMI_COLON = 2

class DOIPDS4LabelUtil:

    def get_doi_fields_from_pds4(self, xml_tree):
        pds4_fields = self.read_pds4(xml_tree)
        doi_fields = self.process_pds4_fields(pds4_fields)
        return doi_fields

    def read_pds4(self, xml_tree):
        """

        :param xml_tree: lxml etree
        :return:
        """
        pds4_field_value_dict = {}

        pds4_namespace = {'pds4': 'http://pds.nasa.gov/pds4/pds/v1'}
        xpath_dict = {
            'lid': '/*/pds4:Identification_Area/pds4:logical_identifier',
            'vid': '/*/pds4:Identification_Area/pds4:version_id',
            'title': '/*/pds4:Identification_Area/pds4:title',
            'publication_year':
                '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:publication_year',
            'modification_date':
                '/*/pds4:Identification_Area/pds4:Modification_History/pds4:Modification_Detail/pds4:modification_date',
            'description': '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:description',
            'product_class': '/*/pds4:Identification_Area/pds4:product_class',
            'authors': '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:author_list',
            'editors': '/*/pds4:Identification_Area/pds4:Citation_Information/pds4:editor_list',
            # Desire only the 'name' field
            'investigation_area': '/*/pds4:Context_Area/pds4:Investigation_Area/pds4:name',
            # Desire only the 'name' field.
            'observing_system_component':
                '/*/pds4:Context_Area/pds4:Observing_System/pds4:Observing_System_Component/pds4:name',
            # Desire only the 'name' field
            'target_identication': '/*/pds4:Context_Area/pds4:Target_Identification/pds4:name',
            'primary_result_summary':  '/pds4:Product_Bundle/pds4:Context_Area/pds4:Primary_Result_Summary/*',

        }

        for key, xpath in xpath_dict.items():
            elmts = xml_tree.xpath(xpath, namespaces=pds4_namespace)
            if elmts:
                pds4_field_value_dict[key] = ' '.join([elmt.text.strip() for elmt in elmts]).strip()

        return pds4_field_value_dict

    def _make_best_guess_method_to_parse_authors(self,pds4_fields_authors):
        # The 'authors' field is inconsistent.  Sometimes it is using comma ',' to separate
        # the names, sometimes it is using semi-colon ';'
        # If after parsing using the get_author_names(), if the 'full_name' is in the dictionary
        # it is a clue that the best method of parsing is the other one.

        o_best_method = None 
        authors_from_comma_split      = pds4_fields_authors.split(',')
        authors_from_semi_colon_split = pds4_fields_authors.split(';')

        authors_list_via_comma = self.get_author_names(authors_from_comma_split)
        authors_list_via_semi_colon = self.get_author_names(authors_from_semi_colon_split)

        logger.debug(f"authors_list_via_comma = {authors_list_via_comma}") 
        logger.debug(f"authors_list_via_semi_colon = {authors_list_via_semi_colon}")

        o_best_method = BestParserMethod.BY_COMMA 
        for one_author in authors_list_via_comma:
            if 'full_name' in one_author.keys():
                o_best_method = BestParserMethod.BY_SEMI_COLON
        for one_author in authors_list_via_semi_colon:
            if 'full_name' in one_author.keys():
                o_best_method = BestParserMethod.BY_COMMA 

        logger.debug(f"o_best_method,pds4_fields_authors {o_best_method,pds4_fields_authors}")
        return o_best_method

    def process_pds4_fields(self, pds4_fields):
        doi_field_value_dict = {}

        product_type = pds4_fields['product_class'].split('_')[1]
        landing_page_template = 'https://pds.jpl.nasa.gov/ds-view/pds/view{}.jsp?identifier={}&version={}'

        site_url = landing_page_template.format(product_type,
                                                requests.utils.quote(pds4_fields['lid']),
                                                requests.utils.quote(pds4_fields['vid']))
        editors = self.get_editor_names(pds4_fields['editors'].split(';')) if 'editors' in pds4_fields.keys() else None


        # The 'authors' field is inconsistent.  Try to make a best guess on which method is better.
        o_best_method =  self._make_best_guess_method_to_parse_authors(pds4_fields['authors'])
        if o_best_method == BestParserMethod.BY_COMMA:
            authors_list = pds4_fields['authors'].split(',')
        elif o_best_method == BestParserMethod.BY_SEMI_COLON:
            authors_list = pds4_fields['authors'].split(';')
        else:
            logger.error(f"o_best_method,pds4_fields['authors'] {o_best_method,pds4_fields['authors']}")
            raise InputFormatException("Cannot split the authors using comma or semi-colon.")

        doi = Doi(title=pds4_fields['title'],
                  description=pds4_fields['description'],
                  publication_date=self.get_publication_date(pds4_fields),
                  product_type=product_type,
                  product_type_specific= "PDS4 Refereed Data " + product_type,
                  related_identifier=pds4_fields['lid'] + '::' + pds4_fields['vid'],
                  site_url=site_url,
                  authors=self.get_author_names(authors_list),
                  editors=editors,
                  keywords=self.get_keywords(pds4_fields)
                  )

        # Add field 'date_record_added' because the XSD requires it.
        if doi.date_record_added is None:
            doi.date_record_added = datetime.now().strftime('%Y-%m-%d')

        return doi

    def get_publication_date(self, pds4_fields):
        # The field 'modification_date' is favored first.  If it occurs, use it, otherwise use 'publication_year' field next.
        if 'modification_date' in pds4_fields.keys():
            return datetime.strptime(pds4_fields['modification_date'], '%Y-%m-%d')
        elif 'publication_year' in pds4_fields.keys():
            return datetime.strptime(pds4_fields['publication_year'], '%Y')
        else:
            return datetime.now()

    def get_keywords(self, pds4_fields):
        keyword_field = {'investigation_area', 'observing_system_component', 'target_identication', 'primary_result_summary'}
        keywords = set()
        for keyword_src in keyword_field:
            if keyword_src in pds4_fields.keys():
                keyword_list = [k.strip()
                                for k in pds4_fields[keyword_src].strip().split(" ") if len(k.strip()) > 0]
                keywords = keywords.union(keyword_list)

        # Take the fields as is as well without splitting on spaces
        if 'description' in pds4_fields.keys():
            keywords = keywords.union([pds4_fields['description'].lstrip().rstrip()])
        if 'investigation_area' in pds4_fields.keys():
            keywords = keywords.union([pds4_fields['investigation_area'].lstrip().rstrip()])
        # Example: 'IRTF 3.0-Meter Telescope'
        if 'observing_system_component' in pds4_fields.keys():
            keywords = keywords.union([pds4_fields['observing_system_component'].lstrip().rstrip()])

        # Remove words that may not be useful, such as 'of', 'or', 'the'.
        not_useful_words = ['of','or','the']
        for word_to_remove in not_useful_words:
            if word_to_remove in keywords:
                keywords.remove(word_to_remove)

        return keywords

    def get_names(self, name_list,
                  first_last_name_order=[0, 1],
                  first_last_name_separator=[' ', '.']):
        persons = []
        logger.debug(f"name_list {name_list}")
        logger.debug(f"first_last_name_order {first_last_name_order}")

        for full_name in name_list:
            logger.debug(f"full_name {full_name}")
            split_full_name = []
            separator_index = 0
            use_dot_split_flag = False
            while len(split_full_name)<2 and separator_index<len(first_last_name_separator):
                if first_last_name_separator[separator_index] == '.':
                    use_dot_split_flag = True
                split_full_name = full_name.strip().split(first_last_name_separator[separator_index])
                separator_index += 1

            logger.debug(f"split_full_name,len(split_full_name) {split_full_name,len(split_full_name)}")
            logger.debug(f"first_last_name_order {first_last_name_order}")
            logger.debug(f"use_dot_split_flag {use_dot_split_flag}")
            if len(split_full_name) >= 2:
                # If the dot '.' was used to split the full_name, the dot need to be add back to the first name.
                corrected_first_name = split_full_name[first_last_name_order[0]].strip()
                if use_dot_split_flag:
                    corrected_first_name = corrected_first_name + "."
                logger.debug(f"corrected_first_name {corrected_first_name}")

                # If the last name contains the dot '.', that means the first and last name are in the wrong order
                # and will need swapping.
                # An example of of split_full_name that need swapping is:
                #     split_full_name = ['Davies,', 'A.']
                # Usually, the expected values should be:
                #     split_full_name ['A.', 'Davis']
                if '.' in split_full_name[first_last_name_order[1]].strip():
                    logger.debug(f"true dot in split_full_name[first_last_name_order[1]].strip() {split_full_name[first_last_name_order[1]].strip()}") 
                    actual_last_name = split_full_name[first_last_name_order[0]].strip() 
                    # Remove comma if actual_last_name ends with ','.
                    if split_full_name[first_last_name_order[0]].strip().endswith(','):
                        pos_of_comma = split_full_name[first_last_name_order[0]].strip().index(',')
                        actual_last_name = split_full_name[first_last_name_order[0]].strip()[0:pos_of_comma];
                    persons.append({'first_name': split_full_name[first_last_name_order[1]].strip(),
                                    'last_name':  actual_last_name})
                else:
                    logger.debug(f"false dot in split_full_name[first_last_name_order[1]].strip() {split_full_name[first_last_name_order[1]].strip()}, len(split_full_name) {len(split_full_name)}") 
                    # Fetch the middle name if provided.
                    if len(split_full_name) >= 3:
                        persons.append({'first_name': corrected_first_name,
                                        'middle_name': split_full_name[2].strip(),
                                        'last_name': split_full_name[first_last_name_order[1]].strip()})
                    else:
                        persons.append({'first_name': corrected_first_name,
                                        'last_name': split_full_name[first_last_name_order[1]].strip()})
            else:
                logger.warning(f"author first name not found for [{full_name}]")
                # Deleted the first_name field as an empty string.
                # OSTI does not like for any fields to be empty string.
                # If cannot parse first_name or last_name, create full_name instead.
                persons.append({'full_name': full_name.strip()}) 

        return persons

    def get_author_names(self, name_list):
        return self.get_names(name_list, first_last_name_order=[0, 1], first_last_name_separator=[' ', '.'])

    def get_editor_names(self, name_list):
        return self.get_names(name_list, first_last_name_order=[1, 0], first_last_name_separator=',')
