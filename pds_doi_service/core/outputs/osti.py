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

import copy
import datetime
from os.path import dirname, join

import pystache

from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.entities.doi import Doi

logger = get_logger('pds_doi_service.core.outputs.osti')


class DOIOutputOsti:
    def __init__(self):
        """Creates a new DOIOutputOsti instance"""
        # Need to find mustache templates relative to current file location
        self._draft_template_path = join(
            dirname(__file__), 'DOI_template_20200407-mustache.xml'
        )
        self._reserve_template_path = join(
            dirname(__file__), 'DOI_IAD2_reserved_template_20200205-mustache.xml'
        )

    def create_osti_doi_draft_record(self, doi: Doi):
        doi_fields = copy.copy(doi.__dict__)

        # It is possible that the 'publication_date' type is string if the input
        # is string, check for it here.
        if not isinstance(doi.publication_date, str):
            doi_fields['publication_date'] = doi.publication_date.strftime('%Y-%m-%d')

        if doi.keywords is not None:
            doi_fields['keywords'] = "; ".join(doi.keywords)

        renderer = pystache.Renderer()

        return renderer.render_path(self._draft_template_path, doi_fields)

    def create_osti_doi_reserved_record(self, dois: list):
        doi_fields_list = []

        for doi in dois:
            doi_fields = copy.copy(doi.__dict__)

            logger.debug(f"convert datetime {doi_fields['publication_date']}")
            logger.debug(f"type(doi_fields['publication_date') "
                         f"{type(doi_fields['publication_date'])}")

            # It is possible that the 'publication_date' type is string if the
            # input is string, check for it here.
            if doi.publication_date and not isinstance(doi.publication_date, str):
                doi_fields['publication_date'] = doi.publication_date.strftime('%Y-%m-%d')

            doi_fields_list.append(doi_fields)

        renderer = pystache.Renderer()

        return renderer.render_path(self._reserve_template_path, {'dois': doi_fields_list})

    def create_osti_doi_review_record(self, dois: list):
        doi_fields_list = []

        for doi in dois:
            # Filter out any keys with None as the value, so the string literal
            # "None" is not written out as an XML tag's text body
            doi_fields_list.append(
                dict(filter(lambda elem: elem[1] is not None, doi.__dict__.items()))
            )

        renderer = pystache.Renderer()

        return renderer.render_path(self._reserve_template_path, {'dois': doi_fields_list})

    def create_osti_doi_release_record(self, doi: Doi):
        doi_fields = copy.copy(doi.__dict__)

        # Convert 'date_record_added' to proper format if value is set and not
        # a string, otherwise use today's date.
        if (doi_fields.get('date_record_added')
                and not isinstance(doi_fields['date_record_added'], str)):
            doi_fields['date_record_added'] = doi_fields['date_record_added'].strftime('%Y-%m-%d')
        else:
            doi_fields['date_record_added'] = datetime.date.today().strftime('%Y-%m-%d')

        renderer = pystache.Renderer()

        return renderer.render_path(self._draft_template_path, doi_fields)
