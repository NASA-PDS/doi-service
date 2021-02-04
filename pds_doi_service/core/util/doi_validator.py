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

from os.path import dirname, join
from lxml import etree

import requests

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import Doi, DoiStatus
from pds_doi_service.core.input.exceptions import (DuplicatedTitleDOIException,
                                                   IllegalDOIActionException,
                                                   SiteURLNotExistException,
                                                   TitleDoesNotMatchProductTypeException,
                                                   UnexpectedDOIActionException)
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

# Get the common logger and set the level for this file.
logger = get_logger('pds_doi_core.util.doi_validator')


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

    def __init__(self,db_name=None):
        self._config = self.m_doi_config_util.get_config()

        if db_name:
            # If database name is specified from user, use it.
            self.m_default_db_file = db_name
        else:
            # Default name of the database.
            self.m_default_db_file = self._config.get('OTHER', 'db_file')

        self._database_obj = DOIDataBase(self.m_default_db_file)

    def get_database_name(self):
        return self._database_obj.get_database_name()

    @staticmethod
    def __lidvid(columns, row):
        return f"{row[columns.index('lid')]}::{row[columns.index('vid')]}"

    def _check_field_site_url(self, doi: Doi):
        """
        If the site_url field exists in the doi object, check to see if it is
        online. If the site is not online, an exception will be thrown.
        """
        logger.debug(f"doi {doi}")
        logger.info(f"doi.site_url {doi.site_url}")

        if doi.site_url:
            try:
                response = requests.get(doi.site_url, timeout=5)
                status_code = response.status_code
                logger.debug(f"from_request:status_code,site_url {status_code,doi.site_url}")
                # Handle cases when a connection can be made to the server but
                # the status is greater than or equal to 400.
                if status_code >= 400:
                    # Need to check its an 404, 503, 500, 403 etc.
                    raise requests.HTTPError(f"status_code,site_url {status_code,doi.site_url}")
                else:
                    logger.debug(f"site_url {doi.site_url} indeed exists")
            except (requests.exceptions.ConnectionError, Exception):
                error_message = f"site_url {doi.site_url} not reachable"
                # Although not being able to connect is an error, the message
                # printed is a warning.
                logger.warning(error_message)
                raise SiteURLNotExistException(error_message)

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

            msg = (f"The title '{doi.title}' has already been used for a DOI "
                   f"by lidvid(s): {lidvids}, status: {status}, doi: {','.join(dois)}. " 
                   "You must use a different title.")
            logger.error(msg)
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

        logger.debug(f"product_type_specific_suffix: {product_type_specific_suffix}, "
                     f"doi.title: {doi.title}")

        if not product_type_specific_suffix.lower() in doi.title.lower():
            msg = (f"DOI with lidvid '{doi.related_identifier}' title '{doi.title}' "
                   f"does not contains product specific type suffix '{product_type_specific_suffix.lower()}'. "
                   "Product specific type suffix should be in the title.")
            logger.debug(msg)
            raise TitleDoesNotMatchProductTypeException(msg)

    def _check_field_lidvid_update(self, doi: Doi):
        """
        If DOI does not have a doi field, and action step is 'release' there is
        no DOI in sqllite database with the same lidvid and a DOI attribute.

        If lidvid exist and doi exist, throw an exception if action is 'release'
        If lidvid exist and doi exist, if action is not 'release', nothing to do.
        If lidvid does not exist, nothing to do.
        """
        # The database expects each field to be a list.
        query_criterias = {'lidvid': [doi.related_identifier]}

        # Query database for rows with given lidvid value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        rows_having_doi = [row for row in rows if row[columns.index('doi')]]

        if rows_having_doi:
            pre_existing_doi = {columns[i]: rows_having_doi[0][i]
                                for i in range(len(columns))}

            if doi.doi is None:
                raise IllegalDOIActionException(
                    f"There is already a DOI {pre_existing_doi['doi']} submitted "
                    f"for this lidvid {doi.related_identifier} "
                    f"(status={pre_existing_doi['status']}). "
                    "You cannot submit a new DOI for the same lidvid."
                )
            elif doi.doi != pre_existing_doi['doi']:
                raise IllegalDOIActionException(
                    f"There is already a DOI {pre_existing_doi['doi']} submitted "
                    f"for this lidvid {doi.related_identifier} "
                    f"(status={pre_existing_doi['status']}). "
                    f"You cannot update DOI {doi.doi} for the same lidvid.")

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

            # A status tuple of ('Pending',3) is higher than ('Draft',2) will cause an error.
            if self.m_workflow_order[prev_status.lower()] > self.m_workflow_order[doi.status.lower()]:
                msg = (
                    f"There is a DOI record {doi_str} with status: '{prev_status.lower()}'. "
                    f"Are you sure you want to restart the workflow from step "
                    f"'{doi.status}' for the lidvid: {doi.related_identifier}?"
                )

                logger.warning(msg)
                raise UnexpectedDOIActionException(msg)

    def validate_against_xsd(self, doi_label):
        # Given a DOI label, validate it against the XSD.
        # The fromstring() requires the parameter type to be bytes.
        # The encode() convert str to bytes.
        xml_file = etree.fromstring(doi_label.encode())

        xsd_filename = join(dirname(__file__), 'iad_schema.xsd')
        xml_validator = etree.XMLSchema(file=xsd_filename)

        # Perform the XSD validation.
        # The validate() function does not throw an exception, but merely
        # returns True or False.
        is_valid = xml_validator.validate(xml_file)
        logger.info(f"xsd_filename,is_valid {xsd_filename,is_valid}")

        # If DOI is not valid, use another method to get exactly where the
        # error(s) occurred.
        use_alternate_validation_method = True

        if not is_valid and use_alternate_validation_method:
            import xmlschema
            schema = xmlschema.XMLSchema(xsd_filename)

            # Save doi_label to disk so it can be compared to historical in next step.
            temporary_file_name = 'temp_doi_label_from_validate_against_xsd.xml'
            temporary_file_ptr = open(temporary_file_name, "w+")
            temporary_file_ptr.write(doi_label + "\n")
            temporary_file_ptr.close()
            logger.info(f"xsd_filename,is_valid,temporary_file_name "
                        f"{xsd_filename,is_valid,temporary_file_name}")

            # If the XSD fail to validate the DOI label, it will throw an exception and exit.
            # It will report where the error occurred. The error will have to be fixed.
            schema.validate(temporary_file_name)

    def validate(self, doi: Doi):
        """
        Given a Doi object, validate certain fields before sending them to OSTI
        or other data center(s). Exception(s) will be raised.
        """
        # TODO check id and doi fields are consistent.

        # Validate the site_url first to give the user a chance to make the correction.
        self._check_field_site_url(doi)
        self._check_field_title_duplicate(doi)
        self._check_field_title_content(doi)
        self._check_field_workflow(doi)

    def validate_osti_submission(self, doi: Doi):
        # do first the critical error check
        self._check_field_lidvid_update(doi)
        self.validate(doi)
