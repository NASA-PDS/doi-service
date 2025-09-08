"""
Utility functions for test cleanup, particularly for Windows compatibility.
"""
import os
import time
import logging

logger = logging.getLogger(__name__)


def safe_remove_file(filepath, max_retries=5, delay=0.1):
    """
    Safely remove a file with retry logic for Windows compatibility.
    
    On Windows, SQLite database files can remain locked for a short time after
    connections are closed. This function implements retry logic to handle
    this scenario.
    
    Parameters
    ----------
    filepath : str
        Path to the file to remove
    max_retries : int, optional
        Maximum number of retry attempts (default: 5)
    delay : float, optional
        Delay in seconds between retry attempts (default: 0.1)
        
    Returns
    -------
    bool
        True if file was successfully removed, False otherwise
    """
    if not os.path.exists(filepath):
        return True
        
    for attempt in range(max_retries):
        try:
            os.remove(filepath)
            logger.debug(f"Successfully removed file: {filepath}")
            return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                logger.debug(f"Permission error removing {filepath}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                logger.warning(f"Failed to remove file {filepath} after {max_retries} attempts: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error removing file {filepath}: {e}")
            return False
    
    return False


def close_all_database_connections(obj, connection_attrs=None):
    """
    Close all database connections found in an object.
    
    Parameters
    ----------
    obj : object
        Object that may contain database connections
    connection_attrs : list, optional
        List of attribute names to check for database connections.
        If None, uses default list of common database connection attributes.
        
    Returns
    -------
    int
        Number of connections closed
    """
    if connection_attrs is None:
        connection_attrs = [
            '_database_obj',
            'm_doi_database', 
            '_doi_database',
            'm_my_conn',
            '_conn'
        ]
    
    closed_count = 0
    
    for attr_name in connection_attrs:
        if hasattr(obj, attr_name):
            db_obj = getattr(obj, attr_name)
            if hasattr(db_obj, 'close_database'):
                try:
                    db_obj.close_database()
                    closed_count += 1
                    logger.debug(f"Closed database connection: {attr_name}")
                except Exception as e:
                    logger.warning(f"Error closing database connection {attr_name}: {e}")
    
    return closed_count
