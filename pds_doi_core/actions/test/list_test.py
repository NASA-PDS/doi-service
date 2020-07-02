import unittest

from types import SimpleNamespace

from pds_doi_core.actions.list import DOICoreActionList


from pds_doi_core.util.general_util import get_logger

logger = get_logger(__name__)

class MyTestCase(unittest.TestCase):
    # We have to set all namespaces to None, except for format_output otherwise Python will attempt to access these fields and fail.
    #_action = DOICoreActionList() # This does not work
    _action = DOICoreActionList(SimpleNamespace(submitter_email=None,node_id=None,doi=None,format_output='JSON',start_update=None,end_update=None,lid=None,lidvid=None))

    def test_1(self):
        logger.info("test making a query to database")
        result_list = self._action.run()
        logger.info(result_list)

if __name__ == '__main__':
    unittest.main()
