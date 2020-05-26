#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------
import logging


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

