import logging

import connexion
from flask_testing import TestCase

from pds_doi_service.api.encoder import JSONEncoder


class BaseTestCase(TestCase):

    def create_app(self):
        logging.getLogger('connexion.operation').setLevel('ERROR')
        app = connexion.App(__name__, specification_dir='../swagger/')
        app.app.json_encoder = JSONEncoder
        app.app.url_map.strict_slashes = False
        app.add_api('swagger.yaml')
        return app.app
