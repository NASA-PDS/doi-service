#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------

import datetime
import json 
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

    def create_q_string_for_transaction_insert(self):
        ''' Build the query string to insert a transaction into the table in the SQLite database. '''

        # Note that this table structure is defined here so if you need to know the structure.
        # Also note that we are not setting all columns, just the ones related to a transaction.
        o_query_string = 'INSERT INTO ' + self.m_default_table_name + ' '

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

    def create_q_string_for_transaction_update_is_latest_field(self):
        ''' Build the query string to update existing rows in the table with the update_date field earlier than the current row in the SQLite database.
            The current row is the row just inserted with the "update_date" value of "latest_update".
            The comparison criteria is less than, meaning any rows inserted earlier will be updated with column
            "is_latest" to zero.'''

        # Note that this table structure is defined here so you need to know the structure.
        # Also note that we setting column is_latest to 0 to signify that all previous rows are now not the latest.
        # Note that the key in dict_row is 'latest_update' not 'update_date' (not same as column name).
        o_query_string = 'UPDATE ' + self.m_default_table_name + ' '
        o_query_string += 'SET '
        o_query_string += 'is_latest = 0 '
        o_query_string += 'WHERE lid = ?'
        o_query_string += ' AND  vid = ?'
        o_query_string += ' AND  (doi = ? or doi is NULL)'
        o_query_string += ';' # Don't forget the last semi-colon for SQL to work.

        logger.debug(f"o_query_string {o_query_string}")

        return o_query_string

    def create_table(self, table_name):
        ''' Create a given table in the SQLite database. '''

        logger.debug(f"self.m_my_conn {self.m_my_conn}")
        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(self.m_default_db_file)

        o_table_exist_flag = self.check_if_table_exist(table_name)
        logger.debug(f"o_table_exist_flag {o_table_exist_flag}")

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
            self.m_my_conn = self.create_connection(self.m_default_db_file)
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

    def write_doi_info_to_database_all(self,doi_fields):
        for field_index in range(0,len(doi_fields)):
            self.write_doi_info_to_database(doi_fields[field_index])

        return 1

    def write_doi_info_to_database(self, lid, vid, transaction_key, doi=None, transaction_date=datetime.datetime.now(), status='unknown',
                                   title='', product_type='', product_type_specific='', submitter='', discipline_node=''):
        '''Write some DOI info from 'reserve' or 'draft' request to database.'''

        if self.m_my_conn is None:
            logger.info(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(self.m_default_db_file)
        o_table_exist_flag = self.check_if_table_exist(self.m_default_table_name)

        # Create the table if it does not already exist.
        if not o_table_exist_flag:
            self.create_table(self.m_default_table_name)

        logger.debug(f"table_name,o_table_exist_flag {self.m_default_table_name},{o_table_exist_flag}")

        # Note that the order of items in data_tuple must match the columns in query in the same order.

        data_tuple = (status, product_type, product_type_specific, True, lid, vid, doi,
                      submitter, transaction_date.timestamp(), discipline_node, title, transaction_key)

        logger.debug(f"TRANSACTION_INFO:data_tuple {data_tuple}")

        try:
            # Create and execute the query to unset latest for record same lid/vid and doi fields.
            query_string = self.create_q_string_for_transaction_update_is_latest_field()
            self.m_my_conn.execute(query_string, (lid, vid, doi if doi else 'NULL' ))

            # Combine the insert and update here so the commit can be applied to both actions.
            query_string = self.create_q_string_for_transaction_insert()
            logger.debug(f"query_string {query_string}")
            self.m_my_conn.execute(query_string,data_tuple)
            self.m_my_conn.commit()
        except sqlite3.Error as e:
            logger.error("Database error: %s" % e)
            logger.error(f"query_string {query_string}")
            raise Exception("Database error: %s" % e) from None
        except Exception as e:
            logger.error("Exception in _query: %s" % e)
            raise Exception("Exception in _query: %s" % e) from None

        return 1

    def select_row_one(self, db_name, table_name, query_criterias):
        ''' Select rows based on a criteria.'''

        logger.debug(f"self.m_my_conn {self.m_my_conn}")
        logger.debug(f"query_criterias [{query_criterias}]")

        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(self.m_default_db_file)
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

    def _parse_query_criterias(self, query_criterias):
        # This function parses the list of query_criterias into their individual tokens of column name and value.
        #
        # The format of query_criterias is a dictionary of fields with keys corresponding to columns:
        # node_id = '10.17189/21259'
        # title = 'Laboratory Shocked Feldspars Collection
        # submitter = 'Qui.T.Chau@jpl.nasa.gov'
        # liv = 'urn:nasa:pds:lab_shocked_feldspars'
        # vid = '1.0'
        # node_id = 'img'
        o_column_names  = []
        o_column_values = []

        if 'doi' in query_criterias:
            # Save the column name and the column value for each criteria
            o_column_names.append ('doi')
            o_column_values.append(query_criterias['doi'])
        if 'lid' in query_criterias:
            # Save the column name and the column value for each criteria
            o_column_names.append ('lid')
            o_column_values.append(query_criterias['lid'])
        if 'lidvid' in query_criterias:
            # If we have existing 'lid' in o_column_names and values, we have to remove them otherwise
            # we will end up having duplicate columns.
            if 'lid' in o_column_names:
                lid_index = o_column_names.index('lid') 
                del o_column_names[lid_index]
                del o_column_values[lid_index]

            # Because the lidvid contains a combination of two things, we have to parse them
            # into individual fields of 'lid', and 'vid'
            lid_values_list = []
            vid_values_list = []
            for ii in range(0,len(query_criterias['lidvid'])):
                tokens = query_criterias['lidvid'][ii].split('::')
                if len(tokens) == 2:
                    # Save the column name and the column value for each criteria
                    lid_values_list.append(tokens[0])
                    if len(tokens) >= 2:
                        vid_values_list.append(tokens[1])
                else:
                    raise Exception("Expecting at least 2 tokens from parsing lidvid %s" % query_criterias['lidvid'][ii]) from None

            # Now that we have the two lid_values_list, vid_values_list, we can save them.
            o_column_names.append ('lid')
            o_column_values.append (lid_values_list)
            o_column_names.append ('vid')
            o_column_values.append (vid_values_list)

        if 'submitter' in query_criterias:
            o_column_names.append ('submitter')
            o_column_values.append(query_criterias['submitter'])
        if 'node' in query_criterias:
            o_column_names.append ('node_id')
            o_column_values.append([x.lower() for x in query_criterias['node']])  # Change to lowercase in case user specified upper case.
        if 'start_update' in query_criterias:
            o_column_names.append ('start_update')
            try:
                o_column_values.append(int(query_criterias['start_update'].timestamp()))
            except Exception as e:
                logger.error("Exception in converting start_update to timestamp %s" % query_criterias['start_update'])
                raise Exception("Exception in converting start_update to timestamp %s" % query_criterias['start_update']) from None
   
        if 'end_update' in query_criterias:
            o_column_names.append ('end_update')
            try:
                o_column_values.append(int(query_criterias['end_update'].timestamp()))
            except Exception as e:
                logger.error("Exception in converting end_update to timestamp %s" % query_criterias['end_update'])
                raise Exception("Exception in converting end_update to timestamp %s" % query_criterias['end_update']) from None

        logger.debug(f"o_column_names {o_column_names},{len(o_column_names)}")
        logger.debug(f"o_column_values {o_column_values},{len(o_column_values)}")

        return (o_column_names,o_column_values)

    def _create_question_marks_tuple(self,column_name,column_values):
        """ Returns a dynamic string containing (?,...,?) depending on how many elements are in column_values field.  One question mark for each element. """

        question_marks_tuple = "("  # Start with parenthesis.  An empty list can be possible, will return "()".
        for ii in range(0,len(column_values)):
            if ii == 0:
                question_marks_tuple = question_marks_tuple +  "?"
            else:
                question_marks_tuple = question_marks_tuple + ",?"
        question_marks_tuple = question_marks_tuple + ")" # Add closing parenthesis.

        logger.debug(f"column_name {column_name}, question_marks_tuple {question_marks_tuple}, len(column_values) {len(column_values)}")

        return question_marks_tuple

    def create_q_string_for_latest_rows(self, table_name, query_criterias):
        """ Build the query string to select all rows with column is_latest = 1 in ascending order."""

        # Parse the query_criterias into column names and values.  The column values will be used to build data_tuple to bind in the execute() function.
        (column_names,column_values) = self._parse_query_criterias(query_criterias)

        query_string = 'SELECT * FROM ' + table_name
        if len(query_criterias) > 0:
            query_string += ' WHERE 2 = 2'   # Add '2 = 2' so we don't have to worry about 'AND' clause.
        for ii in range(len(query_criterias.keys())):
            # Build the WHERE clause
            # Time related fields get special comparison with less than or equal or greater or equal.
            if column_names[ii] == 'start_update':
                query_string += ' AND update_date >= ?'
            elif column_names[ii] == 'end_update':
                query_string += ' AND update_date <= ?'
            else:
                # Only create the ' IN ' clause if there are elements in column_values[ii]
                # otherwise it doesn't make sense to check for ' IN ' of an empty set.
                if len(column_values[ii]) > 0:
                    query_string += ' AND '   + column_names[ii] + ' IN ' + self._create_question_marks_tuple(column_names[ii],column_values[ii])

        if len(query_criterias) > 0:
            query_string += ' AND is_latest = 1'  # Only fetch rows with is_latest is True
        else:
            # If there are no other criterias, use 'WHERE' clause.
            query_string += ' WHERE is_latest = 1'  # Only fetch rows with is_latest is True
        query_string += ' ORDER BY update_date'     # Get the rows with update_date from earliest

        query_string += ';  ' # Don't forget the last semi-colon for SQL to work. 

        logger.debug(f"query_string {query_string}")
        logger.debug(f"query_criterias {query_criterias}")

        return (query_string,column_names,column_values)

    def build_data_tuple(self,column_names,column_values):
        # Build the data_tuple matching exactly the order of the fields in query_string.
        o_data_tuple = () 
        time_related_fields = ['start_update','end_update']

        for ii in range(0,len(column_names)):
            # Time related fields are scalar.  Other fields are list.
            if column_names[ii] in time_related_fields:
                o_data_tuple = o_data_tuple + (column_values[ii],)
            else:
                o_data_tuple = o_data_tuple + tuple(column_values[ii])  # Convert list to tuple with tuple() function.
  
        logger.debug(f"o_data_tuple {o_data_tuple},{len(o_data_tuple)}")
        return o_data_tuple

    def select_latest_rows(self, db_name, table_name, query_criterias={}):
        ''' Select all rows with column is_latest = 1 in ascending order and return output in JSON format.'''
        o_query_result = []

        logger.debug(f"self.m_my_conn {self.m_my_conn}")

        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            # Check to make sure the database file already has been created otherwise can't make query.
            if not os.path.exists(db_name):
                logger.debug(f"Given db_name {db_name} does not exist.")
                raise Exception("Given db_name %s does not exist." % db_name) from None
            self.m_my_conn = self.create_connection(db_name)

        o_table_exist_flag = self.check_if_table_exist(table_name)
        logger.debug(f"table_name,o_table_exist_flag {table_name},{o_table_exist_flag}")

        (query_string,column_names,column_values) = self.create_q_string_for_latest_rows(table_name,query_criterias)

        # Build the data_tuple matching exactly the order of the fields in query_string.
        data_tuple = self.build_data_tuple(column_names,column_values);

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string,data_tuple)

        column_names = list(map(lambda x: x[0], cursor.description))
        records = cursor.fetchall()

        # For each row being returned, parse all columns into a dict object.
        for row_index, row in enumerate(records):
            row_dict = {}
            for col in range(0,self.m_NUM_COLS):
                # Don't use logger.debug() here because some columns are None.
                # Save each solumn as a field in row_dict.
                row_dict[column_names[col]] = row[col]
            o_query_result.append(row_dict)

        logger.debug(f"o_query_result {o_query_result} {type(o_query_result)}")

        # The  return type of o_query_result is a list of dict, which can also be empty.
        return o_query_result

    def doi_select_rows_all(self,db_name,table_name):
        ''' Select all rows. '''
        logger.debug(f"self.m_my_conn {self.m_my_conn}")

        if self.m_my_conn is None:
            logger.warn(f"Connection is None in database {self.get_database_name()}")
            self.m_my_conn = self.create_connection(self.m_default_db_file)
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
            self.m_my_conn = self.create_connection(self.m_default_db_file)
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
