#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
======================
transaction_builder.py
======================

Contains the TransactionBuilder class, which is used to manage transactions
with the local database.
"""

from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.outputs.osti import CONTENT_TYPE_XML, VALID_CONTENT_TYPES
from pds_doi_service.core.outputs.transaction import Transaction
from pds_doi_service.core.outputs.transaction_on_disk import TransactionOnDisk
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger('pds_doi_service.core.outputs.transaction_builder')


class TransactionBuilder:
    """
    This class provides services to build a transaction, transaction logger,
    and database writer that can be used for writing to disk and/or to database.
    """
    m_doi_config_util = DOIConfigUtil()

    # A database writer to write DOI info to table.
    m_doi_database = None
    # A logger to write transaction to disk and to database.
    m_transaction_ondisk_dao = None
    # A transaction contains list of dictionaries containing fields to write
    # to disk and database.
    m_transaction = None

    def __init__(self,db_name=None):
        self._config = self.m_doi_config_util.get_config()
        if db_name:
            self.m_doi_database = DOIDataBase(db_name)
        else:
            self.m_doi_database = DOIDataBase(self._config.get('OTHER', 'db_file'))

        self.m_transaction_ondisk_dao = TransactionOnDisk()

    def get_transaction(self):
        return self.m_transaction

    def get_transaction_logger(self):
        return self.m_transaction_ondisk_dao

    def get_doi_database_writer(self):
        return self.m_doi_database

    def prepare_transaction(self, node_id, submitter_email, dois: list,
                            input_path=None, output_content=None,
                            output_content_type=CONTENT_TYPE_XML):
        """
        Build a Transaction from the inputs and outputs to a 'reserve', 'draft'
        or release action. The Transaction object is returned.

        The field output_content is used for writing the content to disk.
        This is typically the response text from an OSTI request.

        """
        if output_content_type not in VALID_CONTENT_TYPES:
            raise ValueError('Invalid content type requested, must be one of '
                             f'{",".join(VALID_CONTENT_TYPES)}')

        return Transaction(output_content,
                           output_content_type,
                           node_id,
                           submitter_email,
                           dois,
                           self.m_transaction_ondisk_dao,
                           self.m_doi_database,
                           input_path=input_path)

# end class TransactionBuilder
