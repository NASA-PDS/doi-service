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
            f"Subclasses of {DOIWebParser.__name__} must provide an implementation for parse_dois_from_label()"
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
            The single found record. This string is suitable to be written to
            disk as a new label.
        content_type : str
            The determined content type of the provided label.

        """
        raise NotImplementedError(
            f"Subclasses of {DOIWebParser.__name__} must provide an implementation for get_record_for_identifier()"
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

        """
        raise NotImplementedError(
            f"Subclasses of {DOIWebParser.__name__} must provide an implementation for get_record_for_doi()"
        )
