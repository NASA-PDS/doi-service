#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
================
doi_validator.py
================

Contains classes and functions for validation of DOI records and the overall
DOI workflow.
"""

import re

import requests

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import Doi, DoiStatus
from pds_doi_service.core.input.exceptions import (DuplicatedTitleDOIException,
                                                   IllegalDOIActionException,
                                                   InvalidRecordException,
                                                   InvalidLIDVIDException,
                                                   SiteURLNotExistException,
                                                   TitleDoesNotMatchProductTypeException,
                                                   UnexpectedDOIActionException)
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

# Get the common logger and set the level for this file.
logger = get_logger(__name__)

MIN_LID_FIELDS = 4
MAX_LID_FIELDS = 6
"""The expected minimum and maximum fields expected within a LID"""


class DOIValidator:
    m_doi_config_util = DOIConfigUtil()

    # The workflow_order dictionary contains the progression of the status of a DOI:
    m_workflow_order = {
        DoiStatus.Reserved_not_submitted: 0,
        DoiStatus.Reserved: 1,
        DoiStatus.Draft: 2,
        DoiStatus.Review: 3,
        DoiStatus.Pending: 4,
        DoiStatus.Registered: 5
    }

    def __init__(self, db_name=None):
        self._config = self.m_doi_config_util.get_config()

        if db_name:
            # If database name is specified from user, use it.
            self.m_default_db_file = db_name
        else:
            # Default name of the database.
            self.m_default_db_file = self._config.get('OTHER', 'db_file')

        self._database_obj = DOIDataBase(self.m_default_db_file)

    @staticmethod
    def __lidvid(columns, row):
        lid = row[columns.index('lid')]
        vid = row[columns.index('vid')]

        if lid and vid:
            return f"{row[columns.index('lid')]}::{row[columns.index('vid')]}"

        return lid

    def _check_field_site_url(self, doi: Doi):
        """
        If the site_url field exists in the doi object, check to see if it is
        online. If the site is not online, an exception will be thrown.
        """
        logger.debug("doi,site_url: %s,%s", doi, doi.site_url)

        if doi.site_url and doi.site_url != 'N/A':
            try:
                response = requests.get(doi.site_url, timeout=5)
                status_code = response.status_code
                logger.debug("from_request status_code,site_url: %s,%s",
                             status_code, doi.site_url)

                # Handle cases when a connection can be made to the server but
                # the status is greater than or equal to 400.
                if status_code >= 400:
                    # Need to check its an 404, 503, 500, 403 etc.
                    raise requests.HTTPError(f"status_code,site_url {status_code,doi.site_url}")
                else:
                    logger.debug("site_url %s indeed exists", doi.site_url)
            except (requests.exceptions.ConnectionError, Exception):
                raise SiteURLNotExistException(f"site_url {doi.site_url} not reachable")

    def _check_field_title_duplicate(self, doi: Doi):
        """
        Check if the same title exists already in local database for a different
        lidvid.
        """
        query_criterias = {'title': [doi.title]}

        # Query database for rows with given title value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        # keep rows with same title BUT different lidvid
        rows_with_different_lidvid = [
            row for row in rows
            if self.__lidvid(columns, row) != doi.related_identifier
        ]

        if rows_with_different_lidvid:
            lidvids = ','.join([self.__lidvid(columns, row)
                                for row in rows_with_different_lidvid])
            status = ','.join([row[columns.index('status')]
                               for row in rows_with_different_lidvid])

            # Note that it is possible for rows_with_different_lidvid to have
            # some elements while 'doi' field is None. It needs to be checked.
            dois = []

            # Due to the fact that 'doi' field can be None, each field must be
            # inspected before the join operation otherwise will cause indexing error.
            for row in rows_with_different_lidvid:
                if row[columns.index('doi')]:
                    dois.append(row[columns.index('doi')])
                else:
                    dois.append('None')

            msg = (f"The title '{doi.title}' has already been used for records "
                   f"{lidvids}, status: {status}, doi: {','.join(dois)}. " 
                   "You must use a different title.")

            raise DuplicatedTitleDOIException(msg)

    def _check_field_title_content(self, doi: Doi):
        """
        Check if the pds4 label is a bundle then the title should contain bundle
        (ignoring case).

        The same for: dataset, collection, document
        Otherwise we raise a warning.
        """
        product_type_specific_split = doi.product_type_specific.split(' ')

        # The suffix should be the last field in the product_type_specific so
        # if it has many tokens, check the last one.
        product_type_specific_suffix = (product_type_specific_split[-1]
                                        if len(product_type_specific_split) > 1
                                        else '<<< no product specific type found >>> ')

        logger.debug("product_type_specific_suffix: %s", product_type_specific_suffix)
        logger.debug("doi.title: %s", doi.title)

        if not product_type_specific_suffix.lower() in doi.title.lower():
            msg = (f"DOI with lidvid '{doi.related_identifier}' title "
                   f"'{doi.title}' does not contains product specific type "
                   f"suffix '{product_type_specific_suffix.lower()}'. "
                   "Product specific type suffix should be in the title.")

            raise TitleDoesNotMatchProductTypeException(msg)

    def _check_doi_for_existing_lidvid(self, doi: Doi):
        """
        For the LIDVID assigned to the provided Doi object, check the following:

        * If the provided Doi object does not have a doi field assigned, check
          if there is a pre-existing transaction for the LIDVID that does have
          a doi field already assigned.

        * If the provided Doi object has a doi field assigned, check that
          the latest transaction for the same LIDVID has a matching doi.

        Parameters
        ----------
        doi : Doi
            The Doi object to validate.

        Raises
        ------
        IllegalDOIActionException
            If either check fails.

        """
        # The database expects each field to be a list.
        query_criterias = {'lidvid': [doi.related_identifier]}

        # Query database for rows with given lidvid value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        rows_having_doi = [row for row in rows if row[columns.index('doi')]]

        if rows_having_doi:
            pre_existing_doi = dict(zip(columns, rows_having_doi[0]))

            if doi.doi is None:
                raise IllegalDOIActionException(
                    f"There is already a DOI {pre_existing_doi['doi']} submitted "
                    f"for record identifier {doi.related_identifier} "
                    f"(status={pre_existing_doi['status']}).\n"
                    "You cannot update/remove a DOI for an existing record identifier."
                )
            elif doi.doi != pre_existing_doi['doi']:
                raise IllegalDOIActionException(
                    f"There is already a DOI {pre_existing_doi['doi']} submitted "
                    f"for record identifier {doi.related_identifier} "
                    f"(status={pre_existing_doi['status']}).\n"
                    f"You cannot update DOI {doi.doi} for an existing record identifier."
                )

    def _check_lidvid_for_existing_doi(self, doi: Doi):
        """
        For Doi objects with DOI already assigned, ensure the DOI value is
        not already in use for a different LIDVID.

        Parameters
        ----------
        doi : Doi
            The Doi object to validate.

        Raises
        ------
        IllegalDOIActionException
            If the check fails.

        """
        if doi.doi:
            # The database expects each field to be a list.
            query_criterias = {'doi': [doi.doi]}

            # Query database for rows with given DOI value (should only ever be
            # at most one)
            columns, rows = self._database_obj.select_latest_rows(query_criterias)

            if rows and doi.related_identifier != self.__lidvid(columns, rows[0]):
                raise IllegalDOIActionException(
                    f"The DOI ({doi.doi}) provided for record identifier "
                    f"{doi.related_identifier} is already in use for record "
                    f"{self.__lidvid(columns, rows[0])}.\nThe DOI may not be "
                    f"reused with a different record identifier."
                )

    def _check_identifier_fields(self, doi: Doi):
        """
        Checks the fields of a Doi object used for identification for consistency
        and validity.

        Parameters
        ----------
        doi : Doi
            The parsed Doi object to validate

        Raises
        ------
        InvalidDOIException
            If any of the identifier field checks fail

        """
        # Make sure we have an identifier to key off of
        if not doi.related_identifier:
            raise InvalidRecordException(
                'Record provided with missing related_identifier field. '
                'Please ensure a LIDVID or similar identifier is provided for '
                'all DOI requests.'
            )

        # Make sure the doi and id fields are consistent, if present
        if doi.doi and doi.id:
            prefix, suffix = doi.doi.split('/')

            if suffix != doi.id:
                raise InvalidRecordException(
                    f'Record for {doi.related_identifier} has inconsistent '
                    f'DOI ({doi.doi}) and ID ({doi.id}) fields. Please reconcile '
                    'the inconsistency and resubmit the request.'
                )

    def _check_lidvid_field(self, doi: Doi):
        """
        Checks the related_identifier field of a Doi to ensure it conforms
        to the LIDVID format.

        Parameters
        ----------
        doi : Doi
            The parsed Doi object to validate

        Raises
        ------
        InvalidLIDVIDException
            If the related identifier field of the DOI does not conform to
            the LIDVID format. These exceptions should be able to be bypassed
            when the --force flag is provided.

        """

        if '::' in doi.related_identifier:
            lid, vid = doi.related_identifier.split('::')
        else:
            lid = doi.related_identifier
            vid = None

        lid_tokens = lid.split(':')

        try:
            # Make sure we got a URN
            if lid_tokens[0] != 'urn':
                raise InvalidLIDVIDException('LIDVID must start with "urn"')

            # Make sure we got the minimum number of fields, and that
            # the number of fields is consistent with the product type
            if not MIN_LID_FIELDS <= len(lid_tokens) <= MAX_LID_FIELDS:
                raise InvalidLIDVIDException(
                    f'LIDVID must contain only between {MIN_LID_FIELDS} '
                    f'and {MAX_LID_FIELDS} colon-delimited fields, '
                    f'got {len(lid_tokens)} field(s)'
                )

            # Now check each field for the expected set of characters
            token_regex = re.compile(r'[a-z0-9][a-z0-9-._]{0,31}')

            for index, token in enumerate(lid_tokens):
                if not token_regex.fullmatch(token):
                    raise InvalidLIDVIDException(
                        f'LIDVID field {index + 1} ({token}) is invalid. '
                        f'Fields must begin with a letter or digit, and only '
                        f'consist of letters, digits, hyphens (-), underscores (_) '
                        f'or periods (.)'
                    )

            # Finally, make sure the VID conforms to a version number
            version_regex = re.compile(r'^\d+\.\d+$')

            if vid and not version_regex.fullmatch(vid):
                raise InvalidLIDVIDException(
                    f'Parsed VID ({vid}) does not conform to a valid version identifier. '
                    'Version identifier must consist only of a major and minor version '
                    'joined with a period (ex: 1.0)'
                )
        except InvalidLIDVIDException as err:
            raise InvalidLIDVIDException(
                f'The record identifier {doi.related_identifier} (DOI {doi.doi}) '
                f'does not conform to a valid LIDVID format.\n'
                f'Reason: {str(err)}\n'
                'If the identifier is not intended to be a LIDVID, use the '
                'force option to bypass the results of this check.'
            )

    def _check_field_workflow(self, doi: Doi):
        """
        Check that there is not a record in the sqllite database with same
        lidvid but a higher status than the current action (see workflow_order)
        """
        if doi.status.lower() not in self.m_workflow_order:
            msg = (f"Unexpected DOI status of '{doi.status.lower()}' from label. "
                   f"Valid values are {[DoiStatus(key).value for key in self.m_workflow_order.keys()]}")
            logger.error(msg)
            raise UnexpectedDOIActionException(msg)

        # The database expects each field to be a list.
        query_criterias = {'lidvid': [doi.related_identifier]}

        # Query database for rows with given lidvid value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        if rows:
            row = rows[0]
            doi_str = row[columns.index('doi')]
            prev_status = row[columns.index('status')]

            # A status tuple of ('Pending',3) is higher than ('Draft',2) will
            # cause an error.
            if self.m_workflow_order[prev_status.lower()] > self.m_workflow_order[doi.status.lower()]:
                msg = (
                    f"There is a DOI record {doi_str} with status: '{prev_status.lower()}'. "
                    f"Are you sure you want to restart the workflow from step "
                    f"'{doi.status}' for the lidvid: {doi.related_identifier}?"
                )

                raise UnexpectedDOIActionException(msg)

    def validate(self, doi: Doi):
        """
        Given a Doi object, validate certain fields before sending them to OSTI
        or other data center(s). Exception(s) will be raised.
        """
        self._check_doi_for_existing_lidvid(doi)
        self._check_lidvid_for_existing_doi(doi)
        self._check_identifier_fields(doi)
        self._check_lidvid_field(doi)
        self._check_field_site_url(doi)
        self._check_field_title_duplicate(doi)
        self._check_field_title_content(doi)
        self._check_field_workflow(doi)
