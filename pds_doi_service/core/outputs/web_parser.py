#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
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

    """
    _optional_fields = []
    """The optional field names parsed from labels."""

    @staticmethod
    def _get_lidvid_from_site_url(site_url):
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
    def parse_dois_from_label(label_text, content_type=CONTENT_TYPE_XML):
        raise NotImplementedError(
            'Subclasses of DOIWebParser must provide an implementation for '
            'parse_dois_from_label()'
        )

    @staticmethod
    def get_record_for_lidvid(label_file, lidvid):
        raise NotImplementedError(
            'Subclasses of DOIWebParser must provide an implementation for '
            'get_record_for_lidvid()'
        )
