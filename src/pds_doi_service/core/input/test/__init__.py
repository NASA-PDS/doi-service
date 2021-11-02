# encoding: utf-8
"""
Planetary Data System's Digital Object Identifier service — tests for core inputs
"""
import unittest

from . import input_util_test
from . import pds4_util_test


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(input_util_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(pds4_util_test))
    return suite
