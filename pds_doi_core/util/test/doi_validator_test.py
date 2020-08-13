#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import datetime
import unittest
import os
import sys

from pds_doi_core.db.doi_database import DOIDataBase
from pds_doi_core.entities.doi import Doi
from pds_doi_core.input.exceptions  import DuplicatedTitleDOIException, \
    TitleDoesNotMatchProductTypeException, \
    IllegalDOIActionException, \
    UnexpectedDOIActionException
 
from pds_doi_core.util.doi_validator import DOIValidator

from pds_doi_core.util.general_util import get_logger

logger = get_logger(__name__)


class MyTestCase(unittest.TestCase):

    # A note about the names of the tests:
    #
    #     For some strange reason, unittest module run the tests in alphabetical order.
    #     Since we wish to run the test in the order in this file, there is test at the end test_all_tests() that will run all the tests in the specified order.

    db_name = 'doi_temp_for_doi_validator_unit_test.db'  # This file is removed in the beginning and at the end of these tests.

    def setUp(self):
        # This setUp() function is called for every test.
        logger.info(f"setUp() called")

        # This function should be called from the first test to remove any test artifacts and set up some records.

        self._database_obj = DOIDataBase(self.db_name)
        self._doi_validator = DOIValidator(db_name=self.db_name)

        self.lid = 'urn:nasa:pds:lab_shocked_feldspars'
        self.vid = '1.0'
        self.transaction_key = './transaction_history/img/2020-06-15T18:42:45.653317'
        self.transaction_date = datetime.datetime.now()
        self.status = 'Draft'
        self.title = 'Laboratory Shocked Feldspars Collection'  # Change the title so it matches the value of 'product_type' as Collection otherwise tests will fail.
        self.product_type = 'Collection'
        self.product_type_specific = 'PDS4 Collection'
        self.submitter = 'Qui.T.Chau@jpl.nasa.gov'
        self.discipline_node = 'img'

        self.id = '21940'
        self.doi = '10.17189/' + self.id

        # Write a record into database
        # The value of 'doi', 'lid', 'vid' fields are None.  Other later calls write_doi_info_to_database() to write other records with valid 'doi' field.
        # (lid,vid,transaction_key,doi,transaction_date,status,title,product_type,product_type_specific,submitter,discipline_node)
        self._database_obj.write_doi_info_to_database(self.lid, self.vid, self.transaction_key, self.doi,
                                                      self.transaction_date,
                                                      self.status, self.title, self.product_type,
                                                      self.product_type_specific,
                                                      self.submitter, self.discipline_node)

        logger.info("Writing a record to database file {self.db_name}.")


    def tearDown(self):
        logger.info("RUNNING_TEST:_test_last")
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)
            logger.info(f"Removed test artifact database file {self.db_name}")
        else:
            logger.info(f"File not exist, test artifact database file {self.db_name}")

        return 1


    def test_draft_existing_title_new_lidvid_exception(self):
        logger.info("RUNNING_TEST:_test_draft_existing_title_existing_doi_duplicate_exception")
        logger.info("Test validation of 'draft' action with existing title, existing DOI.  Expecting DuplicatedTitleDOIException and will catch it.")

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid+'1',
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        self.assertRaises(DuplicatedTitleDOIException,self._doi_validator.validate,doi_obj)

    def test_draft_new_title_new_lidvid_nominal(self):
        logger.info("RUNNING_TEST:_test_draft_existing_title_existing_doi_duplicate_exception")
        logger.info(
            "Test validation of 'draft' action with existing title, existing DOI.  Expecting DuplicatedTitleDOIException and will catch it.")

        doi_obj = Doi(title=self.title + '111',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid + '1',
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        self._doi_validator.validate(doi_obj)


    def test_draft_new_title_existing_lidvid_nominal(self):
        logger.info("RUNNING_TEST:_test_draft_existing_title_existing_doi_duplicate_exception")
        logger.info(
            "Test validation of 'draft' action with existing title, existing DOI.  Expecting DuplicatedTitleDOIException and will catch it.")

        doi_obj = Doi(title=self.title + ' 111',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        self._doi_validator.validate(doi_obj)

    def test_title_does_not_match_product_type_exception(self):

        doi_obj = Doi(title='test title',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        self.assertRaises(TitleDoesNotMatchProductTypeException,self._doi_validator.validate,doi_obj)

    def test_title_does_match_product_type_nominal(self):

        doi_obj = Doi(title='test title ' + self.product_type_specific,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())
        self._doi_validator.validate(doi_obj)


    def test_release_existing_lidvid_new_doi(self):
        logger.info("RUNNING_TEST:_test_release_new_title_existing_doi_new_lidvid")
        logger.info("Test validation of 'release' action with existing title, new DOI, existing lidvid.  Expect IllegalDOIActionException.")
        # Expecting IllegalDOIActionException because attempt to release an existing lidvid, existing title but different doi than the one in database.
        # To make it valid, the doi being updated should be the same in database.

        doi_obj = Doi(title=self.title + 'different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi + '_new_doi',
                      status=self.status.lower())

        action_name = 'release'
        self.assertRaises(IllegalDOIActionException,self._doi_validator.validate_release,doi_obj)

    def test_release_existing_lidvid_missing_doi(self):
        logger.info("RUNNING_TEST:_test_release_new_title_existing_doi_new_lidvid")
        logger.info(
            "Test validation of 'release' action with existing title, new DOI, existing lidvid.  Expect IllegalDOIActionException.")
        # Expecting IllegalDOIActionException because attempt to release an existing lidvid, existing title but different doi than the one in database.
        # To make it valid, the doi being updated should be the same in database.

        doi_obj = Doi(title=self.title + 'different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=None,
                      doi=None,
                      status=self.status.lower())

        self.assertRaises(IllegalDOIActionException, self._doi_validator.validate_release, doi_obj)


    def test_workflow_sequence_exception(self):

        doi_obj = Doi(title=self.title + 'different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status='reserved')

        self.assertRaises(UnexpectedDOIActionException, self._doi_validator.validate, doi_obj)

    def test_workflow_sequence_nominal(self):

        doi_obj = Doi(title=self.title + 'different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status='registered')

        self._doi_validator.validate(doi_obj)




if __name__ == '__main__':
    unittest.main()
