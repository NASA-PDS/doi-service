#!/usr/bin/env python

import json
import os
from os.path import abspath, join
import unittest

from lxml import etree
from pkg_resources import resource_filename

from pds_doi_service.core.outputs.osti import (CONTENT_TYPE_JSON,
                                               CONTENT_TYPE_XML,
                                               DOIOutputOsti)
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser


class OutputOstiTestCase(unittest.TestCase):
    """Unit tests for the osti.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, '')
        cls.input_dir = abspath(
            join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, 'input')
        )

    def test_create_osti_label_xml(self):
        """Test creation of an OSTI XML label from Doi objects"""
        # Parse sample input to obtain a Doi object
        input_xml_file = join(
            self.input_dir, 'DOI_Release_20200727_from_release.xml'
        )

        with open(input_xml_file, 'r') as infile:
            input_xml = infile.read()
            input_dois, _ = DOIOstiWebParser.parse_osti_response_xml(input_xml)

            # Now create an output label from the parsed Doi
            output_xml = DOIOutputOsti().create_osti_doi_record(
                input_dois, content_type=CONTENT_TYPE_XML
            )
            output_dois, _ = DOIOstiWebParser.parse_osti_response_xml(output_xml)

        # Massage the output a bit so we can do a straight dict comparison
        input_doi_fields = input_dois[0].__dict__
        output_doi_fields = output_dois[0].__dict__

        # Add/update dates are always overwritten when parsing Doi objects
        # from input labels, so remove these key/values from the comparison
        for date_key in ('date_record_added', 'date_record_updated'):
            input_doi_fields.pop(date_key, None)
            output_doi_fields.pop(date_key, None)

        self.assertDictEqual(input_doi_fields, output_doi_fields)

    def test_create_osti_label_json(self):
        """Test creation of an OSTI JSON label from Doi objects"""
        # Parse sample input to obtain a Doi object
        input_json_file = join(
            self.input_dir, 'DOI_Release_20210216_from_release.json'
        )

        with open(input_json_file, 'r') as infile:
            input_json = infile.read()
            dois, _ = DOIOstiWebParser.parse_osti_response_json(input_json)

            # Now create an output label from parsed Doi
            output_json = DOIOutputOsti().create_osti_doi_record(
                dois, content_type=CONTENT_TYPE_JSON
            )

        # Massage the output a bit so we can do a straight dict comparison
        input_json = json.loads(input_json)[0]
        output_json = json.loads(output_json)[0]

        # Add/update dates are always overwritten when parsing Doi objects
        # from input labels, so remove these key/values from the comparison
        for date_key in ('date_record_added', 'date_record_updated'):
            input_json.pop(date_key, None)
            output_json.pop(date_key, None)

        self.assertDictEqual(input_json, output_json)
