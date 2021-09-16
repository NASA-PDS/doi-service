#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
=============
web_parser.py
=============

Contains the abstract base class for parsing DOI objects from label returned or
provided to DOI service endpoints (OSTI, Datacite, etc...).
"""
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML


class DOIWebParser:
    """
    Abstract base class for parsers of DOI labels returned (or submitted)
    to a DOI service endpoint.
    """

    _optional_fields: list[str] = []
    """The optional Doi field names parsed from labels."""

    _mandatory_fields: list[str] = []
    """The mandatory Doi field names parsed from labels."""

    @staticmethod
    def _get_identifier_from_site_url(site_url):
        """
        For some records, the PDS identifier can be parsed from site_url as a
        last resort.

        Ex:
        PDS4: https://...?identifier=urn%3Anasa%3Apds%3Ainsight_cameras&amp;version=1.0
        PDS3: https://...?dsid=LRO-L-MRFLRO-2%2F3%2F5-BISTATIC-V1.0

        """
        # TODO: rewrite to utilize urlparse and support PDS3 labels
        lid_vid_value = None

        site_tokens = site_url.split("identifier=")

        identifier_tokens = site_tokens[1].split(";")

        lid_vid_tokens = identifier_tokens[0].split("&version=")

        if len(lid_vid_tokens) >= 2:
            lid_value = lid_vid_tokens[0].replace("%3A", ":")
            vid_value = lid_vid_tokens[1]

            # Finally combine the lid and vid together.
            lid_vid_value = lid_value + "::" + vid_value

        return lid_vid_value

    @staticmethod
    def parse_dois_from_label(label_text, content_type=CONTENT_TYPE_XML):
        """
        Parses one or more Doi objects from the provided label.

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
        errors: dict
            Dictionary mapping indices of DOI's in the provided label to lists
            of strings containing any errors encountered while parsing.

        """
        raise NotImplementedError(
            f"Subclasses of {DOIWebParser.__name__} must provide an " f"implementation for parse_dois_from_label()"
        )

    @staticmethod
    def get_record_for_identifier(label_file, identifier):
        """
        Returns a new label from the provided containing only the DOI entry
        corresponding to the specified PDS identifier.

        Parameters
        ----------
        label_file : str
            Path to the label file to pull a record from.
        identifier : str
            The PDS identifier (LIDVID or otherwise) to search for within the
            provided label file.

        Returns
        -------
        record : str
            The single found record embedded in a <records> tag. This string is
            suitable to be written to disk as a new label.
        content_type : str
            The determined content type of the provided label.

        """
        raise NotImplementedError(
            f"Subclasses of {DOIWebParser.__name__} must provide an " f"implementation for get_record_for_identifier()"
        )
