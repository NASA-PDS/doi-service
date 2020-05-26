import os
import logging
import unittest
from pds_doi_core.util.config_parser import DOIConfigUtil
from pds_doi_core.input.input_util import DOIInputUtil
from pds_doi_core.cmd.pds_doi_cmd import DOICoreServices
from pds_doi_core.util.general_util import get_logger


logger = get_logger()


class MyTestCase(unittest.TestCase):
    def test_read_xls(self):

        doi_input_util = DOIInputUtil()
        doi_core_service = DOICoreServices()

        i_filepath = os.path.join(os.getcwd(), 'input', 'DOI_Reserved_GEO_200318.xlsx')
        o_num_files_created = doi_input_util.parse_sxls_file(i_filepath)
        logger.info(f"o_num_files_created {o_num_files_created}")

    def test_read_csv(self):

        doi_input_util = DOIInputUtil()
        doi_core_service = DOICoreServices()

        (dict_configList, dict_fixedList) = doi_core_service._get_default_configurations()

        appBasePath = os.path.abspath(os.path.curdir)

        i_filepath = os.path.join(os.getcwd(), 'input','DOI_Reserved_GEO_200318.csv')
        o_num_files_created = doi_input_util.parse_csv_file(i_filepath)
        logger.info(f"o_num_files_created {o_num_files_created}")


if __name__ == '__main__':
    unittest.main()