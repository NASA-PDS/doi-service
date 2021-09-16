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
import sqlite3
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from sqlite3 import Error

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
            "identifier": "TEXT NOT NULL",  # PDS identifier (any version)
            "doi": "TEXT",  # DOI (may be null for pending or draft)
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
            logger.warn("Database connection to %s has not been started or is " "already closed", self.m_database_name)

    def create_connection(self):
        """Create and return a connection to the SQLite database."""
        if self.m_my_conn is not None:
            logger.warning("There is already an open database connection, " "closing existing connection.")
            self.close_database()

        logger.info("Connecting to SQLite3 (ver %s) database %s", sqlite3.version, self.m_database_name)

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
            logger.warn("Not connected to %s, establishing new connection...", self.m_database_name)
            self.create_connection()

        table_pointer = self.m_my_conn.cursor()

        # Get the count of tables with the given name.
        query_string = "SELECT count(name) FROM sqlite_master WHERE type='table' AND " f"name='{table_name}'"

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

    def write_doi_info_to_database(
        self,
        identifier,
        transaction_key,
        doi=None,
        date_added=datetime.now(),
        date_updated=datetime.now(),
        status=DoiStatus.Unknown,
        title="",
        product_type=ProductType.Collection,
        product_type_specific="",
        submitter="",
        discipline_node="",
    ):
        """
        Write a new row to the Sqlite3 transaction database with the provided
        DOI entry information.

        Parameters
        ----------
        identifier : str
            The PDS identifier to associate as the primary key for the new row.
        transaction_key : str
            Path to the local transaction history location associated with the
            new row.
        doi : str, optional
            The DOI value to associate with the new row. Defaults to None.
        date_added : datetime, optional
            Time that the row was initially added to the database. Defaults
            to the current time.
        date_updated : datetime, optional
            Time that the row was last updated. Defaults to the current time.
        status : DoiStatus
            The status of the transaction. Defaults to DoiStatus.Unknown.
        title : str
            The title associated with the transaction. Defaults to an empty string.
        product_type : ProductType
            The product type associated with the transaction. Defaults to
            ProductType.Collection.
        product_type_specific : str
            The specific product type associated with the transaction.
            Defaults to an empty string.
        submitter : str
            The submitter email associated with the transaction. Defaults
            to an empty string.
        discipline_node : str
            The discipline node ID associated with the transaction. Defaults
            to an empty string.

        Raises
        ------
        RuntimeError
            If the database transaction cannot be committed for any reason.

        """
        self.m_my_conn = self.get_connection()

        # Convert timestamps to Unix epoch floats for simpler table storage
        date_added = date_added.replace(tzinfo=timezone.utc).timestamp()
        date_updated = date_updated.replace(tzinfo=timezone.utc).timestamp()

        # Map the inputs to the appropriate column names. By doing so, we
        # can ignore database column ordering for now.
        data = {
            "identifier": identifier,
            "status": status,
            "date_added": date_added,
            "date_updated": date_updated,
            "submitter": submitter,
            "title": title,
            "type": product_type,
            "subtype": product_type_specific,
            "node_id": discipline_node,
            "doi": doi,
            "transaction_key": transaction_key,
            "is_latest": True,
        }

        try:
            # Create and execute the query to unset the is_latest field for all
            # records with the same identifier field.
            query_string = self.query_string_for_is_latest_update(
                self.m_default_table_name, primary_key_column="identifier"
            )

            self.m_my_conn.execute(query_string, (identifier,))
            self.m_my_conn.commit()
        except sqlite3.Error as err:
            msg = f"Failed to update is_latest field for identifier {identifier}, " f"reason: {err}"
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
            msg = f"Failed to commit transaction for identifier {identifier}, " f"reason: {err}"
            logger.error(msg)
            raise RuntimeError(msg)

    def _normalize_rows(self, columns, rows):
        """
        Normalize columns from each rows to be the data types we expect,
        rather than the types which are convenient for table storage
        """
        for row in rows:
            # Convert the add/update times from Unix epoch back to datetime,
            # accounting for the expected (PST) timezone
            for time_column in ("date_added", "date_updated"):
                time_val = row[columns.index(time_column)]
                time_val = datetime.fromtimestamp(time_val, tz=timezone.utc).replace(
                    tzinfo=timezone(timedelta(hours=--8.0))
                )
                row[columns.index(time_column)] = time_val

            # Convert status/product type back to Enums
            row[columns.index("status")] = DoiStatus(row[columns.index("status")].lower())
            row[columns.index("type")] = ProductType(row[columns.index("type")].capitalize())

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

        query_string = f"SELECT * from {table_name} " f"WHERE is_latest=1 {criterias_str} ORDER BY date_updated"

        logger.debug("SELECT query_string: %s", query_string)

        cursor = self.m_my_conn.cursor()
        cursor.execute(query_string, criteria_dict)

        columns = list(map(lambda x: x[0], cursor.description))

        rows = [list(row) for row in cursor]

        rows = self._normalize_rows(columns, rows)

        logger.debug("Query returned %d result(s)", len(rows))

        return columns, rows

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
        wildcard_tokens = list(filter(lambda token: "*" in token, search_tokens))
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

        # Set up the named parameters for the GLOB portion of the WHERE used
        # find tokens containing wildcards
        glob_parameters = " OR ".join(
            [f"{column_name} GLOB :{named_param_id}_glob_{i}" for i in range(len(wildcard_tokens))]
        )

        named_parameter_values.update(
            {f"{named_param_id}_glob_{i}": wildcard_tokens[i] for i in range(len(wildcard_tokens))}
        )

        # Build the portion of the WHERE clause combining the necessary
        # parameters needed to search for all the tokens we were provided
        where_subclause = "AND ("

        if full_tokens:
            where_subclause += f"{column_name} IN ({named_parameters}) "

        if full_tokens and wildcard_tokens:
            where_subclause += " OR "

        if wildcard_tokens:
            where_subclause += f"{glob_parameters}"

        where_subclause += ")"

        logger.debug("WHERE subclause: %s", where_subclause)

        return where_subclause, named_parameter_values

    @staticmethod
    def _get_simple_in_criteria(v, column):
        named_parameters = ",".join([":" + column + "_" + str(i) for i in range(len(v))])
        named_parameter_values = {column + "_" + str(i): v[i].lower() for i in range(len(v))}
        return f" AND lower({column}) IN ({named_parameters})", named_parameter_values

    @staticmethod
    def _get_query_criteria_title(v):
        return DOIDataBase._get_simple_in_criteria(v, "title")

    @staticmethod
    def _get_query_criteria_doi(v):
        return DOIDataBase._get_simple_in_criteria(v, "doi")

    @staticmethod
    def _get_query_criteria_ids(v):
        return DOIDataBase._form_query_with_wildcards("identifier", v)

    @staticmethod
    def _get_query_criteria_submitter(v):
        return DOIDataBase._get_simple_in_criteria(v, "submitter")

    @staticmethod
    def _get_query_criteria_node(v):
        return DOIDataBase._get_simple_in_criteria(v, "node_id")

    @staticmethod
    def _get_query_criteria_status(v):
        return DOIDataBase._get_simple_in_criteria(v, "status")

    @staticmethod
    def _get_query_criteria_start_update(v):
        return (" AND date_updated >= :start_update", {"start_update": v.replace(tzinfo=timezone.utc).timestamp()})

    @staticmethod
    def _get_query_criteria_end_update(v):
        return (" AND date_updated <= :end_update", {"end_update": v.replace(tzinfo=timezone.utc).timestamp()})

    @staticmethod
    def parse_criteria(query_criterias):
        criterias_str = ""
        criteria_dict = {}

        for k, v in query_criterias.items():
            logger.debug("Calling get_query_criteria_%s with value %s", k, v)

            criteria_str, dict_entry = getattr(DOIDataBase, "_get_query_criteria_" + k)(v)

            logger.debug("criteria_str: %s", criteria_str)
            logger.debug("dict_entry: %s", dict_entry)

            criterias_str += criteria_str
            criteria_dict.update(dict_entry)

        return criterias_str, criteria_dict
