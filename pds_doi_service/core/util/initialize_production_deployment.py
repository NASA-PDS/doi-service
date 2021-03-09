#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------

# This is a one-off script to import current DOIs from OSTI server into the production database.
#
# Parameters to this script:
#
#    The -s (required) is email of the PDS operator: -s pds-operator@jpl.nasa.gov
#    The -i is optional. If the input is provided and is a file, parse from it, otherwise query from the URL input: -i https://www.osti.gov/iad2/api/records
#        The format of input XML file is the same format of text returned from querying the OSTI server via a browser or curl command.
#        If provided and a URL of the OSTI server, this will override the url in the config file.
#    The -d is optional.  If provided it is the name of the database file to write records to: -d doi.db
#        If provided, this will override the db_name in the config file.
#    The --dry-run parameter allows the code to parse the input or querying the server without writing to database
#        to see how long the code takes and if there are records skipped.
#    The --debug parameter allows the code to print debug statements useful to see if something goes wrong.
#
# Make sure the -i parameter or the url parameter in config/conf.ini points to the OPS server from OSTI 'https://www.osti.gov/iad2/api/records'
# as the TEST server 'https://www.osti.gov/iad2test/api/records' only has test records and it takes a long time to run.
#
# Example runs:
#
# python3 pds_doi_core/util/initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -i my_input.xml -d temp.db --dry-run --debug >& t1 ; tail -20 t1
# python3 pds_doi_core/util/initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -i https://www.osti.gov/iad2/api/records -d temp.db --dry-run --debug >& t1 ; tail -20 t1
# python3 pds_doi_core/util/initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -i my_input.xml -d temp.db --debug >& t1 ; tail -20 t1
# python3 pds_doi_core/util/initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -d temp.db --debug >& t1 ; tail -20 t1

# Note: As of 10/01/2020, there is one DOI that does not have any info for lidvid that caused the software to crash.  There may be more.
#       10.17189/1517674
#       There is a way to update this information by querying the server with this id and update the output
#       and feed this output with the -i parameter to this script.
#       This is the curl command:
#           curl -v --netrc-file ~/.netrc https://www.osti.gov/iad2/api/records/1517674 -X GET -H "Content-Type: application/xml" -H "Accept: application/xml > my_input.xml
#       Then the file my_input.xml can be edited to include the lidvid in the accession_number tag
#           <accession_number>a:b:c::1.0</accession_number>
# Note: As of 10/05/2020, there are 105 records that does not have info for lidvid.  Ron has been notified.
# Note: As of 10/06/2020, there are 1058 DOIs in the OPS OSTI server associated with the NASA-PDS account.

import argparse
import logging
import os

from datetime import datetime

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.input.exceptions import InputFormatException, CriticalDOIException
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

from pds_doi_service.core.outputs.osti_web_client import DOIOstiWebClient
from pds_doi_service.core.outputs.osti_web_parser import DOIOstiWebParser

# Get the common logger and set the level for this file.
logger = get_logger('pds_doi_core.util.initialize_production_deployment')
logger.setLevel(logging.INFO)

m_doi_config_util = DOIConfigUtil()
m_config = m_doi_config_util.get_config()

def create_cmd_parser():
    parser = argparse.ArgumentParser(
        description='Script to import existing DOIs into local database\n')
    parser.add_argument("-i", "--input", help="Input file to import existing DOIs from or URL of OSTI server.",
                        required=False)
    parser.add_argument("-s", "--submitter_email", help="The email address of the user performing the initialization of deployment database.",
                        required=True)
    parser.add_argument("-d","--db_name", help="Optional database name instead of one from config.",
                        required=False)
    parser.add_argument("--dry-run", help="Flag to suppress the writing of DOIs to database.",
                        required=False,action="store_true")
    parser.add_argument("--debug", help="Flag to print debug statements.",
                        required=False,action="store_true")
    return parser

def _read_from_local_xml(path):
    '''Function read from local xml file containing output from OSTI query.'''
    try:
        with open(path, mode='r') as f:
            doi_xml = f.read()
    except Exception as e:
        raise CriticalDOIException(str(e))
    dois, _ = DOIOstiWebParser.parse_osti_response_xml(doi_xml)
    return dois

