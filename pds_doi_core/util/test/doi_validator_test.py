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
from pds_doi_core.input.exeptions import DuplicatedTitleDOIException, InvalidDOIException, IllegalDOIActionException, UnexpectedDOIActionException
 
from pds_doi_core.util.doi_validator import DOIValidator

from pds_doi_core.util.general_util import get_logger

logger = get_logger(__name__)

# This function remove_test_artifact() is outside of the class to allow access to the removal of a test artifact.
def remove_test_artifact(db_name):
    if os.path.isfile(db_name):
        os.remove(db_name)
        logger.info(f"Removed test artifact database file {db_name}")
    else:
        logger.info(f"File not exist, test artifact database file {db_name}")

class MyTestCase(unittest.TestCase):

    # A note about the names of the tests:
    #
    #     For some strange reason, unittest module run the tests in alphabetical order.
    #     Since we wish to run the test in the order in this file, there is test at the end test_all_tests() that will run all the tests in the specified order.

    db_name = 'doi_temp_for_doi_validator_unit_test.db'  # This file is removed in the beginning and at the end of these tests.

    @classmethod
    def set_initial_states(self):
        logger.info("RUNNING_TEST: set_initial_states")

        # This function should be called from the first test to remove any test artifacts and set up some records.

        self._database_obj = DOIDataBase(self.db_name)
        self._doi_validator = DOIValidator(db_name=self.db_name)

        # This should be done before any testing.
        remove_test_artifact(self.db_name)

        # Use the setUp() function to initializes many fields and write the initial record.
        self.setUp()

        # Write a record into database
        # The value of 'doi', 'lid', 'vid' fields are None.  Other later calls write_doi_info_to_database() to write other records with valid 'doi' field.
        # (lid,vid,transaction_key,doi,transaction_date,status,title,product_type,product_type_specific,submitter,discipline_node)
        self._database_obj.write_doi_info_to_database(None, None, self.transaction_key, None, self.transaction_date,
                                                      self.status, self.title, self.product_type, self.product_type_specific,
                                                      self.submitter, self.discipline_node)

        logger.info("Writing a record to database file {self.db_name}.")

    @classmethod
    def setUp(self):
        # This setUp() function is called for every test.
        logger.info(f"setUp() called")

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

    def _test_draft_existing_title_no_doi(self):

        logger.info("RUNNING_TEST:_test_draft_existing_title_no_doi")
        logger.info("Test validation of 'draft' action with existing title, no 'DOI' minted yet.  Expect no error.")

        # *** This should be the first test in this file due to initial writing of the record.
        self.set_initial_states()

        # Create a Doi object so it can be validated
        # Since 'doi' already taken up, use 'doi_obj' as variable name.
        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=None,
                      doi=None,
                      status=self.status.lower())
 
        action_name = 'draft'
        self._doi_validator.validate(doi_obj,action_name)

    def _test_draft_existing_title_existing_doi(self):
        logger.info("RUNNING_TEST:_test_draft_existing_title_existing_doi")
        logger.info("Test validation of 'draft' action with existing title, existing DOI.  Expect DuplicatedTitleDOIException.")
        # Write another record this time with a valid 'lid', 'vid', and 'doi' fields (DOI has been minted)

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        # The value of 'doi' field now valid
        self._database_obj.write_doi_info_to_database(self.lid, self.vid, self.transaction_key, self.doi, self.transaction_date,
                                                      self.status, self.title, self.product_type, self.product_type_specific,
                                                      self.submitter, self.discipline_node)




        action_name = 'draft'
        self.assertRaises(DuplicatedTitleDOIException,self._doi_validator.validate,doi_obj,action_name)

    def _test_draft_existing_title_existing_doi_duplicate_exception(self):
        logger.info("RUNNING_TEST:_test_draft_existing_title_existing_doi_duplicate_exception")
        logger.info("Test validation of 'draft' action with existing title, existing DOI.  Expecting DuplicatedTitleDOIException and will catch it.")

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'draft'
        self.assertRaises(DuplicatedTitleDOIException,self._doi_validator.validate,doi_obj,action_name)

    def _test_reserve_existing_title_existing_doi_duplicate_exception(self):
        logger.info("RUNNING_TEST:_test_reserve_existing_title_existing_doi_duplicate_exception")
        logger.info("Test validation of 'reserve' action with existing title, existing DOI.  Expect DuplicatedTitleDOIException.")
        # Expecting DuplicatedTitleDOIException raised because cannot reserve an existing DOI with same title.

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'reserve'
        self.assertRaises(DuplicatedTitleDOIException,self._doi_validator.validate,doi_obj,action_name)

    def _test_reserve_existing_title_no_doi(self):
        logger.info("RUNNING_TEST:_test_reserve_existing_title_no_doi")
        logger.info("Test validation of 'reserve' action with existing title, non-existing DOI.  Expect no error.")
        # Reset all initial states.
        self.set_initial_states()

        # Expecting no error since no DOI exist yet for existing title.

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'reserve'
        self._doi_validator.validate(doi_obj,action_name)

    def _test_reserve_existing_title_existing_doi_duplicate_title(self):
        logger.info("RUNNING_TEST:_test_reserve_existing_title_existing_doi_duplicate_title")
        logger.info("Test validation of 'reserve' action with existing title, existing DOI  Expect DuplicatedTitleDOIException.")
        # Expecting DuplicatedTitleDOIException because title already been used for same lidvid and doi fields.

        # The value of 'lid', 'vid' and 'doi' fields are now valid in the database.
        self._database_obj.write_doi_info_to_database(self.lid, self.vid, self.transaction_key, self.doi, self.transaction_date,
                                                      self.status, self.title, self.product_type, self.product_type_specific,
                                                      self.submitter, self.discipline_node)

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'reserve'
        self.assertRaises(DuplicatedTitleDOIException,self._doi_validator.validate,doi_obj,action_name)

    def _test_reserve_existing_title_existing_doi_existing_lidvid(self):
        logger.info("RUNNING_TEST:_test_reserve_existing_title_existing_doi_existing_lidvid")
        logger.info("Test validation of 'reserve' action with existing title, existing DOI, existing lidvid.  Expect DuplicatedTitleDOIException.")

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'reserve'
        self.assertRaises(DuplicatedTitleDOIException,self._doi_validator.validate,doi_obj,action_name)

    def _test_reserve_new_title_existing_doi_new_lidvid(self):
        logger.info("RUNNING_TEST:_test_reserve_new_title_existing_doi_new_lidvid")
        logger.info("Test validation of 'reserve' action with existing new title, existing DOI, new lidvid.  Expect no error.")
        # Expecting no error because title is new and lidvid is new.

        new_title = self.title + ': a new title'
        new_related_identifier = self.lid + '::' + self.vid + '_a_new_lidvid'
        doi_obj = Doi(title=new_title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=new_related_identifier,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'reserve'
        self._doi_validator.validate(doi_obj,action_name)

    def _test_reserve_new_title_existing_doi_existing_lidvid(self):
        logger.info("RUNNING_TEST:_test_reserve_new_title_existing_doi_existing_lidvid")
        logger.info("Test validation of 'reserve' action with new title, existing DOI, existing lidvid.  Expect no error.")
        # Expect no error because reserving existing lidvid with new title.

        doi_obj = Doi(title=self.title + ': a new title',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'reserve'
        self._doi_validator.validate(doi_obj,action_name)

    # Deleted test_AAA_reserve_008() since it is performing the same test as test_AAA_reserve_007().

    def _test_reserve_existing_title_different_doi_existing_lidvid(self):
        logger.info("RUNNING_TEST:_test_reserve_existing_title_different_doi_existing_lidvid")
        logger.info("Test validation of 'reserve' action with same title, different DOI, existing lidvid.  Expect DuplicatedTitleDOIException.")
        # Expecting DuplicatedTitleDOIException because there is already a DOI with same 'title'.

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi + '_new',  # Make the 'doi' field different than the one in database.
                      status=self.status.lower())

        action_name = 'reserve'
        self.assertRaises(DuplicatedTitleDOIException,self._doi_validator.validate,doi_obj,action_name)

    def _test_release_existing_title_existing_doi_existing_lidvid(self):
        logger.info("RUNNING_TEST:_test_release_existing_title_existing_doi_existing_lidvid")
        logger.info("Test validation of 'release' action with existing title, existing DOI, existing lidvid.  Expect no error.")
        # Expecting no error because merely updating some metadata of existing doi.

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'release'
        self._doi_validator.validate(doi_obj,action_name)

    def _test_release_new_title_existing_doi_existing_lidvid(self):
        logger.info("RUNNING_TEST:_test_release_new_title_existing_doi_existing_lidvid")
        logger.info("Test validation of 'release' action with new title, existing DOI, existing lidvid.  Expect no error.")
        # Expecting no error because merely updating some metadata of existing doi.

        doi_obj = Doi(title=self.title + ': a new title',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'release'
        self._doi_validator.validate(doi_obj,action_name)

    def _test_release_new_title_existing_doi_new_lidvid(self):
        logger.info("RUNNING_TEST:_test_release_new_title_existing_doi_new_lidvid")
        logger.info("Test validation of 'release' action with new title, existing DOI, new lidvid.  Expect no error.")
        # Expecting no error because merely updating some metadata of existing doi.

        doi_obj = Doi(title=self.title + ': a new title',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid + '_new_lidvid',
                      id=self.id,
                      doi=self.doi,
                      status=self.status.lower())

        action_name = 'release'
        self._doi_validator.validate(doi_obj,action_name)

    def test_release_existing_title_new_doi_existing_lidvid(self):
        logger.info("RUNNING_TEST:_test_release_new_title_existing_doi_new_lidvid")
        logger.info("Test validation of 'release' action with existing title, new DOI, existing lidvid.  Expect IllegalDOIActionException.")
        # Expecting IllegalDOIActionException because attempt to release an existing lidvid, existing title but different doi than the one in database.
        # To make it valid, the doi being updated should be the same in database.

        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi + '_new_doi',
                      status=self.status.lower())

        action_name = 'release'
        self.assertRaises(IllegalDOIActionException,self._doi_validator.validate,doi_obj,action_name)

    def _test_last(self):
        logger.info("RUNNING_TEST:_test_last")

        # *** This should be the last test in this file due to the removal of the test artifact. ***

        remove_test_artifact(self.db_name)

        return 1

    def test_all_tests(self):
        # Run all tests in this order.

        self._test_draft_existing_title_no_doi()
        self._test_draft_existing_title_existing_doi()
        self._test_draft_existing_title_existing_doi_duplicate_exception()
        self._test_reserve_existing_title_existing_doi_duplicate_exception()
        self._test_reserve_existing_title_no_doi()
        self._test_reserve_existing_title_existing_doi_duplicate_title()
        self._test_reserve_existing_title_existing_doi_existing_lidvid()
        self._test_reserve_new_title_existing_doi_new_lidvid()
        self._test_reserve_new_title_existing_doi_existing_lidvid()
        self._test_reserve_existing_title_different_doi_existing_lidvid()
        self._test_release_existing_title_existing_doi_existing_lidvid()
        self._test_release_new_title_existing_doi_existing_lidvid()
        self._test_release_new_title_existing_doi_new_lidvid()
        self._test_last()

if __name__ == '__main__':
    unittest.main()
