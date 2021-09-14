# encoding: utf-8
"""
Planetary Data System's Digital Object Identifier service — tests for core inputs
"""
import unittest

from . import input_util_test
from . import read_bundle


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(input_util_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(read_bundle))
    return suite
