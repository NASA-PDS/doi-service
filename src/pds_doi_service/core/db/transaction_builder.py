#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
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
from pds_doi_service.core.db.transaction import Transaction
from pds_doi_service.core.outputs.doi_record import CONTENT_TYPE_XML
from pds_doi_service.core.outputs.doi_record import VALID_CONTENT_TYPES
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class TransactionBuilder:
    """
    This class provides services to build a transaction, transaction logger,
    and database writer that can be used for writing to disk and/or to database.
    """

    m_doi_config_util = DOIConfigUtil()

    def __init__(self, db_name=None):
        self._config = self.m_doi_config_util.get_config()

        if db_name:
            self.m_doi_database = DOIDataBase(db_name)
        else:
            self.m_doi_database = DOIDataBase(self._config.get("OTHER", "db_file"))

    def prepare_transaction(self, submitter_email, doi, input_path=None, output_content_type=CONTENT_TYPE_XML):
        """
        Build a Transaction from the inputs and outputs to a reserve, update
        or release action. The Transaction object is returned.

        The field output_content is used for writing the content to disk.
        This is typically the response text from a request to the DOI
        service provider.

        Parameters
        ----------
        submitter_email : str
            The email address associated with the submitter of the transaction
        doi : Doi
            The DOI object created from the transaction.
        input_path : str, optional
            Path to the source input file of the provided Doi object. If provided,
            the file will be copied to the local transaction history.
        output_content_type : str, optional
            The format to use for saving the output label to associate with the
            transaction. Should be one of xml or json. Defaults to xml.

        Returns
        -------
        Transaction
            The prepared Transaction object. Callers of this function may call
            log() on the returned Transaction to commit it to the local database.

        """
        if output_content_type not in VALID_CONTENT_TYPES:
            raise ValueError(f"Invalid content type requested, must be one of {','.join(VALID_CONTENT_TYPES)}")

        return Transaction(
            output_content_type,
            submitter_email,
            doi,
            self.m_doi_database,
            input_path=input_path,
        )
