#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------
import logging
from xml.etree import ElementTree
from datetime import datetime
from pds_doi_core.util.const import *

# Put the function get_logger here in the beginning of the file so we can call it.
def get_logger(module_name=''):
    # If the user specify the module name, we can use it.
    if module_name != '':
        logger =logging.getLogger(module_name)
    else:
        logger =logging.getLogger(__name__)
    my_format = "%(levelname)s %(name)s:%(funcName)s %(message)s"
    logging.basicConfig(format=my_format,
                        filemode='a')

    logger.setLevel(logging.DEBUG)
    return logger

# Get the common logger and set the level for this file.
import logging
logger = get_logger()
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

class DOIGeneralUtil:

    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    def return_keyword_values(self,i_dict_config_list, i_list_keyword_values):
    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
        o_keywords = ""

        #------------------------------                                                                                                 
        # Add the global keyword values in the Config file to those scraped from the Product label
        #    -- <keywords> using the items in list_keyword_values
        #  -- each value must be separated by semi-colon (e.g., "test1 test2")
        # 
        # global_keyword_values preceed values scraped from Product label
        #------------------------------   
        global_keywords = i_dict_config_list.get("global_keyword_values", 'None')

        logger.debug("global_keywords " + str(global_keywords))

        if (global_keywords is not None):
            if ("" in global_keywords):
                kv = global_keywords.split(";")  # Split using semi-colon

                for items in kv:
                    if (not items == ""):
                        o_keywords += items + "; " # Add semi-colon between each keyword
            else:
                if (not len(global_keywords) == 0):
                    o_keywords = global_keywords
                else:
                    o_keywords = "PDS "
        else:
            o_keywords = ""

        #------------------------------                                                                                                 
        # Add the keyword values that were scraped from the Product label
        #    -- ensure no duplicate values between global and scraped
        #------------------------------   
        if (not len(i_list_keyword_values) == 0):
            for items in i_list_keyword_values:
                if (items not in o_keywords):
                    o_keywords += " " + items

        logger.debug("i_list_keyword_values " + str(len(i_list_keyword_values)) + str(i_list_keyword_values))

        return(o_keywords)
