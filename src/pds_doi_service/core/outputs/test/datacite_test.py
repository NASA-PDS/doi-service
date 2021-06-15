#!/usr/bin/env python

import os
from datetime import datetime
from os.path import abspath, join
import unittest

from pkg_resources import resource_filename

from pds_doi_service.core.entities.doi import ProductType, DoiStatus
from pds_doi_service.core.outputs.datacite.datacite_record import DOIDataCiteRecord
from pds_doi_service.core.outputs.datacite.datacite_web_parser import DOIDataCiteWebParser


class DOIDataCiteRecordTestCase(unittest.TestCase):
    """Unit tests for the datacite_record.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, '')
        cls.input_dir = abspath(
            join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, 'input')
        )

    def test_create_datacite_label_json(self):
        """Test creation of a DataCite JSON label from a Doi object"""
        # Parse sample input to obtain a Doi object
        input_json_file = join(
            self.input_dir, 'DOI_Release_20210615_from_reserve.json'
        )

        with open(input_json_file, 'r') as infile:
            input_json = infile.read()
            input_dois, _ = DOIDataCiteWebParser.parse_dois_from_label(input_json)

            # Now create an output label from the parsed Doi
            output_json = DOIDataCiteRecord().create_doi_record(input_dois[0])
            output_dois, _ = DOIDataCiteWebParser.parse_dois_from_label(output_json)

        # Massage the output a bit so we can do a direct comparison
        input_doi_fields = input_dois[0].__dict__
        output_doi_fields = output_dois[0].__dict__

        self.assertDictEqual(input_doi_fields, output_doi_fields)


class DOIODataCiteWebParserTestCase(unittest.TestCase):
    """Unit tests for the datacite_web_parser.py module"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, '')
        cls.input_dir = abspath(
            join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, 'input')
        )

        cls.expected_authors = [{'first_name': 'R.', 'last_name': 'Deen'},
                                {'first_name': 'H.', 'last_name': 'Abarca'},
                                {'first_name': 'P.', 'last_name': 'Zamani'},
                                {'first_name': 'J.', 'last_name': 'Maki'}]
        cls.expected_editors = [{'first_name': 'P. H.', 'last_name': 'Smith'},
                                {'first_name': 'M.', 'last_name': 'Lemmon'},
                                {'first_name': 'R. F.', 'last_name': 'Beebe'}]
        cls.expected_keywords = {'data', 'rdr', 'product', 'experiment', 'lander',
                                 'context', 'PDS', 'raw', 'mars', 'record', 'reduced',
                                 'science', 'edr', 'PDS4', 'camera', 'deployment',
                                 'insight', 'engineering'}

    def _compare_doi_to_expected(self, doi):
        """
        Helper method to test that both mandatory and optional fields from
        a parsed Doi match the expected values and/or formats.
        """
        self.assertListEqual(doi.authors, self.expected_authors)
        self.assertEqual(doi.contributor, 'Engineering')
        self.assertIsInstance(doi.date_record_added, datetime)
        self.assertIsInstance(doi.date_record_updated, datetime)
        self.assertEqual(doi.description,
                         'InSight Cameras Experiment Data Record (EDR) '
                         'and Reduced Data Record (RDR) Data Products')
        self.assertEqual(doi.doi, '10.13143/yzw2-vz66')
        self.assertListEqual(doi.editors, self.expected_editors)
        self.assertEqual(doi.id, 'yzw2-vz66')
        self.assertSetEqual(doi.keywords, self.expected_keywords)
        self.assertEqual(doi.product_type, ProductType.Dataset)
        self.assertEqual(doi.product_type_specific, 'PDS4 Refereed Data Bundle')
        self.assertIsInstance(doi.publication_date, datetime)
        self.assertEqual(doi.publisher, 'NASA Planetary Data System')
        self.assertEqual(doi.related_identifier,
                         'urn:nasa:pds:insight_cameras::1.0')
        # Check that site url HTML was un-escaped as expected
        self.assertIn('&', doi.site_url)
        self.assertNotIn('&amp;', doi.site_url)
        self.assertEqual(doi.status, DoiStatus.Draft)
        self.assertEqual(doi.title, 'InSight Cameras Bundle')

    def test_parse_osti_response_json(self):
        """Test parsing of an OSTI label in JSON format"""
        # Test with a nominal file containing most of the optional fields
        input_json_file = join(
            self.input_dir, 'DOI_Release_20210615_from_reserve.json'
        )

        with open(input_json_file, 'r') as infile:
            input_json = infile.read()
            dois, errors = DOIDataCiteWebParser.parse_dois_from_label(input_json)

        self.assertEqual(len(dois), 1)
        self.assertEqual(len(errors), 0)

        doi = dois[0]

        self._compare_doi_to_expected(doi)


if __name__ == '__main__':
    unittest.main()
