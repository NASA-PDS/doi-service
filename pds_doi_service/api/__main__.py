#!/usr/bin/env python3
#
#  Copyright 2020-21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#

import connexion
from flask_cors import CORS
from waitress import serve

from pds_doi_service.api import encoder
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger


def main():
    """
    Main entry point for the DOI Service API

    The API connexion application is created using the swagger definition and
    fed to a waitress server instance.
    """
    config = DOIConfigUtil().get_config()

    app = connexion.App(__name__, specification_dir='swagger/')
    CORS(app.app)
    app.app.json_encoder = encoder.JSONEncoder

    # Disable the Flask "strict_slashes" checking so endpoints with a trailing
    # slash resolve to the same endpoint as without
    app.app.url_map.strict_slashes = False

    # Feed the swagger definition to the connexion app, this informs the
    # app how to route URL's to endpoints in dois_controller.py
    app.add_api('swagger.yaml',
                arguments={'title': 'Planetary Data System DOI Service API'},
                pythonic_params=True)

    # Set the log level of waitress to match the configured level
    logging_level = config.get('OTHER', 'logging_level', fallback='info')
    logger = get_logger('waitress')
    logger.info(f'Waitress logging configured at level {logging_level}')

    serve(app,
          host=config.get('OTHER', 'api_host', fallback='0.0.0.0'),
          port=config.get('OTHER', 'api_port', fallback=8080))


if __name__ == '__main__':
    main()
