# encoding: utf-8
"""
Planetary Data System's Digital Object Identifier service — tests for API
"""
import unittest

from . import test_dois_controller


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_dois_controller))
    return suite
