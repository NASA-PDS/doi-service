#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
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
import dataclasses
import os
import sqlite3
import stat
from collections import OrderedDict
from datetime import datetime
from datetime import timezone
from sqlite3 import Error

from pds_doi_service.core.entities.doi import DoiRecord
from pds_doi_service.core.entities.doi import DoiStatus
from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger

# Get the common logger and set the level for this file.
logger = get_logger(__name__)


class DOIDataBase:
    """
    Provides a mechanism to write, update and read rows to/from a local SQLite3
    database.
    """

    DOI_DB_SCHEMA = OrderedDict(
        {
            "doi": "TEXT NOT NULL",  # DOI (must be provided for all records)
            "identifier": "TEXT",  # PDS identifier (any version)
            "status": "TEXT NOT NULL",  # current status
            "title": "TEXT",  # title used for the DOI
            "submitter": "TEXT",  # email of the submitter of the DOI
            "type": "TEXT",  # product type
            "subtype": "TEXT",  # subtype of the product
            "node_id": "TEXT NOT NULL",  # steward discipline node ID
            "date_added": "INT",  # as Unix epoch seconds
            "date_updated": "INT NOT NULL",  # as Unix epoch seconds
            "transaction_key": "TEXT NOT NULL",  # transaction (key is node id/datetime)
            "is_latest": "BOOLEAN",  # whether the transaction is the latest
        }
    )
    """
    The schema used to define the DOI DB table. Each key corresponds to a column
    name, and each value corresponds to the data type and column constraint as
    expected by the Sqlite3 CREATE TABLE statement.
    """

    EXPECTED_NUM_COLS = len(DOI_DB_SCHEMA)
    """"The expected number of columns as defined by the schema."""

    def __init__(self, db_file):
        self._config = DOIConfigUtil().get_config()
        self.m_database_name = db_file
        self.m_default_table_name = "doi"
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
            logger.warn("Database connection to %s has not been started or is already closed", self.m_database_name)

    def create_connection(self):
        """Create and return a connection to the SQLite database."""
        if self.m_my_conn is not None:
            logger.warning("There is already an open database connection, closing existing connection.")
            self.close_database()

        logger.info("Connecting to SQLite3 (ver %s) database %s", sqlite3.version, self.m_database_name)

        try:
            self.m_my_conn = sqlite3.connect(self.m_database_name)
        except Error as my_error:
            logger.error("Failed to connect to database, reason: %s", my_error)

        # Make sure Database has proper group permissions set
        st = os.stat(self.m_database_name)
        has_group_rw = bool(st.st_mode & (stat.S_IRGRP | stat.S_IWGRP))

        if not has_group_rw:
            logger.debug("Setting group read/write bits on database %s", self.m_database_name)
            os.chmod(self.m_database_name, st.st_mode | stat.S_IRGRP | stat.S_IWGRP)

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
            logger.warn("Not connected to %s, establishing new connection...", self.m_database_name)
            self.create_connection()

        table_pointer = self.m_my_conn.cursor()

        # Get the count of tables with the given name.
        query_string = f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}'"

        logger.info("Executing query: %s", query_string)
        table_pointer.execute(query_string)

        # If the count is 1, then table exists.
        if table_pointer.fetchone()[0] == 1:
            o_table_exists_flag = True

        logger.debug("o_table_exists_flag: %s", o_table_exists_flag)

        return o_table_exists_flag

    def drop_table(self, table_name):
        """Delete the given table from the SQLite database."""
        if self.m_my_conn:
            logger.debug("Executing query: DROP TABLE %s", table_name)
            self.m_my_conn.execute(f"DROP TABLE {table_name}")

    def query_string_for_table_creation(self, table_name):
        """
        Builds the query string to create a transaction table in the SQLite
        database.

        Parameters
        ----------
        table_name : str
            Name of the table to build the query for.

        Returns
        -------
        o_query_string : str
            The Sqlite3 query string used to create the transaction table within
            the database.

        """
        o_query_string = f"CREATE TABLE {table_name} "
        o_query_string += "("

        for index, (column, constraints) in enumerate(self.DOI_DB_SCHEMA.items()):
            o_query_string += f"{column} {constraints}"

            if index < (self.EXPECTED_NUM_COLS - 1):
                o_query_string += ","

        o_query_string += ");"

        logger.debug("CREATE o_query_string: %s", o_query_string)

        return o_query_string

    def query_string_for_transaction_insert(self, table_name):
        """
        Builds the query string used to insert a transaction row into the SQLite
        database table.

        Parameters
        ----------
        table_name : str
            Name of the table to build the query for.

        Returns
        -------
        o_query_string : str
            The Sqlite3 query string used to insert a new row into the database.

        """
        o_query_string = f"INSERT INTO {table_name} "

        o_query_string += "("

        for index, column in enumerate(self.DOI_DB_SCHEMA):
            o_query_string += f"{column}"

            if index < (self.EXPECTED_NUM_COLS - 1):
                o_query_string += ","

        o_query_string += ") "

        o_query_string += f'VALUES ({",".join(["?"] * self.EXPECTED_NUM_COLS)})'

        logger.debug("INSERT o_query_string: %s", o_query_string)

        return o_query_string

    def query_string_for_is_latest_update(self, table_name, primary_key_column):
        """
        Build the query string to set the is_latest to False (0) for rows
        in the table having a specified primary key (identifier) value.

        Parameters
        ----------
        table_name : str
            Name of the table to build the query for.
        primary_key_column: str
            Name of the database column designated as the primary key.

        Returns
        -------
        o_query_string : str
            The Sqlite3 query string used to perform the is_latest update.

        """
        # Note that we set column "is_latest" to 0 to signify that all previous
        # rows are now not the latest.
        o_query_string = f"UPDATE {table_name} "
        o_query_string += "SET "
        o_query_string += "is_latest = 0 "
        o_query_string += f"WHERE {primary_key_column} = ?"
        o_query_string += ";"  # Don't forget the last semi-colon for SQL to work.

        logger.debug("UPDATE o_query_string: %s", o_query_string)

        return o_query_string

    def create_table(self, table_name):
        """Create a given table in the SQLite database."""
        logger.info('Creating SQLite table "%s"', table_name)
        self.m_my_conn = self.get_connection()

        query_string = self.query_string_for_table_creation(table_name)
        self.m_my_conn.execute(query_string)

        logger.info("Table created successfully")

    def write_doi_info_to_database(self, doi_record):
        """
        Write a new row to the Sqlite3 transaction database with the provided
        DOI entry information.

        Parameters
        ----------
        doi_record : DoiRecord
            The DOI record to create a database new entry with.

        Raises
        ------
        RuntimeError
            If the database transaction cannot be committed for any reason.

        """
        self.m_my_conn = self.get_connection()

        # Convert the DOI record to a dictionary representation. By doing so, we
        # can ignore database column ordering for now.
        data = dataclasses.asdict(doi_record)

        # Convert timestamps to Unix epoch floats for simpler table storage
        data["date_added"] = data["date_added"].replace(tzinfo=timezone.utc).timestamp()
        data["date_updated"] = data["date_updated"].replace(tzinfo=timezone.utc).timestamp()

        try:
            # Create and execute the query to unset the is_latest field for all
            # records with the same identifier field.
            query_string = self.query_string_for_is_latest_update(self.m_default_table_name, primary_key_column="doi")

            self.m_my_conn.execute(query_string, (doi_record.doi,))
            self.m_my_conn.commit()
        except sqlite3.Error as err:
            msg = f"Failed to update is_latest field for DOI {doi_record.doi}, reason: {err}"
            logger.error(msg)
            raise RuntimeError(msg)

        try:
            # Combine the insert and update here so the commit can be applied to both actions.
            query_string = self.query_string_for_transaction_insert(self.m_default_table_name)

            # Create the named parameters tuple in the order expected by the
            # database schema
            data_tuple = tuple([data[column] for column in self.DOI_DB_SCHEMA])

            self.m_my_conn.execute(query_string, data_tuple)
            self.m_my_conn.commit()
        except sqlite3.Error as err:
            msg = f"Failed to commit transaction for DOI {doi_record.doi}, " f"reason: {err}"
            logger.error(msg)
            raise RuntimeError(msg)

    def _normalize_rows(self, columns, rows):
        """
        Normalize columns from each row to be the data types we expect,
        rather than the types which are convenient for table storage
        """
        for row in rows:
            # Convert the add/update times from Unix epoch back to datetime
            for time_column in ("date_added", "date_updated"):
                time_val = row[columns.index(time_column)]
                time_val = datetime.fromtimestamp(time_val, tz=timezone.utc)
                row[columns.index(time_column)] = time_val

            # Convert status/product type back to Enums
            row[columns.index("status")] = DoiStatus(row[columns.index("status")].lower())
            row[columns.index("type")] = ProductType(row[columns.index("type")].capitalize())

            # Convert is_latest flag back to native Python bool (sqlite returns an int)
            row[columns.index("is_latest")] = bool(row[columns.index("is_latest")])

        return rows

    def select_rows(self, query_criterias, table_name=None):
        """Select rows based on the provided query criteria."""
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        query_string = f"SELECT * FROM {table_name}"

        criterias_str, criteria_dict = DOIDataBase.parse_criteria(query_criterias)

        if len(query_criterias) > 0:
            query_string += f" WHERE {criterias_str}"

        query_string += "; "

        logger.debug("SELECT query_string: %s", query_string)

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string, criteria_dict)

        columns = list(map(lambda x: x[0], cursor.description))

        rows = [list(row) for row in cursor]

        rows = self._normalize_rows(columns, rows)

        logger.debug("Query returned %d result(s)", len(rows))

        return columns, rows

    def select_latest_rows(self, query_criterias, table_name=None):
        """Select all rows marked as latest (is_latest column = 1)"""
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        criterias_str, criteria_dict = DOIDataBase.parse_criteria(query_criterias)

        query_string = f"SELECT * from {table_name} WHERE is_latest=1 {criterias_str} ORDER BY date_updated"

        logger.debug("SELECT query_string: %s", query_string)

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string, criteria_dict)

        columns = list(map(lambda x: x[0], cursor.description))

        rows = [list(row) for row in cursor]

        rows = self._normalize_rows(columns, rows)

        logger.debug("Query returned %d result(s)", len(rows))

        return columns, rows

    def select_latest_records(self, query_criterias, table_name=None):
        """
        Returns the latest set of rows from the database matching the provided
        query criteria reformatted as DoiRecord objects.

        Parameters
        ----------
        query_criterias : dict
            Dictionary mapping database column names to criteria values to match.
        table_name : str, optional
            Name of the database table to query. Defaults to the default table
            name "doi".

        Returns
        -------
        records : list of DoiRecord
            The list of DoiRecord objects matching the query criteria.

        """
        columns, rows = self.select_latest_rows(query_criterias, table_name)

        records = [DoiRecord(**dict(zip(columns, row))) for row in rows]

        return records

    def select_all_rows(self, table_name=None):
        """Select all rows from the database"""
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        query_string = f"SELECT * FROM {table_name};"

        logger.debug("SELECT query_string %s", query_string)

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string)

        columns = list(map(lambda x: x[0], cursor.description))

        rows = [list(row) for row in cursor]

        rows = self._normalize_rows(columns, rows)

        logger.debug("Query returned %d result(s)", len(rows))

        return columns, rows

    def update_rows(self, query_criterias, update_list, table_name=None):
        """
        Update all rows and fields (specified in update_list) that match
        the provided query criteria.
        """
        if not table_name:
            table_name = self.m_default_table_name

        self.m_my_conn = self.get_connection(table_name)

        query_string = f"UPDATE {table_name} SET "

        for ii in range(len(update_list)):
            # Build the SET column_1 = new_value_1,
            #               column_2 = new_value_2
            # Only precede the comma for subsequent values
            if ii == 0:
                query_string += update_list[ii]
            else:
                query_string += "," + update_list[ii]

        # Add any query_criterias
        if len(query_criterias) > 0:
            query_string += " WHERE "

        # Build the WHERE clause
        for ii in range(len(query_criterias)):
            if ii == 0:
                query_string += query_criterias[ii]
            else:
                query_string += f" AND {query_criterias[ii]} "

        logger.debug("UPDATE query_string: %s", query_string)

        self.m_my_conn.execute(query_string)

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
        wildcard_tokens = list(filter(lambda token: "*" in token or "?" in token, search_tokens))
        full_tokens = list(set(search_tokens) - set(wildcard_tokens))

        # Clean up the column name provided so it can be used as a suitable
        # named parameter placeholder token
        filter_chars = [" ", "'", ":", "|"]
        named_param_id = column_name

        for filter_char in filter_chars:
            named_param_id = named_param_id.replace(filter_char, "")

        # Set up the named parameters for the IN portion of the WHERE used
        # to find fully specified tokens
        named_parameters = ",".join([f":{named_param_id}_{i}" for i in range(len(full_tokens))])
        named_parameter_values = {f"{named_param_id}_{i}": full_tokens[i] for i in range(len(full_tokens))}

        # Next, because we use actually use LIKE and not GLOB (for the case-insensitivity),
        # we need to convert wildcards from Unix style (*,?) to SQLite style (%,_),
        # but we first need to escape any existing characters reserved by LIKE (& and _)
        like_chars = ["%", "_"]
        glob_chars = ["*", "?"]

        for index, wildcard_token in enumerate(wildcard_tokens):
            for like_char, glob_char in zip(like_chars, glob_chars):
                # Escape reserved wildcards used by LIKE
                wildcard_token = wildcard_token.replace(like_char, f"\\{like_char}")

                # Replace wildcards used by GLOB with equivalent for LIKE
                wildcard_token = wildcard_token.replace(glob_char, like_char)

                # Update the list of wildcards
                wildcard_tokens[index] = wildcard_token

        # Set up the named parameters for the LIKE portion of the WHERE used
        # find tokens containing wildcards
        like_parameters = " OR ".join(
            [f"{column_name} LIKE :{named_param_id}_like_{i}" for i in range(len(wildcard_tokens))]
        )

        named_parameter_values.update(
            {f"{named_param_id}_like_{i}": wildcard_tokens[i] for i in range(len(wildcard_tokens))}
        )

        # Build the portion of the WHERE clause combining the necessary
        # parameters needed to search for all the tokens we were provided
        where_subclause = "AND ("

        if full_tokens:
            where_subclause += f"{column_name} IN ({named_parameters}) "

        if full_tokens and wildcard_tokens:
            where_subclause += " OR "

        if wildcard_tokens:
            where_subclause += f"{like_parameters}"

            # Make sure Sqlite knows were using backslash for escaped chars
            where_subclause += " ESCAPE '\\'"

        where_subclause += ")"

        logger.debug("WHERE subclause: %s", where_subclause)

        return where_subclause, named_parameter_values

    @staticmethod
    def _get_simple_in_criteria(column_name, value):
        named_parameters = ",".join([":" + column_name + "_" + str(i) for i in range(len(value))])
        named_parameter_values = {column_name + "_" + str(i): value[i].lower() for i in range(len(value))}
        return f" AND lower({column_name}) IN ({named_parameters})", named_parameter_values

    @staticmethod
    def _get_query_criteria_title(title_value):
        return DOIDataBase._form_query_with_wildcards("title", title_value)

    @staticmethod
    def _get_query_criteria_doi(doi_value):
        return DOIDataBase._form_query_with_wildcards("doi", doi_value)

    @staticmethod
    def _get_query_criteria_ids(id_value):
        return DOIDataBase._form_query_with_wildcards("identifier", id_value)

    @staticmethod
    def _get_query_criteria_submitter(submitter_value):
        return DOIDataBase._get_simple_in_criteria("submitter", submitter_value)

    @staticmethod
    def _get_query_criteria_node(node_value):
        return DOIDataBase._get_simple_in_criteria("node_id", node_value)

    @staticmethod
    def _get_query_criteria_status(status_value):
        return DOIDataBase._get_simple_in_criteria("status", status_value)

    @staticmethod
    def _get_query_criteria_start_update(start_value):
        return " AND date_updated >= :start_update", {
            "start_update": start_value.replace(tzinfo=timezone.utc).timestamp()
        }

    @staticmethod
    def _get_query_criteria_end_update(end_value):
        return " AND date_updated <= :end_update", {"end_update": end_value.replace(tzinfo=timezone.utc).timestamp()}

    @staticmethod
    def parse_criteria(query_criterias):
        criterias_str = ""
        criteria_dict = {}

        for key, value in query_criterias.items():
            logger.debug("Calling get_query_criteria_%s with value %s", key, value)

            criteria_str, dict_entry = getattr(DOIDataBase, "_get_query_criteria_" + key)(value)

            logger.debug("criteria_str: %s", criteria_str)
            logger.debug("dict_entry: %s", dict_entry)

            criterias_str += criteria_str
            criteria_dict.update(dict_entry)

        return criterias_str, criteria_dict
