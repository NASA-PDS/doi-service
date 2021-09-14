#
#  Copyright 2021, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
==============
osti_record.py
==============

Contains classes used to create OSTI-compatible labels from Doi objects in memory.
"""
import html
import json
from datetime import datetime
from os.path import exists

import pystache
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.doi_record import DOIRecord
from pds_doi_service.core.outputs.doi_record import VALID_CONTENT_TYPES
from pds_doi_service.core.util.general_util import get_logger
from pkg_resources import resource_filename

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
        self._xml_template_path = resource_filename(__name__, "DOI_IAD2_template_20200205-mustache.xml")
        self._json_template_path = resource_filename(__name__, "DOI_IAD2_template_20210216-mustache.json")

        if not exists(self._xml_template_path) or not exists(self._json_template_path):
            raise RuntimeError(
                f"Could not find one or more DOI templates needed by this module\n"
                f"Expected XML template: {self._xml_template_path}\n"
                f"Expected JSON template: {self._json_template_path}"
            )

        self._template_map = {CONTENT_TYPE_XML: self._xml_template_path, CONTENT_TYPE_JSON: self._json_template_path}

    def create_doi_record(self, dois, content_type=CONTENT_TYPE_XML):
        """
        Creates a DOI record from the provided list of Doi objects in the
        specified format.

        Parameters
        ----------
        dois : Doi or list of Dois
            The Doi object to format into the returned record.
        content_type : str
            The type of record to return. Currently, 'xml' and 'json' are
            supported.

        Returns
        -------
        record : str
            The text body of the record created from the provided Doi objects.

        """
        if content_type not in VALID_CONTENT_TYPES:
            raise ValueError("Invalid content type requested, must be one of " f'{",".join(VALID_CONTENT_TYPES)}')

        # If a single DOI was provided, wrap it in a list so the iteration
        # below still works
        if isinstance(dois, Doi):
            dois = [dois]

        doi_fields_list = []

        for index, doi in enumerate(dois):
            # Filter out any keys with None as the value, so the string literal
            # "None" is not written out as an XML tag's text body
            doi_fields = dict(filter(lambda elem: elem[1] is not None, doi.__dict__.items()))

            # Escape any necessary HTML characters from the site-url,
            # we perform this step rather than pystache to avoid
            # unintentional recursive escapes
            if doi.site_url:
                doi_fields["site_url"] = html.escape(doi.site_url)

            # Convert set of keywords back to a semi-colon delimited string
            if doi.keywords:
                doi_fields["keywords"] = ";".join(sorted(doi.keywords))
            else:
                doi_fields.pop("keywords")

            # Remove any extraneous whitespace from a provided description
            if doi.description:
                doi_fields["description"] = str.strip(doi.description)

            # publication_date is assigned to a Doi object as a datetime,
            # need to convert to a string for the OSTI label. Note that
            # even if we only had the publication year from the PDS4 label,
            # the OSTI schema still expects YYYY-mm-dd format.
            if isinstance(doi.publication_date, datetime):
                doi_fields["publication_date"] = doi.publication_date.strftime("%Y-%m-%d")

            # Same goes for date_record_added and date_record_updated
            if doi.date_record_added and isinstance(doi.date_record_added, datetime):
                doi_fields["date_record_added"] = doi.date_record_added.strftime("%Y-%m-%d")

            if doi.date_record_updated and isinstance(doi.date_record_updated, datetime):
                doi_fields["date_record_updated"] = doi.date_record_updated.strftime("%Y-%m-%d")

            # Pre-convert author map into a JSON string to make it play nice
            # with pystache rendering
            if doi.authors and content_type == CONTENT_TYPE_JSON:
                doi_fields["authors"] = json.dumps(doi.authors)

            # The OSTI IAD schema does not support 'Bundle' as a product type,
            # so convert to collection here
            if doi.product_type == ProductType.Bundle:
                doi_fields["product_type"] = ProductType.Collection

            # Lastly, we need a kludge to inform the mustache template whether
            # to include a comma between consecutive entries (JSON only)
            if content_type == CONTENT_TYPE_JSON and index < len(dois) - 1:
                doi_fields["comma"] = True

            doi_fields_list.append(doi_fields)

        renderer = pystache.Renderer()

        rendered_template = renderer.render_path(self._template_map[content_type], {"dois": doi_fields_list})

        # Reindent the output JSON to account for the kludging of the authors field
        if content_type == CONTENT_TYPE_JSON:
            rendered_template = json.dumps(json.loads(rendered_template), indent=4)

        return rendered_template
