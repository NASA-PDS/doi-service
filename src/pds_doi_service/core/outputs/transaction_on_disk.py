#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
======================
transaction_on_disk.py
======================

Defines the TransactionOnDisk class, which manages writing of a transaction's
input and output products to local disk.
"""

import os
import requests
import shutil

from distutils.dir_util import copy_tree

from pds_doi_service.core.input.node_util import NodeUtil
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_service.core.outputs.transaction_logger')


class TransactionOnDisk:
    """
    This class provides services to write a transaction from an action
    (reserve, draft or release) to disk.
    """
    m_doi_config_util = DOIConfigUtil()
    m_node_util = NodeUtil()
    m_doi_database = None

    def __init__(self):
        self._config = self.m_doi_config_util.get_config()

    def write(self, node_id, update_time, input_ref=None, output_content=None,
              output_content_type=None):
        """
        Write a the input and output products from a transaction to disk.
        The location of the written files is returned.
        """
        transaction_dir = self._config.get('OTHER', 'transaction_dir')
        logger.debug(f"transaction_dir {transaction_dir}")

        # Create the local transaction history directory, if necessary.
        final_output_dir = os.path.join(transaction_dir, node_id, update_time.isoformat())
        os.makedirs(final_output_dir, exist_ok=True)

        if input_ref:
            input_content_type = os.path.splitext(input_ref)[-1]

            # Write input file with provided content.
            # Note that the file name is always 'input' plus the extension based
            # on the content_type (input.xml or input.csv or input.xlsx)
            full_input_name = os.path.join(final_output_dir, 'input' + input_content_type)

            # If the provided content is actually a file name, we copy it,
            # otherwise write it to external file using full_input_name as name.
            if os.path.isfile(input_ref):
                shutil.copy2(input_ref, full_input_name)
            elif os.path.isdir(input_ref):
                copy_tree(input_ref, full_input_name)
            else:  # remote resource
                r = requests.get(input_ref, allow_redirects=True)

                with open(full_input_name, 'wb') as outfile:
                    outfile.write(r.content)

                r.close()

        # Write output file with provided content
        # The extension of the file is determined by the provided content type
        if output_content and output_content_type:
            full_output_name = os.path.join(
                final_output_dir, '.'.join(['output', output_content_type])
            )

            with open(full_output_name, 'w') as outfile:
                outfile.write(output_content)

        logger.info(f'transaction files saved in {final_output_dir}')

        return final_output_dir
