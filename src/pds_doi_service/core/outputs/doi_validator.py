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
from typing import Optional

import requests
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.entities.doi import Doi
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.exceptions import DuplicatedTitleDOIException
from pds_doi_service.core.entities.exceptions import IllegalDOIActionException
from pds_doi_service.core.entities.exceptions import InvalidIdentifierException
from pds_doi_service.core.entities.exceptions import InvalidRecordException
from pds_doi_service.core.entities.exceptions import SiteURLNotExistException
from pds_doi_service.core.entities.exceptions import TitleDoesNotMatchProductTypeException
from pds_doi_service.core.entities.exceptions import UnexpectedDOIActionException
from pds_doi_service.core.entities.exceptions import UnknownNodeException
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.util.node_util import NodeUtil


# Get the common logger and set the level for this file.
logger = get_logger(__name__)

MIN_LID_FIELDS = 4
MAX_LID_FIELDS = 6
"""The expected minimum and maximum fields expected within a LID"""


class DOIValidator:
    doi_config_util = DOIConfigUtil()

    # The workflow_order dictionary contains the progression of the status of a DOI:
    workflow_order = {
        DoiStatus.Error: 0,
        DoiStatus.Unknown: 0,
        DoiStatus.Reserved: 1,
        DoiStatus.Draft: 2,
        DoiStatus.Review: 3,
        DoiStatus.Pending: 4,
        DoiStatus.Registered: 5,
        DoiStatus.Findable: 5,
        DoiStatus.Deactivated: 5,
    }

    def __init__(self, db_name=None):
        self._config = self.doi_config_util.get_config()

        # If database name is specified from user, use it.
        default_db_file = db_name if db_name else self._config.get("OTHER", "db_file")

        self._database_obj = DOIDataBase(default_db_file)

    def _check_node_id(self, doi: Doi):
        """
        Checks if the provided Doi object has a valid node ID assigned.

        Parameters
        ----------
        doi : Doi
            The Doi object to check.

        Raises
        ------
        UnknownNodeException
            If the Doi object has an unrecognized node ID assigned, or no
            node ID assigned at all.

        """
        try:
            if not doi.node_id:
                raise UnknownNodeException("Doi object does not have a node ID value assigned.")

            NodeUtil.validate_node_id(doi.node_id)
        except UnknownNodeException as err:
            msg = (
                f"Invalid Node ID for DOI record with identifier {doi.pds_identifier}.\n"
                f"Reason: {str(err)}.\n"
                "Please use the --node option to specify the apporpriate PDS node ID for the transaction."
            )

            raise UnknownNodeException(msg)

    def _check_field_site_url(self, doi: Doi):
        """
        If the site_url field is defined for the provided Doi object, check to
        see if it is online. This check is typically only made for release
        requests, which require a URL field to be set.

        Parameters
        ----------
        doi : Doi
            The Doi object to check.

        Raises
        ------
        SiteURLNotExistException
            If the site URL is defined for the Doi object and is not reachable.

        """
        logger.debug("doi,site_url: %s,%s", doi.doi, doi.site_url)

        if doi.site_url:
            try:
                response = requests.get(doi.site_url, timeout=10)
                status_code = response.status_code
                logger.debug("from_request status_code,site_url: %s,%s", status_code, doi.site_url)

                # Handle cases when a connection can be made to the server but
                # the status is greater than or equal to 400.
                if status_code >= 400:
                    # Need to check its an 404, 503, 500, 403 etc.
                    raise requests.HTTPError(f"status_code,site_url {status_code,doi.site_url}")
                else:
                    logger.info("Landing page URL %s is reachable", doi.site_url)
            except (requests.exceptions.ConnectionError, Exception):
                raise SiteURLNotExistException(
                    f"Landing page URL {doi.site_url} is not reachable. Request "
                    f"should have a valid URL assigned prior to release.\n"
                    f"To bypass this check, rerun the command with the --force "
                    f"flag provided."
                )

    def _check_field_title_duplicate(self, doi: Doi):
        """
        Check the provided Doi object's title to see if the same title has
        already been used with a different DOI record.

        Parameters
        ----------
        doi : Doi
            The Doi object to check.

        Raises
        ------
        DuplicatedTitleDOIException
            If the title for the provided Doi object is in use for another record.

        """
        query_criterias = {"title": [doi.title]}

        # Query database for rows with given title value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        # keep rows with same title BUT different identifier
        rows_with_different_identifier = [row for row in rows if row[columns.index("identifier")] != doi.pds_identifier]

        if rows_with_different_identifier:
            identifiers = ",".join([row[columns.index("identifier")] for row in rows_with_different_identifier])
            status = ",".join([row[columns.index("status")] for row in rows_with_different_identifier])
            dois = ",".join([row[columns.index("doi")] for row in rows_with_different_identifier])

            msg = (
                f"The title '{doi.title}' has already been used for records "
                f"{identifiers}, status: {status}, doi: {dois}. "
                "A different title should be used.\nIf you want to bypass this "
                "check, rerun the command with the --force flag provided."
            )

            raise DuplicatedTitleDOIException(msg)

    def _check_field_title_content(self, doi: Doi):
        """
        Check that the title of the provided Doi object contains the type of
        PDS product (bundle, collection, document, etc...).

        Parameters
        ----------
        doi : Doi
            The Doi object to check.

        Raises
        ------
        TitleDoesNotMatchProductTypeException
            If the title for the provided Doi object does not contain the
            type of PDS product.

        """
        product_type_specific_split = doi.product_type_specific.split(" ")

        # The suffix should be the last field in product_type_specific so
        # if it has many tokens, check the last one.
        product_type_specific_suffix = product_type_specific_split[-1]

        logger.debug("product_type_specific_suffix: %s", product_type_specific_suffix)
        logger.debug("doi.title: %s", doi.title)

        if not product_type_specific_suffix.lower() in doi.title.lower():
            msg = (
                f"DOI with identifier '{doi.pds_identifier}' and title "
                f"'{doi.title}' does not contains the product-specific type "
                f"suffix '{product_type_specific_suffix.lower()}'. "
                "Product-specific type suffix should be in the title.\n"
                "If you want to bypass this check, rerun the command with the "
                "--force flag provided."
            )

            raise TitleDoesNotMatchProductTypeException(msg)

    def _check_for_preexisting_identifier(self, doi: Doi):
        """
        For the identifier assigned to the provided Doi object, check that
        the latest transaction for the same identifier has a matching DOI value.

        Parameters
        ----------
        doi : Doi
            The Doi object to validate.

        Raises
        ------
        IllegalDOIActionException
            If the check fails.

        """
        # The database expects each field to be a list.
        query_criterias = {"ids": [doi.pds_identifier]}

        # Query database for rows with given id value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        for row in rows:
            existing_record = dict(zip(columns, row))

            if doi.doi != existing_record["doi"]:
                raise IllegalDOIActionException(
                    f"There is already a DOI {existing_record['doi']} associated "
                    f"with PDS identifier {doi.pds_identifier} "
                    f"(status={existing_record['status']}).\n"
                    f"You cannot modify a DOI for an existing PDS identifier."
                )

    def _check_for_preexisting_doi(self, doi: Doi):
        """
        For Doi objects with DOI already assigned, this check ensures the DOI
        value is not already in use for a different PDS identifier.

        Parameters
        ----------
        doi : Doi
            The Doi object to validate.

        Raises
        ------
        ValueError
            If the provided Doi object does not have a DOI value assigned to check.
        UnexpectedDOIActionException
            If the check fails.

        """
        if not doi.doi:
            raise ValueError(f"Provided DOI object (id {doi.pds_identifier}) does not have a DOI value assigned.")

        # The database expects each field to be a list.
        query_criterias = {"doi": [doi.doi]}

        # Query database for rows with given DOI value (should only ever be
        # at most one)
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        for row in rows:
            existing_record = dict(zip(columns, row))

            if doi.pds_identifier != existing_record["identifier"]:
                raise UnexpectedDOIActionException(
                    f"The DOI ({doi.doi}) provided for record identifier "
                    f"{doi.pds_identifier} is already in use for record "
                    f"{rows[0][columns.index('identifier')]}.\n"
                    f"Are you sure you want to assign the new identifier {doi.pds_identifier}?\n"
                    f"If so, use the --force flag to bypass this check."
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
        InvalidRecordException
            If any of the identifier field checks fail

        """
        # Make sure we have an identifier to key off of
        if not doi.pds_identifier:
            raise InvalidRecordException(
                "Record provided with missing PDS identifier field. "
                "Please ensure a LIDVID or similar identifier is provided for "
                "all DOI requests."
            )

        # Make sure the doi and id fields are consistent, if present
        if doi.doi and doi.id:
            prefix, suffix = doi.doi.split("/")

            if suffix != doi.id:
                raise InvalidRecordException(
                    f"Record for {doi.pds_identifier} has inconsistent "
                    f"DOI ({doi.doi}) and ID ({doi.id}) fields. Please reconcile "
                    "the inconsistency and resubmit the request."
                )

    def _check_lidvid_field(self, doi: Doi):
        """
        Checks the pds_identifier field of a Doi to ensure it conforms
        to the LIDVID format.

        Parameters
        ----------
        doi : Doi
            The parsed Doi object to validate

        Raises
        ------
        InvalidIdentifierException
            If the PDS identifier field of the DOI does not conform to
            the LIDVID format. These exceptions should be able to be bypassed
            when the --force flag is provided.

        """

        vid: Optional[str]
        if "::" in doi.pds_identifier:
            lid, vid = doi.pds_identifier.split("::")
        else:
            lid = doi.pds_identifier
            vid = None

        lid_tokens = lid.split(":")

        try:
            # Make sure we got a URN
            if lid_tokens[0] != "urn":
                raise InvalidIdentifierException('LIDVID must start with "urn"')

            # Make sure we got the minimum number of fields, and that
            # the number of fields is consistent with the product type
            if not MIN_LID_FIELDS <= len(lid_tokens) <= MAX_LID_FIELDS:
                raise InvalidIdentifierException(
                    f"LIDVID must contain only between {MIN_LID_FIELDS} "
                    f"and {MAX_LID_FIELDS} colon-delimited fields, "
                    f"got {len(lid_tokens)} field(s)"
                )

            # Now check each field for the expected set of characters
            token_regex = re.compile(r"[a-z0-9][a-z0-9-._]{0,31}")

            for index, token in enumerate(lid_tokens):
                if not token_regex.fullmatch(token):
                    raise InvalidIdentifierException(
                        f"LIDVID field {index + 1} ({token}) is invalid. "
                        f"Fields must begin with a letter or digit, and only "
                        f"consist of letters, digits, hyphens (-), underscores (_) "
                        f"or periods (.)"
                    )

            # Finally, make sure the VID conforms to a version number
            version_regex = re.compile(r"^\d+\.\d+$")

            if vid and not version_regex.fullmatch(vid):
                raise InvalidIdentifierException(
                    f"Parsed VID ({vid}) does not conform to a valid version identifier. "
                    "Version identifier must consist only of a major and minor version "
                    "joined with a period (ex: 1.0)"
                )
        except InvalidIdentifierException as err:
            raise InvalidIdentifierException(
                f"The record identifier {doi.pds_identifier} (DOI {doi.doi}) "
                f"does not conform to a valid LIDVID format.\n"
                f"Reason: {str(err)}\n"
                "If the identifier is not intended to be a LIDVID, use the "
                "--force option to bypass the results of this check."
            )

    def _check_field_workflow(self, doi: Doi):
        """
        Check that there is not a record in the Sqlite database with same
        identifier but a higher status than the current action (see workflow_order)

        Parameters
        ----------
        doi : Doi
            The parsed Doi object to check the status of.

        Raises
        ------
        UnexpectedDOIActionException
            If the provided Doi object has an unrecognized status assigned, or if
            the previous status for the Doi is higher in the workflow ordering than
            the current status.

        """
        if doi.status is not None and doi.status not in self.workflow_order:
            msg = (
                f"Unexpected DOI status of '{doi.status.value}' from label. "
                f"Valid values are "
                f"{[DoiStatus(key).value for key in self.workflow_order.keys()]}"
            )
            logger.error(msg)
            raise UnexpectedDOIActionException(msg)

        # The database expects each field to be a list.
        query_criterias = {"doi": [doi.doi]}

        # Query database for rows with given doi value.
        columns, rows = self._database_obj.select_latest_rows(query_criterias)

        for row in rows:
            existing_record = dict(zip(columns, row))
            doi_str = existing_record["doi"]
            prev_status = existing_record["status"]

            # Check the rankings of the current and previous status to see if
            # we're moving backwards through the workflow. For example, a status
            # of 'Findable' (5) is higher than 'Review' (3), so a released
            # DOI record being moved back to review would trip this warning.
            if self.workflow_order[prev_status] > self.workflow_order[doi.status]:  # type: ignore
                msg = (
                    f"There is a record for identifier {doi.pds_identifier} "
                    f"(DOI: {doi_str}) with status: '{prev_status.lower()}'.\n"
                    f"Are you sure you want to restart the workflow from step "
                    f"'{doi.status}'?\nIf so, use the --force flag to bypass the "
                    f"results of this check."
                )

                raise UnexpectedDOIActionException(msg)

    def validate_reserve_request(self, doi: Doi):
        """
        Perform the suite of validation checks applicable to a reserve request
        on the provided Doi object.

        Parameters
        ----------
        doi : Doi
            The parsed Doi object to validate.

        """
        # For reserve requests, need to make sure there is not already an
        # existing DOI with the same PDS identifier
        self._check_for_preexisting_identifier(doi)

        self._check_node_id(doi)
        self._check_identifier_fields(doi)
        self._check_lidvid_field(doi)
        self._check_field_title_duplicate(doi)
        self._check_field_title_content(doi)

    def validate_update_request(self, doi: Doi):
        """
        Perform the suite of validation checks applicable to an update request
        on the provided Doi object.

        Parameters
        ----------
        doi : Doi
            The parsed Doi object to validate.

        """
        # For update requests, need to check if there are any other DOI records
        # using the same PDS identifier
        self._check_for_preexisting_doi(doi)

        self._check_node_id(doi)
        self._check_identifier_fields(doi)
        self._check_lidvid_field(doi)
        self._check_field_title_duplicate(doi)
        self._check_field_title_content(doi)

        # Also need to check if we're moving backwards through the workflow,
        # i.e. updating an already released record.
        self._check_field_workflow(doi)

    def validate_release_request(self, doi: Doi):
        """
        Perform the suite of validation checks applicable to a release request
        on the provided Doi object.

        Parameters
        ----------
        doi : Doi
            The parsed Doi object to validate.

        """
        # For release requests, need to check if there are any other DOI records
        # using the same PDS identifier
        if doi.doi:
            self._check_for_preexisting_doi(doi)

        self._check_node_id(doi)
        self._check_identifier_fields(doi)
        self._check_lidvid_field(doi)
        self._check_field_title_duplicate(doi)
        self._check_field_title_content(doi)

        # Release requests require a valid URL assigned, so check for that here
        self._check_field_site_url(doi)
