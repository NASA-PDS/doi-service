#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
=======
osti.py
=======

Contains OSTI-specific implementations of classes used to create, submit, and
parse DOI records.
"""

import html
import json
import os
import pprint
from datetime import datetime
from os.path import exists

import pystache
import requests
from lxml import etree
from pkg_resources import resource_filename
from requests.auth import HTTPBasicAuth

from pds_doi_service.core.entities.doi import Doi, ProductType, DoiStatus
from pds_doi_service.core.input.exceptions import (WebRequestException,
                                                   InputFormatException,
                                                   UnknownLIDVIDException)
from pds_doi_service.core.outputs.doi_record import (DOIRecord,
                                                     CONTENT_TYPE_XML,
                                                     CONTENT_TYPE_JSON,
                                                     VALID_CONTENT_TYPES)
from pds_doi_service.core.outputs.web_client import DOIWebClient
from pds_doi_service.core.outputs.web_parser import DOIWebParser
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOIOstiRecord(DOIRecord):
    """
    Class used to create a DOI record suitable for submission to the OSTI
    DOI service.

    This class supports output of DOI records in both XML and JSON format.
    """
    def __init__(self):
        """Creates a new DOIOstiRecord instance"""
        # Need to find the mustache DOI templates
        self._xml_template_path = resource_filename(
            __name__, 'DOI_IAD2_template_20200205-mustache.xml'
        )
        self._json_template_path = resource_filename(
            __name__, 'DOI_IAD2_template_20210216-mustache.json'
        )

        if (not exists(self._xml_template_path)
                or not exists(self._json_template_path)):
            raise RuntimeError(
                f'Could not find one or more DOI templates needed by this module\n'
                f'Expected XML template: {self._xml_template_path}\n'
                f'Expected JSON template: {self._json_template_path}'
            )

        self._template_map = {
            CONTENT_TYPE_XML: self._xml_template_path,
            CONTENT_TYPE_JSON: self._json_template_path
        }

    def create_doi_record(self, dois, content_type=CONTENT_TYPE_XML):
        """
        Creates a DOI record from the provided list of Doi objects in the
        specified format.

        Parameters
        ----------
        dois : list of Doi
            The Doi objects to format into the returned record.
        content_type : str
            The type of record to return. Currently, 'xml' and 'json' are
            supported.

        Returns
        -------
        record : str
            The text body of the record created from the provided Doi objects.

        """
        if content_type not in VALID_CONTENT_TYPES:
            raise ValueError('Invalid content type requested, must be one of '
                             f'{",".join(VALID_CONTENT_TYPES)}')

        # If a single DOI was provided, wrap it in a list so the iteration
        # below still works
        if isinstance(dois, Doi):
            dois = [dois]

        doi_fields_list = []

        for index, doi in enumerate(dois):
            # Filter out any keys with None as the value, so the string literal
            # "None" is not written out as an XML tag's text body
            doi_fields = (
                dict(filter(lambda elem: elem[1] is not None, doi.__dict__.items()))
            )

            # Escape any necessary HTML characters from the site-url,
            # we perform this step rather than pystache to avoid
            # unintentional recursive escapes
            if doi.site_url:
                doi_fields['site_url'] = html.escape(doi.site_url)

            # Convert set of keywords back to a semi-colon delimited string
            if doi.keywords:
                doi_fields['keywords'] = ";".join(sorted(doi.keywords))
            else:
                doi_fields.pop('keywords')

            # Remove any extraneous whitespace from a provided description
            if doi.description:
                doi.description = str.strip(doi.description)

            # publication_date is assigned to a Doi object as a datetime,
            # need to convert to a string for the OSTI label. Note that
            # even if we only had the publication year from the PDS4 label,
            # the OSTI schema still expects YYYY-mm-dd format.
            if isinstance(doi.publication_date, datetime):
                doi_fields['publication_date'] = doi.publication_date.strftime('%Y-%m-%d')

            # Same goes for date_record_added and date_record_updated
            if (doi.date_record_added and
                    isinstance(doi.date_record_added, datetime)):
                doi_fields['date_record_added'] = doi.date_record_added.strftime('%Y-%m-%d')

            if (doi.date_record_updated and
                    isinstance(doi.date_record_updated, datetime)):
                doi_fields['date_record_updated'] = doi.date_record_updated.strftime('%Y-%m-%d')

            # Pre-convert author map into a JSON string to make it play nice
            # with pystache rendering
            if doi.authors and content_type == CONTENT_TYPE_JSON:
                doi_fields['authors'] = json.dumps(doi.authors)

            # The OSTI IAD schema does not support 'Bundle' as a product type,
            # so convert to collection here
            if doi.product_type == ProductType.Bundle:
                doi_fields['product_type'] = ProductType.Collection

            # Lastly, we need a kludge to inform the mustache template whether
            # to include a comma between consecutive entries (JSON only)
            if content_type == CONTENT_TYPE_JSON and index < len(dois) - 1:
                doi_fields['comma'] = True

            doi_fields_list.append(doi_fields)

        renderer = pystache.Renderer()

        rendered_template = renderer.render_path(
            self._template_map[content_type], {'dois': doi_fields_list}
        )

        # Reindent the output JSON to account for the kludging of the authors field
        if content_type == CONTENT_TYPE_JSON:
            rendered_template = json.dumps(json.loads(rendered_template), indent=4)

        return rendered_template


class DOIOstiWebParser(DOIWebParser):
    """
    Class used to parse Doi objects from DOI records returned from the OSTI
    DOI service.

    This class supports parsing records in both XML and JSON formats.
    """
    _optional_fields = [
        'id', 'doi', 'sponsoring_organization', 'publisher', 'availability',
        'country', 'description', 'site_url', 'site_code', 'keywords',
        'authors', 'contributors'
    ]
    """The optional field names we parse from input OSTI labels."""

    @staticmethod
    def parse_dois_from_label(label_text, content_type=CONTENT_TYPE_XML):
        """
        Parses one or more Doi objects from the provided OSTI-format label.

        Parameters
        ----------
        label_text : str
            Text body of the OSTI label to parse.
        content_type : str
            The format of the label's content. Both 'xml' and 'json' are
            currently supported.

        Returns
        -------
        dois : list of Doi
            Doi objects parsed from the provided label.
        errors: dict
            Dictionary mapping indices of DOI's in the provided label to lists
            of strings containing any errors encountered while parsing.

        """
        if content_type == CONTENT_TYPE_XML:
            dois, errors = DOIOstiXmlWebParser.parse_dois_from_label(label_text)
        elif content_type == CONTENT_TYPE_JSON:
            dois, errors = DOIOstiJsonWebParser.parse_dois_from_label(label_text)
        else:
            raise InputFormatException(
                'Unsupported content type provided. Value must be one of the '
                f'following: [{CONTENT_TYPE_JSON}, {CONTENT_TYPE_XML}]'
            )

        return dois, errors

    @staticmethod
    def get_record_for_lidvid(label_file, lidvid):
        """
        Returns a new label from the provided one containing only the DOI entry
        corresponding to the specified lidvid.

        Parameters
        ----------
        label_file : str
            Path to the label file to pull a record from.
        lidvid : str
            The LIDVID to search for within the provided label file.

        Returns
        -------
        record : str
            The single found record embedded in a <records> tag. This string is
            suitable to be written to disk as a new OSTI label.
        content_type : str
            The determined content type of the provided label.

        """
        content_type = os.path.splitext(label_file)[-1][1:]

        if content_type == CONTENT_TYPE_XML:
            record = DOIOstiXmlWebParser.get_record_for_lidvid(label_file, lidvid)
        elif content_type == CONTENT_TYPE_JSON:
            record = DOIOstiJsonWebParser.get_record_for_lidvid(label_file, lidvid)
        else:
            raise InputFormatException(
                'Unsupported file type provided. File must have one of the '
                f'following extensions: [{CONTENT_TYPE_JSON}, {CONTENT_TYPE_XML}]'
            )

        return record, content_type


class DOIOstiWebClient(DOIWebClient):
    """
    Class used to submit HTTP requests to the OSTI DOI service.
    """
    _service_name = 'OSTI'
    _web_parser = DOIOstiWebParser()
    _content_type_map = {
        CONTENT_TYPE_XML: 'application/xml',
        CONTENT_TYPE_JSON: 'application/json'
    }

    ACCEPTABLE_FIELD_NAMES_LIST = [
        'id', 'doi', 'accession_number', 'published_before', 'published_after',
        'added_before', 'added_after', 'updated_before', 'updated_after',
        'first_registered_before', 'first_registered_after', 'last_registered_before',
        'last_registered_after', 'status', 'start', 'rows', 'sort', 'order'
    ]

    MAX_TOTAL_ROWS_RETRIEVE = 1000000000
    """Maximum numbers of rows to request from a query to OSTI"""

    def submit_content(self, payload, url, username, password,
                       content_type=CONTENT_TYPE_XML):
        """
        Submits a payload to the OSTI DOI service via the POST action.

        The action taken by the service is determined by the contents of the
        payload.

        Parameters
        ----------
        payload : str
            Payload to submit to the OSTI DOI service. Should correspond to
            an OSTI-format label file containing one or DOI records.
        url : str
            The URL of the OSTI DOI service endpoint.
        username : str
            The user name to authenticate to the OSTI DOI service as.
        password : str
            The password to authenticate to the OSTI DOI service with.
        content_type : str
            The content type to specify the format of the payload, as well as
            the format of the response from OSTI. Currently, 'xml' and 'json'
            are supported.

        Returns
        -------
        dois : list of Doi
            Doi objects parsed from the response label from OSTI.
        response_text : str
            Body of the response label from OSTI.

        """
        response_text = super().submit_content(
            payload, url, username, password, content_type
        )

        # Re-use the parse functions from DOIOstiWebParser class to get the
        # list of Doi objects to return
        dois, _ = self._web_parser.parse_dois_from_label(response_text, content_type)

        return dois, response_text

    def query_doi(self, url, query, username, password,
                  content_type=CONTENT_TYPE_XML):
        """
        Queries the status of a DOI from the OSTI server and returns the
        response text.

        The format of i_url is: https://www.osti.gov/iad2test/api/records/
        and will be appended by fields in query_dict:

            if query_dict = {'id':14108,'status':'Error'}
                then https://www.osti.gov/iad2test/api/records?id=14108&status=Error

            if query_dict = {'id'=1327397,'status'='Registered'}
                then https://www.osti.gov/iad2test/api/records?id=1327397&status=Registered
        """
        if content_type not in self._content_type_map:
            raise ValueError('Invalid content type requested, must be one of '
                             f'{",".join(list(self._content_type_map.keys()))}')

        auth = HTTPBasicAuth(username, password)

        headers = {
            'Accept': self._content_type_map[content_type],
            'Content-Type': self._content_type_map[content_type]
        }

        # OSTI server requires 'rows' field to know how many max rows to fetch at once.
        initial_payload = {'rows': self.MAX_TOTAL_ROWS_RETRIEVE}

        # If user provided a query_dict, append to our initial payload.
        if query:
            initial_payload.update(query)
            # Do a sanity check and only fetch valid field names.
            query_dict = self._validate_field_names(initial_payload)
        else:
            query_dict = initial_payload

        logger.debug("initial_payload: %s", initial_payload)
        logger.debug("query_dict: %s", query_dict)
        logger.debug("i_url: %s", url)

        osti_response = requests.get(
            url, auth=auth, params=query_dict, headers=headers
        )

        try:
            osti_response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            # Detail text is not always present, which can cause json parsing
            # issues
            details = (
                f'Details: {pprint.pformat(json.loads(osti_response.text))}'
                if osti_response.text else ''
            )

            raise WebRequestException(
                'DOI submission request to OSTI service failed, '
                f'reason: {str(http_err)}\n{details}'
            )

        return osti_response.text

    def _validate_field_names(self, query_dict):
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


class DOIOstiXmlWebParser(DOIOstiWebParser):
    """
    Class used to parse OSTI-format DOI labels in XML format.
    """
    @staticmethod
    def _parse_author_names(authors_element):
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
    def _parse_contributors(contributors_element):
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
                    if full_name:
                        o_node_name = full_name[0].text
                        o_node_name = o_node_name.replace('Planetary Data System:', '')
                        o_node_name = o_node_name.replace('Node', '')
                        o_node_name = o_node_name.strip()
                    else:
                        logger.info("missing DataCurator %s", etree.tostring(single_contributor))

        return o_editors_list, o_node_name

    @staticmethod
    def _get_lidvid(record):
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
            lidvid = DOIWebParser._get_lidvid_from_site_url(record.xpath("site_url")[0].text)
        else:
            # For now, do not consider it an error if cannot get the lidvid.
            logger.warning(
                "Could not parse a lidvid from the provided XML record. "
                "Expecting one of ['accession_number','identifier_type',"
                "'report_numbers','site_url'] tags"
            )

        if lidvid:
            # Some related_identifier fields have been observed with leading and
            # trailing whitespace, so remove it here
            lidvid = lidvid.strip()

            # Some PDS3 identifiers have been observed to contain forward
            # slashes, which causes problems with the API endpoints, so
            # replace them with hyphens
            lidvid = lidvid.replace('/', '-')

        return lidvid

    @staticmethod
    def _parse_optional_fields(io_doi, record_element):
        """
        Given a single XML record element, parse the following optional fields
        which may or may not be present in the OSTI response.

        """
        for optional_field in DOIOstiWebParser._optional_fields:
            optional_field_element = record_element.xpath(optional_field)

            if optional_field_element and optional_field_element[0].text is not None:
                if optional_field == 'keywords':
                    io_doi.keywords = set(optional_field_element[0].text.split(';'))
                    logger.debug(f"Adding optional field 'keywords': "
                                 f"{io_doi.keywords}")
                elif optional_field == 'authors':
                    io_doi.authors = DOIOstiXmlWebParser._parse_author_names(
                        optional_field_element[0]
                    )
                    logger.debug(f"Adding optional field 'authors': "
                                 f"{io_doi.authors}")
                elif optional_field == 'contributors':
                    (io_doi.editors,
                     io_doi.contributor) = DOIOstiXmlWebParser._parse_contributors(
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
    def parse_dois_from_label(label_text, content_type=CONTENT_TYPE_XML):
        """
        Parses a response from a GET (query) or a PUT to the OSTI server
        (in XML query format) and return a list of dictionaries.

        By default, all possible fields are extracted. If desire to only extract
        smaller set of fields, they should be specified accordingly.
        Specific fields are extracted from input. Not all fields in XML are used.

        """
        dois = []
        errors = {}

        doc = etree.fromstring(label_text.encode())
        my_root = doc.getroottree()

        # Trim down input to just fields we want.
        for index, record_element in enumerate(my_root.findall('record')):
            status = record_element.get('status')

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
                errors_element = record_element.xpath('errors')
                doi_message = record_element.xpath('doi_message')

                cur_errors = []

                if len(errors_element):
                    for error_element in errors_element[0]:
                        cur_errors.append(error_element.text)

                if len(doi_message):
                    cur_errors.append(doi_message[0].text)

                errors[index] = cur_errors

            lidvid = DOIOstiXmlWebParser._get_lidvid(record_element)

            timestamp = datetime.now()

            publication_date = record_element.xpath('publication_date')[0].text
            product_type = record_element.xpath('product_type')[0].text
            product_type_specific = record_element.xpath('product_type_specific')[0].text

            doi = Doi(
                title=record_element.xpath('title')[0].text,
                publication_date=datetime.strptime(publication_date, '%Y-%m-%d'),
                product_type=ProductType(product_type),
                product_type_specific=product_type_specific,
                related_identifier=lidvid,
                status=DoiStatus(status.lower()),
                date_record_added=timestamp,
                date_record_updated=timestamp
            )

            # Parse for some optional fields that may not be present in
            # every record from OSTI.
            doi = DOIOstiXmlWebParser._parse_optional_fields(doi, record_element)

            dois.append(doi)

        return dois, errors

    @staticmethod
    def get_record_for_lidvid(label_file, lidvid):
        """
        Returns the record entry corresponding to the provided LIDVID from the
        OSTI XML label file.

        Parameters
        ----------
        label_file : str
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
        root = etree.parse(label_file).getroot()

        records = root.xpath('record')

        for record in records:
            if DOIOstiXmlWebParser._get_lidvid(record) == lidvid:
                result = record
                break
        else:
            raise UnknownLIDVIDException(
                f'Could not find entry for lidvid "{lidvid}" in OSTI label file '
                f'{label_file}.'
            )

        new_root = etree.Element('records')
        new_root.append(result)

        return etree.tostring(
            new_root, pretty_print=True, xml_declaration=True, encoding='UTF-8'
        ).decode('utf-8')


