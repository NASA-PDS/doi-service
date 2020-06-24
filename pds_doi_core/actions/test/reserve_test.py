import unittest
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.actions.reserve import DOICoreActionReserve

logger = get_logger(__name__)


class MyTestCase(unittest.TestCase):
    # The two tests below only build the reserve DOI and return the reserve label.
    # The parameter submit_label_flag  is set to False to not send the DOI to OTSI.
    # The parameter write_to_file_flag is set to False to not create individual external file for each record in the XML or CSV file.
    # Inorder to actually the submit the DOI, the ~/.netrc file must have been set up previously.

    _action = DOICoreActionReserve()

    def test_reserve_xlsx(self):
        logger.info("test reserve xlsx file format")
        osti_doi = self._action.run(
            input='input/DOI_Reserved_GEO_200318_with_corrected_identifier.xlsx',
            node='img', submitter='my_user@my_node.gov',
            submit_label_flag=False)
        logger.info(osti_doi)

    def test_reserve_xlsx_and_submit(self):
        logger.info("test reserve xlsx file format")
        osti_doi = self._action.run(
            input='input/DOI_Reserved_GEO_200318_with_corrected_identifier.xlsx',
            node='img', submitter='my_user@my_node.gov',
            submit_label_flag=True)
        logger.info(osti_doi)

    def test_reserve_csv(self):
        logger.info("test reserve csv file format")
        osti_doi = self._action.run(
            input='input/DOI_Reserved_GEO_200318.csv',
            node='img', submitter='my_user@my_node.gov',
            submit_label_flag=False)
        logger.info(osti_doi)


if __name__ == '__main__':
    unittest.main()
