#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import os
import sys
import time

from copy import deepcopy
from datetime import datetime, timezone

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger

# Get the common logger and set the level for this file.
import logging

logger = get_logger('pds_doi_core.outputs.transaction')


class Transaction:
    # This class Transaction provide services to build a transaction object from action {draft,reserved}.

    m_doi_config_util = DOIConfigUtil()
    m_log_dict = None

    def __init__(self,
                 output_content,
                 node_id,
                 submitter_email,
                 dois,
                 transaction_disk_dao,
                 transaction_db_dao,
                 input_path = None):
        self._config = self.m_doi_config_util.get_config()
        self._node_id = node_id.lower()
        self._submitter_email = submitter_email
        self._input_ref = input_path
        self._output_content = output_content
        self._transaction_time = datetime.now()
        self._dois = dois
        self._transaction_disk_dao = transaction_disk_dao
        self._transaction_db_dao = transaction_db_dao

    def log(self):
        transaction_io_dir = self._transaction_disk_dao.write(self._node_id, self._transaction_time,
                                                              input_ref=self._input_ref,
                                                              output_content=self._output_content)

        for doi in self._dois:
            lidvid = doi.related_identifier.split('::')
            doi_field = doi.__dict__
            k_doi_params = dict((k, doi_field[k]) for k in
                 doi_field.keys() & {'doi', 'status', 'title', 'product_type', 'product_type_specific'})

            self._transaction_db_dao.write_doi_info_to_database(
                lid=lidvid[0],
                vid=lidvid[1] if len(lidvid) > 1 else None,
                transaction_date=self._transaction_time,
                submitter=self._submitter_email,
                discipline_node=self._node_id,
                transaction_key=transaction_io_dir,
                **k_doi_params
            )
