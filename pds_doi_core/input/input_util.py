#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
#------------------------------                                                                                                 

from lxml import etree
import xlrd

from datetime import datetime

from pds_doi_core.util.const import *

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.outputs.output_util import DOIOutputUtil
from pds_doi_core.util.file_dir_util import FileDirUtil

class DOIInputUtil:
    global m_debug_mode
    global f_log
    m_module_name = 'DOIInputUtil:'
    f_log = None
    m_debug_mode = False
    #m_debug_mode = True

    m_doiConfigUtil = DOIConfigUtil()
    m_doiOutputUtil = DOIOutputUtil()

    def aggregate_reserve_doi(self,DOI_directory_PathName,i_filelist):
        function_name = self.m_module_name + 'aggregate_reserve_doi:'

        #------------------------------
        # Create a file that groups each DOI record into a single file -- that can singly be submitted
        #
        # <?xml version="1.0" encoding="UTF-8"?>
        # <records>
        #   <record status="Reserved">
        #          ...
        #    </record>
        #   <record status="Reserved">
        #          ...
        #    </record>
        # </records>
        #------------------------------
        o_aggregated_DOI_content = b""

        sString = "aaa_DOI_aggregate_reserved.xml"
        DOI_aggregate_filepath = os.path.join(DOI_directory_PathName,sString)

        try:
            f_DOI_aggregate_file = open(DOI_aggregate_filepath, mode='w')
        except:
            print(function_name,"ERROR: Cannot open file for writing.",DOI_aggregate_filepath)
            sys.exit(1)

        try:
            f_DOI_aggregate_file.writelines("<?xml version='1.0' encoding='UTF-8'?>\n")
            f_DOI_aggregate_file.writelines("<records>\n")
            o_aggregated_DOI_content = b"".join([o_aggregated_DOI_content,"<?xml version='1.0' encoding='UTF-8'?>\n".encode()])
            o_aggregated_DOI_content = b"".join([o_aggregated_DOI_content,"<records>\n".encode()])
        except:
            print(function_name,"ERROR: Cannot write to file.",DOI_aggregate_filepath)

        for doi_filename in i_filelist:
            try:
                f_DOI_file = open(doi_filename,mode='r')
                xmlDOI_Text = f_DOI_file.readlines()
                if m_debug_mode:
                    print(function_name,"type(xmlDOI_Text)",type(xmlDOI_Text))
                    print(function_name,"len(xmlDOI_Text)",len(xmlDOI_Text))
                    print(function_name,"xmlDOI_Text[1:-2]",xmlDOI_Text[1:-2])
                # Remove the first and last lines and leave everything in between:
                #     <records>
                #     </records>
            except:
                print(function_name,"ERROR: Cannnot read from DOI file",doi_filename)
                sys.exit(1)

            # Write everything except first and last line:
            #     <records>
            #     </records>
            try:
                if m_debug_mode:
                    print(function_name,"WRITING_LINES")
                    print(function_name,"len(xmlDOI_Text)",len(xmlDOI_Text))
                    print(function_name,"xmlDOI_Text[1:-2]",xmlDOI_Text[1:-2])
                for ii in range(1,len(xmlDOI_Text)-1):
                    f_DOI_aggregate_file.writelines(xmlDOI_Text[ii])
                    o_aggregated_DOI_content = b"".join([o_aggregated_DOI_content,xmlDOI_Text[ii].encode()])

            except:
                print(function_name,"#0001:ERROR: Cannot write to file.",DOI_aggregate_filepath)
        # end for doi_filename in i_filelist)


        # At this point, all the records have been written.
        try:
            f_DOI_aggregate_file.writelines("</records>\n")
            o_aggregated_DOI_content = b"".join([o_aggregated_DOI_content,"</records>\n".encode()])
            # add code here to write aggregate files
            f_DOI_aggregate_file.close()
        except:
            print(function_name,"#0002:ERROR: Cannot write to file.",DOI_aggregate_filepath)

        #print(function_name,"EARLY_0001")
        #exit(0)

        return(o_aggregated_DOI_content)

    def show_column_names_in_xls(self,xl_sheet):
        function_name = self.m_module_name + 'show_column_names_in_xls:'
        #------------------------------
        # Using 'Open' the XLS workbook & sheet
        #   -- grab the names of the columns
        #------------------------------
        row = xl_sheet.row(0)  # 1st row
        print(function_name,60*'-' + 'n(Column #) value [type]n' + 60*'-')
        for idx, cell_obj in enumerate(row):
            cell_type_str = cell_obj.ctype
            #cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')
            #print(function_name,'(%s) %s [%s]' % (idx, cell_obj.value, cell_type_str, ))
            #print(function_name,'(%s) %s [%s]' % (idx, cell_obj.value, cell_type_str))
            print(function_name,'(%s) %s [%s]' % (idx, cell_obj.value.lstrip().rstrip().strip('\n'), cell_type_str))
        return(1)

    def parse_sxls_file(self,appBasePath,i_filepath,dict_fixedList=None, dict_configList=None, dict_ConditionData=None):
        # Function receives a URI containing SXLS format and create one external file per row to output directory.
        function_name = self.m_module_name + 'parse_sxls_file:'
        global m_debug_mode
        global f_log
        #m_debug_mode = True
        o_doi_label = None
        o_num_files_created = 0

        EXPECTED_NUM_COLUMNS = 7
        i_filelist = [] 

        if m_debug_mode:
            print(function_name,"appBasePath",appBasePath)
            print(function_name,"i_filepath",i_filepath)

        dbl_quote = chr(34)
        parent_xpath = "/records/record/"

        DOI_directory_PathName = os.path.join('.','output')
        FileDirUtil.CreateDir(DOI_directory_PathName)

        #------------------------------
        # Open the DOI reserved XML label
        #   -- ElementTree supports 'findall' using dict_namespaces and designation of instances
        #   -- etree doesn't support designation of instances
        #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
        #------------------------------
        res_pathName = dict_configList.get("DOI_reserve_template")
        if m_debug_mode:
            print(function_name,"res_pathName",res_pathName)

        try:
            tree = etree.parse(res_pathName)
            xmlProd_root = tree.getroot()

        except etree.ParseError as err:
            print(function_name,"  -- ABORT: the xml 'Reserved template label file (%s) could not be parsed\n" % (res_pathName) )
            sys.exit(1)
        else:
            pass

        use_panda_flag = True
        #use_panda_flag = False
        if m_debug_mode:
            print(function_name,"use_panda_flag",use_panda_flag)

        #
        # Depending on value of use_panda_flag, import different module.
        # The type of xl_sheet is different for different module so access to them is different as well. 
        #
        if use_panda_flag:
            import pandas as pd
            xl_wb    = pd.ExcelFile(i_filepath)
            actual_sheet_name = xl_wb.sheet_names[0] # We only want the first sheet.
            xl_wb    = pd.read_excel(i_filepath)
            if m_debug_mode:
                print(function_name,"actual_sheet_name",actual_sheet_name)
            xl_sheet = pd.read_excel(i_filepath,actual_sheet_name)
            num_cols = len(xl_sheet.columns)
            num_rows = len(xl_sheet.index)
            if m_debug_mode:
                print(function_name,"xl_sheet.head()",xl_sheet.head())
        else:
            xl_wb = xlrd.open_workbook(i_filepath,f_log)
            xl_sheet = xl_wb.sheet_by_index(0)
            num_cols = xl_sheet.ncols
            num_rows = xl_sheet.nrows

        if m_debug_mode:
            print(function_name,"num_cols",num_cols)
            print(function_name,"num_rows",num_rows)

        if (num_cols < EXPECTED_NUM_COLUMNS):
            print(function_name,"ERROR: expecting",EXPECTED_NUM_COLUMNS,"columns in XLS file has %i columns." % (num_cols),i_filepath)
            print(function_name,"ERROR:i_filepath",i_filepath)
            if use_panda_flag:
                print("data columns",list(xl_sheet.columns))
            else:
                self.show_column_names_in_xls(xl_sheet)
            sys.exit(1)
        else:
            if m_debug_mode:
                if use_panda_flag:
                    print("data columns",list(xl_sheet.columns))
                else:
                    self.show_column_names_in_xls(xl_sheet)

            if use_panda_flag:
                start_row = 0 # Module pandas read in the column header differently, which make the row 0 the first actual data.
            else:
                start_row = 1 # Module xlrd treats rows 0 as the column header so row 1 is the first actual data.

            for row_idx in range(start_row,num_rows):    # Iterate through rows ignore 1st row
                #------------------------------
                # extract metadata from Columns and populate row-content
                #  -- ignore 1st column 'state' which is used for validation
                #------------------------------
                #------------------------------
                # Generate the FileName using the LIDVID
                #    -- remove "urn:nasa:pds"
                #     -- replace "::" with "-"
                #------------------------------
                actual_index = row_idx
                if use_panda_flag:
                    actual_index = row_idx - 1 # Because of how pandas data frame is structure, we subtract 1.
                    related_resource = xl_sheet.iloc[actual_index,6]
                else:
                    related_resource = xl_sheet.cell(row_idx, 6).value

                if m_debug_mode:
                    print(function_name,"row_idx,related_resource",row_idx,related_resource)

                FileName = related_resource.replace("urn:nasa:pds:", "")
                FileName = FileName.replace("::", "_")

                if m_debug_mode:
                    print(function_name,"related_resource,FileName",related_resource,FileName)

                if m_debug_mode:
                    print(function_name," -- processing Product label file: " + FileName)

                dict_ConditionData[FileName] = {}

                if use_panda_flag:
                    dict_ConditionData[FileName]["title"] = xl_sheet.iloc[actual_index, 1]
                else:
                    dict_ConditionData[FileName]["title"] = xl_sheet.cell(row_idx, 1).value
                #--
                # Eventhough cell is shown to be 'text / unicode' value is actually stored as datetime
                #    -- test for unicode else datetime
                #--
                if use_panda_flag:
                    type_date_column = str(type(xl_sheet.iloc[actual_index, 2]))
                else:
                    type_date_column = str((type(xl_sheet.cell(row_idx, 2).value))) 
                if m_debug_mode:
                    print(function_name,"type_date_column",type_date_column)
                if 'unicode' in type_date_column or 'str' in type_date_column:
                    if use_panda_flag:
                        dict_ConditionData[FileName]["publication_date"] = xl_sheet.iloc[actual_index, 2]
                    else:
                        dict_ConditionData[FileName]["publication_date"] = xl_sheet.cell(row_idx, 2).value
                else:
                    if use_panda_flag:
                        pb_int = xl_sheet.iloc[actual_index,2]
                        pb_datetime = pb_int
                    else:
                        pb_int = xl_sheet.cell(row_idx, 2).value
                        pb_datetime = datetime(*xlrd.xldate_as_tuple(pb_int, xl_wb.datemode))
                        dict_ConditionData[FileName]["publication_date"] = pb_datetime.strftime("%Y-%m-%d")
                        if m_debug_mode:
                            print(function_name,"pb_int, xl_wb.datemode",pb_int, xl_wb.datemode)
                            print(function_name,"type(pb_int), type(xl_wb.datemode)",type(pb_int), type(xl_wb.datemode))
                            print(function_name,"xlrd.xldate_as_tuple(pb_int, xl_wb.datemode)",xlrd.xldate_as_tuple(pb_int, xl_wb.datemode))

                dict_ConditionData[FileName]["product_type"] ="Collection"
                if use_panda_flag:
                    dict_ConditionData[FileName]["product_type_specific"]     = xl_sheet.iloc[actual_index,3]
                    dict_ConditionData[FileName]["authors/author/last_name"]  = xl_sheet.iloc[actual_index,4]
                    dict_ConditionData[FileName]["authors/author/first_name"] = xl_sheet.iloc[actual_index,5]
                    dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"] = xl_sheet.iloc[actual_index,6]
                else:
                    dict_ConditionData[FileName]["product_type_specific"]     = xl_sheet.cell(row_idx, 3).value
                    dict_ConditionData[FileName]["authors/author/last_name"]  = xl_sheet.cell(row_idx, 4).value
                    dict_ConditionData[FileName]["authors/author/first_name"] = xl_sheet.cell(row_idx, 5).value
                    dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"] = xl_sheet.cell(row_idx, 6).value

                if m_debug_mode:
                    print(function_name,"FileName,dict_ConditionData[FileName]",FileName,dict_ConditionData[FileName])

                #------------------------------
                #------------------------------
                # Begin replacing the metadata in the DOI template file with that in Product Label
                #------------------------------
                try:
                    #f_DOI_file = open(res_pathName, mode='r+')
                    f_DOI_file = open(res_pathName, mode='r')
                    xmlDOI_Text = f_DOI_file.read()
                    f_DOI_file.close()

                except:
                    print(function_name,"DOI template file (%s) not found for edit\n" % (res_pathName))
                    sys.exit(1)

                #------------------------------
                # For each key/value in dictionary (that contains the values for the DOI label)
                #------------------------------
                dict_value = dict_ConditionData.get(FileName)

                for key, value in dict_value.items():
                    attr_xpath = parent_xpath + key

                    xmlDOI_Text = self.m_doiOutputUtil.populate_doi_xml_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, value)

                #------------------------------
                # Write the replacement metadata to the DOI file
                #------------------------------
                sString = "DOI_reserved_" + FileName + ".xml"
                sString = sString.replace(":", "_")
                DOI_filepath = os.path.join(DOI_directory_PathName,sString)
                if m_debug_mode:
                    print(function_name,"sString,DOI_filepath",sString,DOI_filepath)

                print(function_name,"FILE_WRITE",DOI_filepath)

                f_DOI_file = open(DOI_filepath, mode='w')
                f_DOI_file.write(xmlDOI_Text.decode())
                f_DOI_file.close()

                # Add the new name created to so we can agggregate them all into one file.
                i_filelist.append(DOI_filepath)

                o_num_files_created += 1
                #print(function_name,"early#exit#0099")
                #sys.exit()
            # end for row_idx in range(1, xl_sheet.nrows):    # Iterate through rows ignore 1st row

            if m_debug_mode:
                print(function_name,"FILE_WRITE_SUMMARY:o_num_files_created",o_num_files_created)
                print(function_name,"FILE_WRITE_SUMMARY:num_rows",num_rows)

            o_aggregated_DOI_content = self.aggregate_reserve_doi(DOI_directory_PathName,i_filelist)

        return(o_num_files_created,o_aggregated_DOI_content)

    def parse_csv_file(self,appBasePath,i_filepath,dict_fixedList=None, dict_configList=None, dict_ConditionData=None):
        # Function receives a URI containing CSV format and create one external file per row to output directory.
        function_name = self.m_module_name + 'parse_csv_file:'
        global m_debug_mode
        global f_log
        m_debug_mode = True
        o_doi_label = None
        o_num_files_created = 0

        EXPECTED_NUM_COLUMNS = 7
        i_filelist = [] 

        if m_debug_mode:
            print(function_name,"appBasePath",appBasePath)
            print(function_name,"i_filepath",i_filepath)

        dbl_quote = chr(34)
        parent_xpath = "/records/record/"

        DOI_directory_PathName = os.path.join('.','output')
        # consider to replace with
        # os.makedirs(DOI_directory_PathName, exist_ok=True)
        FileDirUtil.CreateDir(DOI_directory_PathName)

        #------------------------------
        # Open the DOI reserved XML label
        #   -- ElementTree supports 'findall' using dict_namespaces and designation of instances
        #   -- etree doesn't support designation of instances
        #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
        #------------------------------
        res_pathName = dict_configList.get("DOI_reserve_template")
        if m_debug_mode:
            print(function_name,"res_pathName",res_pathName)

        try:
            tree = etree.parse(res_pathName)
            xmlProd_root = tree.getroot()

        except etree.ParseError as err:
            print(function_name,"  -- ABORT: the xml 'Reserved template label file (%s) could not be parsed\n" % (res_pathName) )
            sys.exit(1)
        else:
            pass

        use_panda_flag = True
        #use_panda_flag = False
        if m_debug_mode:
            print(function_name,"use_panda_flag",use_panda_flag)

        #
        # Depending on value of use_panda_flag, import different module.
        # The type of xl_sheet is different for different module so access to them is different as well. 
        #
        if use_panda_flag:
            import pandas as pd
            xl_sheet = pd.read_csv(i_filepath)
            num_cols = len(xl_sheet.columns)
            num_rows = len(xl_sheet.index)
            if m_debug_mode:
                print(function_name,"xl_sheet.head()",xl_sheet.head())
        else:
            pass
            #xl_wb = xlrd.open_workbook(i_filepath,f_log)
            #xl_sheet = xl_wb.sheet_by_index(0)
            #num_cols = xl_sheet.ncols
            #num_rows = xl_sheet.nrows

        if m_debug_mode:
            print(function_name,"num_cols",num_cols)
            print(function_name,"num_rows",num_rows)

        if (num_cols < EXPECTED_NUM_COLUMNS):
            print(function_name,"ERROR: expecting",EXPECTED_NUM_COLUMNS,"columns in XLS file has %i columns." % (num_cols),i_filepath)
            print(function_name,"ERROR:i_filepath",i_filepath)
            if use_panda_flag:
                print("data columns",list(xl_sheet.columns))
            else:
                self.ShowColumnNamesInXLS(xl_sheet)
            sys.exit(1)
        else:
            if m_debug_mode:
                if use_panda_flag:
                    print("data columns",list(xl_sheet.columns))
                else:
                    self.ShowColumnNamesInXLS(xl_sheet)

            if use_panda_flag:
                start_row = 0 # Module pandas read in the column header differently, which make the row 0 the first actual data.
            else:
                start_row = 1 # Module xlrd treats rows 0 as the column header so row 1 is the first actual data.

            for row_idx in range(start_row,num_rows):    # Iterate through rows ignore 1st row
                #------------------------------
                # extract metadata from Columns and populate row-content
                #  -- ignore 1st column 'state' which is used for validation
                #------------------------------
                #------------------------------
                # Generate the FileName using the LIDVID
                #    -- remove "urn:nasa:pds"
                #     -- replace "::" with "-"
                #------------------------------
                actual_index = row_idx

                # Extra processing if any fields starts with single or double quotes. 

                if use_panda_flag:
                    actual_index = row_idx - 1 # Because of how pandas data frame is structure, we subtract 1.
                    related_resource = xl_sheet.iloc[actual_index,6]
                else:
                    related_resource = xl_sheet.cell(row_idx, 6).value

                if m_debug_mode:
                    print(function_name,"row_idx,related_resource",row_idx,related_resource)
                #print(function_name,"related_resource[" + related_resource + "]")
                #print(function_name,"ZZZ_001")
                #exit(0)

                FileName = related_resource.replace("urn:nasa:pds:", "")
                FileName = FileName.replace("::", "_")

                if m_debug_mode:
                    print(function_name,"related_resource,FileName",related_resource,FileName)

                if m_debug_mode:
                    print(function_name," -- processing Product label file: " + FileName)

                dict_ConditionData[FileName] = {}

                if use_panda_flag:
                    dict_ConditionData[FileName]["title"] = xl_sheet.iloc[actual_index, 1]
                else:
                    dict_ConditionData[FileName]["title"] = xl_sheet.cell(row_idx, 1).value
                #--
                # Eventhough cell is shown to be 'text / unicode' value is actually stored as datetime
                #    -- test for unicode else datetime
                #--
                if use_panda_flag:
                    type_date_column = str(type(xl_sheet.iloc[actual_index, 2]))
                else:
                    type_date_column = str((type(xl_sheet.cell(row_idx, 2).value))) 
                if m_debug_mode:
                    print(function_name,"type_date_column",type_date_column)
                if 'unicode' in type_date_column or 'str' in type_date_column:
                    if use_panda_flag:
                        dict_ConditionData[FileName]["publication_date"] = xl_sheet.iloc[actual_index, 2]
                    else:
                        dict_ConditionData[FileName]["publication_date"] = xl_sheet.cell(row_idx, 2).value
                else:
                    if use_panda_flag:
                        pb_int = xl_sheet.iloc[actual_index,2]
                        pb_datetime = pb_int
                    else:
                        pb_int = xl_sheet.cell(row_idx, 2).value
                        pb_datetime = datetime(*xlrd.xldate_as_tuple(pb_int, xl_wb.datemode))
                        dict_ConditionData[FileName]["publication_date"] = pb_datetime.strftime("%Y-%m-%d")
                        if m_debug_mode:
                            print(function_name,"pb_int, xl_wb.datemode",pb_int, xl_wb.datemode)
                            print(function_name,"type(pb_int), type(xl_wb.datemode)",type(pb_int), type(xl_wb.datemode))
                            print(function_name,"xlrd.xldate_as_tuple(pb_int, xl_wb.datemode)",xlrd.xldate_as_tuple(pb_int, xl_wb.datemode))

                dict_ConditionData[FileName]["product_type"] ="Collection"
                if use_panda_flag:
                    dict_ConditionData[FileName]["product_type_specific"]     = xl_sheet.iloc[actual_index,3]
                    dict_ConditionData[FileName]["authors/author/last_name"]  = xl_sheet.iloc[actual_index,4]
                    dict_ConditionData[FileName]["authors/author/first_name"] = xl_sheet.iloc[actual_index,5]
                    dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"] = xl_sheet.iloc[actual_index,6]
                else:
                    dict_ConditionData[FileName]["product_type_specific"]     = xl_sheet.cell(row_idx, 3).value
                    dict_ConditionData[FileName]["authors/author/last_name"]  = xl_sheet.cell(row_idx, 4).value
                    dict_ConditionData[FileName]["authors/author/first_name"] = xl_sheet.cell(row_idx, 5).value
                    dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"] = xl_sheet.cell(row_idx, 6).value

                if m_debug_mode:
                    print(function_name,"FileName,dict_ConditionData[FileName]",FileName,dict_ConditionData[FileName])

                #------------------------------
                #------------------------------
                # Begin replacing the metadata in the DOI template file with that in Product Label
                #------------------------------
                try:
                    #f_DOI_file = open(res_pathName, mode='r+')
                    f_DOI_file = open(res_pathName, mode='r')
                    xmlDOI_Text = f_DOI_file.read()
                    f_DOI_file.close()

                except:
                    print(function_name,"DOI template file (%s) not found for edit\n" % (res_pathName))
                    sys.exit(1)

                #------------------------------
                # For each key/value in dictionary (that contains the values for the DOI label)
                #------------------------------
                dict_value = dict_ConditionData.get(FileName)

                for key, value in dict_value.items():
                    attr_xpath = parent_xpath + key

                    xmlDOI_Text = self.m_doiOutputUtil.populate_doi_xml_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, value)

                #------------------------------
                # Write the replacement metadata to the DOI file
                #------------------------------
                sString = "DOI_reserved_" + FileName + ".xml"
                sString = sString.replace(":", "_")
                DOI_filepath = os.path.join(DOI_directory_PathName,sString)
                if m_debug_mode:
                    print(function_name,"sString,DOI_filepath",sString,DOI_filepath)

                print(function_name,"FILE_WRITE",DOI_filepath)

                f_DOI_file = open(DOI_filepath, mode='w')
                f_DOI_file.write(xmlDOI_Text.decode())
                f_DOI_file.close()

                # Add the new name created to so we can agggregate them all into one file.
                i_filelist.append(DOI_filepath)

                o_num_files_created += 1
                #print(function_name,"early#exit#0099")
                #sys.exit()
            # end for row_idx in range(1, xl_sheet.nrows):    # Iterate through rows ignore 1st row

            if m_debug_mode:
                print(function_name,"FILE_WRITE_SUMMARY:o_num_files_created",o_num_files_created)
                print(function_name,"FILE_WRITE_SUMMARY:num_rows",num_rows)
            #print(function_name,"early#exit#0099")
            #sys.exit()

            o_aggregated_DOI_content = self.aggregate_reserve_doi(DOI_directory_PathName,i_filelist)

        return(o_num_files_created,o_aggregated_DOI_content)

