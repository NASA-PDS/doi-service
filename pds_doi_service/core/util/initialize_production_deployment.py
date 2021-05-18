#!/usr/bin/env python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
===================================
initialize_production_deployment.py
===================================

Script used to import the available DOIs from OSTI server into a local
production database.
"""

# Parameters to this script:
#
#    The -s (required) is email of the PDS operator: -s pds-operator@jpl.nasa.gov
#    The -i is optional. If the input is provided and is a file, parse from it,
#    otherwise query from the URL input: -i https://www.osti.gov/iad2/api/records
#        The format of input XML file is the same format of text returned from
#        querying the OSTI server via a browser or curl command.
#        If provided and a URL of the OSTI server, this will override the url in
#        the config file.
#    The -d is optional.  If provided it is the name of the database file to
#    write records to: -d doi.db
#        If provided, this will override the db_name in the config file.
#    The --dry-run parameter allows the code to parse the input or querying the
#    server without writing to database to see how long the code takes and if
#    there are records skipped.
#    The --debug parameter allows the code to print debug statements useful to
#    see if something goes wrong.
#
# Make sure the -i parameter or the url parameter in config/conf.ini points to
# the OPS server from OSTI 'https://www.osti.gov/iad2/api/records'
# as the TEST server 'https://www.osti.gov/iad2test/api/records' only has test
# records and it takes a long time to run.
#
# Example runs:
#
# initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -i my_input.xml -d temp.db --dry-run --debug >& t1 ; tail -20 t1
# initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -i https://www.osti.gov/iad2/api/records -d temp.db --dry-run --debug >& t1 ; tail -20 t1
# initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -i my_input.xml -d temp.db --debug >& t1 ; tail -20 t1
# initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -d temp.db --debug >& t1 ; tail -20 t1

# Note: As of 10/01/2020, there is one DOI (10.17189/1517674) that does not have
# any info for lidvid that caused the software to crash. There may be more.
#
#       There is a way to update this information by querying the server with
#       this id and update the output and feed this output with the -i parameter
#       to this script.
#       This is the curl command:
#           curl -v --netrc-file ~/.netrc https://www.osti.gov/iad2/api/records/1517674 \
#               -X GET -H "Content-Type: application/xml" -H "Accept: application/xml > my_input.xml
#       Then the file my_input.xml can be edited to include the lidvid in the accession_number tag
#           <accession_number>a:b:c::1.0</accession_number>
# Note: As of 10/05/2020, there are 105 records that does not have info for lidvid.
#       Ron has been notified.
# Note: As of 10/06/2020, there are 1058 DOIs in the OPS OSTI server associated
#       with the NASA-PDS account.

import argparse
import logging
import os
from datetime import datetime

from pds_doi_service.core.input.exceptions import (InputFormatException,
                                                   CriticalDOIException)
from pds_doi_service.core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser
from pds_doi_service.core.outputs.transaction_builder import TransactionBuilder
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

# Get the common logger and set the level for this file.
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

m_doi_config_util = DOIConfigUtil()
m_config = m_doi_config_util.get_config()


def create_cmd_parser():
    parser = argparse.ArgumentParser(
        description='Script to import existing DOIs from OSTI into the local'
                    'transaction database.'
    )
    parser.add_argument("-i", "--input", required=False,
                        help="Input file to import existing DOIs from, or the "
                             "URL of the OSTI server. If no value is provided, "
                             "the OSTI server URL specified by the DOI service "
                             "configuration INI file is used by default.")
    parser.add_argument("-s", "--submitter-email", required=False,
                        default='pds-operator@jpl.nasa.gov',
                        help="The email address of the user performing the "
                             "deployment database initialization. Defaults to "
                             "pds-operator@jpl.nasa.gov.")
    parser.add_argument("-d", "--db-name", required=False,
                        help="Name of the SQLite3 database file name to commit "
                             "DOI records to. If not provided, the file name is "
                             "obtained from the DOI service INI config.")
    parser.add_argument("-o", "--output-file", required=False, default=None,
                        help="Path to write out the DOI XML labels as returned "
                             "from OSTI. When created, this file can be used "
                             "with the --input option to import records at a "
                             "later time without re-querying the OSTI server. "
                             "This option has no effect if --input already "
                             "specifies an input XML file.")
    parser.add_argument("--dry-run", required=False, action="store_true",
                        help="Flag to suppress actual writing of DOIs to database.")
    parser.add_argument("--debug", required=False, action="store_true",
                        help="Flag to print debug statements.")

    return parser


def _read_from_local_xml(path):
    """Read from a local xml file containing output from an OSTI query."""
    try:
        with open(path, mode='r') as f:
            doi_xml = f.read()
    except Exception as e:
        raise CriticalDOIException(str(e))

    dois, _ = DOIOstiWebParser.parse_osti_response_xml(doi_xml)

    return dois


def _read_from_path(path):
    if path.endswith('.xml'):
        return _read_from_local_xml(path)

    raise InputFormatException(f'File {path} is not supported. '
                               f'Only .xml is supported.')


def _parse_input(input_file):
    if os.path.exists(input_file):
        return _read_from_path(input_file)

    raise InputFormatException(f"Error reading file {input_file}. "
                               f"File may not exist.")


def get_dois_from_osti(target_url, output_file):
    """
    Queries the OSTI server for all the current DOI associated with the PDS-USER
    account. The server name is fetched from the config file with the 'url'
    field in the 'OSTI' grouping if target_url is None.

    """
    query_dict = {}

    o_server_url = target_url

    if o_server_url is None:
        o_server_url = m_config.get('OSTI', 'url')

    logger.info("Using OSTI server URL %s", o_server_url)

    doi_xml = DOIOstiWebClient().webclient_query_doi(
        o_server_url, query_dict,
        i_username=m_config.get('OSTI', 'user'),
        i_password=m_config.get('OSTI', 'password')
    )

    if output_file:
        with open(output_file, 'w') as outfile:
            outfile.write(doi_xml)

    dois, _ = DOIOstiWebParser.parse_osti_response_xml(doi_xml)

    return dois, o_server_url


def _get_node_id_from_contributors(doi_fields):
    """
    Given a doi object, attempt to extract the node_id from contributors field.
    If unable to, return 'eng' as default.
    This function is a one-off as well so no fancy logic.
    """
    o_node_id = 'eng'

    if doi_fields.get('contributor'):
        full_name_orig = doi_fields['contributor']
        full_name = full_name_orig.lower()

        if 'atmospheres' in full_name:
            o_node_id = 'atm'
        elif 'engineering' in full_name:
            o_node_id = 'eng'
        elif 'geosciences' in full_name:
            o_node_id = 'geo'
        elif 'imaging' in full_name:
            o_node_id = 'img'
        elif 'cartography' in full_name:
            o_node_id = 'img'
        # Some uses title: Navigation and Ancillary Information Facility Node
        # Some uses title: Navigational and Ancillary Information Facility
        # So check for both
        elif 'navigation' in full_name and 'ancillary' in full_name:
            o_node_id = 'naif'
        elif 'navigational' in full_name and 'ancillary' in full_name:
            o_node_id = 'naif'
        elif 'plasma' in full_name:
            o_node_id = 'ppi'
        elif 'ring' in full_name and 'moon' in full_name:
            o_node_id = 'rms'
        elif 'small' in full_name or 'bodies' in full_name:
            o_node_id = 'sbn'

        logger.debug("Derived node ID %s from Contributor field %s",
                     o_node_id, full_name_orig)
    else:
        logger.warning("No Contributor field available for DOI %s, "
                       "defaulting to node ID %s", doi_fields['doi'], o_node_id)

    return o_node_id


def perform_import_to_database(db_name, input_source, dry_run, submitter_email,
                               output_file):
    """
    Imports all records from the input source into a local database.
    The input source may either be an existing XML file containing DOIs to parse,
    or a URL pointing to the OSTI server to pull existing records from.

    Note that all records returned from the OSTI server are associated with the
    NASA-PDS user account.

    Parameters
    ----------
    db_name : str
        Name of the database file to import DOI records to.
    input_source : str
        Either a path to an existing XML file containing OSTI DOI records to
        parse and import, or a URL to the OSTI server to query for existing
        records.
    dry_run : bool
        If true, do not actually commit any parsed DOI records to the local
        database.
    submitter_email : str
        Email address of the user initiating the import.
    output_file : str
        Path to write out the XML label obtained from OSTI. If not specified,
        no file is written.

    """
    o_records_found = 0  # Number of records returned from OSTI
    o_records_processed = 0  # At the end, this value should be = o_records_found - o_records_skipped
    o_records_written = 0  # Number of records actually written to database
    o_records_dois_skipped = 0  # Number of records skipped due to missing lidvid or invalid prefix

    # If use_doi_filtering_flag is set to True, we will allow only DOIs that
    # start with the configured PDS DOI token, e.g. '10.17189'.
    # OSTI server(s) may contain records other than expected, especially the test
    # server. For normal operation use_doi_filtering_flag should be set to False.
    # If set to True, the parameter pds_registration_doi_token in config/conf.ini
    # should be set to 10.17189.
    use_doi_filtering_flag = False

    # If flag skip_db_write_flag set to True, will skip writing of records to
    # database.  Use by developer to skip database write action.
    # For normal operation, skip_db_write_flag should be set to False.
    skip_db_write_flag = False

    if dry_run:
        skip_db_write_flag = True

    o_db_name = db_name

    # If db_name is not provided, get one from config file:
    if not o_db_name:
        # This is the local database we'll be writing to
        o_db_name = m_config.get('OTHER', 'db_file')

    logger.info("Using local database %s", o_db_name)

    transaction_builder = TransactionBuilder(o_db_name)

    # If the input is provided and is a file, parse from it, otherwise query
    # from the OSTI server.
    if input_source and os.path.isfile(input_source):
        dois = _parse_input(input_source)
        o_server_url = input_source
    else:
        # Get the dois from OSTI server.
        # Note that because the name of the server is in the config file,
        # it can be the OPS or TEST server.
        dois, o_server_url = get_dois_from_osti(input_source, output_file)

    o_records_found = len(dois)

    logger.info("Parsed %d DOI(s) from %s", o_records_found, o_server_url)

    # Write each Doi object as a row into the database.
    for item_index, doi in enumerate(dois):
        if use_doi_filtering_flag:
            o_pds_doi_token = m_config.get('OTHER', 'pds_registration_doi_token')

            if doi.doi and not doi.doi.startswith(o_pds_doi_token):
                logger.warning("Skipping non-PDS DOI %s, index %d", doi.doi,
                               item_index)

                o_records_dois_skipped += 1
                continue

        # If the field 'related_identifier' is None, we cannot proceed since
        # it serves as the primary key for our transaction database.
        if not doi.related_identifier:
            logger.warning("Skipping DOI with missing related identifier %s, "
                           "index %d", doi.doi, item_index)

            o_records_dois_skipped += 1
            continue

        doi_fields = doi.__dict__  # Convert the Doi object to a dictionary.

        # Get the node_id from 'contributors' field if can be found.
        node_id = _get_node_id_from_contributors(doi_fields)

        logger.debug("------------------------------------")
        logger.debug('Processed DOI at index %d', item_index)
        logger.debug("Title: %s", doi_fields.get('title'))
        logger.debug("DOI: %s", doi_fields.get('doi'))
        logger.debug("Related Identifier: %s", doi_fields.get('related_identifier'))
        logger.debug("Node ID: %s", node_id)
        logger.debug("Status: %s", str(doi_fields.get('status', 'unknown')))

        o_records_processed += 1

        if not skip_db_write_flag:
            # Write a row into the database and save an output label for each
            # DOI to the local transaction history
            transaction = transaction_builder.prepare_transaction(
                node_id,
                submitter_email,
                [doi]
            )

            transaction.log()

            o_records_written += 1

    return (o_records_found, o_records_processed, o_records_written,
            o_records_dois_skipped)


def main():
    """Entry point for initialize_production_deployment.py"""
    start_time = datetime.now()

    # Make a command parser and parse all the arguments.
    # The values can be accessed using the . dot operator
    parser = create_cmd_parser()
    arguments = parser.parse_args()

    if arguments.debug:
        logger.setLevel(logging.DEBUG)

    logger.info('Starting DOI import to local database...')
    logger.debug('Command-line args: %r', arguments)

    # Do the import operation from OSTI server to database.
    (records_found,
     records_processed,
     records_written,
     records_skipped) = perform_import_to_database(arguments.db_name,
                                                   arguments.input,
                                                   arguments.dry_run,
                                                   arguments.submitter_email,
                                                   arguments.output_file)

    stop_time = datetime.now()
    elapsed_seconds = stop_time.timestamp() - start_time.timestamp()

    logger.info("DOI import complete in %.2f seconds.", elapsed_seconds)
    logger.info("Num records found: %d", records_found)
    logger.info("Num records processed: %d", records_processed)
    logger.info("Num records written: %d", records_written)
    logger.info("Num records skipped: %d", records_skipped)


if __name__ == '__main__':
    main()
