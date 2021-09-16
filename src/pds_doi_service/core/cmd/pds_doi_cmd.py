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
    print(output)


if __name__ == "__main__":
    main()
