# encoding: utf-8

'''
Planetary Data System's Digital Object Identifier service — tests for core outputs
'''


import unittest
from . import osti_test


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(osti_test))
    return suite
