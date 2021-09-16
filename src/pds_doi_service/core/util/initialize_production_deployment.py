#!/usr/bin/env python
#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
===================================
initialize_production_deployment.py
===================================

Script used to import the available DOIs from a service provider into the local
production database.
"""
# Parameters to this script:
#
#    The -S (optional) is the name of the DOI service provider to pull existing
#        DOI records from. When used with the -i option, it should correspond
#        to the format of the provided input file. Should be set to either osti
#        or datacite.
#    The -p (optional) may be used to specify a DOI prefix to query for. By
#    default the prefix is obtained from the INI config.
#    The -s (required) is email of the PDS operator: -s pds-operator@jpl.nasa.gov
#    The -i is optional. If the input is provided and is a file, parse from it
#        The format of input file is the same format of text returned from
#        querying the server via a browser or curl command.
#        If provided,, this will override the url in the config file.
#    The -d is optional. If provided it is the name of the database file to
#    write records to: -d doi.db
#        If provided, this will override the db_name in the config file.
#    The --dry-run parameter allows the code to parse the input or querying the
#    server without writing to database to see how long the code takes and if
#    there are records skipped.
#    The --debug parameter allows the code to print debug statements useful to
#    see if something goes wrong.
#
#
# Example runs:
#
# initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -i my_input.xml -d temp.db --dry-run --debug >& t1 ; tail -20 t1
# initialize_production_deployment.py -s pds-operator@jpl.nasa.gov -d temp.db --dry-run --debug >& t1 ; tail -20 t1
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
import json
import logging
import os
from datetime import datetime

from pds_doi_service.core.input.exceptions import CriticalDOIException
from pds_doi_service.core.input.exceptions import InputFormatException
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_JSON
from pds_doi_service.core.outputs.osti.osti_web_parser import DOIOstiXmlWebParser
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.outputs.service import SERVICE_TYPE_DATACITE
from pds_doi_service.core.outputs.service import VALID_SERVICE_TYPES
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
        description="Script to bulk import existing DOIs into the local " "transaction database.",
        epilog="Note: When DOI records are imported to the local transaction "
        "database, the DOI service creates an associated output label "
        "for each record under the transaction_history directory. The "
        "format of this output label is driven by the SERVICE.provider "
        "field of the INI. Please ensure the field is set appropriately "
        "before using this script, as a mismatch could cause parsing "
        "errors when using the DOI service after this script.",
    )
    parser.add_argument(
        "-S",
        "--service",
        required=False,
        default=None,
        help="Name of the service provider to pull existing DOI "
        "records from. If not provided, the provider configured "
        "by the DOI service configuration INI is used by "
        "default. Should be one of: [{}]".format(", ".join(VALID_SERVICE_TYPES)),
    )
    parser.add_argument(
        "-p",
        "--prefix",
        required=False,
        default=None,
        help="Specify the DOI prefix value to query the service "
        "provider for. If not provided, the prefix value "
        "configured to the providing in the INI config is "
        "used by default.",
    )
    parser.add_argument(
        "-s",
        "--submitter-email",
        required=False,
        default="pds-operator@jpl.nasa.gov",
        help="The email address of the user performing the "
        "deployment database initialization. Defaults to "
        "pds-operator@jpl.nasa.gov.",
    )
    parser.add_argument(
        "-d",
        "--db-name",
        required=False,
        help="Name of the SQLite3 database file name to commit "
        "DOI records to. If not provided, the file name is "
        "obtained from the DOI service INI config.",
    )
    parser.add_argument(
        "-i",
        "--input-file",
        required=False,
        help="Input file (XML or JSON) to import existing DOIs from. "
        "If no value is provided, the server URL "
        "specified by the DOI service configuration INI "
        "file is used by default.",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        required=False,
        default=None,
        help="Path to write out the DOI JSON labels as returned "
        "from the query. When created, this file can be used "
        "with the --input option to import records at a "
        "later time without re-querying the server. "
        "This option has no effect if --input already "
        "specifies an input file.",
    )
    parser.add_argument(
        "--dry-run", required=False, action="store_true", help="Flag to suppress actual writing of DOIs to database."
    )
    parser.add_argument("--debug", required=False, action="store_true", help="Flag to print debug statements.")

    return parser


def _read_from_local_xml(path):
    """
    Read from a local xml file containing output from a query.

    Note that since the PDS DOI service only supports XML labels from OSTI,
    that is the default parser used by this function.

    Parameters
    ----------
    path : str
        Path of the XML file to read and parse.

    Returns
    -------
    dois : list of Doi
        The DOI objects parsed from the XML label.

    """
    try:
        with open(path, mode="r") as f:
            doi_xml = f.read()
    except Exception as e:
        raise CriticalDOIException(str(e))

    dois, _ = DOIOstiXmlWebParser.parse_dois_from_label(doi_xml)

    return dois


def _read_from_local_json(service, path):
    """
    Read from a local JSON file containing output from a query.

    The appropriate JSON parser (OSTI or DataCite) is determined based on
    the provided service type.

    Parameters
    ----------
    service : str
        The name of the service provider corresponding to the JSON format
        to read and parse.
    path : str
        Path to the JSON file to read and parse.

    Returns
    -------
    dois : list of Doi
        The DOI objects parsed from the JSON label.

    """
    try:
        with open(path, mode="r") as f:
            doi_json = f.read()
    except Exception as e:
        raise CriticalDOIException(str(e))

    web_parser = DOIServiceFactory.get_web_parser_service(service)

    try:
        dois, _ = web_parser.parse_dois_from_label(doi_json, content_type=CONTENT_TYPE_JSON)
    except Exception:
        raise InputFormatException(
            f"Unable to parse input file {path} using parser {web_parser.__name__}\n"
            f"Please ensure the --service flag is set correctly to specify the "
            f"correct parser type for the format."
        )

    return dois


def _read_from_path(service, path):
    """
    Reads the label at the provided path, using the appropriate parser for the
    provided service type.

    Parameters
    ----------
    service : str
        The name of the service provider corresponding to the format
        to read and parse. Only used for JSON labels.
    path : str
        Path to the label to read and parse. The label format (XML or JSON) is
        derived from the path's file extension.

    Returns
    -------
    dois : list of Doi
        The DOI objects parsed from the label.

    Raises
    ------
    InputFormatException
        If the file path does not exist or does not correspond to an XML or
        JSON file.

    """
    if not os.path.exists(path):
        raise InputFormatException(f"Error reading file {path}. " "File may not exist.")

    if path.endswith(".xml"):
        return _read_from_local_xml(path)
    elif path.endswith(".json"):
        return _read_from_local_json(service, path)

    raise InputFormatException(f"File {path} is not supported. " f"Only .xml and .json are supported.")


def get_dois_from_provider(service, prefix, output_file=None):
    """
    Queries the service provider for all the current DOI associated with the
    provided prefix.

    Parameters
    ----------
    service : str
        Name of the service provider to pull DOI's from.
    prefix : str
        DOI prefix to query for.
    output_file : str, optional
        If provided, path to an output file to write the results of the DOI
        query to.

    Returns
    -------
    dois : list of Doi
        The DOI objects obtained from the service provider.
    server_url : str
        The URL of the service provider endpoint. Helpful for logging purposes.

    """
    if service == SERVICE_TYPE_DATACITE:
        query_dict = {"doi": f"{prefix}/*"}
    else:
        query_dict = {"doi": prefix}

    server_url = m_config.get(service.upper(), "url")

    logger.info("Using %s server URL %s", service, server_url)

    web_client = DOIServiceFactory.get_web_client_service(service)

    doi_json = web_client.query_doi(query=query_dict, content_type=CONTENT_TYPE_JSON)

    if output_file:
        logger.info("Writing query results to %s", output_file)

        with open(output_file, "w") as outfile:
            json.dump(json.loads(doi_json), outfile, indent=4)

    web_parser = DOIServiceFactory.get_web_parser_service(service)

    dois, _ = web_parser.parse_dois_from_label(doi_json, content_type=CONTENT_TYPE_JSON)

    return dois, server_url


def _get_node_id_from_contributors(doi_fields):
    """
    Given a doi object, attempt to extract the node_id from contributors field.
    If unable to, return 'eng' as default.
    This function is a one-off as well so no fancy logic.

    Parameters
    ----------
    doi_fields : dict
        DOI metadata fields to obtain PDS node ID from.

    Returns
    -------
    node_id : str
        The three-character PDS identifier determined from the DOI's contributor
        field.

    """
    node_id = "eng"

    if doi_fields.get("contributor"):
        full_name_orig = doi_fields["contributor"]
        full_name = full_name_orig.lower()

        if "atmospheres" in full_name:
            node_id = "atm"
        elif "engineering" in full_name:
            node_id = "eng"
        elif "geosciences" in full_name:
            node_id = "geo"
        elif "imaging" in full_name:
            node_id = "img"
        elif "cartography" in full_name:
            node_id = "img"
        # Some uses title: Navigation and Ancillary Information Facility Node
        # Some uses title: Navigational and Ancillary Information Facility
        # So check for both
        elif "navigation" in full_name and "ancillary" in full_name:
            node_id = "naif"
        elif "navigational" in full_name and "ancillary" in full_name:
            node_id = "naif"
        elif "plasma" in full_name:
            node_id = "ppi"
        elif "ring" in full_name and "moon" in full_name:
            node_id = "rms"
        elif "small" in full_name or "bodies" in full_name:
            node_id = "sbn"

        logger.debug("Derived node ID %s from Contributor field %s", node_id, full_name_orig)
    else:
        logger.warning(
            "No Contributor field available for DOI %s, " "defaulting to node ID %s", doi_fields["doi"], node_id
        )

    return node_id


def perform_import_to_database(service, prefix, db_name, input_source, dry_run, submitter_email, output_file):
    """
    Imports all records from the input source into a local database.
    The input source may either be an existing file containing DOIs to parse,
    or a URL pointing to the server to pull existing records from.

    Note that all records returned from the server are associated with the
    NASA-PDS user account.

    Parameters
    ----------
    service : str
        Name of the service provider to import DOI's from.
    prefix : str
        DOI prefix value to query for.
    db_name : str
        Name of the database file to import DOI records to.
    input_source : str
        Either a path to an existing file containing DOI records to
        parse and import, or a URL to the server to query for existing
        records.
    dry_run : bool
        If true, do not actually commit any parsed DOI records to the local
        database.
    submitter_email : str
        Email address of the user initiating the import.
    output_file : str
        Path to write out the label obtained from the server. If not specified,
        no file is written.

    """
    o_records_found = 0  # Number of records returned
    o_records_processed = 0  # At the end, this value should be = o_records_found - o_records_skipped
    o_records_written = 0  # Number of records actually written to database
    o_records_dois_skipped = 0  # Number of records skipped due to missing lidvid or invalid prefix

    if not service:
        service = DOIServiceFactory.get_service_type()

    logger.info("Using source service provider %s", service)

    if not prefix:
        prefix = m_config.get(service.upper(), "doi_prefix")

    logger.info("Using DOI prefix %s", prefix)

    # If db_name is not provided, get one from config file:
    if not db_name:
        # This is the local database we'll be writing to
        db_name = m_config.get("OTHER", "db_file")

    logger.info("Using local database %s", db_name)

    transaction_builder = TransactionBuilder(db_name)

    # If the input is provided, parse from it. Otherwise query the server.
    if input_source:
        dois = _read_from_path(service, input_source)
        server_url = input_source
    else:
        # Get the dois from the server.
        # Note that because the name of the server obtained from the config file,
        # it could be the OPS or TEST server.
        dois, server_url = get_dois_from_provider(service, prefix, output_file)

    o_records_found = len(dois)

    logger.info("Parsed %d DOI(s) from %s", o_records_found, server_url)

    # Write each Doi object as a row into the database.
    for item_index, doi in enumerate(dois):
        # If the field 'related_identifier' is None, we cannot proceed since
        # it serves as the primary key for our transaction database.
        if not doi.related_identifier:
            logger.warning("Skipping DOI with missing related identifier %s, " "index %d", doi.doi, item_index)

            o_records_dois_skipped += 1
            continue

        doi_fields = doi.__dict__  # Convert the Doi object to a dictionary.

        # Get the node_id from 'contributors' field if can be found.
        node_id = _get_node_id_from_contributors(doi_fields)

        logger.debug("------------------------------------")
        logger.debug("Processed DOI at index %d", item_index)
        logger.debug("Title: %s", doi_fields.get("title"))
        logger.debug("DOI: %s", doi_fields.get("doi"))
        logger.debug("Related Identifier: %s", doi_fields.get("related_identifier"))
        logger.debug("Node ID: %s", node_id)
        logger.debug("Status: %s", str(doi_fields.get("status", "unknown")))

        o_records_processed += 1

        if not dry_run:
            # Write a row into the database and save an output label for each
            # DOI to the local transaction history. The format (OSTI vs. Datacite)
            # of the output label is based on the service provider setting in
            # the INI config.
            transaction = transaction_builder.prepare_transaction(
                node_id, submitter_email, doi, output_content_type=CONTENT_TYPE_JSON
            )

            transaction.log()

            o_records_written += 1

    return (o_records_found, o_records_processed, o_records_written, o_records_dois_skipped)


def main():
    """Entry point for initialize_production_deployment.py"""
    start_time = datetime.now()

    # Make a command parser and parse all the arguments.
    # The values can be accessed using the . dot operator
    parser = create_cmd_parser()
    arguments = parser.parse_args()

    logger.setLevel(logging.INFO)

    if arguments.debug:
        logger.setLevel(logging.DEBUG)

    logger.info("Starting DOI import to local database...")
    logger.debug("Command-line args: %r", arguments)

    # Do the import operation from remote server to database.
    (records_found, records_processed, records_written, records_skipped) = perform_import_to_database(
        arguments.service,
        arguments.prefix,
        arguments.db_name,
        arguments.input_file,
        arguments.dry_run,
        arguments.submitter_email,
        arguments.output_file,
    )

    stop_time = datetime.now()
    elapsed_seconds = stop_time.timestamp() - start_time.timestamp()

    logger.info("DOI import complete in %.2f seconds.", elapsed_seconds)
    logger.info("Num records found: %d", records_found)
    logger.info("Num records processed: %d", records_processed)
    logger.info("Num records written: %d", records_written)
    logger.info("Num records skipped: %d", records_skipped)


if __name__ == "__main__":
    main()
