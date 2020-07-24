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

    db_name = 'doi_temp.db'
    logger.info("Creating test artifact database file {self.db_name}")

    # Release some DOIs.
    _action = DOICoreActionRelease(db_name=db_name)

    def test_1(self):
        logger.info("test release some DOIs.  This test would only work if the authentication for OSTI has been set up and DOIs exist.")
        result_list = []
        result_list = self._action.run(input='input/DOI_Release_20200723.xml',node='img',submitter='Qui.T.Chau@jpl.nasa.gov')

        if os.path.isfile(self.db_name):
            os.remove(self.db_name)
            logger.info(f"Removed test artifact database file {self.db_name}")
        logger.info(result_list)

if __name__ == '__main__':
    unittest.main()
