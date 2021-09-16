# encoding: utf-8
"""
Planetary Data System's Digital Object Identifier service — API testing base classes
"""
import logging

from flask_testing import TestCase  # type: ignore
from pds_doi_service.api.__main__ import init_app


class BaseTestCase(TestCase):
    def create_app(self):
        logging.getLogger("connexion.operation").setLevel("ERROR")
        app = init_app()
        return app.app
