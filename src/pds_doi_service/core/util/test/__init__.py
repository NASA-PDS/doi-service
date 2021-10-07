# encoding: utf-8
"""
Planetary Data System's Digital Object Identifier service — tests for core utilities
"""
import unittest

from . import config_parser_test
from . import general_util_test


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(config_parser_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(general_util_test))
    return suite