class DOIOstiJsonWebParser(DOIOstiWebParser):
    """
    Class used to parse OSTI-format DOI labels in JSON format.
    """
    @staticmethod
    def _parse_contributors(contributors_record):
        o_editors_list = list(
            filter(
                lambda contributor: contributor['contributor_type'] == 'Editor',
                contributors_record
            )
        )

        data_curator = list(
            filter(
                lambda contributor: contributor['contributor_type'] == 'DataCurator',
                contributors_record
            )
        )

        o_node_name = None

        if data_curator:
            o_node_name = data_curator[0]['full_name']
            o_node_name = o_node_name.replace('Planetary Data System:', '')
            o_node_name = o_node_name.replace('Node', '')
            o_node_name = o_node_name.strip()

        for editor in o_editors_list:
            editor.pop('contributor_type')

        return o_editors_list, o_node_name

    @staticmethod
    def _parse_optional_fields(io_doi, record_element):
        """
        Given a single JSON record element, parse the following optional fields
        which may or may not be present in the OSTI response.

        """
        for optional_field in DOIOstiWebParser._optional_fields:
            optional_field_value = record_element.get(optional_field)

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
                     io_doi.contributor) = DOIOstiJsonWebParser._parse_contributors(
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
    def _get_lidvid(record):
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
            lidvid = DOIWebParser._get_lidvid_from_site_url(record["site_url"])
        else:
            # For now, do not consider it an error if we cannot get a lidvid.
            logger.warning(
                "Could not parse a lidvid from the provided JSON record. "
                "Expecting one of ['accession_number','identifier_type',"
                "'report_numbers','site_url'] fields"
            )

        if lidvid:
            # Some related_identifier fields have been observed with leading and
            # trailing whitespace, so remove it here
            lidvid = lidvid.strip()

            # Some PDS3 identifiers have been observed to contain forward
            # slashes, which causes problems with the API endpoints, so
            # replace them with hyphens
            lidvid = lidvid.replace('/', '-')

        return lidvid

    @staticmethod
    def parse_dois_from_label(label_text, content_type=CONTENT_TYPE_JSON):
        """
        Parses a response from a query to the OSTI server (in JSON format) and
        returns a list of parsed Doi objects.

        Specific fields are extracted from input. Not all fields in the JSON are
        used.

        """
        dois = []
        errors = {}

        osti_response = json.loads(label_text)

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

            lidvid = DOIOstiJsonWebParser._get_lidvid(record)

            timestamp = datetime.now()

            doi = Doi(
                title=record['title'],
                publication_date=datetime.strptime(record['publication_date'], '%Y-%m-%d'),
                product_type=ProductType(record['product_type']),
                product_type_specific=record.get('product_type_specific'),
                related_identifier=lidvid,
                status=DoiStatus(record.get('status', DoiStatus.Unknown).lower()),
                date_record_added=timestamp,
                date_record_updated=timestamp
            )

            # Parse for some optional fields that may not be present in
            # every record from OSTI.
            doi = DOIOstiJsonWebParser._parse_optional_fields(doi, record)

            dois.append(doi)

        return dois, errors

    @staticmethod
    def get_record_for_lidvid(label_file, lidvid):
        """
        Returns the record entry corresponding to the provided LIDVID from the
        OSTI JSON label file.

        Parameters
        ----------
        label_file : str
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
        with open(label_file, 'r') as infile:
            records = json.load(infile)

        for record in records:
            if DOIOstiJsonWebParser._get_lidvid(record) == lidvid:
                result = record
                break
        else:
            raise UnknownLIDVIDException(
                f'Could not find entry for lidvid "{lidvid}" in OSTI label file '
                f'{label_file}.'
            )

        records = [result]

        return json.dumps(records, indent=4)
