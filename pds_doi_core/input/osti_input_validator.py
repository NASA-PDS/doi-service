#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import datetime
import os

from lxml import etree
from lxml import isoschematron

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.input.exceptions import InputFormatException, CriticalDOIException

logger = get_logger('pds_doi_core.input.osti_input_util')


class OSTIInputValidator:
    # This OSTIInputValidator provides some functions to validate the input to 'release' action specific to OSTI.  Other data center may have different format.

    m_doi_config_util = DOIConfigUtil()

    def __init__(self):
        self._config = self.m_doi_config_util.get_config()

        # Parse default schematron from config directory.  The self._schematron will be available for multiple calls to validate_release() function.
        # May need to make distinction later on if the schematron is for 'release' or 'deactivate'.
        self._default_schematron = self._config.get('OSTI', 'release_input_schematron')
        sct_doc = etree.parse(self._default_schematron)
        self._schematron = isoschematron.Schematron(sct_doc, store_report=True)

    def validate_from_file(self, input_as_file):
        """
        Function validate the input file that will be used to submit to OSTI for 'release' action.
        """
        # The input is a file, read it into string and call self.validate()
        try:
            with open(input_as_file, mode='r') as f:
                input_to_osti  = f.read()
            self.validate(input_to_osti)
        except Exception as e:
            raise CriticalDOIException(str(e))

        return 1

    def validate(self, input_to_osti):
        """
        Function validate the XML content that will be used to submit to OSTI for 'release' action.

        :param input_to_osti: file containing text of XML document or the actual XML text
        :return:
        """

        osti_root = etree.fromstring(input_to_osti.encode())
        osti_doc  = osti_root  # The returned from fromstring() function is an Element type and is the root.

        # Validate the given input (as an etree document now) against the schematron.
        if not self._schematron.validate(osti_doc):
            raise InputFormatException(self._schematron.validation_report)

        # Check conditions we cannot check via schematron:
        #
        #     1. Extraneous tags in <records> element. 
        #     2. Bad tag(s) in <record> element.
        #
        # Once the record is submitted to OSTI, the 'Pending' status will be immediately returned and a few minutes later
        # changed to 'Registered'.

        # Moved osti_root variable to above where the content of the tree is parsed either from a file or from a string.

        logger.debug(f"len(osti_root.keys()) {len(osti_root.keys())}")
        logger.debug(f"osti_root.keys() {osti_root.keys()}")

        # Check 1. Extraneous tags in <records> element. 
        if len(osti_root.keys()) > 0:
            msg = f"File {input_to_osti} cannot contain extraneous attribute(s) in main tag: {osti_root.keys()}"
            logger.error(msg)
            raise InputFormatException(msg)

        # Check 2. Bad tag(s) in <record> element, e.g. status='Release'.  It should only be in possible_status_list variable.
        possible_status_list = ['pending', 'registered', 'reserved', 'reserved_not_submitted']
        record_count = 1  # In the world of OSTI, record_count starts at 1.
        for element in osti_root.iter():
            if element.tag == 'record':
                if 'status' in element.keys() and element.attrib['status'].lower() not in possible_status_list:
                    msg = f"If record tag contains 'status' its value must be one of these {possible_status_list}.  Provided {element.attrib['status'].lower()}"
                    logger.error(msg)
                    raise InputFormatException(msg)
                record_count += 1  # Keep track of which record working on for 'record' element.
        # end for element in osti_root.iter():

        return 1

# end class OSTOInputValidator:
