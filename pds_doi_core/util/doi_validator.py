#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------

from pds_doi_core.db.doi_database import DOIDataBase
from pds_doi_core.entities.doi import Doi
from pds_doi_core.input.exeptions import DuplicatedTitleDOIException, InvalidDOIException, IllegalDOIActionException, UnexpectedDOIActionException, TitleDoesNotMatchProductTypeException
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.util.doi_validator')

class DOIValidator:
    m_doi_config_util = DOIConfigUtil()

    # The workflow_order dictionary contains the progression of the status of a DOI:
    m_workflow_order = {'reserved_not_submitted': 0,
                        'reserved'  : 1,
                        'draft'     : 2,
                        'pending'   : 3,
                        'registered': 4}

    def __init__(self,db_name=None):
        self._config = self.m_doi_config_util.get_config()
        if db_name:
            self.m_default_db_file    = db_name # If database name is specified from user, use it.
        else:
            self.m_default_db_file    = self._config.get('OTHER','db_file')   # Default name of the database.
        self._database_obj = DOIDataBase(self.m_default_db_file)

    def get_database_name(self):
        return(self._database_obj.get_database_name())

    def _check_field_title_duplicate(self, doi: Doi,action):
        """ Check if the same title exist already in local database with a DOI.
            If the same title exist but no DOI minted yet, nothing to be done.
            If the same title exist and a DOI has been minted, throw an exception if action is not 'release'
            because we want to allow the 'release' action on the same DOI so the metadata can be updated.
            If no title exist, nothing to be done.
        """
        query_criterias = {}
        query_criterias['title'] = [doi.title]  # The database expect each field to be a list.

        # Query database for rows with given title value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        col_index_to_doi     = columns.index('doi')
        col_index_to_lid     = columns.index('lid')
        col_index_to_vid     = columns.index('vid')
        col_index_to_status  = columns.index('status')
        last_row_index       = len(rows) - 1

        # If there are rows with same title and 'lid' and 'vid' fields exist in database.
        if len(rows) > 0 and (rows[last_row_index][col_index_to_lid] and rows[last_row_index][col_index_to_vid]):
            col_index_to_doi     = columns.index('doi')
            col_index_to_lid     = columns.index('lid')
            col_index_to_vid     = columns.index('vid')
            col_index_to_status  = columns.index('status')

            lidvid = rows[last_row_index][col_index_to_lid] + '::' + rows[last_row_index][col_index_to_vid]
            if doi.related_identifier == lidvid:   # If 'lidvid' field exist already with the same title, throw an exception.
                col_index_to_title   = columns.index('title')

                if action != 'release':
                        logger.error(f"The title: '{doi.title}' has already been used for a DOI by lidvid:{lidvid}, status: {rows[last_row_index][col_index_to_status]} , doi: {rows[last_row_index][col_index_to_doi]} . You must use a different title.")
                        raise DuplicatedTitleDOIException(f"The title: '{doi.title}' has already been used for a DOI by lidvid:{lidvid}, status: {rows[last_row_index][col_index_to_status]} , doi: {rows[last_row_index][col_index_to_doi]}. You must use a different title.")

        return 1

    def _check_field_title_content(self, doi: Doi):
        """ Check if the pds4 label is a bundle the title should contain bundle (ignoring case)
            The same for: dataset, collection, document
            Otherwise we raise a warning.
        """

        if doi.product_type.lower() == 'bundle' and 'bundle' not in doi.title.lower():
            logger.warning(f"A 'bundle' product type should contain 'Bundle' in the title.")
            raise TitleDoesNotMatchProductTypeException("A 'bundle' product type should contain 'Bundle' in the title.")
        elif doi.product_type.lower() == 'collection' and 'collection' not in doi.title.lower():
            logger.warning(f"A 'collection' product type should contain 'Collection' in the title.")
            raise TitleDoesNotMatchProductTypeException("A 'collection' product type should contain 'Collection' in the title.")
        elif doi.product_type.lower() == 'dataset' and 'dataset' not in doi.title.lower():
            logger.warning(f"A 'dataset' product type should contain 'Dataset' in the title.")
            raise TitleDoesNotMatchProductTypeException("A 'dataset' product type should contain 'Dataset' in the title.")
        elif doi.product_type.lower() == 'document' and 'document' not in doi.title.lower():
            logger.warning(f"A 'document' product type should contain 'Document' in the title.")
            raise TitleDoesNotMatchProductTypeException("A 'document' product type should contain 'Document' in the title.")

        return 1

    def _check_field_lidvid_update(self, doi: Doi, action):
        """ If DOI does not have a doi field, and action step is 'release' there is no DOI in sqllite database with the same lidvid and a DOI attribute.
            if lidvid exist and doi exist, throw an exception if action is 'release'
            if lidvid exist and doi exist, if action is not 'release', nothing to do.
            if lidvid does not exist, nothing to do.
        """

        query_criterias = {}
        query_criterias['lidvid'] = [doi.related_identifier]  # The database expect each field to be a list.

        # Query database for rows with given lidvid value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        # The number of times the same lidvid used is the number of rows.  It should be either 0 or 1.
        num_times_lidvid_used = len(rows)

        col_index_to_doi     = columns.index('doi')
        col_index_to_status  = columns.index('status')

        if num_times_lidvid_used > 0:
            last_row_index       = num_times_lidvid_used - 1
            col_index_to_title   = columns.index('title')
            col_index_to_lid     = columns.index('lid')
            col_index_to_vid     = columns.index('vid')

            lidvid = rows[last_row_index][col_index_to_lid] + '::' + rows[last_row_index][col_index_to_vid]
            if rows[last_row_index][col_index_to_doi] is None:
                # Case A: If database does not have a doi field, and action step is 'release'.
                if action == 'release':
                    # Field 'lidvid' has been used but a 'doi' field has not been minted, cannot release the DOI.
                    raise IllegalDOIActionException(f"There is already a DOI submitted for this lidvid (status={rows[last_row_index][col_index_to_status]}). You cannot submit a new DOI for the same lidvid.") 
            elif doi.doi != rows[last_row_index][col_index_to_doi]:
              # Case B: If DOI does indeed exist in database but it is different than the one updating.
              # Essentially does not allow a 'release' action on the same lidvid but different doi.
              if action == 'release':
                  raise IllegalDOIActionException(f"There is already a DOI submitted for this lidvid {doi.related_identifier} (status={rows[last_row_index][col_index_to_status]}). You cannot submit a new DOI for the same lidvid.")

        return 1

    def _check_field_workflow(self, doi: Doi):
        """ There is not record in the sqllite database with same lidvid but a higher status than the current action (see workflow_order)
        """

        query_criterias = {}
        query_criterias['lidvid'] = [doi.related_identifier]  # The database expect each field to be a list.

        # Query database for rows with given lidvid value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        # The number of times the same lidvid used is the number of rows.  It should be either 0 or 1.

        num_times_lidvid_used = len(rows)

        if doi.status.lower() not in self.m_workflow_order:
            logger.error(f"Unexpected status of doi {doi.status.lower()} from label.  Valid values are {self.m_workflow_order.keys()}")
            raise InvalidDOIException(f"Unexpected status of doi {doi.status.lower()} from label.  Valid values are {self.m_workflow_order.keys()}")

        if num_times_lidvid_used > 0:
            last_row_index       = num_times_lidvid_used - 1
            col_index_to_doi     = columns.index('doi')
            col_index_to_lid     = columns.index('lid')
            col_index_to_vid     = columns.index('vid')
            col_index_to_status  = columns.index('status')
            lidvid = rows[last_row_index][col_index_to_lid] + '::' + rows[last_row_index][col_index_to_vid]
            if rows[last_row_index][col_index_to_status].lower() not in self.m_workflow_order:
                logger.error(f"Unexpected status of doi {rows[last_row_index][col_index_to_status].lower()} from database.  Valid values are {self.m_workflow_order.keys()}")
                raise InvalidDOIException(f"Unexpected status of doi {rows[last_row_index][col_index_to_status].lower()} from database.  Valid values are {self.m_workflow_order.keys()}")

            # Translate the 'status' field into a ranking in the workflow, e.g. 'Draft' to 2
            rank_current_doi_status = self.m_workflow_order[doi.status.lower()]

            # Translate the 'status' field of same lidvid in database into a ranking in the workflow, e.g. 'Pending' to 3
            rank_database_doi_status = self.m_workflow_order[rows[last_row_index][col_index_to_status].lower()]

            # A status tuple of ('Pending',3) is higher than ('Draft',2) will cause an error.
            if rank_database_doi_status > rank_current_doi_status:
                logger.error(f"There is a DOI: {rows[last_row_index][col_index_to_doi]} record which status: '{rows[last_row_index][col_index_to_status].lower()}'.  Are you sure you want to restart the workflow from step: {rank_current_doi_status} for the lidvid: {doi.related_identifier}?")
                raise UnexpectedDOIActionException(f"There is a DOI: {rows[last_row_index][col_index_to_doi]} record which status: '{rows[last_row_index][col_index_to_status].lower()}'.  Are you sure you want to restart the workflow from step: {rank_current_doi_status} for the lidvid: {doi.related_identifier}?")

        return 1

    def validate(self, doi: Doi, action):
        """ Given a Doi object, validate certain fields before sending them to OSTI or other data center(s).
            Exception(s) will be raised."""

        # Check 1: Check if the same title exist already in local database with a DOI.
        #    If the same title exist but no DOI minted yet, nothing to be done.
        #    If the same title exist and a DOI has been minted, throw an exception if action is not 'release'
        #    because we want to allow the 'release' action on the same DOI so the metadata can be updated.
        #    If no title exist, nothing to be done.

        self._check_field_title_duplicate(doi,action)

        # Check 2 : Check if the pds4 label is a bundle the title should contain bundle (ignoring case)
        #          The same for: dataset, collection, document
        #          Otherwise raise a warning.

        self._check_field_title_content(doi)

        # Check 3: Check lidvid update.
        #          Case A: If DOI does not have a doi field, and action step is 'release' there is no DOI in sqllite database with the same lidvid and a DOI attributed.
        #          Case B: If DOI not have a doi field, and action step is 'release' and the DOI from database is different than the DOI field updating.
        #          If field 'doi' has been minted and different than the one in database, and action is 'release', throw an exception.
        #          If field 'doi' has been minted and DOI is the same, and action is 'release', nothing to do.  User merely updating
        #          existing metadata.
        #          If field 'doi' has not been minted given 'lidvid' field, nothing to do.

        self._check_field_lidvid_update(doi,action)

        # Check 4: Check the workflow of the current doi with the ones in the database.
        #          A workflow should follow the order in m_workflow_order dictionary set at class initial.

        self._check_field_workflow(doi)

        return 1
