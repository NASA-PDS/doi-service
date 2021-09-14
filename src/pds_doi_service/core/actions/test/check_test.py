#!/usr/bin/env python
import configparser
import datetime
import os
import signal
import subprocess
import tempfile
import time
import unittest
from email import message_from_bytes
from os.path import abspath
from os.path import dirname
from os.path import join
from unittest.mock import patch

import pds_doi_service.core.outputs.datacite.datacite_web_client
import pds_doi_service.core.outputs.osti.osti_web_client
from pds_doi_service.core.actions import DOICoreActionCheck
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.service import SERVICE_TYPE_DATACITE
from pds_doi_service.core.outputs.service import SERVICE_TYPE_OSTI
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pkg_resources import resource_filename


class CheckActionTestCase(unittest.TestCase):
    test_dir = resource_filename(__name__, "")
    input_dir = abspath(join(test_dir, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, "input"))

    @classmethod
    def setUp(cls):
        cls.db_name = join(cls.test_dir, "doi_temp.db")
        cls._database_obj = DOIDataBase(cls.db_name)

        # Write a record with new doi into temporary database
        doi = "10.17189/29348"
        lid = "urn:nasa:pds:lab_shocked_feldspars"
        vid = "1.0"
        identifier = lid + "::" + vid
        transaction_key = "./transaction_history/img/2020-06-15T18:42:45.653317"
        date_added = datetime.datetime.now()
        date_updated = datetime.datetime.now()
        status = DoiStatus.Pending
        title = "Laboratory Shocked Feldspars Bundle"
        product_type = ProductType.Collection
        product_type_specific = "PDS4 Collection"
        discipline_node = "img"
        submitter = "img-submitter@jpl.nasa.gov"

        cls._database_obj.write_doi_info_to_database(
            identifier,
            transaction_key,
            doi,
            date_added,
            date_updated,
            status,
            title,
            product_type,
            product_type_specific,
            submitter,
            discipline_node,
        )

        # Create the check action and assign it our temp database
        cls._action = DOICoreActionCheck(cls.db_name)

    @classmethod
    def tearDown(cls):
        if os.path.exists(cls.db_name):
            os.remove(cls.db_name)

    def webclient_query_patch_nominal(
        self, query, url=None, username=None, password=None, content_type=CONTENT_TYPE_XML
    ):
        """
        Patch for DOIWebClient.query_doi().

        Allows a pending check to occur without actually having to communicate
        with the test server.

        This version simulates a successful registration response from the
        appropriate service provider.
        """
        # Read an output label that corresponds to the DOI we're
        # checking for, and that has a status of 'registered' or 'findable'
        if DOIServiceFactory.get_service_type() == SERVICE_TYPE_OSTI:
            label = join(CheckActionTestCase.input_dir, "DOI_Release_20200727_from_register.xml")
        else:
            label = join(CheckActionTestCase.input_dir, "DOI_Release_20210615_from_release.json")

        with open(label, "r") as infile:
            label_contents = infile.read()

        return label_contents

    def webclient_query_patch_error(self, query, url=None, username=None, password=None, content_type=CONTENT_TYPE_XML):
        """
        Patch for DOIWebClient.query_doi().

        Allows a pending check to occur without actually having to communicate
        with the OSTI test server.

        This version simulates an erroneous registration response from the
        service provider.
        """
        # Read an output label that corresponds to the DOI we're
        # checking for, and that has a status of 'error'
        with open(join(CheckActionTestCase.input_dir, "DOI_Release_20200727_from_error.xml"), "r") as infile:
            xml_contents = infile.read()

        return xml_contents

    def webclient_query_patch_no_change(
        self, query, url=None, username=None, password=None, content_type=CONTENT_TYPE_XML
    ):
        """
        Patch for DOIOstiWebClient.query_doi().

        Allows a pending check to occur without actually having to communicate
        with the OSTI test server.

        This version simulates an response that is still pending release.
        """
        # Read an output label that corresponds to the DOI we're
        # checking for, and that has a status of 'pending'
        with open(join(CheckActionTestCase.input_dir, "DOI_Release_20200727_from_release.xml"), "r") as infile:
            xml_contents = infile.read()

        return xml_contents

    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "query_doi", webclient_query_patch_nominal
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "query_doi",
        webclient_query_patch_nominal,
    )
    def test_check_for_pending_entries(self):
        """Test check action that returns a successfully registered entry"""
        pending_records = self._action.run(email=False)

        self.assertEqual(len(pending_records), 1)

        pending_record = pending_records[0]

        self.assertEqual(pending_record["previous_status"], DoiStatus.Pending)
        self.assertIn(pending_record["status"], (DoiStatus.Registered, DoiStatus.Findable))
        self.assertEqual(pending_record["submitter"], "img-submitter@jpl.nasa.gov")
        self.assertEqual(pending_record["doi"], "10.17189/29348")
        self.assertEqual(pending_record["identifier"], "urn:nasa:pds:lab_shocked_feldspars::1.0")

    @unittest.skipIf(
        DOIServiceFactory.get_service_type() == SERVICE_TYPE_DATACITE, "DataCite does not return errors via label"
    )
    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "query_doi", webclient_query_patch_error
    )
    def test_check_for_pending_entries_w_error(self):
        """Test check action that returns an error result"""
        pending_records = self._action.run(email=False)

        self.assertEqual(len(pending_records), 1)

        pending_record = pending_records[0]

        self.assertEqual(pending_record["previous_status"], DoiStatus.Pending)
        self.assertEqual(pending_record["status"], DoiStatus.Error)
        self.assertEqual(pending_record["submitter"], "img-submitter@jpl.nasa.gov")
        self.assertEqual(pending_record["doi"], "10.17189/29348")
        self.assertEqual(pending_record["identifier"], "urn:nasa:pds:lab_shocked_feldspars::1.0")

        # There should be a message to go along with the error
        self.assertIsNotNone(pending_record["message"])

    @unittest.skipIf(
        DOIServiceFactory.get_service_type() == SERVICE_TYPE_DATACITE,
        "DataCite does not assign a pending state to release requests",
    )
    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "query_doi", webclient_query_patch_no_change
    )
    def test_check_for_pending_entries_w_no_change(self):
        """Test check action when no pending entries have been updated"""
        pending_records = self._action.run(email=False)

        self.assertEqual(len(pending_records), 1)

        pending_record = pending_records[0]

        self.assertEqual(pending_record["previous_status"], DoiStatus.Pending)
        self.assertEqual(pending_record["status"], DoiStatus.Pending)
        self.assertEqual(pending_record["submitter"], "img-submitter@jpl.nasa.gov")
        self.assertEqual(pending_record["doi"], "10.17189/29348")
        self.assertEqual(pending_record["identifier"], "urn:nasa:pds:lab_shocked_feldspars::1.0")

    def get_config_patch(self):
        """
        Return a modified default config that points to a local test smtp
        server for use with the email test
        """
        parser = configparser.ConfigParser()

        # default configuration
        conf_default = "conf.ini.default"
        conf_default_path = abspath(join(dirname(__file__), os.pardir, os.pardir, "util", conf_default))

        parser.read(conf_default_path)
        parser["OTHER"]["emailer_local_host"] = "localhost"
        parser["OTHER"]["emailer_port"] = "1025"

        parser = DOIConfigUtil._resolve_relative_path(parser)

        return parser

    @patch.object(pds_doi_service.core.util.config_parser.DOIConfigUtil, "get_config", get_config_patch)
    @patch.object(
        pds_doi_service.core.outputs.osti.osti_web_client.DOIOstiWebClient, "query_doi", webclient_query_patch_nominal
    )
    @patch.object(
        pds_doi_service.core.outputs.datacite.datacite_web_client.DOIDataCiteWebClient,
        "query_doi",
        webclient_query_patch_nominal,
    )
    def test_email_receipt(self):
        """Test sending of the check action status via email"""
        # Create a new check action so our patched config is pulled in
        action = DOICoreActionCheck(self.db_name)

        with tempfile.TemporaryFile() as temp_file:
            # Stand up a subprocess running a debug smtpd server
            # By default, all this server is does is echo email payloads to
            # standard out, so provide a temp file to capture it
            debug_email_proc = subprocess.Popen(
                ["python", "-u", "-m", "smtpd", "-n", "-c", "DebuggingServer", "localhost:1025"], stdout=temp_file
            )

            # Give the debug smtp server a chance to start listening
            time.sleep(1)

            try:
                # Run the check action and have it send an email w/ attachment
                action.run(email=True, attachment=True, submitter="email-test@email.com")

                # Read the raw email contents (payload) from the subprocess
                # into a string
                temp_file.seek(0)
                email_contents = temp_file.read()
                message = message_from_bytes(email_contents).get_payload()
            finally:
                # Send the debug smtp server a ctrl+C and wait for it to stop
                os.kill(debug_email_proc.pid, signal.SIGINT)
                debug_email_proc.wait()

        # Run some string searches on the email body to ensure what we expect
        # made it in

        # Email address provided to check action should be present
        self.assertIn("email-test@email.com", message)

        # Subject line should be present
        self.assertIn("DOI Submission Status Report For Node", message)

        # Attachment should also be provided
        self.assertIn("Content-Disposition: attachment; filename=doi_status_", message)


if __name__ == "__main__":
    unittest.main()
