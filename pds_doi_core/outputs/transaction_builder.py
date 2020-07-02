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

from datetime import datetime, timezone
from lxml import etree

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.db.doi_database import DOIDataBase
from pds_doi_core.outputs.transaction import Transaction
from pds_doi_core.outputs.transaction_on_disk import TransactionOnDisk

# Get the common logger and set the level for this file.
import logging

logger = get_logger('pds_doi_core.outputs.transaction_builder')


class TransactionBuilder:
    # This class TransactionBuilder provide services to build a transaction, transaction logger, and database writer that can be used
    # for writting to disk and/or to database.

    m_doi_config_util = DOIConfigUtil()
    m_doi_database = None  # A database writer to write DOI info to table.
    m_transaction_ondisk_dao = None  # A logger to write transacton to disk and to database.
    m_transaction = None  # A transaction contains list of dictionaries containing fields to write to disk and database.

    def __init__(self,db_name=None):
        self._config = self.m_doi_config_util.get_config()
        if db_name:
            self.m_doi_database = DOIDataBase(db_name)
        else:
            self.m_doi_database = DOIDataBase(self._config.get('OTHER','db_file') )
        self.m_transaction_ondisk_dao = TransactionOnDisk()

    def get_transaction(self):
        return self.m_transaction

    def get_transaction_logger(self):
        return self.m_transaction_ondisk_dao

    def get_doi_database_writer(self):
        return self.m_doi_database

    def set_doi_fields_osti(self, i_doc, io_doi_fields):
        """Function fetches the status,title,id and doi fields from i_doc and updates the io_doi_fields."""

        # If i_doc is string, we expect it to be in XML format, otherwise an Element object from lxml module.
        if isinstance(i_doc, str):
            my_root = etree.fromstring(i_doc)
        else:
            my_root = i_doc.getroottree()
        element_index = 0

        for element in my_root.iter():
            if element.tag == 'record':
                my_record = my_root.xpath(element.tag)[element_index]
                my_id = my_root.xpath('record/id')[element_index]
                my_doi = my_root.xpath('record/doi')[element_index]
                my_title = my_root.xpath('record/title')[element_index]

                # Add these new fields to io_doi_fields were not there before.
                io_doi_fields['dois'][element_index]['status'] = my_record.attrib['status'].lower()
                io_doi_fields['dois'][element_index]['title'] = my_title.text
                io_doi_fields['dois'][element_index]['id'] = my_id.text
                io_doi_fields['dois'][element_index]['doi'] = my_doi.text

                element_index += 1

        return io_doi_fields

    def prepare_transaction(self, target_url, node_id, submitter_email, doi_fields, output_content=None,
                            web_response=None):
        """Build a transaction from 'reserve' or 'draft' action. The transaction object and transaction logger will be returned.
           The field output_content is used for writing the content to disk.
           The field web_response is from any interaction with OSTI server. The status, id, doi and other fields can parsed from web_response."""

        transaction_dir = self._config.get('OTHER', 'transaction_dir')
        logger.debug(f"transaction_dir {transaction_dir}")

        # Get the current time.
        current_time = datetime.now()
        epoch_time = int(time.time())
        now_is = current_time.isoformat()
        logger.debug(f"now_is {now_is}")

        logger.debug(f"web_response {web_response}")
        logger.debug(f"doi_fields {doi_fields}")
        if web_response:
            doi_fields = self.set_doi_fields_osti(web_response, doi_fields)
            logger.debug(f"doi_fields {doi_fields}")
        logger.debug(f"submitter_email {submitter_email}")

        return Transaction(target_url,
                           output_content,
                           node_id,
                           submitter_email,
                           doi_fields,
                           self.m_transaction_ondisk_dao,
                           self.m_doi_database)

# end class TransactionBuilder:
