#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
=======================
osti_input_validator.py
=======================

Contains functions for validating the contents of an input OSTI XML label.
"""

from os.path import exists
from pkg_resources import resource_filename

from lxml import etree
from lxml import isoschematron

from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.input.exceptions import InputFormatException, CriticalDOIException

logger = get_logger('pds_doi_core.input.osti_input_util')


class OSTIInputValidator:
    """
    OSTIInputValidator provides some functions to validate the input to
    'release' action specific to OSTI. Other data centers may have a different
    format.
    """
    m_doi_config_util = DOIConfigUtil()

    def __init__(self):
        schematron_file = resource_filename(__name__, 'IAD3_scheematron.sch')

        if not exists(schematron_file):
            raise RuntimeError(
                'Could not find the schematron file needed by this module.\n'
                f'Expected schematron file: {schematron_file}'
            )

        sct_doc = etree.parse(schematron_file)
        self._schematron = isoschematron.Schematron(sct_doc, store_report=True)

    def validate_from_file(self, input_as_file):
        """
        Validates the input file that will be submitted to OSTI for the
        'release' action.
        """
        # The input is a file, read it into string and call self.validate()
        try:
            with open(input_as_file, mode='r') as f:
                input_to_osti = f.read()
            self.validate(input_to_osti)
        except Exception as e:
            raise CriticalDOIException(str(e))

    def validate(self, input_to_osti):
        """
        Validates the XML content that will be submitted to OSTI for the
        'release' action.

        :param input_to_osti: file containing text of XML document or the actual XML text
        """
        # The return from fromstring() function is an Element type and is the root.
        osti_root = etree.fromstring(input_to_osti.encode())

        # Validate the given input (as an etree document now) against the schematron.
        if not self._schematron.validate(osti_root):
            raise InputFormatException(self._schematron.validation_report)

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
            msg = (f"File {input_to_osti} cannot contain extraneous attribute(s) "
                   f"in main tag: {osti_root.keys()}")
            logger.error(msg)
            raise InputFormatException(msg)

        # Check 2. Bad tag(s) in <record> element, e.g. status='Release'.
        # It should only be in possible_status_list variable.
        possible_status_list = [
            DoiStatus.Draft, DoiStatus.Reserved, DoiStatus.Reserved_not_submitted,
            DoiStatus.Review, DoiStatus.Pending, DoiStatus.Registered
        ]
        record_count = 1  # In the world of OSTI, record_count starts at 1.
        for element in osti_root.findall('record'):
            if ('status' in element.keys()
                    and element.attrib['status'].lower() not in possible_status_list):
                msg = (f"If record tag contains 'status' its value must be one "
                       f"of these {possible_status_list}. "
                       f"Provided {element.attrib['status'].lower()}")
                logger.error(msg)
                raise InputFormatException(msg)

            # Keep track of which record working on for 'record' element.
            record_count += 1
