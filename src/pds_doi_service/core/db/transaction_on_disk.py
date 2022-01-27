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
import glob
import os
import shutil
from distutils.dir_util import copy_tree
from os.path import exists
from os.path import join

import requests
from pds_doi_service.core.entities.doi import DoiRecord
from pds_doi_service.core.entities.exceptions import NoTransactionHistoryForIdentifierException
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

    @staticmethod
    def get_transaction_key(node_id, doi, transaction_time):
        """
        Returns a transaction key incorporating the provided PDS node ID and
        transaction time. This key may then be used as a local file path for
        storing the input and output products associated with a transaction.

        A transaction key is formed by combined the location of the local
        transaction history directory (specified in the INI config), with
        subdirectories for the node ID, DOI (prefix and suffix) and transaction
        timestamp:

            <transaction dir>/<node ID>/<DOI prefix>/<DOI suffix>/<isoformat transaction time>

        Parameters
        ----------
        node_id : str
            The PDS node identifier associated with the transaction. Becomes
            a subdirectory in the transaction key path returned.
        doi : str
            The DOI for the transaction.
        transaction_time : datetime.datetime
            The time of the transaction. The value is converted to an isoformat
            string and used as a subdirectory in the transaction key returned.

        Returns
        -------
        transaction_key : str
            The transaction key path formed from the provided arguments.

        """
        config = TransactionOnDisk.m_doi_config_util.get_config()

        transaction_dir = config.get("OTHER", "transaction_dir")

        prefix, suffix = doi.split("/", maxsplit=1)

        return os.path.join(transaction_dir, node_id, prefix, suffix, transaction_time.isoformat())

    @staticmethod
    def output_label_for_transaction(transaction_record):
        """
        Returns a path to the output label associated to the provided transaction
        record.

        Parameters
        ----------
        transaction_record : DoiRecord
            Details of a transaction as returned from a list request.

        Returns
        -------
        label_file : str
            Path to the output label associated to the provided transaction record.

        Raises
        ------
        NoTransactionHistoryForIdentifierException
            If the output label associated to the transaction cannot be found
            on local disk.

        """
        # TODO: reconcile this method with the version in the list action
        # Make sure we can locate the output label associated with this
        # transaction
        transaction_location = transaction_record.transaction_key
        label_files = glob.glob(join(transaction_location, "output.*"))

        if not label_files or not exists(label_files[0]):
            raise NoTransactionHistoryForIdentifierException(
                f"Could not find a DOI label associated with identifier {transaction_record.identifier}. "
                "The database and transaction history location may be out of sync."
            )

        label_file = label_files[0]

        return label_file

    def write(self, transaction_dir, input_ref=None, output_content=None, output_content_type=None):
        """
        Write the input and output products from a transaction to disk.
        All directories and files created will have both user and group
        read/write permissions set accordingly.

        Parameters
        ----------
        transaction_dir : str
            Location on disk to commit the transaction input and output files.
            This method creates the directory if it does not already exist and
            ensures group read/write permission bits are set.
        input_ref : str, optional
            Path to the input file or directory to associate with the transaction.
            Determines the input file(s) copied to the transaction history.
        output_content : str, optional
            The output label content to associate to with the transaction.
            Determines the contents of the output file copied to the transaction history.
        output_content_type : str, optional
            The content type of output_content. Should be one of "xml" or "json".

        """

        # Set up the appropriate umask in-case os.makedirs needs to create any
        # intermediate parent directories (its mask arg only affects the created leaf directory)
        prev_umask = os.umask(0o0002)

        # Create the new transaction history directory with group-rw enabled
        os.makedirs(transaction_dir, exist_ok=True, mode=0o0775)

        if input_ref:
            if os.path.isdir(input_ref):
                # Copy the input files, but do not preserve their permissions so
                # the umask we set above takes precedence
                copy_tree(input_ref, os.path.join(transaction_dir, "input"), preserve_mode=False)
            else:
                input_content_type = os.path.splitext(input_ref)[-1]

                # Write input file with provided content.
                # Note that the file name is always 'input' plus the extension based
                # on the content_type (input.xml or input.csv or input.xlsx)
                full_input_name = os.path.join(transaction_dir, "input" + input_content_type)

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
            full_output_name = os.path.join(transaction_dir, ".".join(["output", output_content_type]))

            with open(full_output_name, "w") as outfile:
                outfile.write(output_content)

            # Set up permissions for copied output
            os.chmod(full_output_name, 0o0664)

        logger.info(f"Transaction files saved to {transaction_dir}")

        # Restore the previous umask
        os.umask(prev_umask)
