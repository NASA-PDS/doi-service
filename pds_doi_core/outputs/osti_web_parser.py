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

    def response_get_parse_osti_xml(self,osti_response_text,interested_fields=['status','doi','id','title','date_record_added','date_record_updated','publication_date','product_type','product_type_specific','doi_message','related_identifier']):
        """Function parse a response from a GET (query) or a PUT to the OSTI server (in XML query format) and return a list of dictionaries.
           By default, all possible fields are extracted.  If desire to only extract smaller set of fields, they should be specified accordingly.
           Specific fields are extracted from input.  Not all fields in XML are used."""

        o_response_dicts = []

        doc     = etree.fromstring(osti_response_text)
        my_root = doc.getroottree()

        # Trim down input to just fields we want.
        element_record = 0
        for element in my_root.iter():
            if element.tag == 'record':
                if element.get('status').lower() == 'error':
                    # The 'error' record is parsed differently and does not have all the attributes we desire.
                    # Get the entire text and save it in 'error' key.  Print a WARN only since it is not related to any particular 'doi' or 'id' action.
                    logger.warn(f"ERROR_RECORD {element.text}")
                    #error_record = {} # Save any error messages in this dictionary.
                    #error_record['error'] = etree.tostring(element)
                    continue

                response_dict = {}  # This dictionary will be added to o_response_dicts when all fields have been extracted below.

                if 'status' in interested_fields:
                    response_dict['status']              = element.attrib['status']  # Becareful to get the 'status' from 'record' tag instead of 'records'

                # The xpath has to be checked for each field since it may not exist and cause Python to fail.
                if 'title' in interested_fields and element.xpath('title'):
                    response_dict['title']               = element.xpath('title')[0].text
                if 'id' in interested_fields and element.xpath('id'):
                    response_dict['id']                  = element.xpath('id')[0].text
                if 'doi' in interested_fields and element.xpath('doi'):
                    response_dict['doi']                 = element.xpath('doi')[0].text
                if 'date_record_added' in interested_fields and element.xpath('date_record_added'):
                    response_dict['date_record_added']   = element.xpath('date_record_added')[0].text
                if 'date_record_updated' in interested_fields and element.xpath('date_record_updated'):
                    response_dict['date_record_updated'] = element.xpath('date_record_updated')[0].text
                if 'publication_date' in interested_fields and element.xpath('publication_date'):
                    response_dict['publication_date']      = element.xpath('publication_date')[0].text
                if 'product_type' in interested_fields and element.xpath('product_type'):
                    response_dict['product_type']          = element.xpath('product_type')[0].text
                if 'product_type_specific' in interested_fields and element.xpath('product_type_specific'):
                    response_dict['product_type_specific'] = element.xpath('product_type_specific')[0].text

                # Not all responses have the 'doi_message' field.
                if element.xpath('doi_message'):
                    response_dict['doi_message']     = element.xpath('doi_message')[0].text

                if 'related_identifier' in interested_fields and len(my_root.xpath('record/related_identifiers/related_identifier/identifier_value')) > 0: 
                    response_dict['related_identifier']  = my_root.xpath('record/related_identifiers/related_identifier/identifier_value')[element_record].text

                o_response_dicts.append(response_dict)

                element_record += 1

        # Append the error_record if there is something in it.
        # If desire, add error_record to o_response_dicts.  For now, commented out.
        #if bool(error_record):
        #    o_response_dicts.append(error_record)

        return o_response_dicts

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
