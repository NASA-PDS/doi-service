#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import datetime
from lxml import etree
from lxml import isoschematron

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.input.osti_input_util')

class OSTIInputValidator:
    # This OSTIInputValidator provides some functions to validate the input to 'release' action specific to OSTI.  Other data center may have different format.

    m_doi_config_util = DOIConfigUtil()

    def __init__(self, db_name=None):
        self._config = self.m_doi_config_util.get_config()

        # Parse default schematron from config directory.  The self._schematron will be available for multiple calls to validate_release() function.
        # May need to make distinction later on if the schematron is for 'release' or 'deactivate'.
        self._default_schematron = self._config.get('OSTI', 'release_input_schematron')
        sct_doc = etree.parse(self._default_schematron)
        self._schematron = isoschematron.Schematron(sct_doc, store_report=True)

    def validate(self, input_to_osti):
        """
        Function validate the XML content that will be used to submit to OSTI for 'release' action.

        :param input_to_osti: file containing text of XML document
        :return:
        """

        # Parse input xml into an etree document. 
        osti_doc = etree.parse(input_to_osti)

        # Validate the given input (as an etree document now) against the schematron.
        o_validationResult = self._schematron.validate(osti_doc)

        # Get the validation report to be printed for debug. 
        o_validation_report = self._schematron.validation_report

        # Check conditions we cannot check via schematron:
        #
        #     1. Extraneous tags in <records> element. 
        #     2. Bad tag(s) in <record> element, e.g. status='Release'.  It should only be status='Pending'
        #     3. Bad date format.
        #
        # Once the record is submitted to OSTI, the 'Pending' status will be immediately returned and a few minutes later
        # changed to 'Registered'.

        osti_root= osti_doc.getroot()

        logger.debug(f"len(osti_root.keys()) {len(osti_root.keys())}")
        logger.debug(f"osti_root.keys() {osti_root.keys()}")

        # Check 1. Extraneous tags in <records> element. 
        if len(osti_root.keys()) > 0:
            o_validationResult = False
            logger.error(f"File {input_to_osti} cannot contain extraneous attribute(s) in main tag: {osti_root.keys() }")

        # Check 2. Bad tag(s) in <record> element, e.g. status='Release'.  It should only be status='Pending'
        # Check 3. Bad date formats.
        date_fields_to_check = ['publication_date','date_record_added','date_record_updated']
        record_count = 1  # In the world of OSTI, record_count starts at 1.
        for element in osti_root.iter():
            if element.tag == 'record':
              if 'status' in element.keys() and element.attrib['status'].lower() != 'pending':
                 o_validationResult = False
                 logger.error(f"If record tag contains 'status' its value must be 'Pending' in record {record_count}.")
              for field_to_check in date_fields_to_check:
                if element.xpath(field_to_check):
                    # If the field_to_check is provided, validate it, e.g 'publication_date'.
                    try:
                        datetime.datetime.strptime(element.xpath(field_to_check)[0].text, '%Y-%m-%d')
                    except ValueError:
                        o_validationResult = False
                        logger.error(f"Incorrect field '{field_to_check}' date field format, should be YYYY-MM-DD.  Provided value {element.xpath(field_to_check)[0].text} in record {record_count}.")

              record_count += 1  # Keep track of which record working on for 'record' element.
        # end for element in osti_root.iter():

        # The value of validationResult is either True or False as boolean type.
        logger.debug(f"{input_to_osti} is valid: {str(o_validationResult)}")
        logger.debug(f"o_validation_report {o_validation_report}")

        return (str(o_validationResult),self._default_schematron,o_validation_report) # Return value of validationResult is either 'True' or 'False' as text.
    # end def validate_reserve_input(self, input_to_osti):
# end class OSTOInputValidator:
