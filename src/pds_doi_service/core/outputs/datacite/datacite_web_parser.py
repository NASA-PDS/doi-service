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
from distutils.version import LooseVersion

from dateutil.parser import isoparse
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiEvent
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.entities.exceptions import InputFormatException
from pds_doi_service.core.entities.exceptions import UnknownDoiException
from pds_doi_service.core.entities.exceptions import UnknownIdentifierException
from pds_doi_service.core.entities.exceptions import UnknownNodeException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.web_parser import DOIWebParser
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.util.general_util import is_pds4_identifier
from pds_doi_service.core.util.general_util import parse_identifier_from_site_url
from pds_doi_service.core.util.node_util import NodeUtil

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
        "node_id",
        "identifiers",
        "related_identifiers",
        "description",
        "keywords",
        "authors",
        "site_url",
        "editors",
        "status",
        "date_record_added",
        "date_record_updated",
        "contributor",
        "event",
    ]

    _mandatory_fields = [
        "title",
        "publisher",
        "publication_date",
        "product_type",
        "product_type_specific",
        "pds_identifier",
    ]

    _pds3_identifier_types = ["PDS3 Data Set ID", "PDS3 Dataset ID", "Site ID", "Handle"]
    """The set of identifier types which indicate a PDS3 dataset"""

    _pds4_identifier_types = ["PDS4 LIDVID", "PDS4 Bundle LIDVID", "PDS4 Bundle ID", "Site ID", "URN"]
    """The set of identifier types which indicate a PDS4 dataset"""

    @staticmethod
    def _parse_id(record):
        try:
            if "suffix" in record:
                return record["suffix"]
            else:
                # Parse the ID from the DOI field, if it's available
                return record.get("doi").split("/")[-1]
        except (AttributeError, KeyError):
            raise UserWarning('Could not parse optional field "id"')

    @staticmethod
    def _parse_doi(record):
        try:
            return record["doi"]
        except KeyError:
            raise UserWarning('Could not parse optional field "doi"')

    @staticmethod
    def _parse_event(record):
        try:
            if record.get("event"):
                return DoiEvent(record["event"])
        except ValueError:
            raise UserWarning(f'Provided event "{record["event"]}" could not be parsed to a DoiEvent')

    @staticmethod
    def _parse_identifiers(record):
        try:
            identifiers = record["identifiers"]

            for identifier in identifiers:
                identifier["identifier"] = identifier["identifier"].strip()

            return identifiers
        except KeyError:
            raise UserWarning('Could not parse optional field "identifiers"')

    @staticmethod
    def _parse_related_identifiers(record):
        try:
            related_identifiers = record["relatedIdentifiers"]

            for related_identifier in related_identifiers:
                related_identifier["relatedIdentifier"] = related_identifier["relatedIdentifier"].strip()

            return related_identifiers
        except KeyError:
            raise UserWarning('Could not parse optional field "related_identifiers"')

    @staticmethod
    def _parse_description(record):
        try:
            return record["descriptions"][0]["description"]
        except (IndexError, KeyError):
            raise UserWarning('Could not parse optional field "description"')

    @staticmethod
    def _parse_keywords(record):
        try:
            return set(sorted(subject["subject"] for subject in record["subjects"]))
        except KeyError:
            raise UserWarning('Could not parse optional field "keywords"')

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
                        "affiliation": creator.get("affiliation", []),
                    }
                )

            return authors
        except KeyError:
            raise UserWarning('Could not parse optional field "authors"')

    @staticmethod
    def _parse_site_url(record):
        try:
            return html.unescape(record["url"])
        except (KeyError, TypeError):
            raise UserWarning('Could not parse optional field "site_url"')

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

                    editors.append(
                        {
                            "name": name,
                            "name_identifiers": contributor.get("nameIdentifiers", []),
                            "affiliation": contributor.get("affiliation", []),
                        }
                    )
            return editors
        except KeyError:
            raise UserWarning('Could not parse optional field "editors"')

    @staticmethod
    def _parse_status(record):
        try:
            return DoiStatus(record["state"])
        except (KeyError, ValueError):
            raise UserWarning('Could not parse optional field "status"')

    @staticmethod
    def _parse_date_record_added(record):
        try:
            return isoparse(record["created"])
        except (KeyError, ValueError):
            raise UserWarning('Could not parse optional field "date_record_added"')

    @staticmethod
    def _parse_date_record_updated(record):
        try:
            return isoparse(record["updated"])
        except (KeyError, ValueError):
            raise UserWarning('Could not parse optional field "date_record_updated"')

    @staticmethod
    def _parse_contributor(record):
        try:
            data_curator = next(
                filter(lambda contributor: contributor["contributorType"] == "DataCurator", record["contributors"])
            )

            contributor = data_curator["name"].replace("Planetary Data System:", "").replace("Node", "").strip()

            return contributor
        except (KeyError, StopIteration, ValueError):
            raise UserWarning('Could not parse optional field "contributor"')

    @staticmethod
    def _parse_node_id(record):
        try:
            # Contributor field should be the same as the "long name" version of the Node ID,
            # so attempt to parse it and convert it back to the ID
            contributor = DOIDataCiteWebParser._parse_contributor(record)

            return NodeUtil.get_node_id(contributor)
        except (UserWarning, UnknownNodeException):
            raise UserWarning('Could not parse optional field "node_id"')

    @staticmethod
    def _parse_pds_identifier(record):
        identifier = None

        # First, check identifiers for a PDS ID, giving preference
        # to a PDS3 dataset ID, if present
        for identifier_record in record.get("identifiers", []):
            if identifier_record[
                "identifierType"
            ] in DOIDataCiteWebParser._pds3_identifier_types and not is_pds4_identifier(
                identifier_record["identifier"]
            ):
                identifier = identifier_record["identifier"]
                break

        # Next, try another pass on identifiers, looking for PDS4 URN this time
        if not identifier:
            pds4_identifiers = []
            for identifier_record in record.get("identifiers", []):
                if identifier_record.get(
                    "identifierType", ""
                ) in DOIDataCiteWebParser._pds4_identifier_types and is_pds4_identifier(
                    identifier_record.get("identifier", "")
                ):
                    pds4_identifiers.append(identifier_record["identifier"])

            # There could be multiple PDS4 ID's with the same LID but different
            # VIDs, so take the newest one. The LooseVersion class is used to
            # sort VIDs by basic semantic versioning rules (1.9.0 < 1.10.0)
            # For LID's only, assign a version 0.0 so they're always superseded by
            # a LIDVID
            if pds4_identifiers:
                vids = [
                    pds4_identifier.split("::")[-1] if "::" in pds4_identifier else "0.0"
                    for pds4_identifier in pds4_identifiers
                ]
                sorted_vids = list(sorted(vids, key=LooseVersion))
                identifier = pds4_identifiers[vids.index(sorted_vids[-1])]

        # Lastly, try to parse an ID from the site URL
        if not identifier and "url" in record:
            logger.info("Parsing PDS identifier from URL")
            identifier = parse_identifier_from_site_url(record["url"])

        if identifier is None:
            raise InputFormatException('Failed to parse mandatory field "pds_identifier"')

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
                f"Unexpected content type provided. Value must be one of the following: [{CONTENT_TYPE_JSON}]"
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

                # Everything we care about in a DataCite response is under attributes
                datacite_record = datacite_record["attributes"]

                for mandatory_field in DOIDataCiteWebParser._mandatory_fields:
                    doi_fields[mandatory_field] = getattr(DOIDataCiteWebParser, f"_parse_{mandatory_field}")(
                        datacite_record
                    )
                    logger.debug("Parsed value %s for mandatory field %s", doi_fields[mandatory_field], mandatory_field)

                for optional_field in DOIDataCiteWebParser._optional_fields:
                    try:
                        parser = getattr(DOIDataCiteWebParser, f"_parse_{optional_field}")
                        parsed_value = parser(datacite_record)

                        if parsed_value is not None:
                            doi_fields[optional_field] = parsed_value
                            logger.debug("Parsed value %s for optional field %s", parsed_value, optional_field)
                    except UserWarning as warning:
                        logger.warning("Record %d: %s", index, str(warning))

                doi = Doi(**doi_fields)

                dois.append(doi)
            except InputFormatException as err:
                logger.warning(
                    "Failed to parse a DOI object from record index %d of the provided label, reason: %s",
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
            The single found record. This string is suitable to be written to
            disk as a new label.
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
            record_id = DOIDataCiteWebParser._parse_pds_identifier(record["attributes"])

            if record_id == identifier:
                # Re-add the data key we stripped off earlier
                return json.dumps({"data": record}, indent=4), CONTENT_TYPE_JSON
        else:
            raise UnknownIdentifierException(
                f'Could not find entry for identifier "{identifier}" in DataCite label file {label_file}.'
            )

    @staticmethod
    def get_record_for_doi(label_file, doi):
        """
        Returns a new label from the provided one containing only the entry
        corresponding to the specified DOI.

        Parameters
        ----------
        label_file : str
            Path to the label file to pull a record from.
        doi : str
            The DOI to search for within the provided label file.

        Returns
        -------
        record : str
            The single found record. This string is suitable to be written to
            disk as a new label.
        content_type : str
            The determined content type of the provided label.

        Raises
        ------
        UnknownDoiException
            If there is no record for the DOI in the provided label file.

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
            cur_doi = DOIDataCiteWebParser._parse_doi(record["attributes"])

            if cur_doi == doi:
                # Re-add the data key we stripped off earlier
                return json.dumps({"data": record}, indent=4), CONTENT_TYPE_JSON
        else:
            raise UnknownDoiException(f'Could not find entry for DOI "{doi}" in DataCite label file {label_file}.')
