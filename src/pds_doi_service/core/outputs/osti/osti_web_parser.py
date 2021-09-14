#
#  Copyright 2021, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
==================
osti_web_parser.py
==================

Contains classes used to parse response labels from OSTI DOI service requests.
"""
import html
import json
import os
from datetime import datetime

from lxml import etree
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.exceptions import UnknownIdentifierException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.web_parser import DOIWebParser
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOIOstiWebParser(DOIWebParser):
    """
    Class used to parse Doi objects from DOI records returned from the OSTI
    DOI service.

    This class supports parsing records in both XML and JSON formats.
    """

    _optional_fields = [
        "id",
        "doi",
        "sponsoring_organization",
        "publisher",
        "availability",
        "country",
        "description",
        "site_url",
        "site_code",
        "keywords",
        "authors",
        "contributors",
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
                "Unsupported content type provided. Value must be one of the "
                f"following: [{CONTENT_TYPE_JSON}, {CONTENT_TYPE_XML}]"
            )

        return dois, errors

    @staticmethod
    def get_record_for_identifier(label_file, identifier):
        """
        Returns a new label from the provided one containing only the DOI entry
        corresponding to the specified PDS identifier.

        Parameters
        ----------
        label_file : str
            Path to the label file to pull a record from.
        identifier : str
            The PDS identifier to search for within the provided label file.

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
            record = DOIOstiXmlWebParser.get_record_for_identifier(label_file, identifier)
        elif content_type == CONTENT_TYPE_JSON:
            record = DOIOstiJsonWebParser.get_record_for_identifier(label_file, identifier)
        else:
            raise InputFormatException(
                "Unsupported file type provided. File must have one of the "
                f"following extensions: [{CONTENT_TYPE_JSON}, {CONTENT_TYPE_XML}]"
            )

        return record, content_type


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
            first_name = single_author.xpath("first_name")
            last_name = single_author.xpath("last_name")
            full_name = single_author.xpath("full_name")
            middle_name = single_author.xpath("middle_name")

            author_dict = {}

            if full_name:
                author_dict["full_name"] = full_name[0].text
            else:
                if first_name and last_name:
                    author_dict.update({"first_name": first_name[0].text, "last_name": last_name[0].text})

                if middle_name:
                    author_dict.update({"middle_name": middle_name[0].text})

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
        o_node_name = ""

        # If they exist, collect all the editor contributor fields into a list
        # of dictionaries.
        for single_contributor in contributors_element:
            first_name = single_contributor.xpath("first_name")
            last_name = single_contributor.xpath("last_name")
            full_name = single_contributor.xpath("full_name")
            middle_name = single_contributor.xpath("middle_name")
            contributor_type = single_contributor.xpath("contributor_type")

            if contributor_type:
                if contributor_type[0].text == "Editor":
                    editor_dict = {}

                    if full_name:
                        editor_dict["full_name"] = full_name[0].text
                    else:
                        if first_name and last_name:
                            editor_dict.update({"first_name": first_name[0].text, "last_name": last_name[0].text})

                        if middle_name:
                            editor_dict.update({"middle_name": middle_name[0].text})

                    # It is possible that the record contains no contributor.
                    if editor_dict:
                        o_editors_list.append(editor_dict)
                # Parse the node ID from the name of the data curator
                elif contributor_type[0].text == "DataCurator":
                    if full_name:
                        o_node_name = full_name[0].text
                        o_node_name = o_node_name.replace("Planetary Data System:", "")
                        o_node_name = o_node_name.replace("Node", "")
                        o_node_name = o_node_name.strip()
                    else:
                        logger.info("missing DataCurator %s", etree.tostring(single_contributor))

        return o_editors_list, o_node_name

    @staticmethod
    def _get_identifier(record):
        """
        Depending on versions, a PDS identifier (lidvid or otherwise) can be
        stored in different locations. This function searches each location,
        and returns the first valid result.
        """
        identifier = None

        if record.xpath("accession_number"):
            identifier = record.xpath("accession_number")[0].text
        elif record.xpath("related_identifiers/related_identifier[./identifier_type='URL']"):
            identifier = record.xpath(
                "related_identifiers/related_identifier[./identifier_type='URL']/identifier_value"
            )[0].text
        elif record.xpath("related_identifiers/related_identifier[./identifier_type='URN']"):
            identifier = record.xpath(
                "related_identifiers/related_identifier[./identifier_type='URN']/identifier_value"
            )[0].text
        elif record.xpath("report_numbers"):
            identifier = record.xpath("report_numbers")[0].text
        elif record.xpath("site_url"):
            # For some records, the identifier can be parsed from the 'site_url'
            # field as last resort.
            identifier = DOIWebParser._get_identifier_from_site_url(record.xpath("site_url")[0].text)
        else:
            # For now, do not consider it an error if cannot get an identifier.
            logger.warning(
                "Could not parse a PDS identifier from the provided XML record. "
                "Expecting one of ['accession_number','identifier_type',"
                "'report_numbers','site_url'] tags"
            )

        if identifier:
            # Some identifier fields have been observed with leading and
            # trailing whitespace, so remove it here
            identifier = identifier.strip()

        return identifier

    @staticmethod
    def _parse_optional_fields(io_doi, record_element):
        """
        Given a single XML record element, parse the following optional fields
        which may or may not be present in the OSTI response.

        """
        for optional_field in DOIOstiWebParser._optional_fields:
            optional_field_element = record_element.xpath(optional_field)

            if optional_field_element and optional_field_element[0].text is not None:
                if optional_field == "keywords":
                    io_doi.keywords = set(optional_field_element[0].text.split(";"))
                    logger.debug(f"Adding optional field 'keywords': " f"{io_doi.keywords}")
                elif optional_field == "authors":
                    io_doi.authors = DOIOstiXmlWebParser._parse_author_names(optional_field_element[0])
                    logger.debug(f"Adding optional field 'authors': " f"{io_doi.authors}")
                elif optional_field == "contributors":
                    (io_doi.editors, io_doi.contributor) = DOIOstiXmlWebParser._parse_contributors(
                        optional_field_element[0]
                    )
                    logger.debug(f"Adding optional field 'editors': " f"{io_doi.editors}")
                    logger.debug(f"Adding optional field 'contributor': " f"{io_doi.contributor}")
                elif optional_field == "date_record_added":
                    io_doi.date_record_added = datetime.strptime(optional_field_element[0].text, "%Y-%m-%d")
                    logger.debug(f"Adding optional field 'date_record_added': " f"{io_doi.date_record_added}")
                elif optional_field == "date_record_updated":
                    io_doi.date_record_updated = datetime.strptime(optional_field_element[0].text, "%Y-%m-%d")
                    logger.debug(f"Adding optional field 'date_record_updated': " f"{io_doi.date_record_updated}")
                else:
                    setattr(io_doi, optional_field, optional_field_element[0].text)

                    logger.debug(f"Adding optional field " f"'{optional_field}': {getattr(io_doi, optional_field)}")

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
        for index, record_element in enumerate(my_root.findall("record")):
            status = record_element.get("status")

            if status is None:
                raise InputFormatException(
                    f"Could not parse a status for record {index + 1} from the " f"provided OSTI XML."
                )

            if status.lower() == "error":
                # The 'error' record is parsed differently and does not have all
                # the attributes we desire.
                logger.error(f"Errors reported for record index {index + 1}")

                # Check for any errors reported back from OSTI and save
                # them off to be returned
                errors_element = record_element.xpath("errors")
                doi_message = record_element.xpath("doi_message")

                cur_errors = []

                if len(errors_element):
                    for error_element in errors_element[0]:
                        cur_errors.append(error_element.text)

                if len(doi_message):
                    cur_errors.append(doi_message[0].text)

                errors[index] = cur_errors

            identifier = DOIOstiXmlWebParser._get_identifier(record_element)

            timestamp = datetime.now()

            publication_date = record_element.xpath("publication_date")[0].text
            product_type = record_element.xpath("product_type")[0].text
            product_type_specific = record_element.xpath("product_type_specific")[0].text

            doi = Doi(
                title=record_element.xpath("title")[0].text,
                publication_date=datetime.strptime(publication_date, "%Y-%m-%d"),
                product_type=ProductType(product_type),
                product_type_specific=product_type_specific,
                related_identifier=identifier,
                status=DoiStatus(status.lower()),
                date_record_added=timestamp,
                date_record_updated=timestamp,
            )

            # Parse for some optional fields that may not be present in
            # every record from OSTI.
            doi = DOIOstiXmlWebParser._parse_optional_fields(doi, record_element)

            dois.append(doi)

        return dois, errors

    @staticmethod
    def get_record_for_identifier(label_file, identifier):
        """
        Returns the record entry corresponding to the provided PDS identifier
        from the OSTI XML label file.

        Parameters
        ----------
        label_file : str
            Path to the OSTI XML label file to search.
        identifier : str
            The PDS identifier (LIDVID or otherwise) to search for within the
            provided label file.

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

        records = root.xpath("record")

        for record in records:
            if DOIOstiXmlWebParser._get_identifier(record) == identifier:
                result = record
                break
        else:
            raise UnknownIdentifierException(
                f'Could not find entry for identifier "{identifier}" in OSTI ' f"label file {label_file}."
            )

        new_root = etree.Element("records")
        new_root.append(result)

        return etree.tostring(new_root, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode("utf-8")


class DOIOstiJsonWebParser(DOIOstiWebParser):
    """
    Class used to parse OSTI-format DOI labels in JSON format.
    """

    _mandatory_fields = ["title", "publication_date", "product_type"]

    @staticmethod
    def _parse_contributors(contributors_record):
        o_editors_list = list(
            filter(lambda contributor: contributor["contributor_type"] == "Editor", contributors_record)
        )

        data_curator = list(
            filter(lambda contributor: contributor["contributor_type"] == "DataCurator", contributors_record)
        )

        o_node_name = None

        if data_curator:
            o_node_name = data_curator[0]["full_name"]
            o_node_name = o_node_name.replace("Planetary Data System:", "")
            o_node_name = o_node_name.replace("Node", "")
            o_node_name = o_node_name.strip()

        for editor in o_editors_list:
            editor.pop("contributor_type")

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
                if optional_field == "keywords":
                    io_doi.keywords = set(optional_field_value.split(";"))
                    logger.debug(f"Adding optional field 'keywords': " f"{io_doi.keywords}")
                elif optional_field == "site_url":
                    # In order to match parsing behavior of lxml, unescape
                    # the site url
                    io_doi.site_url = html.unescape(optional_field_value)
                    logger.debug(f"Adding optional field 'site_url': " f"{io_doi.site_url}")
                elif optional_field == "contributors":
                    (io_doi.editors, io_doi.contributor) = DOIOstiJsonWebParser._parse_contributors(
                        optional_field_value
                    )
                    logger.debug(f"Adding optional field 'editors': " f"{io_doi.editors}")
                    logger.debug(f"Adding optional field 'contributor': " f"{io_doi.contributor}")
                elif optional_field == "date_record_added":
                    io_doi.date_record_added = datetime.strptime(optional_field_value, "%Y-%m-%d")
                    logger.debug(f"Adding optional field 'date_record_added': " f"{io_doi.date_record_added}")
                elif optional_field == "date_record_updated":
                    io_doi.date_record_updated = datetime.strptime(optional_field_value, "%Y-%m-%d")
                    logger.debug(f"Adding optional field 'date_record_updated': " f"{io_doi.date_record_updated}")
                else:
                    setattr(io_doi, optional_field, optional_field_value)

                    logger.debug(f"Adding optional field " f"'{optional_field}': {getattr(io_doi, optional_field)}")

        return io_doi

    @staticmethod
    def _get_identifier(record):
        identifier = None

        if "accession_number" in record:
            identifier = record["accession_number"]
        elif "related_identifiers" in record:
            for related_identifier in record["related_identifiers"]:
                if related_identifier.get("identifier_type") == "URL":
                    identifier = related_identifier["identifier_value"]
                    break
        elif "report_numbers" in record:
            identifier = record["report_numbers"]
        elif "site_url" in record:
            identifier = DOIWebParser._get_identifier_from_site_url(record["site_url"])
        else:
            # For now, do not consider it an error if we cannot get an identifier.
            logger.warning(
                "Could not parse a PDS identifier from the provided JSON record. "
                "Expecting one of ['accession_number','identifier_type',"
                "'report_numbers','site_url'] fields"
            )

        if identifier:
            # Some identifier fields have been observed with leading and
            # trailing whitespace, so remove it here
            identifier = identifier.strip()

        return identifier

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
        if "records" in osti_response:
            osti_response = osti_response["records"]

        # Multiple records may come in a list, or a single dict may be provided
        # for a single record, make the loop work either way
        if not isinstance(osti_response, list):
            osti_response = [osti_response]

        for index, record in enumerate(osti_response):
            if record.get("status", "").lower() == "error":
                logger.error(f"Errors reported for record index {index + 1}")

                # Check for any errors reported back from OSTI and save
                # them off to be returned
                cur_errors = []

                if "errors" in record:
                    cur_errors.extend(record["errors"])

                if "doi_message" in record and len(record["doi_message"]):
                    cur_errors.append(record["doi_message"])

                errors[index] = cur_errors

            # Make sure all the mandatory fields are present
            if not all([field in record for field in DOIOstiJsonWebParser._mandatory_fields]):
                raise InputFormatException(
                    "Provided JSON is missing one or more mandatory fields: "
                    f'({", ".join(DOIOstiJsonWebParser._mandatory_fields)})'
                )

            identifier = DOIOstiJsonWebParser._get_identifier(record)

            timestamp = datetime.now()

            doi = Doi(
                title=record["title"],
                publication_date=datetime.strptime(record["publication_date"], "%Y-%m-%d"),
                product_type=ProductType(record["product_type"]),
                product_type_specific=record.get("product_type_specific"),
                related_identifier=identifier,
                status=DoiStatus(record.get("status", DoiStatus.Unknown).lower()),
                date_record_added=timestamp,
                date_record_updated=timestamp,
            )

            # Parse for some optional fields that may not be present in
            # every record from OSTI.
            doi = DOIOstiJsonWebParser._parse_optional_fields(doi, record)

            dois.append(doi)

        return dois, errors

    @staticmethod
    def get_record_for_identifier(label_file, identifier):
        """
        Returns the record entry corresponding to the provided PDS identifier
        from the OSTI JSON label file.

        Parameters
        ----------
        label_file : str
            Path to the OSTI JSON label file to search.
        identifier : str
            The PDS identifier of the record to return from the OSTI label.

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
        with open(label_file, "r") as infile:
            records = json.load(infile)

        if not isinstance(records, list):
            records = [records]

        for record in records:
            if DOIOstiJsonWebParser._get_identifier(record) == identifier:
                result = record
                break
        else:
            raise UnknownIdentifierException(
                f'Could not find entry for identifier "{identifier}" in OSTI ' f"label file {label_file}."
            )

        records = [result]

        return json.dumps(records, indent=4)
