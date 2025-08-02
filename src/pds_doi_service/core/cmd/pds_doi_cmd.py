#!/usr/bin/env python
#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
==============
pds_doi_cmd.py
==============

Contains the main function for the pds_doi_cmd.py script.
"""
import importlib
import os

from pds_doi_service.core.actions.action import DOICoreAction
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


def main():
    """
    Main entry point for the PDS DOI service command-line interface.

    This function serves as the primary entry point for the DOI service CLI,
    handling command-line argument parsing and delegating execution to the
    appropriate action class based on the subcommand provided.

    The function:
    1. Creates and parses command-line arguments using DOICoreAction's parser
    2. Dynamically imports the appropriate action module based on the subcommand
    3. Instantiates the corresponding action class
    4. Executes the action with the provided arguments
    5. Prints any output returned by the action

    Supported subcommands include: reserve, release, update, check, list, roundup

    Returns
    -------
    None
        Output is printed to stdout if the action returns any content.
    """
    parser = DOICoreAction.create_cmd_parser()
    arguments = parser.parse_args()
    action_type = arguments.subcommand

    # Moved many argument parsing to each action class.
    logger.info(f"run_dir {os.getcwd()}")

    module = importlib.import_module(f"pds_doi_service.core.actions.{action_type}")
    action_class = getattr(module, f"DOICoreAction{action_type.capitalize()}")
    action = action_class()

    # Convert the argparse.Namespace to a dictionary that we can feed in as kwargs
    kwargs = vars(arguments)

    # No action subclasses should be expecting subcommand, so remove it here
    kwargs.pop("subcommand", None)

    output = action.run(**kwargs)

    if output is not None:
        print(output)


if __name__ == "__main__":
    main()
