import datetime
import unittest
import os

from pds_doi_core.db.doi_database import DOIDataBase
from pds_doi_core.actions.release import DOICoreActionRelease

from pds_doi_core.util.general_util import get_logger

logger = get_logger(__name__)

class MyTestCase(unittest.TestCase):

    # As of 07/13/2020, OSTI has the below ID records (['22831','22832','22833']) in their test server so this test will work
    # to demonstrate that they have new status of 'Pending' or 'Registered'.  If for some reason the server has been wiped clean, this unit test will still run
    # but won't show any status changed to 'Registered'.
    #
    # Because validation has been added to each action, the force=True is required as the command line is not parsed for unit test.

    db_name = 'doi_temp.db'
    logger.info("Creating test artifact database file {self.db_name}")
    # Remove db_name if exist to have a fresh start otherwise exception will be raised about using existing lidvid.
    if os.path.isfile(db_name):
        os.remove(db_name)
        logger.info(f"Removed test artifact database file {db_name}")

    # Release some DOIs.
    # Move instantation of DOICoreActionRelease() object inside tests since the temporary file is removed after each test
    # and will cause "Exception: Database error: disk I/O error"

    @classmethod
    def setUp(cls):
        cls._action = DOICoreActionRelease(db_name=cls.db_name)
        logger.info(f"Instantiate DOICoreActionRelease with database file {cls.db_name}")

    @classmethod
    def tearDown(cls):
        if os.path.isfile(cls.db_name):
            #os.remove(self.db_name)
            logger.info(f"Removed test artifact database file {cls.db_name}")

    def test_reserve(self):
        # Instantiate DOICoreActionRelease() here so a new database file is created and removed for each test.
        # The setUp() function is called per test.
        logger.info("test release of document from 'reserve' action.  This test would only work if the authentication for OSTI has been set up and DOIs exist.")
        result_list = self._action.run(input='input/DOI_Release_20200727_from_reserve.xml',node='img',submitter='Qui.T.Chau@jpl.nasa.gov',force=True)

        logger.info(result_list)
        # The tearDown() function is called per test.

    def test_draft(self):
        # Instantiate DOICoreActionRelease() here so a new database file is created and removed for each test.
        # The setUp() function is called per test.
        logger.info("test release of document from 'release' output.  This test would only work if the authentication for OSTI has been set up and DOIs exist.")
        result_list = []
        result_list = self._action.run(input='input/DOI_Release_20200727_from_draft.xml',node='img',submitter='Qui.T.Chau@jpl.nasa.gov',force=True)

        logger.info(result_list)
        # The tearDown() function is called per test.

if __name__ == '__main__':
    unittest.main()
