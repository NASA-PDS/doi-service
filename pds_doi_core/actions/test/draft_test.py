import unittest
import os

from pds_doi_core.actions.draft import DOICoreActionDraft


from pds_doi_core.util.general_util import get_logger

logger = get_logger(__name__)

def create_temporary_output_file(doi_label,filename):
    # Save doi_label so it can be compared to.
    temporary_file_name = filename
    temporary_file_ptr = open(temporary_file_name,"w+")
    temporary_file_ptr.write(doi_label + "\n")
    temporary_file_ptr.close()
    return temporary_file_name

class MyTestCase(unittest.TestCase):
    db_name = 'doi_temp.db'
    # Because validation has been added to each action, the force=True is required as the command line is not parsed for unit test.

    @classmethod
    def setUp(self):
        # This setUp() function is called for every test.
        self._action = DOICoreActionDraft(db_name=self.db_name)
        logger.info(f"Instantiate DOICoreActionDraft with database file {self.db_name}")
        # Create output directory if one does not already exist.
        self._temporary_output_dir = './tests/data'
        os.makedirs(self._temporary_output_dir, exist_ok=True)

    @classmethod
    def tearDown(self):
        # This tearDown() function is called at end of every test.
        if os.path.isfile(self.db_name):
            os.remove(self.db_name)
            logger.info(f"Removed test artifact database file {self.db_name}")
        else:
            logger.info(f"File not exist, test artifact database file {self.db_name}")


    def test_local_dir_one_file(self):
        logger.info("test local dir with one file")
        osti_doi = self._action.run(input='input/draft_dir_one_file',
                              node='img',
                              submitter='my_user@my_node.gov',force=True)
        logger.info(osti_doi)

    def test_local_dir_two_files(self):
        logger.info("test local dir with two files")
        osti_doi = self._action.run(input='input/draft_dir_two_files',
                              node='img',
                              submitter='my_user@my_node.gov',force=True)
        logger.info(osti_doi)

    def test_local_bundle(self):
        logger.info("test local bundle")
        osti_doi = self._action.run(input='input/bundle_in_with_contributors.xml',
                              node='img',
                              submitter='my_user@my_node.gov',force=True)
        logger.info(osti_doi)

    def test_remote_bundle(self):
        logger.info("test remote bundle")
        osti_doi = self._action.run(
                                    input='https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml',
                                    node='img',
                                    submitter='my_user@my_node.gov',force=True)
        logger.info(osti_doi)
        #create_temporary_output_file(osti_doi, os.path.join(self._temporary_output_dir,'valid_bundle_doi.xml'))

    def test_remote_collection(self):
        logger.info("test remote collection")
        osti_doi = self._action.run(
                                    input='https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml',
                                    node='img', submitter='my_user@my_node.gov',force=True)
        logger.info(osti_doi)
        #create_temporary_output_file(osti_doi, os.path.join(self._temporary_output_dir,'valid_datacoll_doi.xml'))

    def test_remote_browse_collection(self):
        logger.info("test remote browse collection")
        osti_doi = self._action.run(
                                    input='https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml',
                                    node='img', submitter='my_user@my_node.gov',force=True)
        logger.info(osti_doi)
        #create_temporary_output_file(osti_doi, os.path.join(self._temporary_output_dir,'valid_browsecoll_doi.xml'))

    def test_remote_calibration_collection(self):
        logger.info("test remote calibration collection")
        osti_doi = self._action.run(
                                    input='https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml',
                                    node='img', submitter='my_user@my_node.gov',force=True)
        logger.info(osti_doi)
        #create_temporary_output_file(osti_doi, os.path.join(self._temporary_output_dir,'valid_calibcoll_doi.xml'))

    def test_remote_document_collection(self):
        logger.info("test remote document collection")
        osti_doi = self._action.run(
                                    input='https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml',
                                    node='img', submitter='my_user@my_node.gov',force=True)
        logger.info(osti_doi)
        #create_temporary_output_file(osti_doi, os.path.join(self._temporary_output_dir,'valid_docucoll_doi.xml'))


if __name__ == '__main__':
    unittest.main()
