import unittest
import os
import pathlib
from lxml import etree


class MyTestCase(unittest.TestCase):
    def test_read_bundle(self):
        test_file = os.path.join(pathlib.Path(__file__).parent.absolute(), "data", "bundle.xml")
        pom_doc = etree.parse(test_file)
        r = pom_doc.xpath('/p:Product_Bundle/p:Identification_Area/p:Citation_Information/p:author_list',
                          namespaces={'p': 'http://pds.nasa.gov/pds4/pds/v1'})
        print(r[0].text)
        self.assertEqual(r[0].text, "R. Deen, H. Abarca, P. Zamani, J.Maki")



if __name__ == '__main__':
    unittest.main()
