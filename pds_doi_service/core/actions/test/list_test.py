#!/usr/bin/env python

import json
import os
from os.path import abspath, dirname, join
import unittest
import tempfile

from pds_doi_service.core.actions.draft import DOICoreActionDraft
from pds_doi_service.core.actions.list import DOICoreActionList
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser


class ListActionTestCase(unittest.TestCase):
    # TODO: add additional unit tests for other list query parameters

    def setUp(self):
        self.test_dir = abspath(dirname(__file__))
        self.input_dir = abspath(
            join(self.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, 'input')
        )
        self.db_name = join(self.test_dir, 'doi_temp.db')
        self._list_action = DOICoreActionList(db_name=self.db_name)
        self._draft_action = DOICoreActionDraft(db_name=self.db_name)
        self._release_action = DOICoreActionRelease(db_name=self.db_name)

    def tearDown(self):
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)

    def test_list_by_status(self):
        """Test listing of entries, querying by workflow status"""
        # Submit a draft, then query by draft status to retrieve
        draft_kwargs = {
            'input': join(self.input_dir, 'bundle_in_with_contributors.xml'),
            'node': 'img',
            'submitter': 'my_user@my_node.gov',
            'force': True
        }

        draft_xml = self._draft_action.run(**draft_kwargs)

        dois, _ = DOIOstiWebParser.parse_osti_response_xml(draft_xml)
        doi = dois[0]

        list_kwargs = {
            'status': DoiStatus.Draft
        }

        list_result = json.loads(self._list_action.run(**list_kwargs))

        self.assertEqual(len(list_result), 1)

        list_result = list_result[0]
        self.assertEqual(list_result['status'], doi.status)
        self.assertEqual(list_result['title'], doi.title)
        self.assertEqual(list_result['subtype'], doi.product_type_specific)
        self.assertEqual(list_result['lid'] + '::' + list_result['vid'],
                         doi.related_identifier)

        # Now move the draft to review
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml') as temp_file:
            temp_file.write(draft_xml)
            temp_file.flush()

            review_kwargs = {
                'input': temp_file.name,
                'node': 'img',
                'submitter': 'my_user@my_node.gov',
                'force': True,
                'no_review': False
            }

            review_json = self._release_action.run(**review_kwargs)

        dois, _ = DOIOstiWebParser.parse_osti_response_json(review_json)
        doi = dois[0]

        # Now query for review status
        list_kwargs = {
            'status': DoiStatus.Review
        }

        list_result = json.loads(self._list_action.run(**list_kwargs))

        self.assertEqual(len(list_result), 1)

        list_result = list_result[0]
        self.assertEqual(list_result['status'], doi.status)
        self.assertEqual(list_result['title'], doi.title)
        self.assertEqual(list_result['subtype'], doi.product_type_specific)
        self.assertEqual(list_result['lid'] + '::' + list_result['vid'],
                         doi.related_identifier)

        # Finally, query for draft status again, should get no results back
        list_kwargs = {
            'status': DoiStatus.Draft
        }

        list_result = json.loads(self._list_action.run(**list_kwargs))

        self.assertEqual(len(list_result), 0)


if __name__ == '__main__':
    unittest.main()