def _read_from_path(path):
    if os.path.isfile(path):
        if path.endswith('.xml'):
            return _read_from_local_xml(path)
        else:
            logger.error(f'file {path} not supported.  Only .xml are supported.')
            exit(1)

def _parse_input(input):
    if os.path.exists(input):
        return _read_from_path(input)
    else:
        raise InputFormatException(f"Error reading file {input}.  File may not exist.")

def get_dois_from_osti(target_url):
        """
        Function query the OSTI server for all the current DOI associated with the PDS-USER account.
        The server name is fetched from the config file with the 'url' field in 'OSTI' grouping if target_url is None.
        :return: dois,o_server_url:
        """
        query_dict = {}
        if target_url is None:
            o_server_url = m_config.get('OSTI', 'url')
        else:
            o_server_url = target_url
        logger.info(f"o_server_url {o_server_url}")

        doi_xml = DOIOstiWebClient().webclient_query_doi(o_server_url,
                                                         query_dict,
                                                         i_username=m_config.get('OSTI', 'user'),
                                                         i_password=m_config.get('OSTI', 'password'))
        dois, _ = DOIOstiWebParser.parse_osti_response_xml(doi_xml)

        logger.info(f"o_server_url,len(dois) {o_server_url,len(dois)}")

        return dois, o_server_url

def _get_node_id_from_contributors(doi_field):
    # Given a doi object, attempt to extract the node_id from contributors field.  If not able to, return 'eng' as default.
    # This function is a one-off as well so no fancy logic.
    # m_node_id_dict = {'ATM': 'Atmospheres',
    #                  'ENG': 'Engineering',
    #                  'GEO': 'Geosciences',
    #                  'IMG': 'Cartography and Imaging Sciences Discipline',
    #                  'NAIF': 'Navigational and Ancillary Information Facility',
    #                  'PPI': 'Planetary Plasma Interactions',
    #                  'RMS': 'Ring-Moon Systems',
    #                  'SBN': 'Small Bodies'}

    o_node_id = 'eng'
    full_name = 'dummy_full_name'  # If a 'contributors' field exist, this value will get a valid value set.

    if doi_field['contributors'] and len(doi_field['contributors']) > 0:
        full_name = doi_field['contributors'][0]['full_name']
        if 'Atmospheres'.lower() in full_name.lower():
            o_node_id = 'atm'
        if 'Engineering'.lower() in full_name.lower():
            o_node_id = 'atm'
        if 'Geosciences'.lower() in full_name.lower():
            o_node_id = 'geo'
        if 'Imaging'.lower() in full_name.lower():
            o_node_id = 'img'
        if 'Cartography'.lower() in full_name.lower():
            o_node_id = 'img'
        # Some uses title: Navigation and Ancillary Information Facility Node
        # Some uses title: Navigational and Ancillary Information Facility
        # So check for both
        if 'Navigation'.lower() in full_name.lower() and 'Ancillary'.lower() in full_name.lower():
            o_node_id = 'naif'
        if 'Navigational'.lower() in full_name.lower() and 'Ancillary'.lower() in full_name.lower():
            o_node_id = 'naif'
        if 'Plasma'.lower() in full_name.lower():
            o_node_id = 'ppi'
        if 'Ring'.lower() in full_name.lower() and 'Moon'.lower() in full_name.lower():
            o_node_id = 'rms'
        if 'Small'.lower() in full_name.lower() or 'Bodies'.lower() in full_name.lower():
            o_node_id = 'sbn'
        logger.debug(f"original_full_name,o_node_id {full_name},{o_node_id}")

    logger.debug(f"o_node_id,full_name {o_node_id,full_name}")
    return o_node_id

