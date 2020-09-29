import os
import unittest
from pds_doi_core.input.exceptions import WarningDOIException
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.actions.reserve import DOICoreActionReserve

logger = get_logger(__name__)


class MyTestCase(unittest.TestCase):
    # The two tests below only build the reserve DOI and return the reserve label.
    # The parameter submit_label_flag  is set to False to not send the DOI to OTSI.
    # The parameter write_to_file_flag is set to False to not create individual external file for each record in the XML or CSV file.
    # Inorder to actually the submit the DOI, the ~/.netrc file must have been set up previously.
    # Due to addition of validation of existing 'title', 'lidvid' and 'doi' fields from local database,
    # the DOICoreActionReserve must be instantiated per test and the tear down per test as well to remove temporary database.

    # Because validation has been added to each action, the force=True is required as the command line is not parsed for unit test.
    db_name = 'doi_temp.db'

    def setUp(self):
        # This setUp() function is called for every test.
        self._action = DOICoreActionReserve(db_name=self.db_name)
        logger.info(f"Instantiate DOICoreActionReserve with database file {self.db_name}")

    def tearDown(self):
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)
            logger.info(f"Removed test artifact database file {self.db_name}")


    def test_reserve_xlsx(self):
        # Instantiate DOICoreActionReserve() class per test.
        # The setUp() function is called for every test.
        logger.info("test reserve xlsx file format")

        self._action.run(
            input='input/DOI_Reserved_GEO_200318_with_corrected_identifier.xlsx',
            node='img', submitter='my_user@my_node.gov',
            dry_run=True,force=True)

        # The tearDown() function is called per test.

    def test_reserve_xlsx_and_submit(self):
        # Instantiate DOICoreActionReserve() class per test.
        # The setUp(0 function is called for every test.
        logger.info("test reserve xlsx file format")

        self._action.run(
            input='input/DOI_Reserved_GEO_200318_with_corrected_identifier.xlsx',
            node='img', submitter='my_user@my_node.gov',
            dry_run=True,force=True)

        # The tearDown() function is called per test.

    def test_reserve_csv(self):
        # Instantiate DOICoreActionReserve() class per test.
        # The setUp(0 function is called for every test.
        logger.info("test reserve csv file format")
        osti_doi = self._action.run(
            input='input/DOI_Reserved_GEO_200318.csv',
            node='img', submitter='my_user@my_node.gov',
            dry_run=True,force=True)
        logger.info(osti_doi)

    def test_reserve_csv_and_submit(self):
        logger.info("test reserve csv file format and submit")
        osti_doi = self._action.run(
            input='input/DOI_Reserved_GEO_200318.csv',
            node='img', submitter='my_user@my_node.gov',
            dry_run=False,force=True)
        logger.info(osti_doi)

        # The tearDown() function is called per test.

if __name__ == '__main__':
    unittest.main()
