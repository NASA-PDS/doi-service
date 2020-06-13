#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

import os
import requests
from pds_doi_core.input.node_util import NodeUtil
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger
logger = get_logger('pds_doi_core.outputs.transaction_logger')


class TransactionOnDisk:
    # This class TransactionLogger provide services to write a transaction from an action {reserve,draft}
    # to disk and in database

    m_doi_config_util = DOIConfigUtil()
    m_node_util = NodeUtil()
    m_doi_database = None

    def __init__(self):
        self._config = self.m_doi_config_util.get_config()

    def write(self, node_id, update_time, input_ref, output_content):
        """Write a transaction from 'reserve' or 'draft' to disk.
        The dictionary log_dict will be updated and returned."""

        transaction_dir = self._config.get('OTHER','transaction_dir')
        logger.debug(f"transaction_dir {transaction_dir}")

        input_content_type = input_ref.split('.')[-1]

        # Create directories if they don't exist already.
        final_output_dir = os.path.join(transaction_dir,node_id,update_time.isoformat())
        os.makedirs(final_output_dir, exist_ok=True)

        # Write input file with provided content.
        # Note that the file name is always 'input' plus the extension based on the content_type
        full_input_name = os.path.join(final_output_dir, 'input' + '.' + input_content_type)  # input.xml or input.csv or input.xlsx

        # If the provided content is actually a file name, we copy it, otherwise write it to external file using full_input_name as name.
        if os.path.isfile(input_ref):
            import shutil
            shutil.copy2(input_ref,full_input_name)
        else: # remote resource
            r = requests.get(input_ref, allow_redirects=True)
            open(full_input_name, 'wb').write(r.content)

        # Write output file with provided content.
        # Note that the file name is always 'output.xml'.
        full_output_name = os.path.join(final_output_dir,'output.xml')

        file_ptr = open(full_output_name,"w")
        file_ptr.write(output_content)
        file_ptr.close()

        logger.info(f'transaction files saved in {final_output_dir}')

        return final_output_dir

