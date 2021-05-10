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
                                                   InvalidRecordException,
                                                   InvalidLIDVIDException,
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

    def test_existing_title_new_lidvid_exception(self):
        """
        Test validation of a Doi object with an existing title but new a
        LIDVID.
        Expecting a DuplicatedTitleDOIException: titles should not
        be reused between different LIDVIDs.
        """
        doi_obj = Doi(title=self.title,
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + '1.1',
                      status=self.status)

        self.assertRaises(
            DuplicatedTitleDOIException, self._doi_validator.validate, doi_obj
        )

    def test_new_title_existing_doi_and_lidvid_nominal(self):
        """
        Test validation of a Doi object with a new title but an existing DOI
        and LIDVID pair.
        Expecting no error: Records may update their title as long as the
        DOI/LIDVID have not changed.
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

    def test_new_title_existing_lidvid_exception(self):
        """
        Test validation of a Doi object with a new title, and an existing
        LIDVID but no DOI.
        Expecting IllegalDOIActionException: cannot remove a DOI associated
        to an existing LIDVID.
        """
        doi_obj = Doi(title=self.title + ' (NEW)',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      status=self.status)

        self.assertRaises(
            IllegalDOIActionException, self._doi_validator.validate, doi_obj
        )

    def test_title_does_not_match_product_type_exception(self):
        """
        Test validation of DOI with a non-matching title, existing DOI and
        existing LIDVID.
        Expecting TitleDoesNotMatchProductTypeException: product type is
        expected to be included with a title.
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

    def test_title_matches_product_type_nominal(self):
        """
        Test validation of DOI with existing DOI, and existing
        LIDVID, but an updated title that includes the product type.
        Expecting no error: title updates are allowed for existing DOI/LIDVID
        pairs, and title aligns with assigned product type.
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

    def test_existing_lidvid_new_doi_exception(self):
        """
        Test validation of a Doi object with a new title, new DOI, and
        an existing LIDVID.
        Expecting IllegalDOIActionException: Each LIDVID may only be associated
        to a single DOI value.
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

    def test_existing_doi_new_lidvid_exception(self):
        """
        Test validation of a Doi object with an existing title, existing DOI, and
        a new LIDVID.
        Expecting IllegalDOIActionException: DOI may only be associated to
        a single LIDVID.
        """
        doi_obj = Doi(title=self.title + ' different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + '2.0',
                      id=self.id,
                      doi=self.doi,
                      status=self.status)

        self.assertRaises(
            IllegalDOIActionException, self._doi_validator.validate, doi_obj
        )

    def test_workflow_sequence_exception(self):
        """
        Test validation of Doi object with new title, existing DOI and
        LIDVID with the workflow status status 'reserved', when the existing
        entry is in 'draft'.
        Expecting UnexpectedDOIActionException: Reserve step is upstream
        of Draft step.
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
        Test validation of Doi object with new title, existing DOI and
        LIDVID with the workflow status status 'registered', when the existing
        entry is in 'draft'.
        Expecting no error: Registered step is downstream from Draft.
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

    def test_identifier_validation_missing_related_identifier(self):
        """
        Test validation of Doi object with missing related identifier.
        Expecting InvalidRecordException: Doi objects must always specify
        a related identifier to be valid.
        """
        doi_obj = Doi(title=self.title + ' different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier='',
                      id=self.id + '123',
                      doi=self.doi + '123',
                      status=DoiStatus.Reserved_not_submitted)

        self.assertRaises(
            InvalidRecordException, self._doi_validator.validate, doi_obj
        )

    def test_identifier_validation_invalid_lidvid(self):
        """
        Test validation of Doi object with various invalid LIDVIDs.
        Expecting InvalidLIDVIDException for each test.
        """
        doi_obj = Doi(title=self.title + ' different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier='',
                      status=DoiStatus.Reserved_not_submitted)

        # Test invalid starting token (must be urn)
        doi_obj.related_identifier = 'url:nasa:pds:lab_shocked_feldspars::1.0'

        self.assertRaises(
            InvalidLIDVIDException, self._doi_validator.validate, doi_obj
        )

        # Test invalid number of tokens (too few)
        doi_obj.related_identifier = 'url:nasa:pds::1.0'

        self.assertRaises(
            InvalidLIDVIDException, self._doi_validator.validate, doi_obj
        )

        # Test invalid number of tokens (too many)
        doi_obj.related_identifier = 'url:nasa:pds:lab_shocked_feldspars:collection_1:product_1:dataset_1::1.0'

        self.assertRaises(
            InvalidLIDVIDException, self._doi_validator.validate, doi_obj
        )

        # Test invalid field tokens (invalid characters)
        doi_obj.related_identifier = 'urn:nasa:_pds:lab_shocked_feldspars'

        self.assertRaises(
            InvalidLIDVIDException, self._doi_validator.validate, doi_obj
        )

        doi_obj.related_identifier = 'urn:nasa:pds:lab_$hocked_feldspars'

        self.assertRaises(
            InvalidLIDVIDException, self._doi_validator.validate, doi_obj
        )

        # Test invalid VID
        doi_obj.related_identifier = 'urn:nasa:pds:lab_shocked_feldspars::v1.0'

        self.assertRaises(
            InvalidLIDVIDException, self._doi_validator.validate, doi_obj
        )

    def test_identifier_validation_doi_id_mismatch(self):
        """
        Test validation of Doi with inconsistent doi and id fields.
        Expecting InvalidRecordException: doi and id fields should always
        be consistent.
        """
        doi_obj = Doi(title=self.title + ' different',
                      publication_date=self.transaction_date,
                      product_type=self.product_type,
                      product_type_specific=self.product_type_specific,
                      related_identifier=self.lid + '::' + self.vid,
                      id='1234',
                      doi=self.doi,
                      status=DoiStatus.Reserved_not_submitted)

        self.assertRaises(
            InvalidRecordException, self._doi_validator.validate, doi_obj
        )


if __name__ == '__main__':
    unittest.main()
