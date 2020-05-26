import unittest
from pds_doi_core.references.contributors import DOIContributorUtil


class MyTestCase(unittest.TestCase):
    _doi_contributor_util = DOIContributorUtil('https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_JSON_1D00.JSON',
                                               '0001_NASA_PDS_1.pds.Node.pds.name')

    def test_authorized_contributor(self):


        authorized_contributor = 'Cartography and Imaging Sciences Discipline' \
                                 in self._doi_contributor_util.get_permissible_values()

        self.assertEqual(authorized_contributor, True)

    def test_unauthorized_contributor(self):
        authorized_contributor = 'Cartography and Imaging Sciences Disciine' \
                                 in self._doi_contributor_util.get_permissible_values()

        self.assertEqual(authorized_contributor, False)


if __name__ == '__main__':
    unittest.main()
