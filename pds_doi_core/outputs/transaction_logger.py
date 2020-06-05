#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

import os
import sys
import time
#from lxml import etree

from datetime import datetime,timezone

from pds_doi_core.input.node_util import NodeUtil
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.db.doi_database import DOIDataBase
from pds_doi_core.outputs.transaction import Transaction

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.outputs.transaction_logger')

class TransactionLogger:
    # This class TransactionLogger provide services to write a transaction from an action {reserve,draft}
    # to disk.

    m_doi_config_util = DOIConfigUtil()
    m_node_util = NodeUtil()
    m_doi_database = DOIDataBase()
    #m_transaction = Transaction()

    def __init__(self):
        self._config = self.m_doi_config_util.get_config()

    def write_transaction_to_disk(self,doi_transaction):
        '''Write a transaction from 'reserve' or 'draft' to disk. The dictionary log_dict will be updated and returned.'''

        transaction_dir = self._config.get('OTHER','transaction_dir')
        logger.debug(f"transaction_dir {transaction_dir}")

        # Get the current time.
        current_time = datetime.now()
        epoch_time = int(time.time())
        now_is = current_time.isoformat()
        logger.debug(f"now_is {now_is}")

        # Get the transaction info.
        log_dict = doi_transaction.get_transaction()

        # Get the fields from dictionary.

        discipline_node = log_dict['discipline_node'].lower()  # The discipline node can be lowercase, make it uppercase.
        action_type     = log_dict['action_type'].upper()      # The value of action_type can be lowercase, make it uppercase.
        input_content   = log_dict['input_content']
        content_type    = log_dict['content_type']
        output_content  = log_dict['output_content']

        logger.debug(f"discipline_node,action_type,content_type {discipline_node},{action_type},{content_type}")

        # Make sure the value of discipline_node is valid.
        self.m_node_util.validate_node_id(discipline_node.upper())  # Because the node_id being validated is upppercase, we use upper()

        # Create directories if they don't exist already.
        final_output_dir = os.path.join(transaction_dir,discipline_node,now_is)
        os.makedirs(final_output_dir,exist_ok=True)

        # Write input file with provided content.
        # Note that the file name is always 'input' plus the extension based on the content_type
        full_input_name = os.path.join(final_output_dir,'input' + '.' + content_type)  # input.xml or input.csv or input.xlsx

        # If the provided content is actually a file name, we copy it, otherwise write it to external file using full_input_name as name.
        if os.path.isfile(input_content):
            import shutil
            shutil.copy2(input_content,full_input_name)
        else:
            file_ptr = open(full_input_name,"w") 
            file_ptr.write(input_content) # Write the entire input content to file.
            file_ptr.write("\n")          # Write carriage return for easy reading of file.
            file_ptr.close()

        # Write output file with provided content.
        # Note that the file name is always 'output.xml'.
        full_output_name = os.path.join(final_output_dir,'output.xml')

        # Add fields to log_dict to return. 
        log_dict['submitted_input_link'] = full_input_name
        log_dict['submitted_output_link'] = full_output_name 
        log_dict['transaction_key']       = os.path.join(discipline_node,now_is)
        log_dict['latest_update']         = epoch_time

        file_ptr = open(full_output_name,"w") 

        # If the content type is bytes, convert it to string first.
        if isinstance(output_content,bytes):
           file_ptr.write(output_content.decode()) # Write the entire output content to file after converting to string.
        else:
            file_ptr.write(output_content) # Write the entire output content to file.
        file_ptr.write("\n")           # Write carriage return for easy reading of file.
        file_ptr.close()

        logger.debug(f"TRANSACTION_INFO:data_tuple ({log_dict['status']},{log_dict['submitter']},{epoch_time},{discipline_node},{log_dict['transaction_key']})")

        return log_dict

    def log_transaction(self,log_dict):
        '''Log a DOI transaction from 'reserve' or 'draft' to disk.'''
        log_dict = self.write_transaction_to_disk(log_dict)

        # The writing to database will be called separately.

        return 1
