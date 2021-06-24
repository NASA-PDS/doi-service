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

from pds_doi_service.core.outputs.transaction_on_disk import TransactionOnDisk
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class Transaction:
    """
    Provides services to build a transaction object used to log the inputs and
    outputs from actions such as draft, reserved, etc...
    """

    m_doi_config_util = DOIConfigUtil()

    def __init__(self, output_content, output_content_type, node_id,
                 submitter_email, dois, transaction_db, input_path=None):
        self._config = self.m_doi_config_util.get_config()
        self._node_id = node_id.lower()
        self._submitter_email = submitter_email
        self._input_ref = input_path
        self._output_content = output_content
        self._output_content_type = output_content_type
        self._transaction_time = datetime.now()
        self._dois = dois
        self._transaction_disk = TransactionOnDisk()
        self._transaction_db = transaction_db

    @staticmethod
    def get_lidvid(identifier: str):

        if '::' in identifier:
            lidvid_split = identifier.split('::')
            lid = lidvid_split[0]
            # sometimes, at least once, the vid is duplicated
            # in the identifier, ...::1.0::1.0,
            # this implementation only get the first one
            vid = lidvid_split[1]
        else:
            lid = identifier
            vid = None

        return lid, vid

    @property
    def output_content(self):
        return self._output_content

    def log(self):
        transaction_io_dir = self._transaction_disk.write(
            self._node_id, self._transaction_time, input_ref=self._input_ref,
            output_content=self._output_content,
            output_content_type=self._output_content_type
        )

        for doi in self._dois:
            lid, vid = Transaction.get_lidvid(doi.related_identifier)

            doi_fields = doi.__dict__

            self._transaction_db.write_doi_info_to_database(
                lid=lid,
                vid=vid,
                transaction_key=transaction_io_dir,
                doi=doi_fields['doi'],
                release_date=doi_fields.get('date_record_added', self._transaction_time),
                transaction_date=doi_fields.get('date_record_updated', self._transaction_time),
                status=doi_fields['status'],
                title=doi_fields['title'],
                product_type=doi_fields['product_type'],
                product_type_specific=doi_fields['product_type_specific'],
                submitter=self._submitter_email,
                discipline_node=self._node_id
            )

