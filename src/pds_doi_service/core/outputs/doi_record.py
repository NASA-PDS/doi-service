#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
=============
doi_record.py
=============

Contains the base class for creating a record from DOI objects.
"""

CONTENT_TYPE_XML = "xml"
CONTENT_TYPE_JSON = "json"
"""Constants for the available content types to work with"""

VALID_CONTENT_TYPES = [CONTENT_TYPE_JSON, CONTENT_TYPE_XML]
"""The list of expected content types"""


class DOIRecord:
    """Abstract base class for DOI record generating classes"""

    def create_doi_record(self, dois, content_type=CONTENT_TYPE_XML):
        """
        Creates a DOI record from the provided list of Doi objects in the
        specified format.

        Parameters
        ----------
        dois : Doi or list of Doi
            The Doi object(s) to format into the returned record.
        content_type : str
            The type of record to return.

        Returns
        -------
        record : str
            The text body of the record created from the provided Doi objects.

        """
        raise NotImplementedError(
            f"Subclasses of {self.__class__.__name__} must provide an " f"implementation for create_doi_record()"
        )
