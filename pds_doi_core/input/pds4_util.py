import requests
from datetime import datetime

from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.input.pds4_util')


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
            'investigation_area': '/*/pds4:Context_Area/pds4:Investigation_Area/*',
            'observing_system_component':
                '/*/pds4:Context_Area/pds4:Observing_System/pds4:Observing_System_Component/*',
            'target_identication': '/*/pds4:Context_Area/pds4:Target_Identification/*',
            'primary_result_summary':  '/pds4:Product_Bundle/pds4:Context_Area/pds4:Primary_Result_Summary/*',

        }

        for key, xpath in xpath_dict.items():
            elmts = xml_tree.xpath(xpath, namespaces=pds4_namespace)
            if elmts:
                pds4_field_value_dict[key] = ' '.join([elmt.text.strip() for elmt in elmts]).strip()

        return pds4_field_value_dict

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
