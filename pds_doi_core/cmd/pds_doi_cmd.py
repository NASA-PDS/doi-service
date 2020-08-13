#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------
import importlib
import os


from pds_doi_core.util.general_util import get_logger
from pds_doi_core.input.exceptions import UnknownNodeException
from pds_doi_core.actions.action import DOICoreAction
from pds_doi_core.actions.check import DOICoreActionCheck
from pds_doi_core.actions.reserve import DOICoreActionReserve
from pds_doi_core.actions.draft import DOICoreActionDraft
from pds_doi_core.actions.list import DOICoreActionList
from pds_doi_core.actions.release import DOICoreActionRelease

# Get the common logger and set the level for this file.
logger = get_logger('pds_doi_core.cmd.pds_doi_cmd')


def main():
    parser = DOICoreAction.create_cmd_parser()
    arguments = parser.parse_args()
    action_type = arguments.subcommand
    # Moved many argument parsing to each action class.
    
    logger.info(f"run_dir {os.getcwd()}")

    if action_type in {'draft', 'check', 'list', 'release', 'reserve'}:
        module = importlib.import_module(f'pds_doi_core.actions.{action_type}')
        action_class = getattr(module, f'DOICoreAction{action_type.capitalize()}')
        action = action_class()
        action.parse_arguments_from_cmd(arguments)
        output = action.run()
        print(output)
    else:
        logger.error(f"Action {action_type} is not supported yet.")

if __name__ == '__main__':
    main()
