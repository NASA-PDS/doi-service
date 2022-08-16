#!/usr/bin/env python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
import datetime
import os
import unittest

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiRecord
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.entities.exceptions import DuplicatedTitleDOIException
from pds_doi_service.core.entities.exceptions import IllegalDOIActionException
from pds_doi_service.core.entities.exceptions import InvalidIdentifierException
from pds_doi_service.core.entities.exceptions import InvalidRecordException
from pds_doi_service.core.entities.exceptions import SiteURLNotExistException
from pds_doi_service.core.entities.exceptions import TitleDoesNotMatchProductTypeException
from pds_doi_service.core.entities.exceptions import UnexpectedDOIActionException
from pds_doi_service.core.outputs.doi_validator import DOIValidator


class DoiValidatorTest(unittest.TestCase):
    # This file is removed in the beginning and at the end of these tests.
    db_name = "doi_temp_for_doi_validator_unit_test.db"

    def setUp(self):
        self._database_obj = DOIDataBase(self.db_name)
        self._doi_validator = DOIValidator(db_name=self.db_name)

        self.lid = "urn:nasa:pds:lab_shocked_feldspars"
        self.vid = "1.0"
        self.identifier = self.lid + "::" + self.vid
        self.transaction_key = "./transaction_history/img/2020-06-15T18:42:45.653317"
        self.release_date = datetime.datetime.now(tz=datetime.timezone.utc)
        self.transaction_date = datetime.datetime.now(tz=datetime.timezone.utc)
        self.status = DoiStatus.Draft
        self.title = "Laboratory Shocked Feldspars Collection"
        self.product_type = ProductType.Collection
        self.product_type_specific = "PDS4 Collection"
        self.submitter = "test-submitter@jpl.nasa.gov"
        self.discipline_node = "img"

        self.id = "21940"
        self.doi = "10.17189/" + self.id

        doi_record = DoiRecord(
            identifier=self.identifier,
            status=self.status,
            date_added=self.release_date,
            date_updated=self.transaction_date,
            submitter=self.submitter,
            title=self.title,
            type=self.product_type,
            subtype=self.product_type_specific,
            node_id=self.discipline_node,
            doi=self.doi,
            transaction_key=self.transaction_key,
            is_latest=True,
        )

        # Write a record into database
        # All fields are valid.
        self._database_obj.write_doi_info_to_database(doi_record)

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
        doi_obj = Doi(
            title=self.title,
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + "1.1",
            status=self.status,
        )

        with self.assertRaises(DuplicatedTitleDOIException):
            self._doi_validator._check_field_title_duplicate(doi_obj)

    def test_new_title_existing_doi_and_lidvid_nominal(self):
        """
        Test validation of a Doi object with a new title but an existing DOI
        and LIDVID pair.
        Expecting no error: Records may update their title as long as the
        DOI/LIDVID have not changed.
        """
        doi_obj = Doi(
            title=self.title + " (NEW)",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            id=self.id,
            doi=self.doi,
            status=self.status,
        )

        self._doi_validator._check_field_title_duplicate(doi_obj)

    def test_new_title_existing_lidvid_exception(self):
        """
        Test validation of a Doi object with a new title, and an existing
        LIDVID but no DOI (i.e. a reserve request).
        Expecting IllegalDOIActionException: cannot remove a DOI associated
        to an existing LIDVID.
        """
        doi_obj = Doi(
            title=self.title + " (NEW)",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            status=self.status,
        )

        with self.assertRaises(IllegalDOIActionException):
            self._doi_validator._check_for_preexisting_identifier(doi_obj)

    def test_title_does_not_match_product_type_exception(self):
        """
        Test validation of DOI with a non-matching title, existing DOI and
        existing LIDVID.
        Expecting TitleDoesNotMatchProductTypeException: product type is
        expected to be included with a title.
        """
        doi_obj = Doi(
            title="test title",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            id=self.id,
            doi=self.doi,
            status=self.status,
        )

        with self.assertRaises(TitleDoesNotMatchProductTypeException):
            self._doi_validator._check_field_title_content(doi_obj)

    def test_title_matches_product_type_nominal(self):
        """
        Test validation of DOI with existing DOI, and existing
        LIDVID, but an updated title that includes the product type.
        Expecting no error: title updates are allowed for existing DOI/LIDVID
        pairs, and title aligns with assigned product type.
        """
        doi_obj = Doi(
            title="test title " + self.product_type_specific,
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            id=self.id,
            doi=self.doi,
            status=self.status.lower(),
        )

        self._doi_validator._check_field_title_content(doi_obj)

    def test_existing_lidvid_no_doi_exception(self):
        """
        Test validation of a Doi object with a new title, no DOI assigned, and
        an existing LIDVID.
        Expecting ValueError: Must have a DOI assigned to perform this check.
        """
        doi_obj = Doi(
            title=self.title + " different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            id=self.id,
            doi=None,
            status=self.status,
        )

        with self.assertRaises(ValueError):
            self._doi_validator._check_for_preexisting_doi(doi_obj)

    def test_existing_lidvid_new_doi_exception(self):
        """
        Test validation of a Doi object with a new title, new DOI, and
        an existing LIDVID.
        Expecting IllegalDOIActionException: Each DOI may only be associated
        to a single PDS identifier value.
        """
        doi_obj = Doi(
            title=self.title + " different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            id=self.id,
            doi=self.doi + "_new_doi",
            status=self.status,
        )

        with self.assertRaises(IllegalDOIActionException):
            self._doi_validator._check_for_preexisting_identifier(doi_obj)

    def test_existing_doi_new_lidvid_exception(self):
        """
        Test validation of a Doi object with an existing title, existing DOI, and
        a new LIDVID.
        Expecting UnexpectedDOIActionException: DOI should only be associated to
        a single LIDVID.
        """
        doi_obj = Doi(
            title=self.title + " different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + "2.0",
            id=self.id,
            doi=self.doi,
            status=self.status,
        )

        with self.assertRaises(UnexpectedDOIActionException):
            self._doi_validator._check_for_preexisting_doi(doi_obj)

    def test_workflow_sequence_exception(self):
        """
        Test validation of Doi object with new title, existing DOI and
        LIDVID with the workflow status status 'unknown', when the existing
        entry is in 'draft'.
        Expecting UnexpectedDOIActionException: Unknown step is upstream
        of Draft step.
        """
        doi_obj = Doi(
            title=self.title + "different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            id=self.id,
            doi=self.doi,
            status=DoiStatus.Unknown,
        )

        with self.assertRaises(UnexpectedDOIActionException):
            self._doi_validator._check_field_workflow(doi_obj)

    def test_workflow_sequence_nominal(self):
        """
        Test validation of Doi object with new title, existing DOI and
        LIDVID with the workflow status status 'findable', when the existing
        entry is in 'draft'.
        Expecting no error: Findable step is downstream from Draft.
        """
        doi_obj = Doi(
            title=self.title + "different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            id=self.id,
            doi=self.doi,
            status=DoiStatus.Findable,
        )

        self._doi_validator._check_field_workflow(doi_obj)

    def test_identifier_validation_missing_pds_identifier(self):
        """
        Test validation of Doi object with missing PDS identifier.
        Expecting InvalidRecordException: Doi objects must always specify
        a PDS identifier to be valid.
        """
        doi_obj = Doi(
            title=self.title + " different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier="",
            id=self.id + "123",
            doi=self.doi + "123",
            status=DoiStatus.Draft,
        )

        with self.assertRaises(InvalidRecordException):
            self._doi_validator._check_identifier_fields(doi_obj)

    def test_identifier_validation_valid_lidvid(self):
        """
        Test validation of DOI object with various valid LIDVIDs
        Expecting no errors
        """
        doi_obj = Doi(
            title=self.title + " different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier="",
            status=DoiStatus.Draft,
        )

        # Test max valid identifier length
        partial_id = "urn:nasa:pds:lab_shocked_feldspars"
        doi_obj.pds_identifier = f"{partial_id}{'a'*(255 - len(partial_id))}"

        self._doi_validator._check_lidvid_field(doi_obj)

    def test_identifier_validation_invalid_lidvid(self):
        """
        Test validation of Doi object with various invalid LIDVIDs.
        Expecting InvalidLIDVIDException for each test.
        """
        doi_obj = Doi(
            title=self.title + " different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier="",
            status=DoiStatus.Draft,
        )

        # Test invalid starting token (must be urn)
        doi_obj.pds_identifier = "url:nasa:pds:lab_shocked_feldspars::1.0"

        with self.assertRaises(InvalidIdentifierException):
            self._doi_validator._check_lidvid_field(doi_obj)

        # Test invalid number of tokens (too few)
        doi_obj.pds_identifier = "url:nasa:pds::1.0"

        with self.assertRaises(InvalidIdentifierException):
            self._doi_validator._check_lidvid_field(doi_obj)

        # Test invalid number of tokens (too many)
        doi_obj.pds_identifier = "url:nasa:pds:lab_shocked_feldspars:collection_1:product_1:dataset_1::1.0"

        with self.assertRaises(InvalidIdentifierException):
            self._doi_validator._check_lidvid_field(doi_obj)

        # Test invalid field tokens (invalid mandatory values)
        doi_obj.pds_identifier = "not_urn:nasa:pds:lab_shocked_feldspars"

        with self.assertRaises(InvalidIdentifierException):
            self._doi_validator._check_lidvid_field(doi_obj)

        doi_obj.pds_identifier = "urn:not_nasa:pds:lab_shocked_feldspars"

        with self.assertRaises(InvalidIdentifierException):
            self._doi_validator._check_lidvid_field(doi_obj)

        doi_obj.pds_identifier = "urn:nasa:not_pds:lab_shocked_feldspars"

        with self.assertRaises(InvalidIdentifierException):
            self._doi_validator._check_lidvid_field(doi_obj)

        doi_obj.pds_identifier = "urn:nasa:pds:lab_$hocked_feldspars"

        with self.assertRaises(InvalidIdentifierException):
            self._doi_validator._check_lidvid_field(doi_obj)

        # Test invalid VID
        doi_obj.pds_identifier = "urn:nasa:pds:lab_shocked_feldspars::v1.0"

        with self.assertRaises(InvalidIdentifierException):
            self._doi_validator._check_lidvid_field(doi_obj)

        # Test invalid identifier length
        partial_id = "urn:nasa:pds:lab_shocked_feldspars"
        doi_obj.pds_identifier = f"{partial_id}{'a'*(256 - len(partial_id))}"

        with self.assertRaises(InvalidIdentifierException):
            self._doi_validator._check_lidvid_field(doi_obj)

    def test_identifier_validation_doi_id_mismatch(self):
        """
        Test validation of Doi with inconsistent doi and id fields.
        Expecting InvalidRecordException: doi and id fields should always
        be consistent.
        """
        doi_obj = Doi(
            title=self.title + " different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            id="1234",
            doi=self.doi,
            status=DoiStatus.Draft,
        )

        with self.assertRaises(InvalidRecordException):
            self._doi_validator._check_identifier_fields(doi_obj)

    def test_site_url_validation(self):
        """ """
        # Test with an unreachable (fake) URL
        doi_obj = Doi(
            title=self.title + " different",
            publication_date=self.transaction_date,
            product_type=self.product_type,
            product_type_specific=self.product_type_specific,
            pds_identifier=self.lid + "::" + self.vid,
            id="1234",
            doi=self.doi,
            status=DoiStatus.Draft,
            site_url="http://fakewebsite.fake",
        )

        with self.assertRaises(SiteURLNotExistException):
            self._doi_validator._check_field_site_url(doi_obj)

        # Now try again with a valid URL
        doi_obj.site_url = "http://www.google.com"

        self._doi_validator._check_field_site_url(doi_obj)


if __name__ == "__main__":
    unittest.main()
