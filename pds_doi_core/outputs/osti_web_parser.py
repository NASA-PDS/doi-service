#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

from pds_doi_core.util.general_util import get_logger
from lxml import etree

logger = get_logger('pds_doi_core.cmd.pds_doi_cmd')

class DOIOstiWebParser:
    # This class contains functions related to parsing input/output for interactions with OSTI server.

    def validate_field_names(self, query_dict):
        '''Function validate the provided fields by the user to make sure they match the expected
           fields by OSTI: https://www.osti.gov/iad2test/docs#endpoints-recordlist.'''

        ACCEPTABLE_FIELD_NAMES_LIST = [ \
            'id', 'doi', 'accession_number', 'published_before', 'published_after', \
            'added_before', 'added_after', 'updated_before', 'updated_after', \
            'first_registered_before', 'first_registered_after', 'last_registered_before', \
            'last_registered_after', 'status', 'start', 'rows', 'sort', 'order']

        o_validated_dict = {}

        for key in query_dict:
            # If the key is valid, save the field and value to return.
            if key in ACCEPTABLE_FIELD_NAMES_LIST:
                o_validated_dict[key ] = query_dict[key]
            else:
                logger.error(f"Unexpected field name '{key}' in query_dict")
                exit(1)

        return o_validated_dict

    def response_get_parse_osti_xml(self,osti_response_text):
        """Function parse a response from a query to the OSTI server (in XML query format) and return a JSON object.
           Specific fields are extracted from input.  Not all fields in XML are used."""

        o_response_dict = {}

        doc = etree.fromstring(osti_response_text)
        my_root = doc.getroottree()

        # Trim down input to just fields we want.
        for element in my_root.iter():
            if element.tag == 'record':
                my_record = my_root.xpath(element.tag)[0]

                o_response_dict['status'] = my_record.attrib['status']
                o_response_dict['id']                  = my_root.xpath('record/id')[0].text 
                o_response_dict['doi']                 = my_root.xpath('record/doi')[0].text 
                o_response_dict['date_record_added']   = my_root.xpath('record/date_record_added')[0].text 
                o_response_dict['date_record_updated'] = my_root.xpath('record/date_record_updated')[0].text 

        return o_response_dict

    def response_get_parse_osti_json(self,osti_response,query_dict=None):
        """Function parse a response from a query to the OSTI server (in JSON format) and return a JSON object.
           Specific fields are extracted from input.  Not all fields in JSON are used."""

        o_response_dicts = []  # It is possible that the query resulted in no rows.

        # These are the fields in a record returned by OSTI
        # fields_returned_from_osti = \
        #    ['id','site_code','title' 'sponsoring_organization', 'accession_number', 'doi',\
        #     'authors', 'status', 'publisher', 'availability', 'publication_date', 'country',\
        #     'description', 'site_url', 'product_type', 'product_type_specific',\
        #     'related_identifiers', 'date_record_added', 'date_record_updated',\
        #     'keywords', 'doi_message']

        query_dict_keys_list = list(query_dict.keys())
        for ii in range(0,len(osti_response['records'])):
            response_dict = {}
            for jj in range(0,len(query_dict_keys_list)):
                # Skip 'rows' field since it was used to require server to return many rows
                # instead of the default 25 rows.
                if query_dict_keys_list[jj] == 'rows':
                   continue
                # If the value matches from server, we retrieve the record.
                if query_dict[query_dict_keys_list[jj]] == osti_response['records'][ii][query_dict_keys_list[jj]]:

                    if 'doi_message' in osti_response['records'][ii]:
                        response_dict['doi_message']  = osti_response['records'][ii]['doi_message']
                    response_dict['title']  = osti_response['records'][ii]['title']
                    response_dict['status'] = osti_response['records'][ii]['status']
                    response_dict['id']                  = osti_response['records'][ii]['id']
                    response_dict['doi']                 = osti_response['records'][ii]['doi']
                    response_dict['date_record_added']   = osti_response['records'][ii]['date_record_added']
                    response_dict['date_record_updated'] = osti_response['records'][ii]['date_record_updated']
                    o_response_dicts.append(response_dict)
                    break

        return o_response_dicts
# end class DOIOstiWebParser
