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
import shutil
from distutils.dir_util import copy_tree

import requests
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class TransactionOnDisk:
    """
    This class provides services to write a transaction from an action
    (reserve, update or release) to disk.
    """

    m_doi_config_util = DOIConfigUtil()

    def __init__(self):
        self._config = self.m_doi_config_util.get_config()

    def write(self, node_id, update_time, input_ref=None, output_content=None, output_content_type=None):
        """
        Write the input and output products from a transaction to disk.
        The location of the written files is returned. All directories and files
        created will have both user and group read/write permissions set accordingly.

        Parameters
        ----------
        node_id : str
            PDS Node ID to associate with the transaction to disk. Determines
            which subdirectory the input/output is written to.
        update_time : datetime.datetime
            datetime object corresponding to the time of the original transaction.
            Forms part of the path where the transaction is written to on disk.
        input_ref : str, optional
            Path to the input file or directory to associate with the transaction.
            Determines the input file(s) copied to the transaction history.
        output_content : str, optional
            The output label content to associate to with the transaction.
            Determines the contents of the output file copied to the transaction history.
        output_content_type : str, optional
            The content type of output_content. Should be one of "xml" or "json".

        Returns
        -------
        final_output_dir : str
            Path to the directory in the transaction history created by this
            method. The path has the following form:

                <transaction history root>/<node_id>/<update_time>

            Where <transaction history root> is set in the INI config, <node_id>
            is the value provided for node_id, and <update_time> is the provided
            update_time as an isoformat string.

        """
        transaction_dir = self._config.get("OTHER", "transaction_dir")
        logger.debug(f"transaction_dir {transaction_dir}")

        # Create the local transaction history directory, if necessary.
        final_output_dir = os.path.join(transaction_dir, node_id, update_time.isoformat())

        # Set up the appropriate umask in-case os.makedirs needs to create any
        # intermediate parent directories (its mask arg only affects the created leaf directory)
        prev_umask = os.umask(0o0002)

        # Create the new transaction history directory with group-rw enabled
        os.makedirs(final_output_dir, exist_ok=True, mode=0o0775)

        if input_ref:
            if os.path.isdir(input_ref):
                # Copy the input files, but do not preserve their permissions so
                # the umask we set above takes precedence
                copy_tree(input_ref, os.path.join(final_output_dir, "input"), preserve_mode=False)
            else:
                input_content_type = os.path.splitext(input_ref)[-1]

                # Write input file with provided content.
                # Note that the file name is always 'input' plus the extension based
                # on the content_type (input.xml or input.csv or input.xlsx)
                full_input_name = os.path.join(final_output_dir, "input" + input_content_type)

                if os.path.isfile(input_ref):
                    shutil.copy2(input_ref, full_input_name)
                else:  # remote resource
                    r = requests.get(input_ref, allow_redirects=True)

                    with open(full_input_name, "wb") as outfile:
                        outfile.write(r.content)

                    r.close()

                # Set up permissions for copied input
                os.chmod(full_input_name, 0o0664)

        # Write output file with provided content
        # The extension of the file is determined by the provided content type
        if output_content and output_content_type:
            full_output_name = os.path.join(final_output_dir, ".".join(["output", output_content_type]))

            with open(full_output_name, "w") as outfile:
                outfile.write(output_content)

            # Set up permissions for copied output
            os.chmod(full_output_name, 0o0664)

        logger.info(f"Transaction files saved to {final_output_dir}")

        # Restore the previous umask
        os.umask(prev_umask)

        return final_output_dir
