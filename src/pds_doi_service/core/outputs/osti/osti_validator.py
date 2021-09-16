#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
=================
osti_validator.py
=================

Contains functions for validating the contents of OSTI XML labels.
"""
import tempfile
from distutils.util import strtobool
from os.path import exists

import xmlschema  # type: ignore
from lxml import etree
from lxml import isoschematron  # type: ignore
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.outputs.service_validator import DOIServiceValidator
from pds_doi_service.core.util.general_util import get_logger
from pkg_resources import resource_filename

# Note that in the ↑ list of imports, the ``lxml`` module does have the ``isoschematron``
# member, but the typing stub does not so set just it to ``type: ignore``.


logger = get_logger(__name__)


class DOIOstiValidator(DOIServiceValidator):
    """
    DOIOstiValidator provides methods to validate XML labels submitted to OSTI
    to ensure compliance with their expected format.
    """

    def __init__(self):
        super().__init__()

        schematron_file = resource_filename(__name__, "IAD3_schematron.sch")

        if not exists(schematron_file):
            raise RuntimeError(
                "Could not find the schematron file needed by this module.\n"
                f"Expected schematron file: {schematron_file}"
            )

        sct_doc = etree.parse(schematron_file)
        self._schematron = isoschematron.Schematron(sct_doc, store_report=True)

        xsd_filename = resource_filename(__name__, "iad_schema.xsd")

        if not exists(xsd_filename):
            raise RuntimeError(
                "Could not find the schema file needed by this module.\n" f"Expected schema file: {xsd_filename}"
            )

        self._xsd_validator = etree.XMLSchema(file=xsd_filename)
        self._schema_validator = xmlschema.XMLSchema(xsd_filename)

    def _validate_against_schematron(self, osti_root):
        """
        Validates the XML content to be submitted to OSTI against the
        OSTI schematron.

        Parameters
        ----------
        osti_root : etree.Element
            Root of the parsed OSTI XML label.

        Raises
        ------
        InputFormatException
            If the provided XML fails validation against the OSTI schematron.

        """
        # Validate the given input (as an etree document now) against the schematron.
        if not self._schematron.validate(osti_root):
            raise InputFormatException(self._schematron.validation_report)

    def _validate_against_xsd(self, osti_root):
        """
        Validates the XML content to be submitted to OSTI against the
        OSTI XSD.

        Parameters
        ----------
        osti_root : etree.Element
            Root of the parsed OSTI XML label.

        """
        # Perform the XSD validation.
        # The validate() function does not throw an exception, but merely
        # returns True or False.
        is_valid = self._xsd_validator.validate(osti_root)
        logger.info("is_valid: %s", is_valid)

        # If DOI is not valid, use another method to get exactly where the
        # error(s) occurred.
        if not is_valid:
            # Save doi_label to disk
            with tempfile.NamedTemporaryFile(mode="w", suffix="temp_doi.xml") as temp_file:
                temp_file.write(etree.tostring(osti_root).decode())
                temp_file.flush()

                # If the XSD fails to validate the DOI label, it will throw an
                # exception and exit. It will report where/why the error occurred.
                self._schema_validator.validate(temp_file.name)

    def validate(self, label_contents):
        """
        Validates an OSTI XML label using all available means. Any validation
        errors encountered will result in a raised exception with details of
        the failure.

        Parameters
        ----------
        label_contents : str
            Contents of the OSTI XML label.

        """
        # The return from fromstring() function is an Element type and is the root.
        osti_root = etree.fromstring(label_contents.encode())

        # First validate against the schematron, failure will raise an
        # exception
        self._validate_against_schematron(osti_root)

        # Check conditions we cannot check via schematron:
        #
        #     1. Extraneous tags in <records> element.
        #     2. Bad tag(s) in <record> element.
        #
        # Once the record is submitted to OSTI, the 'Pending' status will be
        # immediately returned and a few minutes later changed to 'Registered'.

        # Moved osti_root variable to above where the content of the tree is
        # parsed either from a file or from a string.
        logger.debug("len(osti_root.keys()): %d", len(osti_root.keys()))
        logger.debug("osti_root.keys(): %s", osti_root.keys())

        # Check 1. Extraneous tags in <records> element.
        if len(osti_root.keys()) > 0:
            msg = f"OSTI XML cannot contain extraneous attribute(s) " f"in main tag: {osti_root.keys()}"
            logger.error(msg)
            raise InputFormatException(msg)

        # Check 2. Bad tag(s) in <record> element, e.g. status='Release'.
        # It should only be in possible_status_list variable.
        possible_status_list = [
            DoiStatus.Draft,
            DoiStatus.Reserved,
            DoiStatus.Reserved_not_submitted,
            DoiStatus.Review,
            DoiStatus.Pending,
            DoiStatus.Registered,
        ]
        record_count = 1  # In the world of OSTI, record_count starts at 1.

        for element in osti_root.findall("record"):
            if "status" in element.keys() and element.attrib["status"].lower() not in possible_status_list:
                msg = (
                    f"Invalid status provided for record {record_count}. "
                    f"Status value must be one of {possible_status_list}. "
                    f"Provided {element.attrib['status'].lower()}"
                )
                logger.error(msg)
                raise InputFormatException(msg)

            # Keep track of which record working on for 'record' element.
            record_count += 1

        # Determine if we need to validate against the schema as well
        validate_against_schema = self._config.get("OSTI", "validate_against_schema", fallback="False")

        if strtobool(validate_against_schema):
            self._validate_against_xsd(osti_root)
