#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
from lxml import etree
from datetime import datetime

from pds_doi_core.util.general_util import get_logger
from pds_doi_core.entities.doi import Doi
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

    @staticmethod
    def response_get_parse_osti_xml(osti_response_text,interested_fields=['status','doi','id','title','date_record_added','date_record_updated','publication_date','product_type','product_type_specific','doi_message','related_identifier']):
        """Function parse a response from a GET (query) or a PUT to the OSTI server (in XML query format) and return a list of dictionaries.
           By default, all possible fields are extracted.  If desire to only extract smaller set of fields, they should be specified accordingly.
           Specific fields are extracted from input.  Not all fields in XML are used."""

        dois = []

        doc     = etree.fromstring(osti_response_text)
        my_root = doc.getroottree()

        # Trim down input to just fields we want.
        element_record = 0
        for element in my_root.iter():
            if element.tag == 'record':
                if element.get('status').lower() == 'error':
                    # The 'error' record is parsed differently and does not have all the attributes we desire.
                    # Get the entire text and save it in 'error' key.  Print a WARN only since it is not related to any particular 'doi' or 'id' action.
                    logger.error(f"ERROR OSTI RECORD {element.text}")
                    continue
                else:
                    doi = Doi(title=element.xpath('title')[0].text,
                              publication_date=element.xpath('publication_date')[0].text,
                              product_type=element.xpath('product_type')[0].text,
                              product_type_specific=element.xpath('product_type_specific')[0].text,
                              related_identifier=element.xpath("related_identifiers/related_identifier[./identifier_type='URL']/identifier_value")[0].text,
                              id=element.xpath('id')[0].text,
                              doi=element.xpath('doi')[0].text,
                              status=element.attrib['status'].lower(),
                              date_record_added=datetime.strptime(element.xpath('date_record_added')[0].text, '%Y-%m-%d'),
                              date_record_updated=datetime.strptime(element.xpath('date_record_updated')[0].text, '%Y-%m-%d'),
                              )

                    # Not all responses have the 'doi_message' field.
                    if element.xpath('doi_message'):
                        doi.message = element.xpath('doi_message')[0].text

                    dois.append(doi)

                    element_record += 1

        return dois

    def response_get_parse_osti_json(self,osti_response):
        """Function parse a response from a query to the OSTI server (in JSON format) and return a JSON object.
           Specific fields are extracted from input.  Not all fields in JSON are used."""

        dois = []  # It is possible that the query resulted in no rows.

        # These are the fields in a record returned by OSTI
        # fields_returned_from_osti = \
        #    ['id','site_code','title' 'sponsoring_organization', 'accession_number', 'doi',\
        #     'authors', 'status', 'publisher', 'availability', 'publication_date', 'country',\
        #     'description', 'site_url', 'product_type', 'product_type_specific',\
        #     'related_identifiers', 'date_record_added', 'date_record_updated',\
        #     'keywords', 'doi_message']

        for record in osti_response['records']:
            doi = Doi(title=record['title'],
                      publication_date=record['publication_date'],
                      product_type=record['product_type'],
                      product_type_specific=record['product_type_specific'],
                      related_identifier=record['related_identifiers'][0]['identifier_value'],
                      status=record['status'],
                      id=record['id'],
                      doi=record['doi'],
                      date_record_added=record['date_record_added'],
                      date_record_updated=record['date_record_updated'])
            if 'doi_message' in record:
                doi.message = record['doi_message']

            dois.append(doi)

        return dois

        # query_dict_keys_list = list(query_dict.keys())
        # for ii in range(0,len(osti_response['records'])):
        #     response_dict = {}
        #     for jj in range(0,len(query_dict_keys_list)):
        #         # Skip 'rows' field since it was used to require server to return many rows
        #         # instead of the default 25 rows.
        #         if query_dict_keys_list[jj] == 'rows':
        #            continue
        #         # If the value matches from server, we retrieve the record.
        #         if query_dict[query_dict_keys_list[jj]] == osti_response['records'][ii][query_dict_keys_list[jj]]:
        #
        #             if 'doi_message' in osti_response['records'][ii]:
        #                 response_dict['doi_message']  = osti_response['records'][ii]['doi_message']
        #             response_dict['title']  = osti_response['records'][ii]['title']
        #             response_dict['status'] = osti_response['records'][ii]['status']
        #             response_dict['id']                  = osti_response['records'][ii]['id']
        #             response_dict['doi']                 = osti_response['records'][ii]['doi']
        #             response_dict['date_record_added']   = osti_response['records'][ii]['date_record_added']
        #             response_dict['date_record_updated'] = osti_response['records'][ii]['date_record_updated']
        #             o_response_dicts.append(response_dict)
        #             break

        #return o_response_dicts
# end class DOIOstiWebParser
