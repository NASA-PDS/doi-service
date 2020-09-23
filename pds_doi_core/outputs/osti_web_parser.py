#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
from lxml import etree
from datetime import datetime

from pds_doi_core.entities.doi import Doi
from pds_doi_core.input.exceptions import InputFormatException
from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.outputs.osti_web_parser')

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

    def parse_author_names(self,authors_element):
        """ Given a list of authors element, parse for individual 'first_name', 'middle_name', 'last_name' or 'full_name' fields."""
        o_authors_list = []
        # If exist, collect all the first_name, middle_name, last_name or full_name fields into a list of dictionaries.
        for single_author in authors_element:
            first_name = single_author.xpath('author/first_name')
            last_name  = single_author.xpath('author/last_name')
            full_name  = single_author.xpath('author/full_name')
            middle_name = single_author.xpath('author/middle_name')

            if full_name:
                author_dict = {'full_name': full_name[0].text}
            else:
                if first_name and last_name:
                    if middle_name:
                        author_dict = {'first_name': first_name[0].text, 'middle_name' : middle_name[0].text, 'last_name' : last_name[0].text} 
                    else:
                        author_dict = {'first_name': first_name[0].text, 'last_name' : last_name[0].text} 
            o_authors_list.append(author_dict)
        return o_authors_list

    def parse_optional_fields(self,io_doi,single_record_element):
        """ Given a single record element, parse for optional fields that may not be present from the OSTI response:
                'id', 'site_url', 'doi', 'date_record_added', 'date_record_updated', 'doi_message', 'authors'."""

        if single_record_element.xpath('id'):
            io_doi.id = single_record_element.xpath('id')[0].text
            logger.debug(f"Adding optional field 'id'")

        if single_record_element.xpath('site_url'):
            io_doi.site_url = single_record_element.xpath('site_url')[0].text
            logger.debug(f"Adding optional field 'site_url'")

        if single_record_element.xpath('doi'):
            io_doi.doi = single_record_element.xpath('doi')[0].text
            logger.debug(f"Adding optional field 'doi'")

        if single_record_element.xpath('date_record_added'):
            logger.debug(f"Adding optional field 'date_record_added'")
            # It is possible have bad date format.
            try:
                io_doi.date_record_added = datetime.strptime(single_record_element.xpath('date_record_added')[0].text, '%Y-%m-%d') 
            except Exception as e:
                logger.error(f"Cannot parse field 'date_record_added'.  Expecting format '%Y-%m-%d'.  Received {single_record_element.xpath('date_record_added')[0].text}")
                raise InputFormatException(f"Cannot parse field 'date_record_added'.  Expecting format '%Y-%m-%d'.  Received {single_record_element.xpath('date_record_added')[0].text}")

        if single_record_element.xpath('date_record_updated'):
            logger.debug(f"Adding optional field 'date_record_updated'")
            # It is possible have bad date format.
            try:
                io_doi.date_record_updated = datetime.strptime(single_record_element.xpath('date_record_updated')[0].text, '%Y-%m-%d') 
            except Exception as e:
                logger.error(f"Cannot parse field 'date_record_updated'.  Expecting format '%Y-%m-%d'.  Received {single_record_element.xpath('date_record_updated')[0].text}")
                raise InputFormatException(f"Cannot parse field 'date_record_updated'.  Expecting format '%Y-%m-%d'.  Received {single_record_element.xpath('date_record_updated')[0].text}")

        if single_record_element.xpath('doi_message'):
            logger.debug(f"Adding optional field 'doi_message'")
            io_doi.message = single_record_element.xpath('doi_message')[0].text

        if single_record_element.xpath('authors'):
            logger.debug(f"Adding optional field 'authors'")
            io_doi.authors = DOIOstiWebParser().parse_author_names(single_record_element.xpath('authors')) 

        logger.debug(f"io_doi {io_doi}")

        return io_doi

    @staticmethod
    def response_get_parse_osti_xml(osti_response_text):
        """Function parse a response from a GET (query) or a PUT to the OSTI server (in XML query format) and return a list of dictionaries.
           By default, all possible fields are extracted.  If desire to only extract smaller set of fields, they should be specified accordingly.
           Specific fields are extracted from input.  Not all fields in XML are used."""

        dois = []

        doc     = etree.fromstring(osti_response_text)
        my_root = doc.getroottree()

        # Trim down input to just fields we want.
        for single_record_element in my_root.iter():
            if single_record_element.tag == 'record':
                status = single_record_element.get('status')
                if status is not None and status.lower() == 'error':
                    # The 'error' record is parsed differently and does not have all the attributes we desire.
                    # Get the entire text and save it in 'error' key.  Print a WARN only since it is not related to any particular 'doi' or 'id' action.
                    logger.error(f"ERROR OSTI RECORD {single_record_element.text}")
                    continue
                else:
                    # It is important to check if either 'URL' or 'URN' are in the single_record_element.xpath for related_identifiers before accessing it
                    # otherwise an index error will occur.
                    if single_record_element.xpath("related_identifiers/related_identifier[./identifier_type='URL']"):
                        identifier_parsed = single_record_element.xpath("related_identifiers/related_identifier[./identifier_type='URL']/identifier_value")[0].text
                    elif single_record_element.xpath("related_identifiers/related_identifier[./identifier_type='URN']"):
                        identifier_parsed = single_record_element.xpath("related_identifiers/related_identifier[./identifier_type='URN']/identifier_value")[0].text
                    else:
                        raise InputFormatException("Cannot find identifier_value.  Expecting either URL or URN for identifier_type")

                    # The following 4 fields were deleted from constructor of Doi to inspect individually since the code was failing:
                    #     ['id','doi','date_record_added',date_record_updated']
                    doi = Doi(title=single_record_element.xpath('title')[0].text,
                              publication_date=single_record_element.xpath('publication_date')[0].text,
                              product_type=single_record_element.xpath('product_type')[0].text,
                              product_type_specific=single_record_element.xpath('product_type_specific')[0].text,
                              related_identifier=identifier_parsed,
                              status=status)

                    # Parse for some optional fields that may not be present in every record from OSTI.
                    doi= DOIOstiWebParser().parse_optional_fields(doi,single_record_element)

                    dois.append(doi)
        # end for single_record_element in my_root.iter():

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
# end class DOIOstiWebParser
