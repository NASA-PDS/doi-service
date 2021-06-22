# encoding: utf-8

'''
Planetary Data System's Digital Object Identifier service — API testing base classes
'''


from flask_testing import TestCase
from pds_doi_service.api.encoder import JSONEncoder
import connexion
import logging


class BaseTestCase(TestCase):

    def create_app(self):
        logging.getLogger('connexion.operation').setLevel('ERROR')
        app = connexion.App(__name__, specification_dir='../swagger/')
        app.app.json_encoder = JSONEncoder
        app.app.url_map.strict_slashes = False
        app.add_api('swagger.yaml')
        return app.app
