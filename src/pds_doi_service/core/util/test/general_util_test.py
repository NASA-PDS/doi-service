#!/usr/bin/env python
import unittest

from pds_doi_service.core.entities.doi import ProductType
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import create_landing_page_url
from pds_doi_service.core.util.general_util import get_global_keywords
from pds_doi_service.core.util.general_util import is_pds4_identifier
from pds_doi_service.core.util.general_util import parse_identifier_from_site_url
from pds_doi_service.core.util.general_util import sanitize_json_string


class GeneralUtilTest(unittest.TestCase):
    """Unit tests for functions defined in the util/general_util.py module"""

    def test_parse_identifier_from_site_url(self):
        """Tests for general_util.parse_identifier_from_site_url()"""
        # Test with PDS4-style URL with both LID and VID
        site_url = "https://website.com?identifier=urn%3Anasa%3Apds%3Ainsight_cameras&amp;version=1.0"

        identifier = parse_identifier_from_site_url(site_url)

        self.assertEqual(identifier, "urn:nasa:pds:insight_cameras::1.0")

        # Test with PDS4-style URL with LID only
        site_url = "https://website.com?identifier=urn%3Anasa%3Apds%3Ainsight_cameras"

        identifier = parse_identifier_from_site_url(site_url)

        self.assertEqual(identifier, "urn:nasa:pds:insight_cameras")

        # Test with a PDS3-style URL
        site_url = "https://website.com?dsid=LRO-L-MRFLRO-2%2F3%2F5-BISTATIC-V1.0"

        identifier = parse_identifier_from_site_url(site_url)

        self.assertEqual(identifier, "LRO-L-MRFLRO-2/3/5-BISTATIC-V1.0")

        # Test with an invalid URL (no query section)
        site_url = "https://website.com"

        identifier = parse_identifier_from_site_url(site_url)

        self.assertIsNone(identifier)

        # Test with an invalid URL (unexpected query)
        site_url = "https://website.com?font=wingdings&size=42"

        identifier = parse_identifier_from_site_url(site_url)

        self.assertIsNone(identifier)

        # Test with an invalid URL (malformed)
        site_url = 123456789

        identifier = parse_identifier_from_site_url(site_url)

        self.assertIsNone(identifier)

    def test_is_pds4_identifier(self):
        """Tests for general_util.is_pds4_identifier()"""
        # LID-only
        self.assertTrue(is_pds4_identifier("urn:nasa:pds:insight_cameras"))

        # LIDVID
        self.assertTrue(is_pds4_identifier("urn:nasa:pds:insight_cameras::1.0"))

        # PDS3 (or anything else really)
        self.assertFalse(is_pds4_identifier("LRO-L-MRFLRO-2/3/5-BISTATIC-V1.0"))

    def test_create_landing_page_url(self):
        """Tests for general_util.create_landing_page_url()"""
        # Test PDS4 style LIDVID
        identifier = "urn:nasa:pds:insight_cameras::1.0"
        product_type = ProductType.Bundle

        site_url = create_landing_page_url(identifier, product_type)

        self.assertEqual(
            site_url,
            "https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn%3Anasa%3Apds%3Ainsight_cameras&amp;version=1.0",
        )

        # Test PDS4 style LID only
        identifier = "urn:nasa:pds:insight_cameras"
        product_type = ProductType.Collection

        site_url = create_landing_page_url(identifier, product_type)

        self.assertEqual(
            site_url,
            "https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn%3Anasa%3Apds%3Ainsight_cameras",
        )

        # Test PDS3 style ID
        identifier = "LRO-L-MRFLRO-2/3/5-BISTATIC-V1.0"
        product_type = ProductType.Dataset

        site_url = create_landing_page_url(identifier, product_type)

        self.assertEqual(
            site_url, "https://pds.nasa.gov/ds-view/pds/viewDataset.jsp?dsid=LRO-L-MRFLRO-2/3/5-BISTATIC-V1.0"
        )

    def test_get_global_keywords(self):
        """Tests for general_util.get_global_keywords()"""
        config = DOIConfigUtil().get_config()

        # Save the current global keywords in the INI so they can be restored later
        global_keyword_values = config.get("OTHER", "global_keyword_values")

        try:
            # Test on standard semi-colon delimited keywords
            config.set("OTHER", "global_keyword_values", "PDS; PDS4;")

            global_keywords = get_global_keywords()

            self.assertSetEqual(global_keywords, {"PDS", "PDS4"})

            # Test on same keywords, but comma-delimited and with extraneous whitespace
            config.set("OTHER", "global_keyword_values", " PDS, PDS4 ")

            global_keywords = get_global_keywords()

            self.assertSetEqual(global_keywords, {"PDS", "PDS4"})

            # Test to make sure empty string is not added as a keyword
            config.set("OTHER", "global_keyword_values", "PDS;PDS4, ,,")

            global_keywords = get_global_keywords()

            self.assertSetEqual(global_keywords, {"PDS", "PDS4"})

            # Test some numbers used as keywords to ensure they're maintained as strings
            config.set("OTHER", "global_keyword_values", "123,456,7.89;")

            global_keywords = get_global_keywords()

            self.assertSetEqual(global_keywords, {"123", "456", "7.89"})
        finally:
            # Restore the original global keywords to the config
            config.set("OTHER", "global_keyword_values", global_keyword_values)

    def test_sanitizing_json_strings(self):
        """Ensure we can properly sanitize JSON strings about to go into Jinja2 templates.

        ☝️ Note: using Jinja2 templates to generate JSON is not a bulletproof way to go. In the
        future, it would be better to just create JSON structures in memory and then serialize them.
        Serialization > templating.
        """
        self.assertEqual("", sanitize_json_string(""))
        self.assertEqual("", sanitize_json_string(" "))
        self.assertEqual("", sanitize_json_string("   "))
        self.assertEqual("👋", sanitize_json_string("👋"))
        self.assertEqual("👋", sanitize_json_string(" 👋"))
        self.assertEqual("👋", sanitize_json_string("👋 "))
        self.assertEqual("👋", sanitize_json_string(" 👋 "))
        self.assertEqual('👋\\"', sanitize_json_string('👋"'))


if __name__ == "__main__":
    unittest.main()
