#
#  Copyright 2021, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
======================
datacite_web_parser.py
======================

Contains classes used to parse response labels from DataCite DOI service requests.
"""
import html
import json
from datetime import datetime

from dateutil.parser import isoparse
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.exceptions import UnknownIdentifierException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.web_parser import DOIWebParser
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class DOIDataCiteWebParser(DOIWebParser):
    """
    Class used to parse Doi objects from DOI records returned from the
    DataCite service.

    This class only supports parsing records in JSON format.
    """

    _optional_fields = [
        "id",
        "doi",
        "identifiers",
        "description",
        "keywords",
        "authors",
        "site_url",
        "editors",
        "status",
        "date_record_added",
        "date_record_updated",
        "contributor",
    ]

    _mandatory_fields = [
        "title",
        "publisher",
        "publication_date",
        "product_type",
        "product_type_specific",
        "related_identifier",
    ]

    @staticmethod
    def _parse_id(record):
        try:
            if "suffix" in record:
                return record["suffix"]
            else:
                # Parse the ID from the DOI field, it it's available
                return record.get("doi").split("/")[-1]
        except (AttributeError, KeyError):
            logger.warning('Could not parse optional field "id"')

    @staticmethod
    def _parse_doi(record):
        try:
            return record["doi"]
        except KeyError:
            logger.warning('Could not parse optional field "doi"')

    @staticmethod
    def _parse_identifiers(record):
        try:
            identifiers = filter(lambda identifier: identifier["identifierType"] != "DOI", record["identifiers"])
            return list(identifiers)
        except KeyError:
            logger.warning('Could not parse optional field "identifiers"')

    @staticmethod
    def _parse_description(record):
        try:
            return record["descriptions"][0]["description"]
        except (IndexError, KeyError):
            logger.warning('Could not parse optional field "description"')

    @staticmethod
    def _parse_keywords(record):
        try:
            return set(sorted(subject["subject"] for subject in record["subjects"]))
        except KeyError:
            logger.warning('Could not parse optional field "keywords"')

    @staticmethod
    def _parse_authors(record):
        try:
            authors = []

            for creator in record["creators"]:
                if all(name_type in creator for name_type in ("givenName", "familyName")):
                    name = f"{creator['givenName']} {creator['familyName']}"
                else:
                    name = creator["name"]

                authors.append(
                    {
                        "name": name,
                        "name_type": creator["nameType"],
                        "name_identifiers": creator.get("nameIdentifiers", []),
                    }
                )

            return authors
        except KeyError:
            logger.warning('Could not parse optional field "authors"')

    @staticmethod
    def _parse_site_url(record):
        try:
            return html.unescape(record["url"])
        except (KeyError, TypeError):
            logger.warning('Could not parse optional field "site_url"')

    @staticmethod
    def _parse_editors(record):
        try:
            editors = []

            for contributor in record["contributors"]:
                if contributor["contributorType"] == "Editor":
                    if all(name_type in contributor for name_type in ("givenName", "familyName")):
                        name = f"{contributor['givenName']} {contributor['familyName']}"
                    else:
                        name = contributor["name"]

                    editors.append({"name": name, "name_identifiers": contributor.get("nameIdentifiers", [])})
            return editors
        except KeyError:
            logger.warning('Could not parse optional field "editors"')

    @staticmethod
    def _parse_status(record):
        try:
            return DoiStatus(record["state"])
        except (KeyError, ValueError):
            logger.warning('Could not parse optional field "status"')

    @staticmethod
    def _parse_date_record_added(record):
        try:
            return isoparse(record["created"])
        except (KeyError, ValueError):
            logger.warning('Could not parse optional field "date_record_added"')

    @staticmethod
    def _parse_date_record_updated(record):
        try:
            return isoparse(record["updated"])
        except (KeyError, ValueError):
            logger.warning('Could not parse optional field "date_record_updated"')

    @staticmethod
    def _parse_contributor(record):
        try:
            data_curator = next(
                filter(lambda contributor: contributor["contributorType"] == "DataCurator", record["contributors"])
            )

            contributor = data_curator["name"].replace("Planetary Data System:", "").replace("Node", "").strip()

            return contributor
        except (KeyError, StopIteration, ValueError):
            logger.warning('Could not parse optional field "contributor"')

    @staticmethod
    def _parse_related_identifier(record):
        identifier = None

        try:
            identifier = record["relatedIdentifiers"][0]["relatedIdentifier"]
        except (IndexError, KeyError):
            if "identifiers" in record:
                for identifier_record in record["identifiers"]:
                    if identifier_record["identifier"].startswith("urn:"):
                        identifier = identifier_record["identifier"]
                        break
            elif "url" in record:
                logger.info("Parsing related identifier from URL")
                identifier = DOIWebParser._get_identifier_from_site_url(record["url"])

        if identifier is None:
            raise InputFormatException('Failed to parse mandatory field "related_identifier"')

        return identifier.strip()

    @staticmethod
    def _parse_title(record):
        try:
            return record["titles"][0]["title"]
        except (IndexError, KeyError):
            raise InputFormatException('Failed to parse mandatory field "title"')

    @staticmethod
    def _parse_publisher(record):
        try:
            return record["publisher"]
        except KeyError:
            raise InputFormatException('Failed to parse mandatory field "publisher"')

    @staticmethod
    def _parse_publication_date(record):
        try:
            return datetime.strptime(str(record["publicationYear"]), "%Y")
        except (KeyError, ValueError):
            raise InputFormatException('Failed to parse mandatory field "publication_date"')

    @staticmethod
    def _parse_product_type(record):
        try:
            return ProductType(record["types"]["resourceTypeGeneral"])
        except (KeyError, ValueError):
            raise InputFormatException('Failed to parse mandatory field "product_type"')

    @staticmethod
    def _parse_product_type_specific(record):
        try:
            return record["types"]["resourceType"]
        except KeyError:
            raise InputFormatException('Failed to parse mandatory field "product_type_specific"')

    @staticmethod
    def parse_dois_from_label(label_text, content_type=CONTENT_TYPE_JSON):
        """
        Parses one or more Doi objects from the provided DataCite label.

        Parameters
        ----------
        label_text : str
            Text body of the label to parse.
        content_type : str
            The format of the label's content.

        Returns
        -------
        dois : list of Doi
            Doi objects parsed from the provided label.
        errors: list
            List of strings containing any errors encountered while parsing.

        """
        if content_type != CONTENT_TYPE_JSON:
            raise InputFormatException(
                "Unexpected content type provided. Value must be one of the " f"following: [{CONTENT_TYPE_JSON}]"
            )

        dois = []
        errors = []  # DataCite does not return error information in response

        datacite_records = json.loads(label_text)["data"]

        # DataCite can return multiple records in a list under the data key, or
        # a just a dictionary for a single record, make the loop work either way
        if not isinstance(datacite_records, list):
            datacite_records = [datacite_records]

        for index, datacite_record in enumerate(datacite_records):
            try:
                logger.info("Parsing record index %d", index)
                doi_fields = {}

                # Everything we care about in a DataCite response is under
                # attributes
                datacite_record = datacite_record["attributes"]

                for mandatory_field in DOIDataCiteWebParser._mandatory_fields:
                    doi_fields[mandatory_field] = getattr(DOIDataCiteWebParser, f"_parse_{mandatory_field}")(
                        datacite_record
                    )
                    logger.debug("Parsed value %s for mandatory field %s", doi_fields[mandatory_field], mandatory_field)

                for optional_field in DOIDataCiteWebParser._optional_fields:
                    parsed_value = getattr(DOIDataCiteWebParser, f"_parse_{optional_field}")(datacite_record)

                    if parsed_value is not None:
                        doi_fields[optional_field] = parsed_value
                        logger.debug("Parsed value %s for optional field %s", parsed_value, optional_field)

                doi = Doi(**doi_fields)

                dois.append(doi)
            except InputFormatException as err:
                logger.warning(
                    "Failed to parse a DOI object from record index %d " "of the provided label, reason: %s",
                    index,
                    str(err),
                )
                continue

        logger.info("Parsed %d DOI objects from %d records", len(dois), len(datacite_records))

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
            suitable to be written to disk as a new label.
        content_type : str
            The determined content type of the provided label.

        Raises
        ------
        UnknownIdentifierException
            If there is no record for the PDS ID in the provided label file.

        """
        with open(label_file, "r") as infile:
            records = json.load(infile)

        if "data" in records:
            # Strip off the stuff we don't care about
            records = records["data"]

        # May have been handed a single record, if so wrap in a list so loop
        # below still works
        if not isinstance(records, list):
            records = [records]

        for record in records:
            record_id = DOIDataCiteWebParser._parse_related_identifier(record["attributes"])

            if record_id == identifier:
                # Re-add the data key we stripped off earlier
                return json.dumps({"data": record}, indent=4), CONTENT_TYPE_JSON
        else:
            raise UnknownIdentifierException(
                f'Could not find entry for identifier "{identifier}" in ' f"DataCite label file {label_file}."
            )
