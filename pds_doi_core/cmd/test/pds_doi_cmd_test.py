import unittest
from pds_doi_core.cmd.pds_doi_cmd import DOICoreServices
from pds_doi_core.util.general_util import get_logger

logger = get_logger(__name__)

class MyTestCase(unittest.TestCase):
    _doi_code_service = DOICoreServices()

    def test_local_bundle(self):
        logger.info("test local bundle")
        osti_doi = self._doi_code_service.create_doi_label(
            'input/bundle_in_with_contributors.xml',
            'Cartography and Imaging Sciences Discipline')
        logger.info(osti_doi)

    def test_remote_bundle(self):
        logger.info("test remote bundle")
        osti_doi = self._doi_code_service.create_doi_label(
            'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml',
            'Cartography and Imaging Sciences Discipline')
        logger.info(osti_doi)

    def test_remote_collection(self):
        logger.info("test remote collection")
        osti_doi = self._doi_code_service.create_doi_label(
            'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml',
            'Cartography and Imaging Sciences Discipline')
        logger.info(osti_doi)


    def test_remote_browse_collection(self):
        logger.info("test remote browse collection")
        osti_doi = self._doi_code_service.create_doi_label(
            'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml',
            'Cartography and Imaging Sciences Discipline')
        logger.info(osti_doi)

    def test_remote_calibration_collection(self):
        logger.info("test remote calibration collection")
        osti_doi = self._doi_code_service.create_doi_label(
            'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml',
            'Cartography and Imaging Sciences Discipline')
        logger.info(osti_doi)

    def test_remote_document_collection(self):
        logger.info("test remote document collection")
        osti_doi = self._doi_code_service.create_doi_label(
            'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml',
            'Cartography and Imaging Sciences Discipline')
        logger.info(osti_doi)

    # The two tests below only build the reserve DOI and return the reserve label.
    # The parameter submit_label_flag  is set to False to not send the DOI to OTSI.
    # The parameter write_to_file_flag is set to False to not create individual external file for each record in the XML or CSV file.
    # Inorder to actually the submit the DOI, the ~/.netrc file must have been set up previously.

    def test_reserve_xlsx(self):
        logger.info("test reserve xlsx file format")
        osti_doi = self._doi_code_service.reserve_doi_label(
            'input/DOI_Reserved_GEO_200318.xlsx',
            'Cartography and Imaging Sciences Discipline',
            'NASA Planetary Data System',
            submit_label_flag=False,
            write_to_file_flag=False)
        logger.info(osti_doi)

    def test_reserve_csv(self):
        logger.info("test reserve csv file format")
        osti_doi = self._doi_code_service.reserve_doi_label(
            'input/DOI_Reserved_GEO_200318.csv',
            'Cartography and Imaging Sciences Discipline',
            'NASA Planetary Data System',
            submit_label_flag=False,
            write_to_file_flag=False)
        logger.info(osti_doi)

if __name__ == '__main__':
    unittest.main()