def perform_import_to_database(db_name, input, dry_run, submitter_email):
    # Function import all records from input (if provided) into local database.  If not provided will query from OSTI server.
    # Note that all records returned from are associated with the NASA-PDS user account.

    o_records_found        = 0 # Number of records returned from OSTI.
    o_records_processed    = 0 # At the end, this value should be the same as o_records_found
    o_records_written      = 0 # Number of records written to database.
    o_records_dois_skipped = 0 # Number of records not processed because of missing lidvid or not start with '10.17189'.
    o_records_valid        = 0 # Number of good or valid records with all metadata required.
    o_pds_doi_token        = None   # Will be set to valid value if use_doi_filtering_flag is True.

    m_doi_config_util = DOIConfigUtil()
    m_config = m_doi_config_util.get_config()

    # If flag use_doi_filtering_flag set to True, will filter only DOIs that starts with o_pds_doi_token, e.g. '10.17189'.
    # OSTI server(s) may contain records other than expected especially the test server.
    # For normal operation use_doi_filtering_flag should be set to False.
    # If set to True, the parameter pds_registration_doi_token in config/conf.ini should be set to 10.17189.
    use_doi_filtering_flag = False
    if use_doi_filtering_flag:
        o_pds_doi_token = m_config.get('OTHER','pds_registration_doi_token')

    # If flag skip_db_write_flag set to True, will skip writing of records to database.  Use by developer to skip database write action.
    # For normal operation, skip_db_write_flag should be set to False.
    skip_db_write_flag = False
    if dry_run:
        skip_db_write_flag = True
    logger.info(f"skip_db_write_flag {skip_db_write_flag}")
    logger.info(f"db_name {db_name}")

    # If db_name is not provided, get one from config file:
    if db_name is None:
        # This is the local database (the metadata from OSTI) will be written to.
        o_db_name = m_config.get('OTHER','db_file')
        # TODO: remove next line once done testing.
        #o_db_name = 'temp_doi_temp.db'
    else:
        o_db_name = db_name

    logger.info(f"o_db_name {o_db_name}")

    if not o_db_name.endswith('.db'):
        logger.error(f"File name for Sqlite3 database should end with '.db'.  Provided {o_db_name}")
        exit(0)

    transaction_db_dao = DOIDataBase(o_db_name)

    o_server_url = None
    # If the input is provided and is a file, parse from it, otherwise query from the OSTI server.
    if input and os.path.isfile(input):
       dois =  _parse_input(input)
    else:
        # Get the dois from OSTI server.
        # Note that because the name of the server is in the config file, it can be the OPS or TEST server.
        dois, o_server_url = get_dois_from_osti(input)

    o_records_found = len(dois)

    logger.info(f"input,o_server_url,o_records_found {input,o_server_url,o_records_found}")

    transaction_dir = m_config.get('OTHER','transaction_dir')
    transaction_time = datetime.now()

    # Because the database requires transaction_key to be non-null, we build one here for 'eng' node for all transactions.
    node_id            = 'eng'
    transaction_io_dir = os.path.join(transaction_dir, node_id, transaction_time.isoformat())

    item_index = 0 # Used in debugging to show where the record is in the list.

    # Write each Doi object as a row into the database.
    for doi in dois:

        if use_doi_filtering_flag:
            if hasattr(doi, 'doi') and not doi.doi.startswith(o_pds_doi_token):
                logger.debug(f"SKIPPING_NON_PDS_DOI {doi.doi}")
                o_records_dois_skipped += 1
                o_records_processed += 1
                item_index += 1
                continue # Skip this record because it is not associated with the DOI group given to PDS.

        # If the field 'related_identifier' is None, we cannot proceed since database writing does not allow a None value.
        lidvid = [None]
        if doi.related_identifier is None:
                logger.debug(f"SKIPPING_NONE_RELATED_IDENTIFIER {doi.doi}")
                o_records_dois_skipped += 1
                o_records_processed += 1
                item_index += 1
                continue

        # The lidvid is two parts separated by "::", e.g. "urn:nasa:pds:lab_shocked_feldspars_3::1.0"
        if doi.related_identifier:
            lidvid = doi.related_identifier.split('::')
        doi_field = doi.__dict__  # Convert the Doi object to a dictionary.

        # Get the node_id from 'contributors' field if can be found.
        node_id = _get_node_id_from_contributors(doi_field)

        logger.debug(f"node_id,submitter_email,doi.contributors {node_id,submitter_email,doi.contributors}")

        # Create a dictionary with these fields {'doi', 'status', 'title', 'product_type', 'product_type_specific'}
        # from fields in doi_field dictionary.
        k_doi_params = dict((k, doi_field[k]) for k in
             doi_field.keys() & {'doi', 'status', 'title', 'product_type', 'product_type_specific'})

        logger.info(f"DOI_item_only {k_doi_params['doi']}")
        logger.info(f"DOI_item,status {k_doi_params['doi'],k_doi_params['status']}")

        logger.debug(f"--------------------")
        logger.debug(f"item_index:title {item_index,k_doi_params['title']}")
        logger.debug(f"item_index:doi {item_index,k_doi_params['doi']}")
        logger.debug(f"item_index:lidvid[0] {item_index,lidvid[0]}")
        if len(lidvid) > 1:
            logger.debug(f"item_index:lidvid[1] {item_index,lidvid[1]}")
        logger.debug(f"item_index:transaction_time {item_index,transaction_time}")
        logger.debug(f"item_index:submitter_email {item_index,submitter_email}")
        logger.debug(f"item_index:node_id {item_index,node_id}")
        logger.debug(f"item_index:transaction_io_dir {item_index,transaction_io_dir}")
        logger.debug(f"item_index:k_doi_params {item_index,k_doi_params}")

        o_records_processed += 1
        o_records_valid     += 1

        if not skip_db_write_flag:
            # Write a row into the database.
            transaction_db_dao.write_doi_info_to_database(
                lid=lidvid[0],
                vid=lidvid[1] if len(lidvid) > 1 else None,
                transaction_date=transaction_time,
                submitter=submitter_email,
                discipline_node=node_id,
                transaction_key=transaction_io_dir,
                **k_doi_params
            )
            o_records_written += 1

        item_index += 1
    # end for doi in dois:

    return o_server_url, o_pds_doi_token, o_records_found, o_db_name, o_records_processed, o_records_written, o_records_dois_skipped, o_records_valid

