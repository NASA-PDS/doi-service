# encoding: utf-8
"""
Planetary Data System's Digital Object Identifier service — tests for core database
"""
import unittest

from . import doi_database_test
from . import transaction_test


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(doi_database_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(transaction_test))
    return suite
