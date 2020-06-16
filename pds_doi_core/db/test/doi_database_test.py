import os
import unittest
from pds_doi_core.db.doi_database import DOIDataBase
from pds_doi_core.util.general_util import get_logger

logger = get_logger(__name__)

class MyTestCase(unittest.TestCase):
    _doi_database = DOIDataBase()

    def test_select_latest_rows(self):
        logger.info("test selecting latest rows from database")

        # Delete temporary file doi_temp.db if exist for unit test.
        if os.path.exists("doi_temp.db"):
            os.remove("doi_temp.db")

        # Create a temporary database 'doi_temp.db' and a 'doi' table.
        self._doi_database.create_connection('doi_temp.db')
        self._doi_database.create_table('doi')

        # Set a list of 1 dict to some values.
        doi_fields = [{'discipline_node': 'img', 'action_type': 'reserve', 'input_content': 'input/DOI_Reserved_GEO_200318.csv', 'content_type': 'csv', 'submitter': 'Qui.T.Chau@jpl.nasa.gov', 'status': 'reserved', 'lid': 'urn:nasa:pds:lab_shocked_feldspars', 'vid': '1.0', 'id': '21729', 'doi': '10.17189/21729', 'title': 'Laboratory Shocked Feldspars Bundle', 'type': 'Collection', 'subtype': 'PDS4 Collection', 'output_content': b'<records>\n    <record status="Reserved"> \n        <title>Laboratory Shocked Feldspars Bundle</title>\n        <creators/>\n        <authors>\n             <author>\n                <first_name>J. R.</first_name>\n                <last_name>Johnson</last_name>\n            </author>\n        </authors>\n        <publication_date>03/11/2020</publication_date>\n        <product_type>Collection</product_type>\n        <product_type_specific>PDS4 Collection</product_type_specific>\n\n        <related_identifiers>\n            <related_identifier>\n                <identifier_type>URL</identifier_type>\n                <identifier_value>urn:nasa:pds:lab_shocked_feldspars::1.0</identifier_value>\n                <relation_type>Cites</relation_type>\n            </related_identifier>\n        </related_identifiers>        \n    </record>\n    <record status="Reserved"> \n        <title>Laboratory Shocked Feldspars Collection</title>\n        <creators/>\n        <authors>\n             <author>\n                <first_name>J2. R2.</first_name>\n                <last_name>Johnson_2</last_name>\n            </author>\n        </authors>\n        <publication_date>03/12/2020</publication_date>\n        <product_type>Collection</product_type>\n        <product_type_specific>PDS4 Bundle</product_type_specific>\n\n        <related_identifiers>\n            <related_identifier>\n                <identifier_type>URL</identifier_type>\n                <identifier_value>urn:nasa:pds:lab_shocked_feldspars_2::1.0</identifier_value>\n                <relation_type>Cites</relation_type>\n            </related_identifier>\n        </related_identifiers>        \n    </record>\n    <record status="Reserved"> \n        <title>Laboratory Shocked Feldspars Collection</title>\n        <creators/>\n        <authors>\n             <author>\n                <first_name>J3. R3.</first_name>\n                <last_name>Johnson_3</last_name>\n            </author>\n        </authors>\n        <publication_date>03/12/2020</publication_date>\n        <product_type>Collection</product_type>\n        <product_type_specific>PDS4 Bundle</product_type_specific>\n\n        <related_identifiers>\n            <related_identifier>\n                <identifier_type>URL</identifier_type>\n                <identifier_value>urn:nasa:pds:lab_shocked_feldspars_3::1.0</identifier_value>\n                <relation_type>Cites</relation_type>\n            </related_identifier>\n        </related_identifiers>        \n    </record>\n</records>\n', 'submitted_input_link': './transaction_history/img/2020-06-15T18:42:45.653317/input.csv', 'submitted_output_link': './transaction_history/img/2020-06-15T18:42:45.653317/output.xml', 'transaction_key': 'img/2020-06-15T18:42:45.653317', 'latest_update': 1592271765}]


        # Inserting a row in the 'doi' table.
        self._doi_database.write_doi_info_to_database_all(doi_fields)

        # Select the row we just added.  The type of o_query_result should be JSON and a list of 1.

        o_query_result = self._doi_database.select_latest_rows(
            'doi_temp.db',
            'doi',
            [])
        logger.info(o_query_result)
        logger.info(f"{type(o_query_result)}")

        # Remove test artifact.
        if os.path.exists("doi_temp.db"):
            os.remove("doi_temp.db")

if __name__ == '__main__':
    unittest.main()
