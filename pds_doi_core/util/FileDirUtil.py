#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

from pds_doi_core.util.const import *;

class FileDirUtil:
    global m_debug_mode;
    m_module_name = 'FileDirUtil:'
    #m_debug_mode = True;
    #m_debug_mode = False;

    @staticmethod
    def CreateDir(i_dir):
        # Function create a directory if it does not already exist.
        # If the i_dir resolves to a file, the directory containing it will be created.
        # This function only works on the lowest sub directory level, e.g. given ~/my_temp_directory_1/my_temp_directory2/my_file
        # if /my_home/my_directory_1 does not already exist, the code will fail.
        function_name = 'CreateDir:';
        global m_debug_mode
        actual_dir = i_dir; 
        if m_debug_mode:
            print(function_name,"i_dir     ",i_dir);
            print(function_name,"actual_dir",actual_dir);
        if os.path.isfile(i_dir):
            actual_dir = os.path.dirname(i_dir);
            if m_debug_mode:
                print(function_name,"ISFILE_TRUE",i_dir);
                print(function_name,"actual_dir",actual_dir);

        # Check if directory already exist.
        if os.path.isdir(actual_dir):
            if m_debug_mode:
                print(function_name,"FILE_DIR_EXIST",actual_dir);
            #print(function_name,"early#0004");
            #exit(0);
            return(1);
 
        try:
            os.mkdir(actual_dir)
        except OSError:
            print(function_name,"Creation of the directory %s failed" % actual_dir)
        else:
            print(function_name,"Successfully created the directory %s" % actual_dir)
        return(1);
        
if __name__ == '__main__':
    global m_debug_mode
    function_name = 'main:';
    #print(function_name,'entering');
    m_debug_mode = True;
    #m_debug_mode = False;

    fileDirUtil = FileDirUtil();
    #fileDirUtil.CreateDir('~/my_temp_directory_1/my_temp_directory_2/my_file');
    fileDirUtil.CreateDir('/home/qchau//my_temp_directory_1/my_temp_directory_2/my_file');
