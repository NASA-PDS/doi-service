import unittest

from pds_doi_core.actions.draft import DOICoreActionDraft


from pds_doi_core.util.general_util import get_logger

logger = get_logger(__name__)

class MyTestCase(unittest.TestCase):
    _action = DOICoreActionDraft()

    def test_local_bundle(self):
        logger.info("test local bundle")
        osti_doi = self._action.run(
                                    'input/bundle_in_with_contributors.xml',
                                    'img', 'my_user@my_node.gov')
        logger.info(osti_doi)

    def test_remote_bundle(self):
        logger.info("test remote bundle")
        osti_doi = self._action.run(
                                    'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/bundle.xml',
                                    'img', 'my_user@my_node.gov')
        logger.info(osti_doi)

    def test_remote_collection(self):
        logger.info("test remote collection")
        osti_doi = self._action.run(
                                    'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/data/collection_data.xml',
                                    'img', 'my_user@my_node.gov')
        logger.info(osti_doi)


    def test_remote_browse_collection(self):
        logger.info("test remote browse collection")
        osti_doi = self._action.run(
                                    'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/browse/collection_browse.xml',
                                    'img', 'my_user@my_node.gov')
        logger.info(osti_doi)

    def test_remote_calibration_collection(self):
        logger.info("test remote calibration collection")
        osti_doi = self._action.run(
                                    'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/calibration/collection_calibration.xml',
                                    'img', 'my_user@my_node.gov')
        logger.info(osti_doi)

    def test_remote_document_collection(self):
        logger.info("test remote document collection")
        osti_doi = self._action.run(
                                    'https://pds-imaging.jpl.nasa.gov/data/nsyt/insight_cameras/document/collection_document.xml',
                                    'img', 'my_user@my_node.gov')
        logger.info(osti_doi)



if __name__ == '__main__':
    unittest.main()
