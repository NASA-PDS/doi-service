#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

import os;
import sys;

class WhereAmI():
    # This WhereAmI class allows the developer to exit the program and print the stack.  Useful when you want to stop
    # the program and know which function and line you stopped at.

    m_module_name = "WhereAmI:";
    m_debug_mode  = False;
#    m_debug_mode = True;
    if (os.getenv('MUSES_DEBUG_FLAG','') == 'true'):
        m_debug_mode  = True;

    def __init__(self):
        function_name = self.m_module_name + "__init__:";
        if (self.m_debug_mode):
            print(function_name);
        return;

    @staticmethod
    def ExitImmediately(i_called_from_module,i_called_label,exit_flag=False):
        # Static method does not have self in the parameter list.
        function_name = "WhereAmI:ExitImmediately:";
        import traceback;
        traceback.print_stack();
        if exit_flag:
            print(function_name,"TRUE_EXITING_AT_CALLED_MODULE",i_called_from_module,"WITH_LABEL",i_called_label);
            exit(0);
        else:
            print(function_name,"FALSE_EXITING_AT_CALLED_MODULE",i_called_from_module,"WITH_LABEL",i_called_label);
        return(1);

if __name__ == '__main__':
    # The code below is for unit testing purpose only by developer.
    #
    #     /pkg/lang/python-3.6.4/bin/python3.6 WhereAmI.py
    #

    function_name = "WhereAmI:";
    my_object = WhereAmI();

    exit(0);
