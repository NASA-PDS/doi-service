# encoding: utf-8
"""
Planetary Data System's Digital Object Identifier service — tests for core actions
"""
import unittest

from . import check_test
from . import list_test
from . import release_test
from . import reserve_test
from . import update_test


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(check_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(list_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(release_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(reserve_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(update_test))
    return suite
