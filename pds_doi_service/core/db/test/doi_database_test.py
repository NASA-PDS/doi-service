import datetime
import os
import unittest
from pds_doi_service.core.db.doi_database import DOIDataBase
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)

class MyTestCase(unittest.TestCase):


    def test_select_latest_rows(self):
        logger.info("test selecting latest rows from database")

        # Delete temporary file doi_temp.db if exist for unit test.
        if os.path.exists("doi_temp.db"):
            os.remove("doi_temp.db")

        self._doi_database = DOIDataBase('doi_temp.db')

        # Set many field values.

        lid = 'urn:nasa:pds:lab_shocked_feldspars'
        vid = '1.0'
        transaction_key = 'img/2020-06-15T18:42:45.653317'
        doi = '10.17189/21729'
        transaction_date = datetime.datetime.now()
        status = 'unknown'
        title = 'Laboratory Shocked Feldspars Bundle'
        product_type = 'Collection'
        product_type_specific = 'PDS4 Collection'
        submitter = 'Qui.T.Chau@jpl.nasa.gov'
        discipline_node = 'img'

        # Inserting a row in the 'doi' table.
        self._doi_database.write_doi_info_to_database(lid, vid, transaction_key, doi, transaction_date, status,
                                   title, product_type, product_type_specific, submitter, discipline_node)

        # Select the row we just added.  The type of o_query_result should be JSON and a list of 1.
        o_query_result = self._doi_database.select_latest_rows( {'doi': [doi]})

        logger.info(o_query_result)

        # Remove test artifact.
        if os.path.exists("doi_temp.db"):
            os.remove("doi_temp.db")

if __name__ == '__main__':
    unittest.main()
