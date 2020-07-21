#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

from lxml import etree
from lxml import isoschematron

from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.input.osti_input_util')

class OSTIInputValidator:
    # This OSTIInputValidator provides some functions to validate the input to 'release' action specific to OSTI.  Other data center may have different format.

    def validate_release_input(self, input_to_osti):
        """
        Function validate the XML content that will be used to submit to OSTI for 'release' action.

        :param input_to_osti: file containing text of XML document
        :return:
        """
        o_default_schematron = 'config/osti_release_input_schematron.xml'

        # Parse default schematron from config directory.
        sct_doc = etree.parse(o_default_schematron)
        schematron = isoschematron.Schematron(sct_doc, store_report=True)

        # Parse input xml into an etree document. 
        osti_doc = etree.parse(input_to_osti)

        # Validate the given input (as an etree document now) against the schematron.
        o_validationResult = schematron.validate(osti_doc)

        # Get the validation report to be printed for debug. 
        o_validation_report = schematron.validation_report

        # The value of validationResult is either True or False as boolean type.
        logger.debug(f"{input_to_osti} is valid: {str(o_validationResult)}")
        logger.debug(f"o_validation_report {o_validation_report}")

        return (str(o_validationResult),o_default_schematron,o_validation_report) # Return value of validationResult is either 'True' or 'False' as text.
    # end def validate_reserve_input(self, input_to_osti):
# end class OSTOInputValidator:
