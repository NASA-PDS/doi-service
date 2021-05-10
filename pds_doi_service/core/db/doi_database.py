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
from datetime import datetime, timezone, timedelta

import sqlite3
from sqlite3 import Error

from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.entities.doi import DoiStatus, ProductType
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

    def query_string_for_table_creation(self, table_name):
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

    def query_string_for_transaction_insert(self, table_name):
        """
        Build the query string used to insert a transaction row into the SQLite
        database table.
        """
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

    def query_string_for_is_latest_update(self, table_name, lid, vid):
        """
        Build the query string to update existing rows in the table with an
        update_date field earlier than the current row in the SQLite database.

        The current row is the row inserted with the "update_date" value of
        "latest_update". The comparison criteria is less than, meaning any rows
        inserted earlier will be updated with the column "is_latest" to zero.

        The query string and named parameter values returned are determined
        based on whether both a LID and VID are provided, or only a LID.

        """
        # Note that we set column "is_latest" to 0 to signify that all previous
        # rows are now not the latest.
        query_string = f'UPDATE {table_name} '
        query_string += 'SET '
        query_string += 'is_latest = 0 '
        query_string += 'WHERE lid = ?'

        if vid:
            query_string += ' AND vid = ?'
        else:
            query_string += ' AND vid is null'

        query_string += ';'  # Don't forget the last semi-colon for SQL to work.

        logger.debug("UPDATE o_query_string: %s", query_string)

        named_parameter_values = (lid, vid) if vid else (lid,)

        return query_string, named_parameter_values

    def create_table(self, table_name):
        """Create a given table in the SQLite database."""
        logger.info('Creating SQLite table "%s"', table_name)
        self.m_my_conn = self.get_connection()

        query_string = self.query_string_for_table_creation(table_name)
        self.m_my_conn.execute(query_string)

        logger.info("Table created successfully")

    def write_doi_info_to_database(self, lid, vid, transaction_key, doi=None,
                                   release_date=datetime.now(),
                                   transaction_date=datetime.now(),
                                   status=DoiStatus.Unknown, title='',
                                   product_type='', product_type_specific='',
                                   submitter='', discipline_node=''):
        """Write some DOI info from a 'reserve' or 'draft' request to the database."""
        self.m_my_conn = self.get_connection()

        # Convert timestamps to Unix epoch floats for simpler table storage
        release_date = release_date.replace(tzinfo=timezone.utc).timestamp()
        update_date = transaction_date.replace(tzinfo=timezone.utc).timestamp()

        data_tuple = (status,                 # status
                      update_date,            # update_date
                      submitter,              # submitter
                      title,                  # title
                      product_type,           # type
                      product_type_specific,  # subtype
                      discipline_node,        # node_id
                      lid,                    # lid
                      vid,                    # vid
                      doi,                    # doi
                      release_date,           # release_date
                      transaction_key,        # transaction_key
                      True)                   # is_latest

        try:
            # Create and execute the query to unset the is_latest field for all
            # records with the same LIDVID and DOI fields.
            query_string, named_parameters = self.query_string_for_is_latest_update(
                self.m_default_table_name, lid, vid
            )

            self.m_my_conn.execute(query_string, named_parameters)
            self.m_my_conn.commit()
        except sqlite3.Error as err:
            msg = (f"Failed to update is_latest field for LIDVID {lid}::{vid}, "
                   f"reason: {err}")
            logger.error(msg)
            raise RuntimeError(msg)

        try:
            # Combine the insert and update here so the commit can be applied to both actions.
            query_string = self.query_string_for_transaction_insert(self.m_default_table_name)

            self.m_my_conn.execute(query_string, data_tuple)
            self.m_my_conn.commit()
        except sqlite3.Error as err:
            msg = (f"Failed to commit transaction for LIDVID {lid}::{vid}, "
                   f"reason: {err}")
            logger.error(msg)
            raise RuntimeError(msg)

    def _normalize_rows(self, columns, rows):
        """
        Normalize columns from each rows to be the data types we expect,
        rather than the types which are convenient for table storage
        """
        for row in rows:
            # Convert the release/update times from Unix epoch back to datetime,
            # accounting for the expected (PST) timezone
            for time_column in ('release_date', 'update_date'):
                time_val = row[columns.index(time_column)]
                time_val = (datetime.fromtimestamp(time_val, tz=timezone.utc)
                            .replace(tzinfo=timezone(timedelta(hours=--8.0))))
                row[columns.index(time_column)] = time_val

            # Convert status/product type back to Enums
            row[columns.index('status')] = DoiStatus(row[columns.index('status')].lower())
            row[columns.index('type')] = ProductType(row[columns.index('type')].capitalize())

        return rows

    def select_rows(self, query_criterias, table_name=None):
        """Select rows based on the provided query criteria."""
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        query_string = f'SELECT * FROM {table_name}'

        criterias_str, criteria_dict = DOIDataBase.parse_criteria(query_criterias)

        if len(query_criterias) > 0:
            query_string += f' WHERE {criterias_str}'

        query_string += '; '

        logger.debug("SELECT query_string: %s", query_string)

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string, criteria_dict)

        columns = list(map(lambda x: x[0], cursor.description))

        rows = [list(row) for row in cursor]

        rows = self._normalize_rows(columns, rows)

        logger.debug('Query returned %d result(s)', len(rows))

        return columns, rows

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

        columns = list(map(lambda x: x[0], cursor.description))

        rows = [list(row) for row in cursor]

        rows = self._normalize_rows(columns, rows)

        logger.debug('Query returned %d result(s)', len(rows))

        return columns, rows

    def select_all_rows(self, table_name=None):
        """Select all rows from the database"""
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        query_string = f'SELECT * FROM {table_name};'

        logger.debug("SELECT query_string %s", query_string)

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string)

        columns = list(map(lambda x: x[0], cursor.description))

        rows = [list(row) for row in cursor]

        rows = self._normalize_rows(columns, rows)

        logger.debug('Query returned %d result(s)', len(rows))

        return columns, rows

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

        # Clean up the column name provided so it can be used as a suitable
        # named parameter placeholder token
        filter_chars = [' ', '\'', ':', '|']
        named_param_id = column_name

        for filter_char in filter_chars:
            named_param_id = named_param_id.replace(filter_char, '')

        # Set up the named parameters for the IN portion of the WHERE used
        # to find fully specified tokens
        named_parameters = ','.join([f':{named_param_id}_{i}'
                                     for i in range(len(full_tokens))])
        named_parameter_values = {f'{named_param_id}_{i}': full_tokens[i]
                                  for i in range(len(full_tokens))}

        # Set up the named parameters for the GLOB portion of the WHERE used
        # find tokens containing wildcards
        glob_parameters = ' OR '.join([f'{column_name} GLOB :{named_param_id}_glob_{i}'
                                       for i in range(len(wildcard_tokens))])

        named_parameter_values.update({f'{named_param_id}_glob_{i}': wildcard_tokens[i]
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
        criterias_str = ''
        criterias_dict = {}

        # First filter out any LID-only entries and query those separately
        lidvids = list(filter(lambda s: '::' in s, v))
        lids = list(set(v) - set(lidvids))

        if lids:
            criterias_str, criterias_dict = DOIDataBase._get_query_criteria_lid(lids)

        # To combine the 'lid' and 'vid' we need to add the '::' to compare to
        # lidvid values
        if lidvids:
            lidvid_column_name = "lid || '::' || vid"
            criteria_str, criteria_dict = DOIDataBase._form_query_with_wildcards(
                lidvid_column_name, lidvids
            )

            criterias_str += criteria_str
            criterias_dict.update(criteria_dict)

        return criterias_str, criterias_dict

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
                {'start_update': v.replace(tzinfo=timezone.utc).timestamp()})

    @staticmethod
    def _get_query_criteria_end_update(v):
        return (' AND update_date <= :end_update',
                {'end_update': v.replace(tzinfo=timezone.utc).timestamp()})

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
