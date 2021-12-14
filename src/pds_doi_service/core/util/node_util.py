#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
from pds_doi_service.core.entities.exceptions import UnknownNodeException
from pds_doi_service.core.util.general_util import get_logger

# Get the common logger and set the level for this file.
logger = get_logger(__name__)


class NodeUtil:
    """
    Provides methods to look up the long name for a PDS node ID and vice-versa.
    """

    node_id_to_long_name = {
        "atm": "Atmospheres",
        "eng": "Engineering",
        "geo": "Geosciences",
        "img": "Cartography and Imaging Sciences Discipline",
        "naif": "Navigational and Ancillary Information Facility",
        "ppi": "Planetary Plasma Interactions",
        "rs": "Radio Science",
        "rms": "Ring-Moon Systems",
        "sbn": "Small Bodies",
        "unk": "Unknown",
    }

    long_name_to_node_id = {long_name.lower(): node_id for node_id, long_name in node_id_to_long_name.items()}

    @classmethod
    def get_node_long_name(cls, node_id):
        cls.validate_node_id(node_id.lower())
        return cls.node_id_to_long_name[node_id.lower()]

    @classmethod
    def get_node_id(cls, long_name):
        cls.validate_node_long_name(long_name.lower())
        return cls.long_name_to_node_id[long_name.lower()]

    @classmethod
    def validate_node_long_name(cls, long_name):
        if long_name not in cls.get_permissible_long_names():
            raise UnknownNodeException(
                f"Node {long_name.capitalize()} is not a permissible node name. Must be one of {cls.long_name_to_node_id.keys()}"
            )

    @classmethod
    def validate_node_id(cls, node_id):
        if node_id not in cls.get_permissible_node_ids():
            raise UnknownNodeException(
                f"Node {node_id.upper()} is not a permissible ID. Must be one of {cls.node_id_to_long_name.keys()}"
            )

    @classmethod
    def get_permissible_node_ids(cls):
        return cls.node_id_to_long_name.keys()

    @classmethod
    def get_permissible_long_names(cls):
        return cls.long_name_to_node_id.keys()
