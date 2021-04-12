#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
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

import html
import json
import os

from datetime import datetime
from lxml import etree

from pds_doi_service.core.entities.doi import Doi, DoiStatus, ProductType
from pds_doi_service.core.input.exceptions import InputFormatException, UnknownLIDVIDException
from pds_doi_service.core.outputs.osti import CONTENT_TYPE_XML, CONTENT_TYPE_JSON
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_service.core.outputs.osti_web_parser')


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

    OPTIONAL_FIELDS_LIST = [
        'id', 'doi', 'sponsoring_organization', 'publisher', 'availability',
        'country', 'description', 'site_url', 'site_code', 'date_record_added',
        'date_record_updated', 'keywords', 'authors', 'contributors'
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
    def parse_author_names_xml(authors_element):
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
    def parse_contributors_xml(contributors_element):
        """
        Given a list of contributors elements, parse the individual 'first_name',
        'middle_name', 'last_name' or 'full_name' fields for any contributors
        with type "Editor".
        """
        o_editors_list = []
        o_node_name = ''

        # If they exist, collect all the editor contributor fields into a list
        # of dictionaries.
        for single_contributor in contributors_element:
            first_name = single_contributor.xpath('first_name')
            last_name = single_contributor.xpath('last_name')
            full_name = single_contributor.xpath('full_name')
            middle_name = single_contributor.xpath('middle_name')
            contributor_type = single_contributor.xpath('contributor_type')

            if contributor_type:
                if contributor_type[0].text == 'Editor':
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
                # Parse the node ID from the name of the data curator
                elif contributor_type[0].text == 'DataCurator':
                    o_node_name = full_name[0].text
                    o_node_name = o_node_name.replace('Planetary Data System:', '')
                    o_node_name = o_node_name.replace('Node', '')
                    o_node_name = o_node_name.strip()

        return o_editors_list, o_node_name

    @staticmethod
    def parse_contributors_json(contributors_record):
        o_editors_list = list(
            filter(
                lambda contributor: contributor['contributor_type'] == 'Editor',
                contributors_record
            )
        )

        data_curator = next(
            filter(
                lambda contributor: contributor['contributor_type'] == 'DataCurator',
                contributors_record
            )
        )

        o_node_name = data_curator['full_name']
        o_node_name = o_node_name.replace('Planetary Data System:', '')
        o_node_name = o_node_name.replace('Node', '')
        o_node_name = o_node_name.strip()

        for editor in o_editors_list:
            editor.pop('contributor_type')

        return o_editors_list, o_node_name

    @staticmethod
    def parse_optional_fields_xml(io_doi, single_record_element):
        """
        Given a single XML record element, parse the following optional fields
        which may or may not be present in the OSTI response.

        """
        for optional_field in DOIOstiWebParser.OPTIONAL_FIELDS_LIST:
            optional_field_element = single_record_element.xpath(optional_field)

            if optional_field_element and optional_field_element[0].text is not None:
                if optional_field == 'keywords':
                    io_doi.keywords = set(optional_field_element[0].text.split(';'))
                    logger.debug(f"Adding optional field 'keywords': "
                                 f"{io_doi.keywords}")
                elif optional_field == 'authors':
                    io_doi.authors = DOIOstiWebParser.parse_author_names_xml(
                        optional_field_element[0]
                    )
                    logger.debug(f"Adding optional field 'authors': "
                                 f"{io_doi.authors}")
                elif optional_field == 'contributors':
                    (io_doi.editors,
                     io_doi.contributor) = DOIOstiWebParser.parse_contributors_xml(
                        optional_field_element[0]
                    )
                    logger.debug(f"Adding optional field 'editors': "
                                 f"{io_doi.editors}")
                    logger.debug(f"Adding optional field 'contributor': "
                                 f"{io_doi.contributor}")
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

        return io_doi

    @staticmethod
    def parse_optional_fields_json(io_doi, single_json_record):
        """
        Given a single JSON record element, parse the following optional fields
        which may or may not be present in the OSTI response.

        """
        for optional_field in DOIOstiWebParser.OPTIONAL_FIELDS_LIST:
            optional_field_value = single_json_record.get(optional_field)

            if optional_field_value is not None:
                if optional_field == 'keywords':
                    io_doi.keywords = set(optional_field_value.split(';'))
                    logger.debug(f"Adding optional field 'keywords': "
                                 f"{io_doi.keywords}")
                elif optional_field == 'site_url':
                    # In order to match parsing behavior of lxml, unescape
                    # the site url
                    io_doi.site_url = html.unescape(optional_field_value)
                    logger.debug(f"Adding optional field 'site_url': "
                                 f"{io_doi.site_url}")
                elif optional_field == 'contributors':
                    (io_doi.editors,
                     io_doi.contributor) = DOIOstiWebParser.parse_contributors_json(
                        optional_field_value
                    )
                    logger.debug(f"Adding optional field 'editors': "
                                 f"{io_doi.editors}")
                    logger.debug(f"Adding optional field 'contributor': "
                                 f"{io_doi.contributor}")
                elif optional_field == 'date_record_added':
                    io_doi.date_record_added = datetime.strptime(
                        optional_field_value, '%Y-%m-%d'
                    )
                    logger.debug(f"Adding optional field 'date_record_added': "
                                 f"{io_doi.date_record_added}")
                elif optional_field == 'date_record_updated':
                    io_doi.date_record_updated = datetime.strptime(
                        optional_field_value, '%Y-%m-%d'
                    )
                    logger.debug(f"Adding optional field 'date_record_updated': "
                                 f"{io_doi.date_record_updated}")
                else:
                    setattr(io_doi, optional_field, optional_field_value)

                    logger.debug(
                        f"Adding optional field "
                        f"'{optional_field}': {getattr(io_doi, optional_field)}"
                    )

        return io_doi

    @staticmethod
    def get_lidvid_from_site_url(site_url):
        """
        For some records, the lidvid can be parsed from site_url as a last resort.

        Ex:
            https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn%3Anasa%3Apds%3Ainsight_cameras&amp;version=1.0

        """
        site_tokens = site_url.split("identifier=")

        identifier_tokens = site_tokens[1].split(";")

        lid_vid_tokens = identifier_tokens[0].split("&version=")
        lid_value = lid_vid_tokens[0].replace("%3A", ":")
        vid_value = lid_vid_tokens[1]

        # Finally combine the lid and vid together.
        lid_vid_value = lid_value + '::' + vid_value

        return lid_vid_value

    @staticmethod
    def get_lidvid_from_xml(record):
        """
        Depending on versions, a lidvid can be stored in different locations.
        This function searches each location, and returns the first encountered
        LIDVID.
        """
        lidvid = None

        if record.xpath("accession_number"):
            lidvid = record.xpath("accession_number")[0].text
        elif record.xpath("related_identifiers/related_identifier[./identifier_type='URL']"):
            lidvid = record.xpath(
                "related_identifiers/related_identifier[./identifier_type='URL']/identifier_value")[0].text
        elif record.xpath("related_identifiers/related_identifier[./identifier_type='URN']"):
            lidvid = record.xpath(
                "related_identifiers/related_identifier[./identifier_type='URN']/identifier_value")[0].text
        elif record.xpath("report_numbers"):
            lidvid = record.xpath("report_numbers")[0].text
        elif record.xpath("site_url"):
            # For some record, the lidvid can be parsed from 'site_url' field as last resort.
            lidvid = DOIOstiWebParser.get_lidvid_from_site_url(record.xpath("site_url")[0].text)
        else:
            # For now, do not consider it an error if cannot get the lidvid.
            logger.warning(
                "Could not parse a lidvid from the provided XML record. "
                "Expecting one of ['accession_number','identifier_type',"
                "'report_numbers','site_url'] tags"
            )

        return lidvid

    @staticmethod
    def get_lidvid_from_json(record):
        lidvid = None

        if "accession_number" in record:
            lidvid = record["accession_number"]
        elif "related_identifiers" in record:
            for related_identifier in record["related_identifiers"]:
                if related_identifier.get("identifier_type") == "URL":
                    lidvid = related_identifier["identifier_value"]
                    break
        elif "report_numbers" in record:
            lidvid = record["report_numbers"]
        elif "site_url" in record:
            lidvid = DOIOstiWebParser.get_lidvid_from_site_url(record["site_url"])
        else:
            # For now, do not consider it an error if cannot get the lidvid.
            logger.warning(
                "Could not parse a lidvid from the provided JSON record. "
                "Expecting one of ['accession_number','identifier_type',"
                "'report_numbers','site_url'] fields"
            )

        return lidvid

    @staticmethod
    def get_record_for_lidvid(osti_label_file, lidvid):
        content_type = os.path.splitext(osti_label_file)[-1][1:]

        if content_type == CONTENT_TYPE_XML:
            record = DOIOstiWebParser.get_record_for_lidvid_xml(osti_label_file, lidvid)
        elif content_type == CONTENT_TYPE_JSON:
            record = DOIOstiWebParser.get_record_for_lidvid_json(osti_label_file, lidvid)
        else:
            raise InputFormatException(
                'Unsupported file type provided. File must have one of the '
                f'following extensions: [{CONTENT_TYPE_JSON}, {CONTENT_TYPE_XML}]'
            )

        return record, content_type

    @staticmethod
    def get_record_for_lidvid_xml(osti_label_file, lidvid):
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
            if DOIOstiWebParser.get_lidvid_from_xml(record) == lidvid:
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
    def get_record_for_lidvid_json(osti_label_file, lidvid):
        """
        Returns the record entry corresponding to the provided LIDVID from the
        OSTI JSON label file.

        Parameters
        ----------
        osti_label_file : str
            Path to the OSTI JSON label file to search.
        lidvid : str
            The LIDVID of the record to return from the OSTI label.

        Returns
        -------
        record : str
            The single found record formatted as a JSON string. This string is
            suitable to be written to disk as a new OSTI label.

        Raises
        ------
        UnknownLIDVIDException
            If no record for the requested LIDVID is found in the provided OSTI
            label file.

        """
        with open(osti_label_file, 'r') as infile:
            records = json.load(infile)

        for record in records:
            if DOIOstiWebParser.get_lidvid_from_json(record) == lidvid:
                result = record
                break
        else:
            raise UnknownLIDVIDException(
                f'Could not find entry for lidvid "{lidvid}" in OSTI label file '
                f'{osti_label_file}.'
            )

        records = [result]

        return json.dumps(records, indent=4)

    @staticmethod
    def parse_osti_response_xml(osti_response_text):
        """
        Parses a response from a GET (query) or a PUT to the OSTI server
        (in XML query format) and return a list of dictionaries.

        By default, all possible fields are extracted. If desire to only extract
        smaller set of fields, they should be specified accordingly.
        Specific fields are extracted from input. Not all fields in XML are used.

        """
        dois = []
        errors = {}

        doc = etree.fromstring(osti_response_text.encode())
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
                logger.error(
                    f"Errors reported for record index {index + 1}"
                )

                # Check for any errors reported back from OSTI and save
                # them off to be returned
                errors_element = single_record_element.xpath('errors')
                doi_message = single_record_element.xpath('doi_message')

                cur_errors = []

                if len(errors_element):
                    for error_element in errors_element[0]:
                        cur_errors.append(error_element.text)

                if len(doi_message):
                    cur_errors.append(doi_message[0].text)

                errors[index] = cur_errors

            lidvid = DOIOstiWebParser.get_lidvid_from_xml(single_record_element)

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
                doi = DOIOstiWebParser.parse_optional_fields_xml(doi, single_record_element)

                dois.append(doi)

        # end for index, single_record_element in enumerate(my_root.findall('record')):

        return dois, errors

    @staticmethod
    def parse_osti_response_json(osti_response_text):
        """
        Parses a response from a query to the OSTI server (in JSON format) and
        returns a list of parsed Doi objects.

        Specific fields are extracted from input. Not all fields in the JSON are
        used.

        """
        dois = []
        errors = {}

        osti_response = json.loads(osti_response_text)

        # Responses from OSTI come wrapped in 'records' key, strip it off
        # before continuing
        if 'records' in osti_response:
            osti_response = osti_response['records']

        for index, record in enumerate(osti_response):
            if record.get('status', '').lower() == 'error':
                logger.error(
                    f"Errors reported for record index {index + 1}"
                )

                # Check for any errors reported back from OSTI and save
                # them off to be returned
                cur_errors = []

                if 'errors' in record:
                    cur_errors.extend(record['errors'])

                if 'doi_message' in record and len(record['doi_message']):
                    cur_errors.append(record['doi_message'])

                errors[index] = cur_errors

            # Make sure all the mandatory fields are present
            mandatory_fields = ['title', 'publication_date', 'site_url',
                                'product_type']

            if not all([field in record for field in mandatory_fields]):
                raise InputFormatException(
                    'Provided JSON is missing one or more mandatory fields: '
                    f'({", ".join(mandatory_fields)})'
                )

            lidvid = DOIOstiWebParser.get_lidvid_from_json(record)

            if lidvid:
                doi = Doi(
                    title=record['title'],
                    publication_date=datetime.strptime(record['publication_date'], '%Y-%m-%d'),
                    product_type=ProductType(record['product_type']),
                    product_type_specific=record.get('product_type_specific'),
                    related_identifier=lidvid,
                    status=DoiStatus(record.get('status', DoiStatus.Unknown).lower())
                )

                # Parse for some optional fields that may not be present in
                # every record from OSTI.
                doi = DOIOstiWebParser.parse_optional_fields_json(doi, record)

                dois.append(doi)

        return dois, errors
