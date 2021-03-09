#!/usr/bin/env python

import datetime
import os
import unittest
from os.path import abspath, dirname, join
from unittest.mock import patch

import pds_doi_service.core.outputs.osti_web_client
from pds_doi_service.core.actions.check import DOICoreActionCheck
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.outputs.osti import CONTENT_TYPE_XML


class CheckActionTestCase(unittest.TestCase):
    test_dir = abspath(dirname(__file__))
    input_dir = abspath(
        join(test_dir, os.pardir, os.pardir, os.pardir, os.pardir, 'input')
    )

    @classmethod
    def setUp(cls):
        cls.db_name = join(cls.test_dir, 'doi_temp.db')
        cls._database_obj = DOIDataBase(cls.db_name)

        # Write a record with new doi into temporary database
        doi = '10.17189/29348'
        lid = 'urn:nasa:pds:lab_shocked_feldspars'
        vid = '1.0'
        transaction_key = './transaction_history/img/2020-06-15T18:42:45.653317'
        transaction_date = datetime.datetime.now()
        status = DoiStatus.Pending
        title = 'Laboratory Shocked Feldspars Bundle'
        product_type = 'Collection'
        product_type_specific = 'PDS4 Collection'
        discipline_node = 'img'
        submitter = 'img-submitter@jpl.nasa.gov'

        cls._database_obj.write_doi_info_to_database(
            lid, vid, transaction_key, doi, transaction_date, status,
            title, product_type, product_type_specific, submitter, discipline_node
        )

        # Create the check action and assign it our temp database
        cls._action = DOICoreActionCheck(cls.db_name)

    @classmethod
    def tearDown(cls):
        if os.path.exists(cls.db_name):
            os.remove(cls.db_name)

    def webclient_query_patch(self, i_url, query_dict=None, i_username=None,
                              i_password=None, content_type=CONTENT_TYPE_XML):
        """
        Patch for DOIOstiWebClient.webclient_query_doi().

        Allows a pending check to occur without actually having to communicate
        with the OSTI test server.
        """
        # Read an XML output label that corresponds to the DOI we're
        # checking for, and that has a status of 'registered'
        with open(join(CheckActionTestCase.input_dir,
                       'DOI_Release_20200727_from_release.xml'), 'r') as infile:
            xml_contents = infile.read()

        return xml_contents

    @patch.object(
        pds_doi_service.core.outputs.osti_web_client.DOIOstiWebClient,
        'webclient_query_doi', webclient_query_patch)
    def test_check_for_pending_entries(self):
        # By default, the DOICoreActionCheck will query for status = 'Pending'
        # in database record. The parameter query_criterias is for query
        # criteria that are different than the default ones.
        # The parameter to_send_mail_flag is set to True by default if not
        # specified.  We don't want to send out emails needlessly.
        # If desire to get the email, the parameter to_send_mail_flag can be set to True
        pending_records = self._action.run(to_send_mail_flag=False)

        self.assertEqual(len(pending_records), 1)

        pending_record = pending_records[0]

        self.assertEqual(pending_record['initial_status'], DoiStatus.Pending)
        self.assertEqual(pending_record['status'], DoiStatus.Registered)
        self.assertEqual(pending_record['submitter'], 'img-submitter@jpl.nasa.gov')
        self.assertEqual(pending_record['doi'], '10.17189/29348')


if __name__ == '__main__':
    unittest.main()
