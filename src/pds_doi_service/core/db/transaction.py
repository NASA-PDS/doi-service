#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
==============
transaction.py
==============

Defines the Transaction class, which is used to log transactions both to local
disk and database table.
"""
from datetime import datetime
from datetime import timezone

from pds_doi_service.core.db.transaction_on_disk import TransactionOnDisk
from pds_doi_service.core.entities.doi import DoiRecord
from pds_doi_service.core.outputs.service import DOIServiceFactory
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import checksum
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class Transaction:
    """
    Provides services to build a transaction object used to log the inputs and
    outputs from actions such as reserve, release etc...
    """

    m_doi_config_util = DOIConfigUtil()

    def __init__(self, output_content_type, submitter_email, doi, transaction_db, input_path=None):
        self._config = self.m_doi_config_util.get_config()
        self._doi = doi
        self._node_id = self._doi.node_id
        self._submitter_email = submitter_email
        self._input_ref = input_path
        self._output_content_type = output_content_type
        self._transaction_time = datetime.now(tz=timezone.utc)

        self._record_service = DOIServiceFactory.get_doi_record_service()
        self._transaction_disk = TransactionOnDisk()
        self._transaction_db = transaction_db

    def log(self):
        """
        Logs a new record to the transaction database using the provided Doi object.
        An output JSON label corresponding to the Doi object is also created and
        stored in the transaction history for the record.

        Database logging only occurs if the provided Doi object and its output label
        do not match what is stored for the latest database record associated to the
        DOI value.

        Returns
        -------
        doi_logged : bool
            True if the transaction was logged. False otherwise.

        """
        doi_logged = False
        latest_record = None
        latest_label = None

        # Get the latest available entry in the DB for this DOI, if it exists
        query_criteria = {"doi": [self._doi.doi]}
        latest_records = self._transaction_db.select_latest_records(query_criteria)

        # Get the latest transaction record for this DOI so we can carry
        # forward certain fields to the next transaction
        if latest_records:
            latest_record = latest_records[0]

            # Carry original release date forward
            self._doi.date_record_added = latest_record.date_added

            # We might have a PDS ID already in the database from a previous reserve
            if not self._doi.pds_identifier and latest_record.identifier:
                self._doi.pds_identifier = latest_record.identifier

            label_file = self._transaction_disk.output_label_for_transaction(latest_record)

            with open(label_file, "r") as infile:
                latest_label = infile.read()

        # Create the output label that's written to the local transaction
        # history on disk. This label should represent the most up-to-date
        # version for this DOI/LIDVID
        output_label = self._record_service.create_doi_record(self._doi, content_type=self._output_content_type)

        # Translate the Doi object into a DoiRecord for easy import into
        # the database
        doi_fields = self._doi.__dict__

        date_added = doi_fields.get("date_record_added", self._transaction_time)
        date_updated = doi_fields.get("date_record_updated", self._transaction_time)

        # Determine where the updated label will be written to local disk
        transaction_io_dir = self._transaction_disk.get_transaction_key(self._node_id, self._doi.doi, date_updated)

        doi_record = DoiRecord(
            identifier=doi_fields["pds_identifier"],
            status=doi_fields["status"],
            date_added=date_added,
            date_updated=date_updated,
            submitter=self._submitter_email,
            title=doi_fields["title"],
            type=doi_fields["product_type"],
            subtype=doi_fields["product_type_specific"],
            node_id=self._node_id,
            doi=doi_fields["doi"],
            transaction_key=transaction_io_dir,
            is_latest=True,
        )

        # Before committing the new transaction, check to see if there are any
        # differences between the current commit and latest available record.
        # If not, don't bother committing.
        if not latest_record or doi_record != latest_record or checksum(output_label) != checksum(latest_label):
            self._transaction_disk.write(
                transaction_io_dir,
                input_ref=self._input_ref,
                output_content=output_label,
                output_content_type=self._output_content_type,
            )

            self._transaction_db.write_doi_info_to_database(doi_record)

            doi_logged = True

        return doi_logged
