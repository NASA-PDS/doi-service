from lxml import etree
from datetime import datetime

from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.input.osti_input_util')

class OSTIInputUtil:
    def read_osti_xml(self, osti_response_text):
        """
        Function parses XML content possibly from output from OSTI.
        The format has <records> tags with iteration of <record> tags for each record.

        :param osti_response_text: text of XML document
        :return:
        """

        o_response_dicts = []  # Return a list of dictionary with each dictionary a record in the input file.

        # Convert the XML text to a tree so we can use etree to parse through it
        doc = etree.fromstring(osti_response_text)
        my_root = doc.getroottree()

        # Trim down input to just fields we want.
        element_count = 0
        for element in my_root.iter():
            response_dict = {} 
            if element.tag == 'record':
                if my_root.xpath('record/id') :
                    response_dict['id']       = my_root.xpath('record/id')[element_count].text
                if my_root.xpath('record/site_url'):
                    response_dict['site_url']      = my_root.xpath('record/site_url')[element_count].text
                if my_root.xpath('record/title'):
                    response_dict['title']      = my_root.xpath('record/title')[element_count].text
                if my_root.xpath('record/doi'):
                    response_dict['doi']      = my_root.xpath('record/doi')[element_count].text
                if my_root.xpath('record/publication_date'):
                    response_dict['publication_date'] = my_root.xpath('record/publication_date')[element_count].text
                if my_root.xpath('record/product_type'):
                    response_dict['product_type'] = my_root.xpath('record/product_type')[element_count].text
                if my_root.xpath('record/product_type_specific'):
                    response_dict['product_type_specific'] = my_root.xpath('record/product_type_specific')[element_count].text
                if my_root.xpath('record/date_first_registered'):
                    response_dict['date_first_registered'] = my_root.xpath('record/date_first_registered')[element_count].text
                if my_root.xpath('record/date_last_registered'):
                    response_dict['date_last_registered'] = my_root.xpath('record/date_last_registered')[element_count].text
                if my_root.xpath('record/date_record_added'):
                    response_dict['date_record_added'] = my_root.xpath('record/date_record_added')[element_count].text
                if my_root.xpath('record/authors'):
                    num_authors = len(my_root.xpath('record/authors')[0])
                    response_dict['authors'] = []
                    for ii in range(num_authors):
                        one_author = {}
                        one_author['first_name']  = (my_root.xpath('record/authors')[element_count]).xpath('author/first_name')[ii].text
                        one_author['last_name']   = (my_root.xpath('record/authors')[element_count]).xpath('author/last_name') [ii].text
                        response_dict['authors'].append(one_author)

                if my_root.xpath('record/related_identifiers'):
                    num_identifiers = len(my_root.xpath('record/related_identifiers')[0])
                    response_dict['related_identifiers'] = []
                    for ii in range(num_identifiers):
                        one_identifier = {}
                        one_identifier['identifier_type']  = (my_root.xpath('record/related_identifiers')[element_count]).xpath('related_identifier/identifier_type') [ii].text
                        one_identifier['identifier_value'] = (my_root.xpath('record/related_identifiers')[element_count]).xpath('related_identifier/identifier_value')[ii].text
                        one_identifier['relation_type']    = (my_root.xpath('record/related_identifiers')[element_count]).xpath('related_identifier/relation_type')[ii].text
                        response_dict['related_identifiers'].append(one_identifier)

                o_response_dicts.append(response_dict)  # App the dictionary response_dict to o_response_dicts list.
                element_count += 1

        return o_response_dicts

    def process_pds4_fields(self, pds4_fields):
        doi_field_value_dict = {}
        landing_page_template = 'https://pds.jpl.nasa.gov/ds-view/pds/view{}.jsp?identifier={}&version={}'

        doi_field_value_dict['title'] = pds4_fields['title']
        doi_field_value_dict['publication_date'] = self.get_publication_date(pds4_fields)  # datetime object
        doi_field_value_dict['description'] = pds4_fields['description']
        doi_field_value_dict["product_type"] = pds4_fields['product_class'].split('_')[1]
        doi_field_value_dict["product_type_specific"] = "PDS4 " + doi_field_value_dict["product_type"]
        doi_field_value_dict['related_identifier'] = pds4_fields['lid'] + '::' + pds4_fields['vid']
        doi_field_value_dict['site_url'] = landing_page_template.format(doi_field_value_dict["product_type"],
                                                                        requests.utils.quote(pds4_fields['lid']),
                                                                        requests.utils.quote(pds4_fields['vid']))
        doi_field_value_dict['authors'] = self.get_author_names(pds4_fields['authors'].split(','))
        if 'editors' in pds4_fields.keys():
            doi_field_value_dict['editors'] = self.get_editor_names(pds4_fields['editors'].split(';'))
        doi_field_value_dict['keywords'] = self.get_keywords(pds4_fields)

        return doi_field_value_dict

    def get_publication_date(self, pds4_fields):
        if 'publication_year' in pds4_fields.keys():
            return datetime.strptime(pds4_fields['publication_year'], '%Y')
        elif 'modification_date' in pds4_fields.keys():
            return datetime.strptime(pds4_fields['modification_date'], '%Y-%m-%d')
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
        return keywords

    def get_names(self, name_list,
                  first_last_name_order=[0, 1],
                  first_last_name_separator=' '):
        persons = []
        logger.debug(f"name_list {name_list}")
        logger.debug(f"first_last_name_order {first_last_name_order}")

        for full_name in name_list:
            logger.debug(f"full_name {full_name}")
            split_full_name = full_name.strip().split(first_last_name_separator)
            if len(split_full_name) == 2:
                persons.append({'first_name': split_full_name[first_last_name_order[0]].strip(),
                                'last_name': split_full_name[first_last_name_order[1]].strip()})
            else:
                logger.warning(f"author first name not found for [{full_name}]")
                # Since we cannot determine the first name and last name from splitting, we assume the first name is blank
                # and last_name as full_name.
                persons.append({'first_name': '',
                                'last_name': full_name.lstrip().rstrip()})
                logger.debug(f"persons {persons}")
                
        return persons

    def get_author_names(self, name_list):
        return self.get_names(name_list, first_last_name_order=[0, 1], first_last_name_separator=' ')

    def get_editor_names(self, name_list):
        return self.get_names(name_list, first_last_name_order=[1, 0], first_last_name_separator=',')
