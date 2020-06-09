#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

import os
import sys
import time

from datetime import datetime,timezone

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.outputs.transaction')

class Transaction:
    # This class Transaction provide services to build a transaction object from action {draft,reserved}.

    m_doi_config_util = DOIConfigUtil()
    m_log_dict = None 

    def __init__(self,target_url, node_id, action_type, submitter_email, input_content=None):
        self._config = self.m_doi_config_util.get_config()
        self.m_log_dict = self._build_transaction(target_url, node_id, action_type, submitter_email, input_content)

    def get_transaction(self):
        '''Returns the transaction info.'''
        return self.m_log_dict

    def add_field(self, field_name, field_value):
        '''Add a field to the transaction info.'''
        self.m_log_dict[field_name] = field_value

    def _build_transaction(self, target_url, node_id, action_type, submitter_email, input_content=None):
        '''Build a transaction object (dict) so we write a transaction to log.'''
        o_log_dict = {}
        o_log_dict['discipline_node'] = node_id
        o_log_dict['action_type']     = action_type
        o_log_dict['input_content']   = target_url
        if input_content:
            o_log_dict['input_content'] = input_content # If content is provided, use it.

        target_extension = target_url.split('.')[-1]

        if target_extension == 'xml':
            o_log_dict['content_type'] = 'xml'
        elif target_extension == 'xlsx':
            o_log_dict['content_type'] = 'xlsx'
        elif target_extension == 'csv':
            o_log_dict['content_type'] = 'csv'

        # Get provided submitter_email instead of using configuration value.
        o_log_dict['submitter']  = submitter_email

        return o_log_dict
