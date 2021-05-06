#!/usr/bin/env python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

import datetime
import unittest
import os

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import Doi, DoiStatus, ProductType
from pds_doi_service.core.input.exceptions import (DuplicatedTitleDOIException,
                                                   TitleDoesNotMatchProductTypeException,
                                                   IllegalDOIActionException,
                                                   UnexpectedDOIActionException)

from pds_doi_service.core.util.doi_validator import DOIValidator


class DoiValidatorTest(unittest.TestCase):
    # This file is removed in the beginning and at the end of these tests.
    db_name = 'doi_temp_for_doi_validator_unit_test.db'

    def setUp(self):
        self._database_obj = DOIDataBase(self.db_name)
        self._doi_validator = DOIValidator(db_name=self.db_name)

        self.lid = 'urn:nasa:pds:lab_shocked_feldspars'
        self.vid = '1.0'
        self.transaction_key = './transaction_history/img/2020-06-15T18:42:45.653317'
        self.release_date = datetime.datetime.now()
        self.transaction_date = datetime.datetime.now()
        self.status = DoiStatus.Draft
        self.title = 'Laboratory Shocked Feldspars Collection'
        self.product_type = ProductType.Collection
        self.product_type_specific = 'PDS4 Collection'
        self.submitter = 'test-submitter@jpl.nasa.gov'
        self.discipline_node = 'img'

        self.id = '21940'
        self.doi = '10.17189/' + self.id

        # Write a record into database
        # All fields are valid.
        self._database_obj.write_doi_info_to_database(
            self.lid, self.vid, self.transaction_key, self.doi,
            self.release_date, self.transaction_date,
            self.status, self.title, self.product_type,
            self.product_type_specific, self.submitter, self.discipline_node
        )

    def tearDown(self):
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)

    def test_draft_existing_title_new_lidvid_exception(self):
        """
        Test validation of 'draft' action with existing title and DOI but new a
        LIDVID. Expecting a DuplicatedTitleDOIException.
        """
        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid + '.1',
                      id=self.id,
                      doi=self.doi,
                      status=self.status)

        self.assertRaises(
            DuplicatedTitleDOIException, self._doi_validator.validate, doi_obj
        )

    def test_draft_new_title_new_lidvid_nominal(self):
        """
        Test validation of 'draft' action with new title but an existing DOI.
        Expecting no error: Allow to draft a new title with existing DOI.
        """
        doi_obj = Doi(title=self.title + ' (NEW)',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid + '.1',
                      id=self.id,
                      doi=self.doi,
                      status=self.status)

        self._doi_validator.validate(doi_obj)

    def test_draft_new_title_existing_lidvid_nominal(self):
        """
        Test validation of 'draft' action with a new title, and an existing
        DOI/LIDVID. Expecting no error: Allowed to draft a new title with
        existing LIDVID.
        """
        doi_obj = Doi(title=self.title + ' (NEW)',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status)

        self._doi_validator.validate(doi_obj)

    def test_title_does_not_match_product_type_exception(self):
        """
        Test validation of DOI with a non-matching title, existing DOI and
        existing LIDVID. Expecting TitleDoesNotMatchProductTypeException.
        """
        doi_obj = Doi(title='test title',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=self.status)

        self.assertRaises(
            TitleDoesNotMatchProductTypeException, self._doi_validator.validate, doi_obj
        )

    def test_title_does_match_product_type_nominal(self):
        """
        Test validation of DOI with matching title, existing DOI, and existing
        LIDVID. Expecting no error: The title matches the last token from
        product_type_specific.
        """
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
        """
        Test validation of 'release' action with existing title, new DOI, and
        existing LIDVID. Expecting IllegalDOIActionException.
        """
        doi_obj = Doi(title=self.title + ' different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi + '_new_doi',
                      status=self.status)

        self.assertRaises(
            IllegalDOIActionException, self._doi_validator.validate, doi_obj
        )

    def test_release_existing_lidvid_missing_doi(self):
        """
        Test validation of 'release' action with new title, no DOI, and an
        existing LIDVID. Expect IllegalDOIActionException.
        """
        doi_obj = Doi(title=self.title + 'different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      status=self.status)

        self.assertRaises(
            IllegalDOIActionException, self._doi_validator.validate, doi_obj
        )

    def test_workflow_sequence_exception(self):
        """
        Test validation of 'reserved' action with new title, existing DOI,
        existing LIDVID when DOI already exists with status 'draft'.
        Expect UnexpectedDOIActionException.
        """
        doi_obj = Doi(title=self.title + 'different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=DoiStatus.Reserved)

        self.assertRaises(
            UnexpectedDOIActionException, self._doi_validator.validate, doi_obj
        )

    def test_workflow_sequence_nominal(self):
        """
        Test validation of 'registered' action with new title, existing DOI,
        existing LIDVID when DOI already exists with status 'draft'.
        Expect no error since 'registered' is downstream from 'draft'.
        """
        doi_obj = Doi(title=self.title + 'different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id=self.id,
                      doi=self.doi,
                      status=DoiStatus.Registered)

        self._doi_validator.validate(doi_obj)


if __name__ == '__main__':
    unittest.main()
