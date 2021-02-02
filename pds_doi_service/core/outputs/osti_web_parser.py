#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
==================
osti_web_parser.py
==================

Contains classes and functions for parsing OSTI XML labels.
"""

from datetime import datetime
from lxml import etree

from pds_doi_service.core.entities.doi import Doi, DoiStatus, ProductType
from pds_doi_service.core.input.exceptions import InputFormatException, UnknownLIDVIDException
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_core.outputs.osti_web_parser')


class DOIOstiWebParser:
    """
    Contains functions related to parsing input/output for interactions with
    the OSTI server.
    """
    ACCEPTABLE_FIELD_NAMES_LIST = [
        'id', 'doi', 'accession_number', 'published_before', 'published_after',
        'added_before', 'added_after', 'updated_before', 'updated_after',
        'first_registered_before', 'first_registered_after', 'last_registered_before',
        'last_registered_after', 'status', 'start', 'rows', 'sort', 'order'
    ]

    def validate_field_names(self, query_dict):
        """
        Validates the provided fields by the user to make sure they match the
        expected fields by OSTI:

            https://www.osti.gov/iad2test/docs#endpoints-recordlist

        """
        o_validated_dict = {}

        for key in query_dict:
            # If the key is valid, save the field and value to return.
            if key in self.ACCEPTABLE_FIELD_NAMES_LIST:
                o_validated_dict[key] = query_dict[key]
            else:
                logger.error(f"Unexpected field name '{key}' in query_dict")
                exit(1)

        return o_validated_dict

    @staticmethod
    def parse_author_names(authors_element):
        """
        Given a list of author elements, parse for individual 'first_name',
        'middle_name', 'last_name' or 'full_name' fields.
        """
        o_authors_list = []

        # If they exist, collect all the first name, middle name, last names or
        # full name fields into a list of dictionaries.
        for single_author in authors_element:
            first_name = single_author.xpath('first_name')
            last_name = single_author.xpath('last_name')
            full_name = single_author.xpath('full_name')
            middle_name = single_author.xpath('middle_name')

            author_dict = {}

            if full_name:
                author_dict['full_name'] = full_name[0].text
            else:
                if first_name and last_name:
                    author_dict.update(
                        {'first_name': first_name[0].text,
                         'last_name': last_name[0].text}
                    )

                if middle_name:
                    author_dict.update({'middle_name': middle_name[0].text})

            # It is possible that the record contains no authors.
            if author_dict:
                o_authors_list.append(author_dict)

        return o_authors_list

    @staticmethod
    def parse_editor_names(contributors_element):
        """
        Given a list of contributors elements, parse the individual 'first_name',
        'middle_name', 'last_name' or 'full_name' fields for any contributors
        with type "Editor".
        """
        o_editors_list = []

        # If they exist, collect all the editor contributor fields into a list
        # of dictionaries.
        for single_contributor in contributors_element:
            first_name = single_contributor.xpath('first_name')
            last_name = single_contributor.xpath('last_name')
            full_name = single_contributor.xpath('full_name')
            middle_name = single_contributor.xpath('middle_name')
            contributor_type = single_contributor.xpath('contributor_type')

            # We only care about parsing Editor contributor types, since
            # this should be the only type to carry over (the DataCurator entry
            # is ignored here since it's hardcoded into the OSTI template).
            if contributor_type and contributor_type[0].text == 'Editor':
                editor_dict = {}

                if full_name:
                    editor_dict['full_name'] = full_name[0].text
                else:
                    if first_name and last_name:
                        editor_dict.update(
                            {'first_name': first_name[0].text,
                             'last_name': last_name[0].text}
                        )

                    if middle_name:
                        editor_dict.update({'middle_name': middle_name[0].text})

                # It is possible that the record contains no contributor.
                if editor_dict:
                    o_editors_list.append(editor_dict)

        return o_editors_list

    @staticmethod
    def parse_optional_fields(io_doi, single_record_element):
        """
        Given a single record element, parse the following optional fields which
        may not be present from the OSTI response:

            'id', 'site_url', 'doi', 'date_record_added', 'date_record_updated',
            'doi_message', 'authors'.

        """
        optional_fields = ['id', 'doi', 'sponsoring_organization',
                           'publisher', 'availability', 'country',
                           'description', 'site_url', 'site_code',
                           'date_record_added', 'date_record_updated',
                           'keywords', 'authors', 'contributors']

        for optional_field in optional_fields:
            optional_field_element = single_record_element.xpath(optional_field)

            if optional_field_element and optional_field_element[0].text is not None:
                if optional_field == 'keywords':
                    io_doi.keywords = set(optional_field_element[0].text.split('; '))
                    logger.debug(f"Adding optional field 'keywords': "
                                 f"{io_doi.keywords}")
                elif optional_field == 'authors':
                    io_doi.authors = DOIOstiWebParser.parse_author_names(
                        optional_field_element[0]
                    )
                    logger.debug(f"Adding optional field 'authors': "
                                 f"{io_doi.authors}")
                elif optional_field == 'contributors':
                    io_doi.editors = DOIOstiWebParser.parse_editor_names(
                        optional_field_element[0]
                    )
                    logger.debug(f"Adding optional field 'editors': "
                                 f"{io_doi.editors}")
                elif optional_field == 'date_record_added':
                    io_doi.date_record_added = datetime.strptime(
                        optional_field_element[0].text, '%Y-%m-%d'
                    )
                    logger.debug(f"Adding optional field 'date_record_added': "
                                 f"{io_doi.date_record_added}")
                elif optional_field == 'date_record_updated':
                    io_doi.date_record_updated = datetime.strptime(
                        optional_field_element[0].text, '%Y-%m-%d'
                    )
                    logger.debug(f"Adding optional field 'date_record_updated': "
                                 f"{io_doi.date_record_updated}")
                else:
                    setattr(io_doi, optional_field, optional_field_element[0].text)

                    logger.debug(
                        f"Adding optional field "
                        f"'{optional_field}': {getattr(io_doi, optional_field)}"
                    )

        logger.debug(f"io_doi {io_doi}")

        return io_doi

    @staticmethod
    def get_lidvid_from_site_url(record):
        """
        For some records, the lidvid can be parsed from site_url as a last resort.

        Ex:
            https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn%3Anasa%3Apds%3Ainsight_cameras&amp;version=1.0

        """
        site_url = record.xpath("site_url")[0].text
        site_tokens = site_url.split("identifier=")

        identifier_tokens = site_tokens[1].split(";")

        lid_vid_tokens = identifier_tokens[0].split("&version=")
        lid_value = lid_vid_tokens[0].replace("%3A", ":")
        vid_value = lid_vid_tokens[1]

        # Finally combine the lid and vid together.
        lid_vid_value = lid_value + '::' + vid_value

        return lid_vid_value

    @staticmethod
    def get_lidvid(record):
        """
        Depending on versions, a lidvid can be stored in different locations.
        This function searches each location, and returns the first encountered
        LIDVID.
        """
        if record.xpath("accession_number"):
            return record.xpath("accession_number")[0].text
        elif record.xpath("related_identifiers/related_identifier[./identifier_type='URL']"):
            return record.xpath(
                "related_identifiers/related_identifier[./identifier_type='URL']/identifier_value")[0].text
        elif record.xpath("related_identifiers/related_identifier[./identifier_type='URN']"):
            return record.xpath(
                "related_identifiers/related_identifier[./identifier_type='URN']/identifier_value")[0].text
        elif record.xpath("report_numbers"):
            return record.xpath("report_numbers")[0].text
        elif record.xpath("site_url"):
            # For some record, the lidvid can be parsed from 'site_url' field as last resort.
            lid_vid_value = DOIOstiWebParser.get_lidvid_from_site_url(record)
            return lid_vid_value
        else:
            # For now, do not consider it an error if cannot get the lidvid.
            logger.debug("Cannot find identifier_value. "
                         "Expecting one of ['accession_number','identifier_type','report_numbers'] tags")
            return None

    @staticmethod
    def get_record_for_lidvid(osti_label_file, lidvid):
        """
        Returns the record entry corresponding to the provided LIDVID from the
        OSTI XML label file.

        Parameters
        ----------
        osti_label_file : str
            Path to the OSTI XML label file to search.
        lidvid : str
            The LIDVID of the record to return from the OSTI label.

        Returns
        -------
        record : str
            The single found record embedded in a <records> tag. This string is
            suitable to be written to disk as a new OSTI label.

        Raises
        ------
        UnknownLIDVIDException
            If no record for the requested LIDVID is found in the provided OSTI
            label file.

        """
        root = etree.parse(osti_label_file).getroot()

        records = root.xpath('record')

        for record in records:
            if DOIOstiWebParser.get_lidvid(record) == lidvid:
                result = record
                break
        else:
            raise UnknownLIDVIDException(
                f'Could not find entry for lidvid "{lidvid}" in OSTI label file '
                f'{osti_label_file}.'
            )

        new_root = etree.Element('records')
        new_root.append(result)

        return etree.tostring(
            new_root, pretty_print=True, xml_declaration=True, encoding='UTF-8'
        ).decode('utf-8')

    @staticmethod
    def response_get_parse_osti_xml(osti_response_text):
        """
        Parses a response from a GET (query) or a PUT to the OSTI server
        (in XML query format) and return a list of dictionaries.

        By default, all possible fields are extracted. If desire to only extract
        smaller set of fields, they should be specified accordingly.
        Specific fields are extracted from input. Not all fields in XML are used.

        """
        dois = []
        errors = []

        doc = etree.fromstring(osti_response_text)
        my_root = doc.getroottree()

        # Trim down input to just fields we want.
        for index, single_record_element in enumerate(my_root.findall('record')):
            status = single_record_element.get('status')

            if status is None:
                raise InputFormatException(
                    f'Could not parse a status for record {index + 1} from the '
                    f'provided OSTI XML.'
                )

            if status.lower() == 'error':
                # The 'error' record is parsed differently and does not have all
                # the attributes we desire.
                # Get the entire text and save it in 'error' key. Print a WARN
                # only since it is not related to any particular 'doi' or 'id' action.
                logger.error(f"ERROR OSTI RECORD {single_record_element.text}")

                # Check for any errors reported back from OSTI and save
                # them off to be returned
                errors_element = single_record_element.xpath('errors')

                if len(errors_element):
                    for error_element in errors_element[0]:
                        errors.append(error_element.text)
            else:
                lidvid = DOIOstiWebParser.get_lidvid(single_record_element)

                if lidvid:
                    publication_date = single_record_element.xpath('publication_date')[0].text
                    product_type = single_record_element.xpath('product_type')[0].text
                    product_type_specific = single_record_element.xpath('product_type_specific')[0].text

                    # Move the fetching of identifier_type in parse_optional_fields() function.
                    # The following 4 fields were deleted from constructor of Doi
                    # to inspect individually since the code was failing:
                    #     ['id','doi','date_record_added',date_record_updated']
                    doi = Doi(
                        title=single_record_element.xpath('title')[0].text,
                        publication_date=datetime.strptime(publication_date, '%Y-%m-%d'),
                        product_type=ProductType(product_type),
                        product_type_specific=product_type_specific,
                        related_identifier=lidvid,
                        status=DoiStatus(status.lower())
                    )

                    # Parse for some optional fields that may not be present in
                    # every record from OSTI.
                    doi = DOIOstiWebParser.parse_optional_fields(doi, single_record_element)

                    dois.append(doi)
                else:
                    logger.warning(
                        f"No lidvid reference found in DOI "
                        f"{single_record_element.xpath('doi')[0].text}"
                    )

        # end for index, single_record_element in enumerate(my_root.findall('record')):

        return dois, errors

    @staticmethod
    def response_get_parse_osti_json(osti_response):
        """
        Parses a response from a query to the OSTI server (in JSON format) and
        returns a JSON object.

        Specific fields are extracted from input. Not all fields in JSON are used.

        """
        dois = []  # It is possible that the query resulted in no rows.

        # These are the fields in a record returned by OSTI
        # fields_returned_from_osti =
        #    ['id','site_code','title' 'sponsoring_organization', 'accession_number', 'doi',
        #     'authors', 'status', 'publisher', 'availability', 'publication_date', 'country',
        #     'description', 'site_url', 'product_type', 'product_type_specific',
        #     'related_identifiers', 'date_record_added', 'date_record_updated',
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
