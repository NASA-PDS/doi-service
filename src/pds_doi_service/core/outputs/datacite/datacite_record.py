#
#  Copyright 2021 by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
==================
datacite_record.py
==================

Contains classes used to create DataCite-compatible labels from Doi objects in
memory.
"""
from os.path import exists

import jinja2
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import DOIRecord
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.util.general_util import sanitize_json_string
from pkg_resources import resource_filename

logger = get_logger(__name__)


class DOIDataCiteRecord(DOIRecord):
    """
    Class used to create a DOI record suitable for submission to the DataCite
    DOI service.

    This class only supports output of DOI records in JSON format.
    """

    def __init__(self):
        """Creates a new instance of DOIDataCiteRecord"""
        self._config = DOIConfigUtil().get_config()

        # Locate the jinja template
        self._json_template_path = resource_filename(__name__, "DOI_DataCite_template_20210520-jinja2.json")

        if not exists(self._json_template_path):
            raise RuntimeError(
                "Could not find the DOI template needed by this module\n"
                f"Expected JSON template: {self._json_template_path}"
            )

        with open(self._json_template_path, "r") as infile:
            self._template = jinja2.Template(infile.read(), lstrip_blocks=True, trim_blocks=True)

    def create_doi_record(self, dois, content_type=CONTENT_TYPE_JSON):
        """
        Creates a DataCite format DOI record from the provided list of Doi
        objects.

        Parameters
        ----------
        dois : Doi or list of Doi
            The Doi object(s) to format into the returned record.
        content_type : str, optional
            The type of record to return. Only 'json' is supported.

        Returns
        -------
        record : str
            The text body of the record created from the provided Doi objects.

        """
        if content_type != CONTENT_TYPE_JSON:
            raise ValueError(f"Only {CONTENT_TYPE_JSON} is supported for records created " f"from {__name__}")

        # If a single DOI was provided, wrap it in a list so the iteration
        # below still works
        if isinstance(dois, Doi):
            dois = [dois]

        rendered_dois = []

        for doi in dois:
            # Filter out any keys with None as the value, so the string literal
            # "None" is not written out to the template
            doi_fields = dict(filter(lambda elem: elem[1] is not None, doi.__dict__.items()))

            # If this entry does not have a DOI assigned (i.e. reserve request),
            # DataCite wants to know our assigned prefix instead
            if not doi.doi:
                doi_fields["prefix"] = self._config.get("DATACITE", "doi_prefix")

            # 'Bundle' is not supported as a product type in DataCite, so
            # promote to 'Collection'
            if doi.product_type == ProductType.Bundle:
                doi_fields["product_type"] = ProductType.Collection

            # Sort keywords so we can output them in the same order each time
            doi_fields["keywords"] = sorted(map(sanitize_json_string, doi.keywords))

            # Convert datetime objects to isoformat strings
            if doi.date_record_added:
                doi_fields["date_record_added"] = doi.date_record_added.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            if doi.date_record_updated:
                doi_fields["date_record_updated"] = doi.date_record_updated.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            # Cleanup extra whitespace that could break JSON format from title
            # and description
            if doi.title:
                doi_fields["title"] = sanitize_json_string(doi.title)

            if doi.description:
                doi_fields["description"] = sanitize_json_string(doi.description)

            # Publication year is a must-have
            doi_fields["publication_year"] = doi.publication_date.strftime("%Y")

            rendered_dois.append(doi_fields)

        template_vars = {"dois": rendered_dois}

        rendered_template = self._template.render(template_vars)

        return rendered_template
