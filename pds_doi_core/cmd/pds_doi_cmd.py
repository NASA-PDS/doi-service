#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------
import os
import datetime

from pds_doi_core.util.cmd_parser import create_cmd_parser
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.actions.reserve import DOICoreActionReserve
from pds_doi_core.actions.draft import DOICoreActionDraft
from pds_doi_core.actions.list import DOICoreActionList

# Get the common logger and set the level for this file.
logger = get_logger('pds_doi_core.cmd.pds_doi_cmd')


def main():
    parser = create_cmd_parser()
    arguments = parser.parse_args()
    action_type = arguments.action
    submitter_email = arguments.submitter_email
    node_id = arguments.node_id.lstrip().rstrip()  # Remove any leading and trailing blanks.
    input_location = arguments.input

    query_criterias = {}
    # Action 'list' has more arguments to parse.
    if action_type == 'list':
        input_doi_token = arguments.doi
        output_format = arguments.format_output
        start_update  = arguments.start_update
        end_update    = arguments.end_update
        lid           = arguments.lid
        lidvid        = arguments.lidvid

        if input_doi_token:
            query_criterias['doi'] = input_doi_token.split(',') 
        if lid:
            query_criterias['lid'] = lid.split(',') 
        if lidvid:
            query_criterias['lidvid'] = lidvid.split(',') 
        query_criterias['submitter'] = submitter_email.split(',') 
        query_criterias['node'] = node_id.split(',') 
        if start_update:
            query_criterias['start_update'] = datetime.datetime.strptime(start_update,'%Y-%m-%dT%H:%M:%S.%f');
        if end_update:
            query_criterias['end_update']   = datetime.datetime.strptime(end_update,'%Y-%m-%dT%H:%M:%S.%f');
        logger.debug(f"output_format ['{output_format}']")
        logger.debug(f"query_criterias ['{query_criterias}']")
    
    logger.info(f"run_dir {os.getcwd()}")
    logger.info(f"input_location {input_location}")
    logger.info(f"node_id ['{node_id}']")

    try:
        if action_type == 'draft':
            draft = DOICoreActionDraft()
            o_doi_label = draft.run(input_location, node_id, submitter_email)
            print(o_doi_label)

        elif action_type == 'list':
            list_obj = DOICoreActionList() # The token 'list' is a reserved word so we are using list_obj instead.
            # The variable input_location is the name of the database file.  It should already exist.
            # The 'list' action does not take node_id as a parameter since it is part of the query_criterias dictionary as a list.
            o_doi_list = list_obj.run(input_location,
                                       output_format,
                                       query_criterias)
            print(o_doi_list)

        elif action_type == 'reserve':
            reserve = DOICoreActionReserve()
            o_doi_label = reserve.run(input_location,
                                      node_id,
                                      submitter_email,
                                      submit_label_flag=True)
            # By default, submit_label_flag=True if not specified.
            # By default, write_to_file_flag=True if not specified.
            print(o_doi_label)
        else:
            logger.error(f"Action {action_type} is not supported yet.")
            exit(1)
    except UnknownNodeException as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
