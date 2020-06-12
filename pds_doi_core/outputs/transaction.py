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

from copy import deepcopy
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

    def __init__(self,target_url,node_id,action_type,submitter_email,transaction_dict_list):
        self._config = self.m_doi_config_util.get_config()
        self.m_log_dict = [] 

        # Remove any extraneous fields from transaction_dict_list that would caue Python to crash.
        transaction_dict_list = self._remove_extraneous_fields(transaction_dict_list)

        for ii in range(0,len(transaction_dict_list)):
            logger.debug(transaction_dict_list[ii])
            self.m_log_dict.append(self._build_transaction(target_url,node_id,action_type,submitter_email,**transaction_dict_list[ii]))
    def _remove_extraneous_fields(self,transaction_dict_list):
         # Some fields need to be deleted so as not to cause Python to crash when _build_transaction is called.
        field_to_delete_list = ['description', 'identifier', 'site_url', 'authors', 'keywords', 'publisher', 'contributor','submitter_email','editors']
        updated_dict_list = deepcopy(transaction_dict_list)

        for dict_index in range(0,len(transaction_dict_list)):
            my_keys = list(transaction_dict_list[dict_index].keys())
            for key_index in range(0,len(my_keys)):
                if my_keys[key_index] in field_to_delete_list:
                    del updated_dict_list[dict_index][my_keys[key_index]]
                    #print("remove_extraneous_fields:REMOVING_KEY",my_keys[key_index])
                else:
                    pass
                    #print("remove_extraneous_fields:KEEPING_KEY",my_keys[key_index])

        return updated_dict_list

    def get_transaction(self):
        '''Returns the transaction info.'''
        return self.m_log_dict

    def add_field(self, field_name, field_value, dict_index,):
        '''Add a field to the transaction info.'''
        self.m_log_dict[dict_index][field_name] = field_value

    def _build_transaction(self, target_url, node_id, action_type,
                           submitter_email,
                           status=None, title=None, authors=None, publication_date=None,
                           product_type=None, product_type_specific=None, related_identifier=None, input_content=None,
                           output_content=None, lid=None, vid=None, id=None, doi=None,
                           latest_update=None, transaction_key=None):

        '''Build a transaction object (dict) so we can write a transaction to log.'''
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

        if input_content:
            o_log_dict['input_content']  = input_content 
        if output_content:
            o_log_dict['output_content']  = output_content 
        if status:
            o_log_dict['status']  = status

        if related_identifier:
            identifier_tokens = related_identifier.split('::')
            if len(identifier_tokens) < 2:
                logger.error(f"Expecting at least 2 tokens from parsing {related_identifier}")
                exit(1)
            o_log_dict['lid'] = identifier_tokens[0]
            o_log_dict['vid'] = identifier_tokens[1]

        if lid:
            o_log_dict['lid']  = lid
        if vid:
            o_log_dict['vid']  = vid
        if id:
            o_log_dict['id']  = id
        if doi:
            o_log_dict['doi']  = doi
        if title:
            o_log_dict['title']  = title
        if product_type:
            o_log_dict['type']  = product_type 
        if product_type_specific:
            o_log_dict['subtype']  = product_type_specific
        if latest_update:
            o_log_dict['latest_update']  = latest_update
        if transaction_key:
            o_log_dict['transaction_key']  = transaction_key

        return o_log_dict
