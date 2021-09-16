#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
==================
dois_controller.py
==================

Contains the request handlers for the PDS DOI API.
"""
import csv
import glob
import json
from os.path import exists
from os.path import join
from tempfile import NamedTemporaryFile

import connexion  # type: ignore
from flask import current_app
from pds_doi_service.api.models import DoiRecord
from pds_doi_service.api.models import DoiSummary
from pds_doi_service.api.util import format_exceptions
from pds_doi_service.core.actions import DOICoreActionCheck
from pds_doi_service.core.actions import DOICoreActionDraft
from pds_doi_service.core.actions import DOICoreActionList
from pds_doi_service.core.actions import DOICoreActionRelease
from pds_doi_service.core.actions import DOICoreActionReserve
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.input.exceptions import NoTransactionHistoryForIdentifierException
from pds_doi_service.core.input.exceptions import UnknownIdentifierException
from pds_doi_service.core.input.exceptions import WarningDOIException
from pds_doi_service.core.input.exceptions import WebRequestException
from pds_doi_service.core.input.input_util import DOIInputUtil
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


def _get_db_name():
    """
    Helper function to return a database name to use with the endpoint.
    Used primarily for substituting in a pre-existing database when testing.

    Returns
    -------
    db_name : str
        Path to the database instance to use with an action class.
        If testing mode on the Flask app is disabled, or no name was specified
        with the request arguments, then None is returned.

    """
    db_name = None

    # If were testing, check if theres a pre-defined database we should be using
    if current_app.config["TESTING"]:
        db_name = connexion.request.args.get("db_name")

    return db_name


def _write_csv_from_labels(temp_file, labels):
    """
    Writes the provided list of labels in CSV format to the open temporary
    file handle. The contents are flushed to disk before this function returns.

    Parameters
    ----------
    temp_file : tempfile.NamedTemporaryFile
        The open temporary file to write CSV contents to.
    labels : list of dict
        List of labels to be written out in CSV format.

    """
    csv_writer = csv.DictWriter(temp_file, fieldnames=DOIInputUtil.MANDATORY_COLUMNS)

    csv_writer.writeheader()

    for label in labels:
        csv_writer.writerow(label)

    temp_file.flush()


def _records_from_dois(dois, node=None, submitter=None, doi_label=None):
    """
    Reformats a list of DOI objects into a corresponding list of DoiRecord
    objects.

    Parameters
    ----------
    dois : list of Doi
        The list of pds_doi_service.core.entities.doi.Doi objects to reformat
        into DoiRecords.
    node : str, optional,
        The PDS node to associate with each record.
    submitter : str, optional
        Submitter email address to associate with each record.
    doi_label : str, optional
        DOI label to associate with each record.

    Returns
    -------
    records : list of DoiRecord
        The records produced from the provided Doi objects.

    """
    records = []

    list_action = DOICoreActionList(db_name=_get_db_name())

    for doi in dois:
        # Pull info from transaction database so we can get the most accurate
        # info for the DOI
        list_kwargs = {"ids": doi.related_identifier}
        list_result = json.loads(list_action.run(**list_kwargs))[0]

        records.append(
            DoiRecord(
                doi=doi.doi or list_result["doi"],
                identifier=doi.related_identifier,
                title=doi.title,
                node=node,
                submitter=submitter,
                status=doi.status,
                creation_date=list_result["date_added"],
                update_date=list_result["date_updated"],
                record=doi_label,
                message=doi.message,
            )
        )

    return records


def get_dois(doi=None, submitter=None, node=None, status=None, ids=None, start_date=None, end_date=None):
    """
    List the DOI requests within the transaction database which match
    the specified criteria. If no criteria are provided, all database entries
    are returned.

    Parameters
    ----------
    doi : list of str, optional
        List of DOIs to fetch from transaction database.
    submitter : list of str, optional
        List of submitter email addresses to filter DOIs by.
    node : list of str, optional
        List of PDS node names cited as contributor of the DOI to filter by.
        Each identifier must be one of the valid PDS steward IDs.
    status : list of str, optional
        List of DOI workflow status values to filter results by.
        Each status value should correspond to one of the enumeration values in
        DoiStatus.
    ids : list of str, optional
        List of PDS identifiers to filter DOIs by. Each identifier may
        contain one or more Unix-style wildcards (*) to pattern match against.
    start_date : str
        A start date to filter resulting DOI records by. Only records with an
        update time after this date will be returned. Value must be of the form
        <YYYY>-<mm>-<dd>T<HH>:<MM>:<SS>.<ms>
    end_date : str
        An end date to filter resulting DOI records by. Only records with an
        update time prior to this date will be returned. Value must be of the
        form <YYYY>-<mm>-<dd>T<HH>:<SS>.<ms>
    Returns
    -------
    records : list of DoiSummary
        The available DOI records from within the transaction database that
        match the requested criteria.

    """
    logger.info("GET /dois request received")

    list_action = DOICoreActionList(db_name=_get_db_name())

    # List action expects multiple inputs as comma-delimited
    if doi:
        doi = ",".join(doi)

    if submitter:
        submitter = ",".join(submitter)

    if node:
        node = ",".join(node)

    if status:
        status = ",".join(status)

    if ids:
        ids = ",".join(ids)

    list_kwargs = {
        "doi": doi,
        "ids": ids,
        "submitter": submitter,
        "node": node,
        "status": status,
        "start_update": start_date,
        "end_update": end_date,
    }

    logger.debug("GET /dois list action arguments: %s", list_kwargs)

    try:
        results = list_action.run(**list_kwargs)
    except ValueError as err:
        # Most likely from an malformed start/end date. Report back "Invalid
        # argument" code
        return format_exceptions(err), 400
    except Exception as err:
        # Treat any unexpected Exception as an "Internal Error" and report back
        return format_exceptions(err), 500

    records = []

    for result in json.loads(results):
        records.append(
            DoiSummary(
                doi=result["doi"],
                identifier=result["identifier"],
                title=result["title"],
                node=result["node_id"],
                submitter=result["submitter"],
                status=result["status"],
                update_date=result["date_updated"],
            )
        )

    logger.info("GET /dois request returned %d result(s)", len(records))

    return records, 200


def post_dois(action, submitter, node, url=None, body=None, force=False):
    """
    Submit a DOI in reserve or draft status. The input to the action may be
    either a JSON labels payload (for reserve or draft), or a URL to a PDS4
    XML label file (draft only).

    Parameters
    ----------
    action : str
        The submission action to perform. Must be one of "reserve" or "draft".
    submitter : str
        Email address of the submission requester.
    node : str
        The PDS node name to cite as contributor of the DOI. Must be one of the
        valid PDS steward IDs.
    url : str, optional
        URL to provide as the record to register a DOI for. URL must start with
        either "http://" or "https://" and resolve to a valid PDS4 label in XML
        format. Only used when action is set to "draft". If provided, any
        requestBody contents are ignored by the draft action.
    body : str or dict
        requestBody contents. If provided, should contain an PSD4 label (for
        draft) or one or more LabelPayload structures (for reserve). Required if
        the action is set to "reserve", otherwise it can be used optionally in
        lieu of url when the action is set to "draft".
    force : bool
        If true, forces a request to completion, ignoring any warnings
        encountered.

    Returns
    -------
    record : DoiRecord
        A record of the DOI submission request.
    response_code : int
        The HTTP response code corresponding to the result.

    """
    logger.info("POST /dois request received, action: %s", action)

    # Get the appropriate parser for the currently configured service
    web_parser = DOIServiceFactory.get_web_parser_service()

    try:
        if action == "reserve":
            # Extract the list of labels from the requestBody, if one was provided
            if not connexion.request.is_json:
                raise ValueError("No JSON requestBody provided for reserve POST " "request.")
            else:
                body = connexion.request.get_json()

            reserve_action = DOICoreActionReserve(db_name=_get_db_name())

            with NamedTemporaryFile("w", prefix="labels_", suffix=".csv") as csv_file:
                logger.debug("Writing temporary label to %s", csv_file.name)

                _write_csv_from_labels(csv_file, body["labels"])

                reserve_kwargs = {
                    "node": node,
                    "submitter": submitter,
                    "input": csv_file.name,
                    "force": force,
                    "dry_run": False,
                }

                doi_label = reserve_action.run(**reserve_kwargs)

            # Parse the JSON string back into a list of DOIs
            dois, _ = web_parser.parse_dois_from_label(doi_label, content_type=CONTENT_TYPE_JSON)
        elif action == "draft":
            if not body and not url:
                raise ValueError(
                    "No requestBody or URL parameter provided "
                    "as input to draft request. One or the other "
                    "must be provided."
                )

            draft_action = DOICoreActionDraft(db_name=_get_db_name())

            # Determine how the input label(s) was sent
            if url:
                draft_kwargs = {"node": node, "submitter": submitter, "input": url, "force": force}

                doi_label = draft_action.run(**draft_kwargs)
            else:
                # Swagger def only specified application/xml and application/json
                # as potential input types, so it should be sufficient to just
                # check for JSON here
                if connexion.request.is_json:
                    content_type = CONTENT_TYPE_JSON
                else:
                    content_type = CONTENT_TYPE_XML

                with NamedTemporaryFile("wb", prefix="labels_", suffix=f".{content_type}") as outfile:
                    logger.debug("Writing temporary label to %s", outfile.name)

                    outfile.write(body)
                    outfile.flush()

                    draft_kwargs = {"node": node, "submitter": submitter, "input": outfile.name, "force": force}

                    doi_label = draft_action.run(**draft_kwargs)

            # Parse the label back into a list of DOIs
            dois, _ = web_parser.parse_dois_from_label(doi_label)
        else:
            raise ValueError('Action must be either "draft" or "reserve". ' 'Received "{}"'.format(action))
    # These exceptions indicate some kind of input error, so return the
    # Invalid Argument code
    except (InputFormatException, WarningDOIException, ValueError) as err:
        return format_exceptions(err), 400
    # For everything else, return the Internal Error code
    except Exception as err:
        return format_exceptions(err), 500

    records = _records_from_dois(dois, node=node, submitter=submitter, doi_label=doi_label)

    logger.info('Posted %d record(s) to status "%s"', len(records), action)

    return records, 200


def post_submit_doi(identifier, force=None):
    """
    Move a DOI record from draft/reserve status to "review".

    Parameters
    ----------
    identifier : str
        The PDS identifier associated with the record to submit for review.
    force : bool, optional
        If true, forces a submit request to completion, ignoring any warnings
        encountered.

    Returns
    -------
    record : DoiRecord
        Record of the DOI submit action.

    """
    logger.info("POST /dois/submit request received for identifier %s", identifier)

    # A submit action is the same as invoking the release endpoint with
    # --no-review set to False
    kwargs = {"identifier": identifier, "force": force, "no_review": False}

    return post_release_doi(**kwargs)


def post_release_doi(identifier, force=False, **kwargs):
    """
    Move a DOI record from draft/reserve status to "release".

    Parameters
    ----------
    identifier : str
        The PDS identifier associated with the record to release.
    force : bool, optional
        If true, forces a release request to completion, ignoring any warnings
        encountered.
    kwargs : dict
        Additional keyword arguments to forward to the DOI release action.

    Returns
    -------
    record : DoiRecord
        Record of the DOI release action.

    """
    try:
        list_action = DOICoreActionList(db_name=_get_db_name())

        # Get the latest transaction record for this identifier
        list_record = list_action.transaction_for_identifier(identifier)

        # Make sure we can locate the output label associated with this
        # transaction
        transaction_location = list_record["transaction_key"]
        label_files = glob.glob(join(transaction_location, "output.*"))

        if not label_files or not exists(label_files[0]):
            raise NoTransactionHistoryForIdentifierException(
                "Could not find a DOI label associated with identifier {}. "
                "The database and transaction history location may be out of sync. "
                "Please try resubmitting the record in reserve or draft.".format(identifier)
            )

        label_file = label_files[0]

        # An output label may contain entries other than the requested
        # identifier, extract only the appropriate record into its own temporary
        # file and feed it to the release action
        web_parser = DOIServiceFactory.get_web_parser_service()
        record, content_type = web_parser.get_record_for_identifier(label_file, identifier)

        with NamedTemporaryFile("w", prefix="output_", suffix=f".{content_type}") as temp_file:
            logger.debug("Writing temporary label to %s", temp_file.name)

            temp_file.write(record)
            temp_file.flush()

            # Prepare the release action
            release_action = DOICoreActionRelease(db_name=_get_db_name())

            release_kwargs = {
                "node": list_record["node_id"],
                "submitter": list_record["submitter"],
                "input": temp_file.name,
                "force": force,
                # Default for this endpoint should be to skip review and release
                # directly to the DOI service provider
                "no_review": kwargs.get("no_review", True),
            }

            release_label = release_action.run(**release_kwargs)

        dois, errors = web_parser.parse_dois_from_label(release_label, content_type=CONTENT_TYPE_JSON)

        # Propagate any errors returned from the attempt in a single exception
        if errors:
            raise WarningDOIException(
                "Received the following errors from the release request:\n" "{}".format("\n".join(errors))
            )
    except (ValueError, WarningDOIException) as err:
        # Some warning or error prevented release of the DOI
        return format_exceptions(err), 400
    except UnknownIdentifierException as err:
        # Could not find an entry for the requested ID
        return format_exceptions(err), 404
    except Exception as err:
        # Treat any unexpected Exception as an "Internal Error" and report back
        return format_exceptions(err), 500

    records = _records_from_dois(
        dois, node=list_record["node_id"], submitter=list_record["submitter"], doi_label=release_label
    )

    logger.info('Posted %d record(s) to status "%s"', len(records), "release" if kwargs.get("no_review") else "review")

    return records, 200


def get_doi_from_id(identifier):  # noqa: E501
    """
    Get the status of a DOI from the transaction database.

    Parameters
    ----------
    identifier : str
        The PDS identifier associated with the record to status.

    Returns
    -------
    record : DoiRecord
        The record for the requested identifier.

    """
    logger.info("GET /doi request received for identifier %s", identifier)

    # Get the appropriate parser for the currently configured service
    web_parser = DOIServiceFactory.get_web_parser_service()

    list_action = DOICoreActionList(db_name=_get_db_name())

    list_kwargs = {"ids": identifier}

    try:
        list_results = json.loads(list_action.run(**list_kwargs))

        if not list_results:
            raise UnknownIdentifierException("No record(s) could be found for identifier {}".format(identifier))

        # Extract the latest record from all those returned
        list_record = list_results[0]

        # Make sure we can locate the output label associated with this
        # transaction
        transaction_location = list_record["transaction_key"]
        label_files = glob.glob(join(transaction_location, "output.*"))

        if not label_files or not exists(label_files[0]):
            raise NoTransactionHistoryForIdentifierException(
                "Could not find a DOI label associated with identifier {}. "
                "The database and transaction history location may be out of sync. "
                "Please try resubmitting the record in reserve or draft.".format(identifier)
            )

        label_file = label_files[0]

        # Get only the record corresponding to the requested identifier
        (label_for_id, content_type) = web_parser.get_record_for_identifier(label_file, identifier)
    except UnknownIdentifierException as err:
        # Return "not found" code
        return format_exceptions(err), 404
    except Exception as err:
        # Treat any unexpected Exception as an "Internal Error" and report back
        return format_exceptions(err), 500

    # Parse the label associated with the lidvid so we can return a full DoiRecord
    dois, _ = web_parser.parse_dois_from_label(label_for_id, content_type)

    records = _records_from_dois(
        dois, node=list_record["node_id"], submitter=list_record["submitter"], doi_label=label_for_id
    )

    # Should only ever be one record since we filtered by a single id
    return records[0], 200


def get_check_dois(submitter, email=False, attachment=False):
    """
    Check submission status of all records pending release.

    Parameters
    ----------
    submitter : str
        The email address of the user to register as author of the check action.
        This address is also included in the list of recipients.
    email : bool
        If true, the check action sends results to the default recipients and
        pending DOI submitters.
    attachment : bool
        If true, the check action sends results as an email attachment. Has no
        effect if the email flag is not set to true.

    Returns
    -------
    records : list of DoiRecord
        Records containing the current status of all DOI's listed as pending
        within the transaction database when this endpoint is called.

    """
    logger.info("GET /dois/check request received")

    check_action = DOICoreActionCheck(db_name=_get_db_name())

    check_kwargs = {"submitter": submitter, "email": email, "attachment": attachment}

    logger.debug("GET /dois/check action arguments: %s", check_kwargs)

    try:
        pending_results = check_action.run(**check_kwargs)
    except WebRequestException as err:
        # Host was unreachable
        return format_exceptions(err), 400
    except Exception as err:
        # Treat any unexpected Exception as an "Internal Error" and report back
        return format_exceptions(err), 500

    records = [
        DoiRecord(
            doi=pending_result["doi"],
            identifier=pending_result["identifier"],
            title=pending_result["title"],
            node=pending_result["node_id"],
            submitter=submitter,
            status=pending_result["status"],
            creation_date=pending_result["date_added"],
            update_date=pending_result["date_updated"],
            message=pending_result["message"],
        )
        for pending_result in pending_results
    ]

    return records, 200


def put_doi_from_id(identifier, submitter=None, node=None, url=None):  # noqa: E501
    """
    Update the record associated with an existing DOI.

    Notes
    -----
    This endpoint has deprecated in favor of the GET /dois endpoint.

    Parameters
    ----------
    identifier : str
        The PDS identifier associated with the record to update.
    submitter : str, optional
        Email address of the DOI update requester.
    node : str, optional
        The PDS node name to cite as contributor of the DOI. Must be one of the
        valid PDS steward IDs.
    url : str, optional
        URL to provide as the record to update the DOI with. URL must start with
        either "http://" or "https://" and resolve to a valid PDS4 label in XML
        format.

    Returns
    -------
    record : DoiRecord
        A record of the DOI update transaction.

    """
    return format_exceptions(NotImplementedError("Please use the POST /doi endpoint for record " "updates")), 501
