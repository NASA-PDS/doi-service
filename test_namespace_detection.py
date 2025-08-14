#!/usr/bin/env python3
"""
Test script to demonstrate namespace detection functionality.

This script shows how to use the get_default_namespace and get_namespace_map
methods from the DOIPDS4LabelUtil class to identify namespaces in PDS4 XML documents.
"""

import sys
import os
from lxml import etree

# Add the src directory to the Python path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pds_doi_service.core.input.pds4_util import DOIPDS4LabelUtil

def test_namespace_detection():
    """Test the namespace detection methods with a sample PDS4 XML."""
    
    # Sample PDS4 XML document (from user's example)
    sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Product_Document
    xmlns="http://pds.nasa.gov/pds4/pds/v1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1 https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1O00.xsd">
    
    <Identification_Area>
        <logical_identifier>urn:nasa:pds:example:data::1.0</logical_identifier>
        <version_id>1.0</version_id>
        <title>Example PDS4 Document</title>
        <product_class>Product_Document</product_class>
    </Identification_Area>
    
</Product_Document>'''
    
    try:
        # Parse the XML
        xml_tree = etree.fromstring(sample_xml.encode())
        
        # Create an instance of the utility class
        pds4_util = DOIPDS4LabelUtil()
        
        # Test default namespace detection
        print("=== Testing Default Namespace Detection ===")
        default_ns = pds4_util.get_default_namespace(xml_tree)
        print(f"Default namespace: {default_ns}")
        
        # Test complete namespace mapping
        print("\n=== Testing Complete Namespace Mapping ===")
        ns_map = pds4_util.get_namespace_map(xml_tree)
        print("Namespace map:")
        for prefix, uri in ns_map.items():
            print(f"  {prefix}: {uri}")
        
        # Test with a more complex XML that has additional namespaces
        print("\n=== Testing with Additional Namespaces ===")
        complex_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Product_Document
    xmlns="http://pds.nasa.gov/pds4/pds/v1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:disp="http://pds.nasa.gov/pds4/disp/v1"
    xmlns:img="http://pds.nasa.gov/pds4/img/v1"
    xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1 https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1O00.xsd
                        http://pds.nasa.gov/pds4/disp/v1 https://pds.nasa.gov/pds4/disp/v1/PDS4_DISP_1O00.xsd
                        http://pds.nasa.gov/pds4/img/v1 https://pds.nasa.gov/pds4/img/v1/PDS4_IMG_1O00.xsd">
    
    <Identification_Area>
        <logical_identifier>urn:nasa:pds:example:complex::1.0</logical_identifier>
        <version_id>1.0</version_id>
        <title>Complex PDS4 Document</title>
        <product_class>Product_Document</product_class>
    </Identification_Area>
    
</Product_Document>'''
        
        complex_tree = etree.fromstring(complex_xml.encode())
        complex_ns_map = pds4_util.get_namespace_map(complex_tree)
        print("Complex namespace map:")
        for prefix, uri in complex_ns_map.items():
            print(f"  {prefix}: {uri}")
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("PDS4 Namespace Detection Test")
    print("=" * 40)
    
    success = test_namespace_detection()
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
