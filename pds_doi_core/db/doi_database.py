#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import datetime
import os

import sqlite3
from sqlite3 import Error

from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.util.general_util import get_logger

# Get the common logger and set the level for this file.
import logging
logger = get_logger('pds_doi_core.db_util.doi_database')

class DOIDataBase:
    # This DOIDataBase class provides mechanism to write a row, update a row into sqlite database.
    m_database_name = None
    m_my_conn = None
    m_NUM_COLS = 13    # We are only expecting 13 colums in the doi table.  If table structure changes, this value needs updated.
    m_doi_config_util = DOIConfigUtil()

    def __init__(self):
        self._config = self.m_doi_config_util.get_config()
        self.m_default_table_name = self._config.get('OTHER','db_table')  # Default name of table.
        self.m_default_db_file    = self._config.get('OTHER','db_file')   # Default name of the database.

    def get_database_name(self):
        ''' Returns the name of the SQLite database. '''

        return self.m_database_name

    def close_database(self):
        ''' Close database connection to a SQLite database. '''

        logger.debug(f"Closing database {self.m_database_name}") 

        if self.m_my_conn:
            self.m_my_conn.close()

            # Set m_database_name to None to signify that there is no connection. 
            self.m_database_name = None
        else:
            logger.warn(f"Database connection has not been started or is already closed:m_database_name [{self.m_database_name}]")

        return

    def create_connection(self, db_file):
        ''' Create a database connection to a SQLite database '''

        self.m_my_conn = None
        try:
            self.m_my_conn = sqlite3.connect(db_file)
            logger.info(f"sqlite3.version {sqlite3.version}")
            # Connection is a success, we can now save the database filename.
            self.m_database_name = db_file
        except Error as my_error:
            logger.error(f"{my_error}")
        # For now, don't close the connection.
        #finally:
        #    if self.m_my_conn:
        #        self.close_database()
        return self.m_my_conn

    def check_if_table_exist(self,table_name):
        ''' Check if the table name does exist in the database.'''

        o_table_exist_flag = True
        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name}")
            self.m_my_conn = self.create_connection(self.m_database_name)
        table_pointer = self.m_my_conn.cursor()
            
        # Get the count of tables with the given name.
        query_string = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='" + table_name + "'"
        table_pointer.execute(query_string)

        # If the count is 1, then table exists.
        if table_pointer.fetchone()[0] == 1:
            pass
        else :
            o_table_exist_flag = False
        return o_table_exist_flag

    def drop_table(self, db_name, table_name):
        ''' Delete the given table from the SQLite database. '''

        self.m_my_conn.execute('DROP TABLE ' + table_name)
        logger.debug(f"DROP TABLE {table_name}")
        return 1

    def create_q_string_for_create(self, table_name):
        ''' Build the query string to create a table in the SQLite database. '''

        # Note that this table structure is defined here so if you need to know the structure.
        o_query_string = 'CREATE TABLE ' + table_name  +  ' '
        o_query_string += '(status TEXT NOT NULL'       # current status, among: pending, draft, reserved, released, deactivated)
        o_query_string += ',update_date INT NOT NULL' # as Unix Time, the number of seconds since 1970-01-01 00:00:00 UTC.
        o_query_string += ',submitter TEXT '    # email of the submitter of the DOI
        o_query_string += ',title TEXT '        # title used for the DOI
        o_query_string += ',type TEXT '         # product type
        o_query_string += ',subtype TEXT'      # subtype of the product 
        o_query_string += ',node_id TEXT NOT NULL'      # steward discipline node ID
        o_query_string += ',lid TEXT '
        o_query_string += ',vid TEXT '
        o_query_string += ',doi TEXT'                   # DOI provided by the provider (may be null if pending or draft)
        o_query_string += ',release_date INT '  # as Unix Time, the number of seconds since 1970-01-01 00:00:00 UTC.
        o_query_string += ',transaction_key TEXT NOT NULL' # transaction (key is node id /datetime) 
        o_query_string += ',is_latest BOOLEAN NULL); ' # when the transaction is the latest 
        logger.debug(f"o_query_string {o_query_string}")

        return o_query_string

    def create_q_string_for_insert(self, table_name):
        ''' Build the query string to insert into the table in the SQLite database. '''

        # Note that this table structure is defined here so if you need to know the structure.
        o_query_string = 'INSERT INTO ' + table_name + ' '

        o_query_string += '(status'
        o_query_string += ',update_date'
        o_query_string += ',submitter'
        o_query_string += ',title'
        o_query_string += ',type'
        o_query_string += ',subtype'
        o_query_string += ',node_id'
        o_query_string += ',lid'
        o_query_string += ',vid'
        o_query_string += ',doi'
        o_query_string += ',release_date'
        o_query_string += ',transaction_key'
        o_query_string += ',is_latest) VALUES '
        o_query_string += '(?,?,?,?,?,?,?,?,?,?,?,?,?)'

        logger.debug(f"o_query_string {o_query_string}")

        return o_query_string

    def create_q_string_for_transaction_insert(self, table_name):
        ''' Build the query string to insert a transaction into the table in the SQLite database. '''

        # Note that this table structure is defined here so if you need to know the structure.
        # Also note that we are not setting all columns, just the ones related to a transaction.
        o_query_string = 'INSERT INTO ' + table_name + ' '

        o_query_string += '(status'
        o_query_string += ',type'
        o_query_string += ',subtype'
        o_query_string += ',is_latest'
        o_query_string += ',lid'
        o_query_string += ',vid'
        o_query_string += ',doi'
        o_query_string += ',submitter'
        o_query_string += ',update_date'
        o_query_string += ',node_id'
        o_query_string += ',title'
        o_query_string += ',transaction_key) VALUES '
        o_query_string += '(?,?,?,?,?,?,?,?,?,?,?,?)'

        logger.debug(f"o_query_string {o_query_string}")

        return o_query_string

    def create_q_string_for_transaction_update(self, table_name, dict_row):
        ''' Build the query string to update existing rows in the table with the update_date field earlier than the current row in the SQLite database. '''

        # Note that this table structure is defined here so if you need to know the structure.
        # Also note that we setting column is_latest to 0 to signify that all previous rows are now not the latest.
        # Note that the key in dict_row is latest_update
        o_query_string = 'UPDATE ' + table_name + ' '

        o_query_string += 'SET '
        o_query_string += 'is_latest = 0 '
        o_query_string += 'WHERE lid = "' + str(dict_row['lid']) + '"'
        o_query_string += ' AND  vid = "' + str(dict_row['vid']) + '"'
        o_query_string += ' AND  update_date < ' + str(dict_row['latest_update'])  # We only want record earlier than the one just inserted
        o_query_string += ';' # Don't forget the last semi-colon for SQL to work.


        logger.debug(f"o_query_string {o_query_string}")

        return o_query_string

    def create_table(self, table_name):
        ''' Create a given table in the SQLite database. '''

        logger.debug(f"self.m_my_conn {self.m_my_conn}")
        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(db_file)

        o_table_exist_flag = self.check_if_table_exist(table_name)
        logger.debug(f"o_table_exist_flag {o_table_exist_flag}")

