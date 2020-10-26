#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

from pds_doi_service.core.util.general_util import get_logger
from pds_doi_service.core.input.exceptions import UnknownNodeException

# Get the common logger and set the level for this file.
logger = get_logger('pds_doi_core.input.node_util')

class NodeUtil:
    # This class NodeUtil provide services to look up a short name for a long name of the node id.

    m_node_id_dict = {'ATM': 'Atmospheres',
                      'ENG': 'Engineering',
                      'GEO': 'Geosciences',
                      'IMG': 'Cartography and Imaging Sciences Discipline',
                      'NAIF': 'Navigational and Ancillary Information Facility',
                      'PPI': 'Planetary Plasma Interactions',
                      'RMS': 'Ring-Moon Systems',
                      'SBN': 'Small Bodies'}


    def get_node_long_name(self,node_id):
        self.validate_node_id(node_id.upper())
        return self.m_node_id_dict[node_id.upper()]

    def validate_node_id(self,node_id):
        if node_id.upper() not in self.m_node_id_dict:
            raise UnknownNodeException(f"node_id {node_id.upper()} is not found in permissible nodes {self.m_node_id_dict.keys()}")

    @classmethod
    def get_permissible_values(cls):
        return [c.lower() for c in cls.m_node_id_dict.keys()]

#    @classmethod
#    def get_keys(cls):
#        return [c.lower() for c in cls.m_node_id_dict.keys()]
