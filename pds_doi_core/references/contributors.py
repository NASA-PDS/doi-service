#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

from pds_doi_core.util.general_util import DOIGeneralUtil, get_logger

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.references.contributor')
#logger.setLevel(logging.INFO)  # Comment this line once happy with the level of logging set in get_logger() function.
# Note that the get_logger() function may already set the level higher (e.g. DEBUG).  Here, we may reset
# to INFO if we don't want debug statements.

class DOIContributorUtil:
    def get_permissible_values(self,json_value_1,json_key_1):
            # Function returns the PerrmissibleValueList for attributeDictionary where one element matches with PDS_NODE_IDENTIFIER.
            PDS_NODE_IDENTIFIER = '0001_NASA_PDS_1.pds.Node.pds.name'

            found_identifier_flag = False
            found_permissible_value_flag = False
            o_permissible_value_list = [] # Is a list of dict, where each dict has a key 'PermissibleValue' points to a dict with key 'value' to the actual value.
            # If json_value_1 is a list and the json_key_1 is 'classDictionary' , we dig to the next level

            if isinstance(json_value_1,list) and json_key_1 == 'attributeDictionary':
                for ii in range(0,len(json_value_1)):
                  if not found_permissible_value_flag:
                    for json_key_2, json_value_2 in json_value_1[ii].items():
                      if not found_permissible_value_flag:
                        # Each json_value_2 is a dictionary, we loop through.
                        if isinstance(json_value_2,dict):
                            for json_key_3, json_value_3 in json_value_2.items():
                                # If the type of json_value_3 is a list, we look through for PDS_NODE_IDENTIFIER
                                if isinstance(json_value_3,list):
                                    if found_identifier_flag and json_key_3 == 'PermissibleValueList':
                                        o_permissible_value_list = json_value_3
                                        found_permissible_value_flag = True  # Setting this to True allow the code to return immediatey.
                                        break  # Break out of json_key_3, json_value_3 loop.
                                    for kk in range(0,len(json_value_3)):
                                        for json_key_4, json_value_4 in json_value_3[kk].items():
                                            # If the type of json_value_4 is dict, we look for 'identifier' 
                                            if isinstance(json_value_4,dict):
                                                for json_key_5, json_value_5 in json_value_4.items():
                                                    if json_key_5 == 'identifier' and json_value_5 == PDS_NODE_IDENTIFIER:
                                                        # Save where we found it.
                                                        o_found_dict = json_value_4
                                                        found_key_1 = json_key_1
                                                        found_key_2 = json_key_2
                                                        found_key_3 = json_key_3
                                                        found_key_4 = json_key_4
                                                        found_key_5 = json_key_5
                                                        found_index_1 = ii # Found this in index ii in found_key_1
                                                        found_index_2 = kk # Found this in index kk of found_key_3
                                                        logger.info("FOUND_PDS_NODE_IDENTIFIER,json_value_3 %s" % json_value_3)
                                                        logger.info("FOUND_PDS_NODE_IDENTIFIER,json_value_4 %s" % json_value_4)
                                                        exit(0) # This should never get here.
                                            if isinstance(json_value_4,list):
                                                logger.info("FOUND_LIST:len(json_value_4) %d " % len(json_value_4))
                                                logger.info("FOUND_LIST:json_value_4",json_value_4)
                                                logger.info("FOUND_LIST:json_key_1,json_key_2,json_key_3,json_key_4",json_key_1,json_key_2,json_key_3,json_key_4)
                                                exit(0) # This should never get here.
                                else:
                                    if json_key_3 == 'identifier' and json_value_3 == PDS_NODE_IDENTIFIER:
                                        found_identifier_flag = True
                                    if found_identifier_flag and json_key_3 == 'PermissibleValueList':
                                        logger.info("FOUND_PDS_NODE_IDENTIFIER,json_key_3,json_value_3",json_key_3,json_value_3)
                                        logger.info("PermissibleValueList",PermissibleValueList)
                                        exit(0) # This should never get here.

                        # If json_value_2 is a list, we dig to the next level
                        if isinstance(json_value_2,list):
                            logger.info("FOUND_LIST:json_key_1,json_key_2 %s %s" % (json_key_1,json_key_2))
                            exit(0) # # This should never get here.
                    # end for ii in range(0,len(json_value_1)):

            #  json_key_1 Title
            #  json_key_1 Version
            #  json_key_1 Date
            #  json_key_1 Description
            #  json_key_1 classDictionary
            #  json_key_1 attributeDictionary
            #  json_key_1 dataTypeDictionary
            #  json_key_1 unitDictionary
            if found_permissible_value_flag:
                pass

            logger.debug("json_key_1 [%s] [%d] o_permissible_value_list [%s]" % (json_key_1,len(o_permissible_value_list),o_permissible_value_list))

            # If found_permissible_value_flag is true, the length of o_permissible_value_list will be greater than zero.
            return(o_permissible_value_list)


if __name__ == '__main__':
    function_name = 'main:'
    doiContributorUtil = DOIContributorUtil()
