import unittest

from pds_doi_core.actions.list import DOICoreActionList

from pds_doi_core.util.general_util import get_logger

logger = get_logger(__name__)

class MyTestCase(unittest.TestCase):
    _action = DOICoreActionList()

    def test_1(self):
        logger.info("test making a query to database")
        result_list = self._action.run(node='img')
        logger.info(result_list)

if __name__ == '__main__':
    unittest.main()
