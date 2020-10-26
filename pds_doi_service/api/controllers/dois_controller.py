#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
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

from datetime import datetime
import json

import connexion
from flask import current_app

from pds_doi_service.api.models import DoiRecord
from pds_doi_service.api.models import DoiSummary
from pds_doi_service.core.actions.draft import DOICoreActionDraft
from pds_doi_service.core.actions.list import DOICoreActionList
from pds_doi_service.core.actions.reserve import DOICoreActionReserve
from pds_doi_service.core.input.exceptions import WarningDOIException
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser


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
    if current_app.config['TESTING']:
        db_name = connexion.request.args.get('db_name')

    return db_name


def get_dois(doi=None, submitter=None, node=None, lid=None):
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
    lid : list of str, optional
        List of LIDs to filter DOIs by. An LID may include the VID appended to
        the end.

    Returns
    -------
    records : list of DoiSummary
        The available DOI records from within the transaction database that
        match the requested criteria.

    """
    list_action = DOICoreActionList(db_name=_get_db_name())

    # List action expects multiple inputs as comma-delimited
    if doi:
        doi = ','.join(doi)

    if submitter:
        submitter = ','.join(submitter)

    if node:
        node = ','.join(node)

    lidvid = None

    if lid:
        # Separate the LID from LIDVID
        lidvid = list(filter(lambda s: '::' in s, lid))
        lid = list(set(lid) - set(lidvid))

        lidvid = ','.join(lidvid)
        lid = ','.join(lid)

    list_kwargs = {
        'doi': doi,
        'lid': lid,
        'lidvid': lidvid,
        'submitter': submitter,
        'node': node
    }

    results = list_action.run(**list_kwargs)

    records = []

    for result in json.loads(results):
        records.append(
            DoiSummary(
                doi=result['doi'], lid=result['lid'], vid=result['vid'],
                submitter=result['submitter'], status=result['status'],
                # TODO: unsure where to find creation_date, not provided in
                #       the results from list action
                # creation_date=None,
                update_date=datetime.fromtimestamp(result['update_date'])
            )
        )

    return records, 200


def post_dois(action, submitter, node, url):
    """
    Submit a DOI in reserve or draft status. The payload includes a URLs for
    one record to be submitted. Record URLs must resolve to PDS4 label
    files (xml).

    Parameters
    ----------
    action : str
        The submission action to perform. Must be one of "reserve" or "draft".
    submitter : str
        Email address of the submission requester.
    node : str
        The PDS node name to cite as contributor of the DOI. Must be one of the
        valid PDS steward IDs.
    url : str
        URL to provide as the record to register a DOI for. URL must start with
        either "http://" or "https://" and resolve to a valid PDS4 label in XML
        format.

    Returns
    -------
    record : DoiRecord
        A record of the DOI submission request.

    """
    try:
        # TODO: reserve action allows multiple bundles to be specified as
        #       comma-delimited list, whereas draft can only accept a single
        #       path. For now this means both are limited to a single path at
        #       a time.

        if action == 'reserve':
            reserve_action = DOICoreActionReserve(db_name=_get_db_name())

            # If we're unit testing, don't submit anything to OSTI
            dry_run = current_app.config['TESTING']

            # TODO: expose dry_run/force flags at API level?
            reserve_kwargs = {
                'node': node,
                'submitter': submitter,
                'input': url,
                'dry_run': dry_run
            }

            result = reserve_action.run(**reserve_kwargs)
        elif action == 'draft':
            draft_action = DOICoreActionDraft(db_name=_get_db_name())

            draft_kwargs = {
                'node': node,
                'submitter': submitter,
                'input': url
            }

            result = draft_action.run(**draft_kwargs)
        else:
            raise ValueError('Action must be either "draft" or "reserve". '
                             'Received "{}"'.format(action))
    # These exceptions indicate some kind of input error, so return the
    # Invalid Argument code
    except (WarningDOIException, ValueError) as err:
        return str(err), 400
    # For everything else, return the Internal Error code
    except Exception as err:
        return str(err), 500

    # Parse the OSTI XML string back into a list of DOIs
    result = bytes(result, encoding='utf-8')
    dois = DOIOstiWebParser().response_get_parse_osti_xml(result)

    records = []

    for doi in dois:
        lid, vid = doi.related_identifier.split('::')
        records.append(
            DoiRecord(
                doi=doi.doi, lid=lid, vid=vid,
                submitter=submitter, status=doi.status,
                creation_date=doi.date_record_added,
                update_date=doi.date_record_updated,
                # TODO: not sure what record refers to in results
                record=None,
                message=doi.message
            )
        )

    return records, 200


def post_release_doi(doi_prefix, doi_suffix):  # noqa: E501
    """
    Move a DOI record from draft/reserve status to "release".

    Parameters
    ----------
    doi_prefix : str
        The prefix of the DOI identifier.
    doi_suffix : str
        The suffix of the DOI identifier.

    Returns
    -------
    record : DoiRecord
        Record of the DOI release action.

    """
    return 'Not Implemented', 200


def get_doi_from_id(doi_prefix, doi_suffix):  # noqa: E501
    """
    Get the status of a DOI from the transaction database.

    Parameters
    ----------
    doi_prefix : str
        The prefix of the DOI identifier.
    doi_suffix : str
        The suffix of the DOI identifier

    Returns
    -------
    record : DoiRecord
        The record for the requested DOI.

    """
    return 'Not Implemented', 200


def put_doi_from_id(doi_prefix, doi_suffix, submitter, node, url):  # noqa: E501
    """
    Update the record associated with an existing DOI.

    Parameters
    ----------
    doi_prefix : str
        The prefix of the DOI identifier.
    doi_suffix : str
        The suffix of the DOI identifier.
    submitter : str
        Email address of the DOI update requester.
    node : str
        The PDS node name to cite as contributor of the DOI. Must be one of the
        valid PDS steward IDs.
    url : str
        URL to provide as the record to update the DOI with. URL must start with
        either "http://" or "https://" and resolve to a valid PDS4 label in XML
        format.

    Returns
    -------
    record : DoiRecord
        A record of the DOI update transaction.

    """
    return 'Not Implemented', 200
