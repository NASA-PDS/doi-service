# encoding: utf-8
"""
Planetary Data System's Digital Object Identifier service — tests.
"""
import unittest

import pds_doi_service.api.test
import pds_doi_service.core.actions.test
import pds_doi_service.core.db.test
import pds_doi_service.core.input.test
import pds_doi_service.core.outputs.test
import pds_doi_service.core.references.test
import pds_doi_service.core.util.test


def suite():
    suite = unittest.TestSuite()
    suite.addTests(pds_doi_service.core.util.test.suite())
    suite.addTests(pds_doi_service.core.input.test.suite())
    suite.addTests(pds_doi_service.core.references.test.suite())
    suite.addTests(pds_doi_service.core.actions.test.suite())
    suite.addTests(pds_doi_service.core.db.test.suite())
    suite.addTests(pds_doi_service.core.outputs.test.suite())
    suite.addTests(pds_doi_service.api.test.suite())
    return suite