if __name__ == '__main__':
    global f_log   
    global m_debug_mode
    function_name = 'main:'
    #print(function_name,'entering')
    f_log     = None 
    m_debug_mode = True
    m_debug_mode = False


    doiInputUtil = DOIInputUtil()
    doiConfigUtil = DOIConfigUtil()

    # Get the default configuration from external file.  Location may have to be absolute.
    xmlConfigFile = os.path.join('.','config','default_config.xml')

    dict_configList = {}
    dict_fixedList  = {}
    (dict_configList, dict_fixedList) = doiConfigUtil.get_config_file_metadata(xmlConfigFile)

    appBasePath = os.path.abspath(os.path.curdir)
    #------------------------------
    # Set the values for the common parameters
    #------------------------
    root_path = dict_configList.get("root_path")
    pds_uri   = dict_fixedList.get("pds_uri")
   
    dict_fileName_matched_status = {}
    dict_siteURL = {}
    dict_ConditionData = {}
    dict_LIDVID_submitted = {}

    i_filepath = os.path.join('.','input','DOI_Reserved_GEO_200318.xlsx')
    #o_num_files_created = doiInputUtil.ParseSXLSFile(appBasePath,i_filepath,dict_fixedList=dict_fixedList,dict_configList=dict_configList,dict_ConditionData=dict_ConditionData)
    #print(function_name,"o_num_files_created",o_num_files_created)


    i_filepath = os.path.join('.','input','DOI_Reserved_GEO_200318.csv')
    o_num_files_created = doiInputUtil.ParseCSVFile(appBasePath,i_filepath,dict_fixedList=dict_fixedList,dict_configList=dict_configList,dict_ConditionData=dict_ConditionData)
    print(function_name,"o_num_files_created",o_num_files_created)
