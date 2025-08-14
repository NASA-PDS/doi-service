#!/usr/bin/env python3
"""
Practical example of using namespace detection in PDS4 XML processing.

This script demonstrates how to use the namespace detection methods
for XPath queries and XML processing in the PDS4 DOI service.
"""

import sys
import os
from lxml import etree

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pds_doi_service.core.input.pds4_util import DOIPDS4LabelUtil

def example_xpath_with_namespaces():
    """Example of using namespace detection for XPath queries."""
    
    # Sample PDS4 XML with your exact structure
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Product_Document
    xmlns="http://pds.nasa.gov/pds4/pds/v1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://pds.nasa.gov/pds4/pds/v1 https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_1O00.xsd">
    
    <Identification_Area>
        <logical_identifier>urn:nasa:pds:example:data::1.0</logical_identifier>
        <version_id>1.0</version_id>
        <title>Example PDS4 Document</title>
        <product_class>Product_Document</product_class>
        <Citation_Information>
            <publication_year>2024</publication_year>
            <description>This is an example PDS4 document for testing namespace detection.</description>
        </Citation_Information>
    </Identification_Area>
    
</Product_Document>'''
    
    # Parse the XML
    xml_tree = etree.fromstring(xml_content.encode())
    pds4_util = DOIPDS4LabelUtil()
    
    print("=== Namespace Detection Example ===")
    
    # Get the default namespace
    default_ns = pds4_util.get_default_namespace(xml_tree)
    print(f"Default namespace: {default_ns}")
    
    # Get complete namespace mapping
    ns_map = pds4_util.get_namespace_map(xml_tree)
    print(f"Complete namespace map: {ns_map}")
    
    # Example 1: Using XPath with namespace mapping
    print("\n=== Example 1: XPath with Namespace Mapping ===")
    
    # Method 1: Using the namespace map directly
    title_elements = xml_tree.xpath('//pds4:title', namespaces={'pds4': default_ns})
    if title_elements:
        print(f"Title (using namespace map): {title_elements[0].text}")
    
    # Method 2: Using the utility's XPath conversion
    converted_xpath = pds4_util.convert_xpath_for_default_namespace('//pds4:title')
    title_elements = xml_tree.xpath(converted_xpath)
    if title_elements:
        print(f"Title (using converted XPath): {title_elements[0].text}")
    
    # Example 2: Extracting multiple elements
    print("\n=== Example 2: Extracting Multiple Elements ===")
    
    # Get logical identifier
    lid_elements = xml_tree.xpath('//pds4:logical_identifier', namespaces={'pds4': default_ns})
    if lid_elements:
        print(f"Logical Identifier: {lid_elements[0].text}")
    
    # Get version ID
    vid_elements = xml_tree.xpath('//pds4:version_id', namespaces={'pds4': default_ns})
    if vid_elements:
        print(f"Version ID: {vid_elements[0].text}")
    
    # Get publication year
    pub_year_elements = xml_tree.xpath('//pds4:publication_year', namespaces={'pds4': default_ns})
    if pub_year_elements:
        print(f"Publication Year: {pub_year_elements[0].text}")
    
    # Example 3: Working with nested elements
    print("\n=== Example 3: Working with Nested Elements ===")
    
    # Get description from Citation_Information
    desc_elements = xml_tree.xpath('//pds4:Citation_Information/pds4:description', namespaces={'pds4': default_ns})
    if desc_elements:
        print(f"Description: {desc_elements[0].text}")
    
    # Example 4: Using the utility's existing methods
    print("\n=== Example 4: Using Existing Utility Methods ===")
    
    # The utility already has methods that handle namespace conversion
    # Let's see how it works with the existing xpath_dict
    xpath_dict = pds4_util.xpath_dict
    
    print("Available XPath mappings:")
    for field, xpath in xpath_dict.items():
        print(f"  {field}: {xpath}")
    
    # Convert one of the XPaths for default namespace
    converted_title_xpath = pds4_util.convert_xpath_for_default_namespace(xpath_dict['title'])
    print(f"\nConverted title XPath: {converted_title_xpath}")
    
    # Use the converted XPath
    title_elements = xml_tree.xpath(converted_title_xpath)
    if title_elements:
        print(f"Title from converted XPath: {title_elements[0].text}")

def example_error_handling():
    """Example of error handling with namespace detection."""
    
    print("\n=== Error Handling Example ===")
    
    # XML without default namespace
    xml_no_ns = '''<?xml version="1.0" encoding="UTF-8"?>
<Product_Document>
    <Identification_Area>
        <title>Document without namespace</title>
    </Identification_Area>
</Product_Document>'''
    
    xml_tree = etree.fromstring(xml_no_ns.encode())
    pds4_util = DOIPDS4LabelUtil()
    
    # This should return None
    default_ns = pds4_util.get_default_namespace(xml_tree)
    print(f"Default namespace (no namespace XML): {default_ns}")
    
    # This should return empty dict or minimal mapping
    ns_map = pds4_util.get_namespace_map(xml_tree)
    print(f"Namespace map (no namespace XML): {ns_map}")

if __name__ == "__main__":
    print("PDS4 Namespace Detection - Practical Examples")
    print("=" * 50)
    
    try:
        example_xpath_with_namespaces()
        example_error_handling()
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error in examples: {e}")
        sys.exit(1)