def main():
    start_time = datetime.now()

    parser = create_cmd_parser()    # Make a command parser.
    logger.info(f"parser {parser}")
    arguments = parser.parse_args() # Parse all the arguments.  The values can be accessed using the . dot operator
    logger.info(f"arguments {arguments}")
    logger.info(f"arguments.submitter_email {arguments.submitter_email}")
    if arguments.submitter_email is None: # Value of arguments.submitter_email can be None if -s parameter becomes optional.
        submitter_email = 'pds-operator@jpl.nasa.gov'  # Use default value
    else:
        submitter_email = arguments.submitter_email
    dry_run = False
    # Note that the parameter --dry-run (with dash) is now dry_run (with underscore) in arguments object.
    if arguments.dry_run is not None and arguments.dry_run == True:
        dry_run = True
    debug_flag = False
    if arguments.debug is not None and arguments.debug == True:
        debug_flag = True
        logger.setLevel(logging.DEBUG)  # Useful to see debug statements.

    # Do the import operation from OSTI server to database.
    server_url, pds_doi_token, records_found, db_name, records_processed, records_written, num_dois_skipped, records_valid = perform_import_to_database(arguments.db_name,arguments.input,dry_run,submitter_email)

    stop_time = datetime.now()
    logger.info(f"server_url,pds_doi_token,records_found,db_name {server_url,pds_doi_token,records_found,db_name}")
    logger.info(f"records_found,records_processed,records_written,num_dois_skipped,records_valid {records_found,records_processed,records_written,num_dois_skipped,records_valid}")
    elapsed_seconds = stop_time.timestamp() - start_time.timestamp()
    logger.info(f"start_time      {start_time}")
    logger.info(f"stop_time       {stop_time}")
    logger.info(f"elapsed_seconds {elapsed_seconds}")
    logger.info(f"Done with perform_import_to_database()")

if __name__ == '__main__':
    main()
