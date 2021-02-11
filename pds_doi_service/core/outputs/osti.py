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

Contains classes for creating output OSTI labels from DOI objects.
"""

import datetime
from os.path import dirname, join

import pystache

from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.entities.doi import Doi

logger = get_logger('pds_doi_service.core.outputs.osti')


class DOIOutputOsti:
    def __init__(self):
        """Creates a new DOIOutputOsti instance"""
        # Need to find mustache template relative to current file location
        self._template_path = join(
            dirname(__file__), 'DOI_IAD2_template_20200205-mustache.xml'
        )

    def create_osti_doi_record(self, dois):
        # If a single DOI was provided, wrap it in a list so the iteration
        # below still works
        if isinstance(dois, Doi):
            dois = [dois]

        doi_fields_list = []

        for doi in dois:
            # Filter out any keys with None as the value, so the string literal
            # "None" is not written out as an XML tag's text body
            doi_fields = (
                dict(filter(lambda elem: elem[1] is not None, doi.__dict__.items()))
            )

            # Convert set of keywords back to a semi-colon delimited string
            if doi.keywords:
                doi_fields['keywords'] = ";".join(sorted(doi.keywords))

            # publication_date is assigned to a Doi object as a datetime,
            # need to convert to a string for the OSTI label. Note that
            # even if we only had the publication year from the PDS4 label,
            # the OSTI schema still expects YYYY-mm-dd format.
            if isinstance(doi.publication_date, datetime.datetime):
                doi_fields['publication_date'] = doi.publication_date.strftime('%Y-%m-%d')

            # Same goes for date_record_added
            if doi.date_record_added:
                if isinstance(doi.date_record_added, datetime.datetime):
                    doi_fields['date_record_added'] = doi.date_record_added.strftime('%Y-%m-%d')
            else:
                doi_fields['date_record_added'] = datetime.date.today().strftime('%Y-%m-%d')

            doi_fields_list.append(doi_fields)

        renderer = pystache.Renderer()

        return renderer.render_path(self._template_path, {'dois': doi_fields_list})
