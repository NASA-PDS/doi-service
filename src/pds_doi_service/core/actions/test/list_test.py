#!/usr/bin/env python
import json
import os
import tempfile
import unittest
from os.path import abspath
from os.path import join
from unittest.mock import patch

import pds_doi_service.core.outputs.datacite.datacite_web_client
import pds_doi_service.core.outputs.osti.osti_web_client
from pds_doi_service.core.actions.list import DOICoreActionList
from pds_doi_service.core.actions.release import DOICoreActionRelease
from pds_doi_service.core.actions.reserve import DOICoreActionReserve
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.web_client import WEB_METHOD_POST
from pkg_resources import resource_filename


# TODO: add additional unit tests for other list query parameters
class ListActionTestCase(unittest.TestCase):
    _record_service = None
    _web_parser = None

    @classmethod
    def setUpClass(cls):
        cls.test_dir = resource_filename(__name__, "")
        cls.input_dir = abspath(join(cls.test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))
        cls.db_name = join(cls.test_dir, "doi_temp.db")
        cls._list_action = DOICoreActionList(db_name=cls.db_name)
        cls._reserve_action = DOICoreActionReserve(db_name=cls.db_name)
        cls._release_action = DOICoreActionRelease(db_name=cls.db_name)
        cls._web_parser = DOIServiceFactory.get_web_parser_service()
        cls._record_service = DOIServiceFactory.get_doi_record_service()

    @classmethod
    def tearDownClass(cls):
        if os.path.isfile(cls.db_name):
            os.remove(cls.db_name)

    def webclient_submit_patch(
        self, payload, url=None, username=None, password=None, method=WEB_METHOD_POST, content_type=CONTENT_TYPE_XML
    ):
        """
        Patch for DOIWebClient.submit_content().

        Allows a reserve to occur without actually submitting anything to the
        service provider's test server.
        """
        # Parse the DOI's from the input label, add a dummy DOI value,
        # and create the output label
        dois, _ = ListActionTestCase._web_parser.parse_dois_from_label(payload, content_type=CONTENT_TYPE_JSON)

        doi = dois[0]

        doi.doi = "10.17189/abc123"

        o_doi_label = ListActionTestCase._record_service.create_doi_record(doi, content_type=CONTENT_TYPE_JSON)

        return doi, o_doi_label

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "submit_content", webclient_submit_patch
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "submit_content",
        webclient_submit_patch,
    )
    def test_list_by_status(self):
        """Test listing of entries, querying by workflow status"""
        # Submit a reserve, then query by draft status to retrieve
        reserve_kwargs = {
            "input": join(self.input_dir, "bundle_in_with_contributors.xml"),
            "node": "img",
            "submitter": "my_user@my_node.gov",
            "force": True,
        }

        doi_label = self._reserve_action.run(**reserve_kwargs)

        dois, _ = self._web_parser.parse_dois_from_label(doi_label)
        doi = dois[0]

        list_kwargs = {"status": DoiStatus.Draft}

        list_result = json.loads(self._list_action.run(**list_kwargs))

        self.assertEqual(len(list_result), 1)

        list_result = list_result[0]
        self.assertEqual(list_result["status"], doi.status)
        self.assertEqual(list_result["title"], doi.title)
        self.assertEqual(list_result["subtype"], doi.product_type_specific)
        self.assertEqual(list_result["identifier"], doi.pds_identifier)

        # Now move the draft to review, use JSON as the format to ensure
        # this test works for both DataCite and OSTI
        doi_label = self._record_service.create_doi_record(dois, content_type=CONTENT_TYPE_JSON)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as temp_file:
            temp_file.write(doi_label)
            temp_file.flush()

            review_kwargs = {
                "input": temp_file.name,
                "node": "img",
                "submitter": "my_user@my_node.gov",
                "force": True,
                "review": True,
            }

            review_json = self._release_action.run(**review_kwargs)

        dois, _ = self._web_parser.parse_dois_from_label(review_json, content_type=CONTENT_TYPE_JSON)

        doi = dois[0]

        # Now query for review status
        list_kwargs = {"status": DoiStatus.Review}

        list_result = json.loads(self._list_action.run(**list_kwargs))

        self.assertEqual(len(list_result), 1)

        list_result = list_result[0]
        self.assertEqual(list_result["status"], doi.status)
        self.assertEqual(list_result["title"], doi.title)
        self.assertEqual(list_result["subtype"], doi.product_type_specific)
        self.assertEqual(list_result["identifier"], doi.pds_identifier)

        # Finally, query for draft status again, should get no results back
        list_kwargs = {"status": DoiStatus.Draft}

        list_result = json.loads(self._list_action.run(**list_kwargs))

        self.assertEqual(len(list_result), 0)


if __name__ == "__main__":
    unittest.main()
