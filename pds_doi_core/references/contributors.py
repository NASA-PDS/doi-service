#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

import requests
from pds_doi_core.util.general_util import get_logger


# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.references.contributor')

class DOIContributorUtil:
    def __init__(self, dictionnary_url, pds_node_identifier):
        self._url = dictionnary_url
        self._pds_node_identifier = pds_node_identifier


    def get_permissible_values(self):
        '''Return a list of permissible values for contributors.'''
        response = requests.get(self._url, stream=False, headers={'Connection': 'close'})
        json_data = response.json()

        attributeDictionaries = json_data[0]['dataDictionary']['attributeDictionary']
        node_dictionnary = [x for x in attributeDictionaries if x['attribute']['identifier']==self._pds_node_identifier][0]['attribute']

        return [pv['PermissibleValue']['value'] for pv in node_dictionnary['PermissibleValueList']]

