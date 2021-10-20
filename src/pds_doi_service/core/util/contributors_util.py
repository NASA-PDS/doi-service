#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
"""
====================
contributors_util.py
====================

General utility functions for managing contributor fields in DOI records.
"""
import requests
from pds_doi_service.core.util.general_util import get_logger


logger = get_logger(__name__)


class DOIContributorUtil:
    def __init__(self, dictionary_url, pds_node_identifier):
        self._url = dictionary_url
        self._pds_node_identifier = pds_node_identifier

    def get_permissible_values(self):
        """Return a list of permissible values for contributors."""
        response = requests.get(self._url, stream=False, headers={"Connection": "close"})
        json_data = response.json()

        attribute_dictionaries = json_data[0]["dataDictionary"]["attributeDictionary"]
        node_dictionary = [
            x for x in attribute_dictionaries if x["attribute"]["identifier"] == self._pds_node_identifier
        ][0]["attribute"]

        return [pv["PermissibleValue"]["value"] for pv in node_dictionary["PermissibleValueList"]]
