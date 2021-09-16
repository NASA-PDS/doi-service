#!/usr/bin/env python
import json
import os
import tempfile
import unittest
from os.path import abspath
from os.path import join

from pds_doi_service.core.actions.draft import DOICoreActionDraft
from pds_doi_service.core.actions.list import DOICoreActionList
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pkg_resources import resource_filename


class ListActionTestCase(unittest.TestCase):
    # TODO: add additional unit tests for other list query parameters

    def setUp(self):
        self.test_dir = resource_filename(__name__, "")
        self.input_dir = abspath(join(self.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))
        self.db_name = join(self.test_dir, "doi_temp.db")
        self._list_action = DOICoreActionList(db_name=self.db_name)
        self._draft_action = DOICoreActionDraft(db_name=self.db_name)
        self._release_action = DOICoreActionRelease(db_name=self.db_name)
        self._web_parser = DOIServiceFactory.get_web_parser_service()
        self._record_service = DOIServiceFactory.get_doi_record_service()

    def tearDown(self):
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)

    def test_list_by_status(self):
        """Test listing of entries, querying by workflow status"""
        # Submit a draft, then query by draft status to retrieve
        draft_kwargs = {
            "input": join(self.input_dir, "bundle_in_with_contributors.xml"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        doi_label = self._draft_action.run(**draft_kwargs)

        dois, _ = self._web_parser.parse_dois_from_label(doi_label)
        doi = dois[0]

        list_kwargs = {"status": DoiStatus.Draft}

        list_result = json.loads(self._list_action.run(**list_kwargs))

        self.assertEqual(len(list_result), 1)

        list_result = list_result[0]
        self.assertEqual(list_result["status"], doi.status)
        self.assertEqual(list_result["title"], doi.title)
        self.assertEqual(list_result["subtype"], doi.product_type_specific)
        self.assertEqual(list_result["identifier"], doi.related_identifier)

        # Now move the draft to review, use JSON as the format to ensure
        # this test works for both DataCite and OSTI
        doi_label = self._record_service.create_doi_record(dois, content_type="json")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as temp_file:
            temp_file.write(doi_label)
            temp_file.flush()

            review_kwargs = {
                "input": temp_file.name,
                "node": "img",
                "submitter": "my_user@my_node.gov",
                "force": True,
                "no_review": False,
            }

            review_json = self._release_action.run(**review_kwargs)

        dois, _ = self._web_parser.parse_dois_from_label(review_json, content_type="json")

        doi = dois[0]

        # Now query for review status
        list_kwargs = {"status": DoiStatus.Review}

        list_result = json.loads(self._list_action.run(**list_kwargs))

        self.assertEqual(len(list_result), 1)

        list_result = list_result[0]
        self.assertEqual(list_result["status"], doi.status)
        self.assertEqual(list_result["title"], doi.title)
        self.assertEqual(list_result["subtype"], doi.product_type_specific)
        self.assertEqual(list_result["identifier"], doi.related_identifier)

        # Finally, query for draft status again, should get no results back
        list_kwargs = {"status": DoiStatus.Draft}

        list_result = json.loads(self._list_action.run(**list_kwargs))

        self.assertEqual(len(list_result), 0)


if __name__ == "__main__":
    unittest.main()
