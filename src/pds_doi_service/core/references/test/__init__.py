# encoding: utf-8
"""
Planetary Data System's Digital Object Identifier service — tests for core references
"""
import unittest

from . import contributors_test


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(contributors_test))
    return suite