#        if o_table_exist_flag:
#            logger.warn(f"Table {table_name} already exist")
#
#        # Table does not already exist, we can create it now.

        query_string = self.create_q_string_for_create(table_name)
        logger.debug(f'doi_create_table:query_string {query_string}')
        self.m_my_conn.execute(query_string)

        logger.debug(f"Table created successfully")

        return 1

    def _int_columns_check(self,db_name,table_name,dict_row):
       ''' Do a sanity check on the types of all the date columns.  The ones we need to check are:

             update_date
             release_date

           since they should be of type int. '''

       long_int_type_list = ['update_date', 'release_date']
       for long_int_field in long_int_type_list:
           if long_int_field in dict_row:
               logger.debug(f"long_int_field,type(dict_row[long_int_field]) {long_int_field},{type(dict_row[long_int_field])}")
               logger.debug(f"long_int_field,isinstance(dict_row[long_int_field],int) {long_int_field},{isinstance(dict_row[long_int_field],int)}")
               if not isinstance(dict_row[long_int_field],int):
                   logger.error(f"Expecting field {long_int_field} to be of type int but otherwise:{type(dict_row[long_int_field])}")
                   logger.error(f"db_name,table_name {db_name},{table_name}")
                   exit(1)
       # end for long_int_field in long_int_type_list:

       return 1

    def insert_row(self, db_name, table_name, dict_row, drop_exist_table_flag=False):
        '''Insert a row into the table table_name the database db_name. All fields in dict dict_row are expected to be there.'''
        logger.debug(f"self.m_my_conn {self.m_my_conn}")

        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(db_file)
        o_table_exist_flag = self.check_if_table_exist(table_name)
        logger.debug(f"table_name,o_table_exist_flag {table_name},{o_table_exist_flag}")

        # Do a sanity check on the types of all the columns int.
        donotcare = self._int_columns_check(db_name,table_name,dict_row)

        query_string = self.create_q_string_for_insert(table_name)

        # Note that the order of items in data_tuple must match the columns in the table in the same order.
        data_tuple = (dict_row['status'],           # 1
                      dict_row['update_date'],    # 2
                      dict_row['submitter'],        # 3
                      dict_row['title'],            # 4
                      dict_row['type'],             # 5
                      dict_row['subtype'],          # 6
                      dict_row['node_id'],          # 7
                      dict_row['lid'],              # 8
                      dict_row['vid'],              # 9
                      dict_row['doi'],              # 10
                      dict_row['release_date'],     # 11 
                      dict_row['transaction_key'],  # 12
                      dict_row['is_latest'])        # 13

        logger.debug(f"query_string {query_string}")

        self.m_my_conn.execute(query_string,data_tuple)
        self.m_my_conn.commit()

        return 1

    def update_previous_records(self,dict_row):
        '''Update all records that share the same lid,vid before the current update_date field in dict_row.'''

        logger.debug(f"dict_row {dict_row}")

        # Create the query string with the criteria for lid, vid and update_date
        query_string = self.create_q_string_for_transaction_update(self.m_default_table_name, dict_row)

        self.m_my_conn.execute(query_string)
        self.m_my_conn.commit()

        return 1

    def write_doi_info_to_database(self,dict_row):
        '''Write some DOI info from 'reserve' or 'draft' request to database.'''

        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(self.m_default_db_file)
        o_table_exist_flag = self.check_if_table_exist(self.m_default_table_name)

        # Create the table if it does not already exist.
        if not o_table_exist_flag:
            self.create_table(self.m_default_table_name)

        logger.debug(f"table_name,o_table_exist_flag {self.m_default_table_name},{o_table_exist_flag}")

        # Do a sanity check on the types of all the int columns.
        donotcare = self._int_columns_check(self.m_default_db_file,self.m_default_table_name,dict_row)

        query_string = self.create_q_string_for_transaction_insert(self.m_default_table_name)

        logger.debug(f"query_string {query_string}")

        status          = dict_row['status'].lower()
        if 'title' in dict_row:
            title           = dict_row['title']
        else:
            logger.warn(f"Field 'title' is missing from dict_row")
            title           = None 
        if 'type' in dict_row:
            product_type    = dict_row['type']    # PYTHON_NOTE: Cannot use 'type' as a variable as it is a keyword.
        else:
            logger.warn(f"Field 'type' is missing from dict_row")
            product_type    = None 
        if 'subtype' in dict_row:
            subtype         = dict_row['subtype']
        else:
            logger.warn(f"Field 'subtype' is missing from dict_row")
            subtype         = None 
        is_latest       = True
        if 'lid' in dict_row:
            lid             = dict_row['lid']
        else:
            logger.warn(f"Field 'lid' is missing from dict_row")
            lid             = None 
        if 'vid' in dict_row:
            vid             = dict_row['vid']
        else:
            logger.warn(f"Field 'vid' is missing from dict_row")
            vid             = None 
        if 'doi' in dict_row:
            doi             = dict_row['doi']
        else:
            logger.warn(f"Field 'doi' is missing from dict_row")
            doi             = None 
        update_date     = dict_row['latest_update']   # Note that the key is latest_update from translation_logger
        submitter       = dict_row['submitter']
        discipline_node = dict_row['discipline_node'].lower()
        transaction_key = dict_row['transaction_key']
        action_type     = dict_row['action_type'].upper()
        input_content   = dict_row['input_content']
        content_type    = dict_row['content_type']
        output_content  = dict_row['output_content']
        submitted_input_link  = dict_row['submitted_input_link']
        submitted_output_link = dict_row['submitted_output_link']

        logger.debug(f"submitted_input_link,submitted_output_link {submitted_input_link},{submitted_output_link}")
        logger.debug(f"product_type,subtype {product_type,subtype}")

        # Note that the order of items in data_tuple must match the columns in query in the same order.
        # TODO: More columns should be written to represent a transaction.

        data_tuple = (status,product_type,subtype,is_latest,lid,vid,doi,submitter,update_date,discipline_node,title,transaction_key)

        logger.debug(f"TRANSACTION_INFO:data_tuple {data_tuple}")

        self.m_my_conn.execute(query_string,data_tuple)
        self.m_my_conn.commit()

        donotcare = self.update_previous_records(dict_row)

        return 1

    def select_row_one(self, db_name, table_name, query_criterias):
        ''' Select rows based on a criteria.'''

        logger.debug(f"self.m_my_conn {self.m_my_conn}")
        logger.debug(f"query_criterias [{query_criterias}]")

        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(db_file)
        o_table_exist_flag = self.check_if_table_exist(table_name)
        logger.debug(f"table_name,o_table_exist_flag {table_name},{o_table_exist_flag}")

        query_string = 'SELECT * FROM ' + table_name
        if len(query_criterias) > 0:
            query_string += ' WHERE '
        for ii in range(len(query_criterias)):
            # Build the WHERE clause
            if ii == 0:
                query_string += query_criterias[ii]
            else:
                query_string += ' AND '   + query_criterias[ii]

        query_string += ';  '

        logger.debug(f"query_string {query_string}")

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string)
        column_names = list(map(lambda x: x[0], cursor.description))
        records = cursor.fetchall()

        for row_index, row in enumerate(records):
            for col in range(0,self.m_NUM_COLS):
             logger.debug("row_index,col,column_names[col],type(row[col]),row[col]",row_index,col,column_names[col],type(row[col]),row[col])

        return 1

    def doi_select_rows_all(self,db_name,table_name):
        ''' Select all rows. '''
        logger.debug(f"self.m_my_conn {self.m_my_conn}")

        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(db_file)
        o_table_exist_flag = self.check_if_table_exist(table_name)
        logger.debug(f"table_name,o_table_exist_flag {table_name},{o_table_exist_flag}")

        query_string = 'SELECT * FROM ' + table_name + ';   '
        logger.debug(f"doi_select_rows_all:query_string {query_string}")

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string)
        column_names = list(map(lambda x: x[0], cursor.description))
        records = cursor.fetchall()

        logger.debug("len(records)",len(records))
        for row_index, row in enumerate(records):
            for col in range(0,10):
             logger.debug("row_index,col,column_names[col],type(row[col]),row[col]",row_index,col,column_names[col],type(row[col]),row[col])

        return 1

    def update_row(self, db_name, table_name, update_list, query_criterias):
        ''' Update all rows and fields (specified in update_list matching query_criterias.'''

        logger.debug(f"self.m_my_conn {self.m_my_conn}")

        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(db_file)
        o_table_exist_flag = self.check_if_table_exist(table_name)
        logger.debug(f"table_name,o_table_exist_flag {table_name},{o_table_exist_flag}")

        query_string = 'UPDATE ' + table_name + ' SET '
        for ii in range(len(update_list)):
            # Build the SET column_1 = new_value_1,
            #               column_2 = new_value_2
            # Only preceed the comma if not the first one.
            if ii == 0:
                query_string += update_list[ii]
            else:
                query_string += ',' + update_list[ii]

        # Add any query_criterias
        if len(query_criterias) > 0:
            query_string += ' WHERE '
        for ii in range(len(query_criterias)):
            if ii == 0:
                query_string += query_criterias[ii]
            else:
                query_string += ' AND ' + query_criterias[ii]
        logger.debug(f"query_string {query_string}")

        self.m_my_conn.execute(query_string)

        return 1

# end of doi_database.py
