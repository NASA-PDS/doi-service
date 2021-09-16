#
#  Copyright 2021, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
=====================
datacite_validator.py
=====================

Contains functions for validating the contents of DataCite JSON labels.
"""
import json
from distutils.util import strtobool
from os.path import exists

import jsonschema
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.outputs.service_validator import DOIServiceValidator
from pds_doi_service.core.util.general_util import get_logger
from pkg_resources import resource_filename

logger = get_logger(__name__)


class DOIDataCiteValidator(DOIServiceValidator):
    """
    DataCiteValidator provides methods to validate JSON labels submitted to
    DataCite to ensure compliance with their expected format.
    """

    def __init__(self):
        super().__init__()

        schema_file = resource_filename(__name__, "datacite_4.3_schema.json")

        if not exists(schema_file):
            raise RuntimeError(
                "Could not find the schema file needed by this module.\n" f"Expected schema file: {schema_file}"
            )

        with open(schema_file, "r") as infile:
            schema = json.load(infile)

        try:
            jsonschema.Draft7Validator.check_schema(schema)
        except jsonschema.exceptions.SchemaError as err:
            raise RuntimeError(f"Schema file {schema_file} is not a valid JSON schema, " f"reason: {err}")

        self._schema_validator = jsonschema.Draft7Validator(schema)

    def validate(self, label_contents):
        """
        Validates contents of a DataCite JSON label against their JSON schema
        to ensure compliance prior to submission.

        Parameters
        ----------
        label_contents : str
            Contents of the DataCite JSON label.

        Raises
        ------
        InputFormatException
            If the provided label text fails schema validation.

        """
        validate_against_schema = self._config.get("DATACITE", "validate_against_schema", fallback="False")

        # Check the label contents against the DataCite JSON schema
        if strtobool(validate_against_schema):
            json_contents = json.loads(label_contents)

            if "data" in json_contents:
                # Strip off the stuff that is not covered by the JSON schema
                json_contents = json_contents["data"]

            # DataCite labels can contain a single or multiple records,
            # wrap single records in a list for a common interface
            if not isinstance(json_contents, list):
                json_contents = [json_contents]

            error_message = ""

            for index, record in enumerate(json_contents):
                if "attributes" not in record:
                    error_message += (
                        f"JSON record at index {index} does not appear "
                        "to be in DataCite format.\n"
                        "Please ensure the label is valid DataCite "
                        "JSON (as opposed to OSTI-format)."
                    )
                elif not self._schema_validator.is_valid(record["attributes"]):
                    error_message += (
                        f"JSON record at index {index} does not " f"conform to the DataCite Schema, reason(s):\n"
                    )

                    for error in self._schema_validator.iter_errors(record["attributes"]):
                        error_message += "{path}: {message}\n".format(
                            path="/".join(map(str, error.path)), message=error.message
                        )

            if error_message:
                raise InputFormatException(error_message)
