#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

"""
===============
doi_database.py
===============

Contains classes and functions for interfacing with the local transaction
database (SQLite3).
"""

import datetime

import sqlite3
from sqlite3 import Error

from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.util.general_util import get_logger

# Get the common logger and set the level for this file.
logger = get_logger(__name__)


class DOIDataBase:
    """
    Provides a mechanism to write, update and read rows to/from a local SQLite3
    database.
    """

    EXPECTED_NUM_COLS = 13
    """"
    We are only expecting 13 columns in the doi table. If table structure changes,
    this value must be updated.
    """

    def __init__(self, db_file):
        self._config = DOIConfigUtil().get_config()
        self.m_database_name = db_file
        self.m_default_table_name = 'doi'
        self.m_my_conn = None

    def get_database_name(self):
        """Returns the name of the SQLite database."""
        return self.m_database_name

    def close_database(self):
        """Close connection to the SQLite database."""
        logger.debug("Closing database %s", self.m_database_name)

        if self.m_my_conn:
            self.m_my_conn.close()

            # Set m_my_conn to None to signify that there is no connection.
            self.m_my_conn = None
        else:
            logger.warn("Database connection to %s has not been started or is "
                        "already closed", self.m_database_name)

    def create_connection(self):
        """Create and return a connection to the SQLite database."""
        if self.m_my_conn is not None:
            logger.warning("There is already an open database connection, "
                           "closing existing connection.")
            self.close_database()

        logger.info(
            "Connecting to SQLite3 (ver %s) database %s",
            sqlite3.version, self.m_database_name
        )

        try:
            self.m_my_conn = sqlite3.connect(self.m_database_name)
        except Error as my_error:
            logger.error("Failed to connect to database, reason: %s", my_error)

    def get_connection(self, table_name=None):
        """
        Returns a connection to the SQLite database. If a connection does
        already exist, it is created using the default database file.

        The default table is also created by this method if it does not exist.
        """
        if not table_name:
            table_name = self.m_default_table_name

        if not self.m_my_conn:
            self.create_connection()

            if not self.check_if_table_exists(table_name):
                self.create_table(table_name)

        return self.m_my_conn

    def check_if_table_exists(self, table_name):
        """
        Check if the expected default table exists in the current database.

        If a database connection has not been made yet, one is created by
        this method.
        """
        logger.info("Checking for existence of DOI table %s", table_name)

        o_table_exists_flag = False

        if self.m_my_conn is None:
            logger.warn("Not connected to %s, establishing new connection...",
                        self.m_database_name)
            self.create_connection()

        table_pointer = self.m_my_conn.cursor()

        # Get the count of tables with the given name.
        query_string = (
            "SELECT count(name) FROM sqlite_master WHERE type='table' AND "
            f"name='{table_name}'"
        )

        logger.info('Executing query: %s', query_string)
        table_pointer.execute(query_string)

        # If the count is 1, then table exists.
        if table_pointer.fetchone()[0] == 1:
            o_table_exists_flag = True

        logger.debug('o_table_exists_flag: %s', o_table_exists_flag)

        return o_table_exists_flag

    def drop_table(self, table_name):
        """Delete the given table from the SQLite database."""
        if self.m_my_conn:
            logger.debug("Executing query: DROP TABLE %s", table_name)
            self.m_my_conn.execute(f'DROP TABLE {table_name}')

    def create_q_string_for_create(self, table_name):
        """Build the query string to create a table in the SQLite database."""

        o_query_string = f'CREATE TABLE {table_name} '
        o_query_string += '(status TEXT NOT NULL'  # current status
        o_query_string += ',update_date INT NOT NULL'  # as Unix Time
        o_query_string += ',submitter TEXT'  # email of the submitter of the DOI
        o_query_string += ',title TEXT'  # title used for the DOI
        o_query_string += ',type TEXT'  # product type
        o_query_string += ',subtype TEXT'  # subtype of the product
        o_query_string += ',node_id TEXT NOT NULL'  # steward discipline node ID
        o_query_string += ',lid TEXT'
        o_query_string += ',vid TEXT'
        o_query_string += ',doi TEXT'  # DOI (may be null for pending or draft)
        o_query_string += ',release_date INT'  # as Unix Time
        o_query_string += ',transaction_key TEXT NOT NULL'  # transaction (key is node id/datetime)
        o_query_string += ',is_latest BOOLEAN NULL); '  # whether the transaction is the latest

        logger.debug("CREATE o_query_string: %s", o_query_string)

        return o_query_string

    def create_q_string_for_insert(self, table_name):
        """Build the query string to insert into the SQLite database table."""

        o_query_string = f'INSERT INTO {table_name} '
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

        logger.debug("INSERT o_query_string: %s", o_query_string)

        return o_query_string

    def create_q_string_for_transaction_insert(self, table_name):
        """Build the query string to insert a transaction into the SQLite database table."""

        # Note that we are not setting all columns, just the ones related to a transaction.
        o_query_string = f'INSERT INTO {table_name} '
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

        logger.debug("INSERT o_query_string: %s", o_query_string)

        return o_query_string

    def create_q_string_for_transaction_update_is_latest_field(self, table_name):
        """
        Build the query string to update existing rows in the table with an
        update_date field earlier than the current row in the SQLite database.

        The current row is the row inserted with the "update_date" value of
        "latest_update". The comparison criteria is less than, meaning any rows
        inserted earlier will be updated with the column "is_latest" to zero.
        """

        # Note that we set column "is_latest" to 0 to signify that all previous
        # rows are now not the latest. The key in dict_row is 'latest_update',
        # not 'update_date' (not same as column name).
        o_query_string = f'UPDATE {table_name} '
        o_query_string += 'SET '
        o_query_string += 'is_latest = 0 '
        o_query_string += 'WHERE lid = ?'
        o_query_string += ' AND  vid = ?'
        o_query_string += ' AND  (doi = ? or doi is NULL)'
        o_query_string += ';'  # Don't forget the last semi-colon for SQL to work.

        logger.debug("UPDATE o_query_string: %s", o_query_string)

        return o_query_string

    def create_table(self, table_name):
        """Create a given table in the SQLite database."""
        logger.info('Creating SQLite table "%s"', table_name)
        self.m_my_conn = self.get_connection()

        query_string = self.create_q_string_for_create(table_name)
        self.m_my_conn.execute(query_string)

        logger.info("Table created successfully")

    def _int_columns_check(self, dict_row):
        """
        Perform a sanity check on the types of all the date columns.

        The ones we need to check are:

             update_date
             release_date

        """
        long_int_type_list = ['update_date', 'release_date']

        for long_int_field in long_int_type_list:
            if long_int_field in dict_row:
                if not isinstance(dict_row[long_int_field], int):
                    msg = ("Expecting field {long_int_field} to be of "
                           f"type int but got {type(dict_row[long_int_field])}")
                    logger.error(msg)
                    raise RuntimeError(msg)

    def insert_row(self, table_name, dict_row):
        """Insert a row into the requested database table."""
        if self.m_my_conn is None:
            logger.warn("Not connected to %s, establishing new connection...",
                        self.m_database_name)
            self.create_connection()

        o_table_exist_flag = self.check_if_table_exists(table_name)
        logger.debug("table_name, o_table_exist_flag: %s, %s",
                     table_name, o_table_exist_flag)

        # Do a sanity check on the types of all the columns int.
        self._int_columns_check(dict_row)

        query_string = self.create_q_string_for_insert(table_name)

        # Note that the order of items in data_tuple must match the columns in
        # the table in the same order.
        data_tuple = (dict_row['status'],           # 1
                      dict_row['update_date'],      # 2
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

        logger.debug("INSERT query_string: %s", query_string)

        self.m_my_conn.execute(query_string, data_tuple)
        self.m_my_conn.commit()

    def write_doi_info_to_database(self, lid, vid, transaction_key, doi=None,
                                   transaction_date=datetime.datetime.now(),
                                   status=DoiStatus.Unknown, title='',
                                   product_type='', product_type_specific='',
                                   submitter='', discipline_node=''):
        """Write some DOI info from a 'reserve' or 'draft' request to the database."""
        self.m_my_conn = self.get_connection()

        data_tuple = (status,
                      product_type,
                      product_type_specific,
                      True,
                      lid,
                      vid,
                      doi,
                      submitter,
                      transaction_date.replace(tzinfo=datetime.timezone.utc).timestamp(),
                      discipline_node,
                      title,
                      transaction_key)

        # Create and execute the query to unset latest for record same lid/vid and doi fields.
        query_string = self.create_q_string_for_transaction_update_is_latest_field(self.m_default_table_name)

        try:
            self.m_my_conn.execute(query_string, (lid, vid, doi if doi else 'NULL'))

            # Combine the insert and update here so the commit can be applied to both actions.
            query_string = self.create_q_string_for_transaction_insert(self.m_default_table_name)

            self.m_my_conn.execute(query_string, data_tuple)
            self.m_my_conn.commit()
        except sqlite3.Error as err:
            msg = f"Failed to commit to database, reason: {err}"
            logger.error(msg)
            raise RuntimeError(msg)

    def select_rows(self, query_criterias, table_name=None):
        """Select rows based on the provided query criteria."""
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        query_string = f'SELECT * FROM {table_name}'

        if len(query_criterias) > 0:
            query_string += ' WHERE '

        # Build the WHERE clause
        for ii in range(len(query_criterias)):
            if ii == 0:
                query_string += query_criterias[ii]
            else:
                query_string += f' AND {query_criterias[ii]} '

        query_string += '; '

        logger.debug("SELECT query_string: %s", query_string)

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string)
        records = cursor.fetchall()

        logger.debug('Query returned %d result(s)', len(records))

        return records

    def select_latest_rows(self, query_criterias, table_name=None):
        """Select all rows marked as latest (is_latest column = 1)"""
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        criterias_str, criteria_dict = DOIDataBase.parse_criteria(query_criterias)

        query_string = (f'SELECT * from {table_name} '
                        f'WHERE is_latest=1 {criterias_str} ORDER BY update_date')

        logger.debug('SELECT query_string: %s', query_string)

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string, criteria_dict)

        column_names = list(map(lambda x: x[0], cursor.description))

        records = [row for row in cursor]

        return column_names, records

    def select_all_rows(self, table_name=None):
        """Select all rows from the database"""
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        query_string = f'SELECT * FROM {table_name};'

        logger.debug("SELECT query_string %s", query_string)

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string)
        records = cursor.fetchall()

        logger.debug('Query returned %d result(s)', len(records))

        return records

    def update_rows(self, query_criterias, update_list, table_name=None):
        """
        Update all rows and fields (specified in update_list) that match
        the provided query criteria.
        """
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        query_string = f'UPDATE {table_name} SET '

        for ii in range(len(update_list)):
            # Build the SET column_1 = new_value_1,
            #               column_2 = new_value_2
            # Only precede the comma for subsequent values
            if ii == 0:
                query_string += update_list[ii]
            else:
                query_string += ',' + update_list[ii]

        # Add any query_criterias
        if len(query_criterias) > 0:
            query_string += ' WHERE '

        # Build the WHERE clause
        for ii in range(len(query_criterias)):
            if ii == 0:
                query_string += query_criterias[ii]
            else:
                query_string += f' AND {query_criterias[ii]} '

        logger.debug("UPDATE query_string: %s", query_string)

        self.m_my_conn.execute(query_string)

    @staticmethod
    def _get_simple_in_criteria(v, column):
        named_parameters = ','.join([':' + column + '_' + str(i) for i in range(len(v))])
        named_parameter_values = {column + '_' + str(i): v[i].lower() for i in range(len(v))}
        return f' AND lower({column}) IN ({named_parameters})', named_parameter_values

    @staticmethod
    def _get_query_criteria_title(v):
        return DOIDataBase._get_simple_in_criteria(v, 'title')

    @staticmethod
    def _get_query_criteria_doi(v):
        return DOIDataBase._get_simple_in_criteria(v, 'doi')

    @staticmethod
    def _form_query_with_wildcards(column_name, search_tokens):
        """
        Helper method to form a portion of an SQL WHERE clause that returns
        matches from the specified column using the provided list of tokens.

        The list of tokens may either contain fully specified identifiers, or
        identifiers containing Unix-style wildcards (*), aka globs. The method
        partitions the tokens accordingly, and forms the appropriate clause
        to capture all results.

        Parameters
        ----------
        column_name : str
            Name of the SQL table column name that will be searched by the
            returned query.
        search_tokens : list of str
            List of tokens to search for. Tokens may either be full identifiers,
            or contain one or more wildcards (*).

        Returns
        -------
        where_subclause : str
            Query portion which can be used with a WHERE clause to find the
            requested set of tokens. This subclause is parameterized, and should
            be used with the returned named parameter dictionary.
        named_parameter_values : dict
            The dictionary mapping the named parameters in the returned subclause
            with the actual values to use.

        """
        # Partition the tokens containing wildcards from the fully specified ones
        wildcard_tokens = list(filter(lambda token: '*' in token, search_tokens))
        full_tokens = list(set(search_tokens) - set(wildcard_tokens))

        # Set up the named parameters for the IN portion of the WHERE used
        # to find fully specified tokens
        named_parameters = ','.join([f':token_{i}'
                                     for i in range(len(full_tokens))])
        named_parameter_values = {f'token_{i}': full_tokens[i]
                                  for i in range(len(full_tokens))}

        # Set up the named parameters for the GLOB portion of the WHERE used
        # find tokens containing wildcards
        glob_parameters = ' OR '.join([f'{column_name} GLOB :glob_{i}'
                                       for i in range(len(wildcard_tokens))])

        named_parameter_values.update({f'glob_{i}': wildcard_tokens[i]
                                       for i in range(len(wildcard_tokens))})

        # Build the portion of the WHERE clause combining the necessary
        # parameters needed to search for all the tokens we were provided
        where_subclause = "AND ("

        if full_tokens:
            where_subclause += f"{column_name} IN ({named_parameters}) "

        if full_tokens and wildcard_tokens:
            where_subclause += ' OR '

        if wildcard_tokens:
            where_subclause += f'{glob_parameters}'

        where_subclause += ")"

        logger.debug("WHERE subclause: %s", where_subclause)

        return where_subclause, named_parameter_values

    @staticmethod
    def _get_query_criteria_lid(v):
        lid_column_name = 'lid'
        return DOIDataBase._form_query_with_wildcards(lid_column_name, v)

    @staticmethod
    def _get_query_criteria_lidvid(v):
        # To combine the 'lid' and 'vid' we need to add the '::' to compare to
        # lidvid values
        lidvid_column_name = "lid || '::' || vid"
        return DOIDataBase._form_query_with_wildcards(lidvid_column_name, v)

    @staticmethod
    def _get_query_criteria_submitter(v):
        return DOIDataBase._get_simple_in_criteria(v, 'submitter')

    @staticmethod
    def _get_query_criteria_node(v):
        return DOIDataBase._get_simple_in_criteria(v, 'node_id')

    @staticmethod
    def _get_query_criteria_status(v):
        return DOIDataBase._get_simple_in_criteria(v, 'status')

    @staticmethod
    def _get_query_criteria_start_update(v):
        return (' AND update_date >= :start_update',
                {'start_update': v.replace(tzinfo=datetime.timezone.utc).timestamp()})

    @staticmethod
    def _get_query_criteria_end_update(v):
        return (' AND update_date <= :end_update',
                {'end_update': v.replace(tzinfo=datetime.timezone.utc).timestamp()})

    @staticmethod
    def parse_criteria(query_criterias):
        criterias_str = ''
        criteria_dict = {}

        for k, v in query_criterias.items():
            logger.debug("Calling get_query_criteria_%s with value %s", k, v)

            criteria_str, dict_entry = getattr(DOIDataBase, '_get_query_criteria_' + k)(v)

            logger.debug("criteria_str: %s", criteria_str)
            logger.debug("dict_entry: %s", dict_entry)

            criterias_str += criteria_str
            criteria_dict.update(dict_entry)

        return criterias_str, criteria_dict
