#!/usr/bin/env python3
#
#  Copyright 2020–21, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
import logging
from urllib.parse import urlparse

import connexion  # type: ignore
from flask import jsonify
from flask_cors import CORS  # type: ignore
from pds_doi_service.api import encoder
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from pds_doi_service.core.util.general_util import get_logger
from waitress import serve

logging.basicConfig(level=logging.INFO)

# We create the connexion app here so we can access underlying Flask decorators
app = connexion.App(__name__, specification_dir="swagger/")
# We also add an initialization flag to ensure that calls to init_app() only
# add the swagger api once
app.initialized = False


class InvalidReferrer(Exception):
    """Raised when the referrer check fails."""

    status_code = 401

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message

        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        rv = {"message": self.message, "status_code": self.status_code}
        return rv


@app.app.errorhandler(InvalidReferrer)
def handle_invalid_usage(error):
    """Registers a handler for InvalidReferrer exceptions caught by Flask"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.app.before_request
def _check_referrer():
    """
    Checks the referrer header field of the current request to ensure it was
    sent by a valid endpoint. The list of valid referrers is defined by the
    DOI service INI config. If not valid referrers are defined by the config,
    this function will allow all requests through.

    Raises
    ------
    InvalidReferrer
        If no referrer is provided with the request, or the referrer is not
        within the list of valid hosts.

    Returns
    -------
    None if the referrer is valid (meaning the request should continue).

    """
    logger = logging.getLogger(__name__)
    config = DOIConfigUtil().get_config()

    referrer = connexion.request.referrer
    logger.debug("Referrer: %s", referrer)

    valid_referrers = config.get("OTHER", "api_valid_referrers", fallback=None)

    # if no valid referrers are configured, just return None to allow
    # request to go forward
    if not valid_referrers:
        return None

    valid_referrers = list(map(str.strip, valid_referrers.split(",")))
    logger.debug("Valid referrers: %s", valid_referrers)

    if not referrer:
        raise InvalidReferrer("No referrer specified from request")

    parsed_referrer = urlparse(referrer)

    if parsed_referrer.hostname not in valid_referrers and referrer not in valid_referrers:
        raise InvalidReferrer("Request referrer is not allowed access to the API", status_code=403)


def init_app():
    """
    Performs one-time initialization on the Connexion application that serves
    the DOI API. This includes feeding in the swagger OpenAPI YAML file
    that defines the operations of the API.

    Initialization is only performed on the first call to this function. All
    future calls only return a handle to the app itself. This makes the function
    safe for use with the flask_testing package.

    Returns
    -------
    app : Connexion.App
        The initialized Connexion (Flask) application

    """
    if not app.initialized:
        CORS(app.app)
        app.app.json_encoder = encoder.JSONEncoder

        # Disable the Flask "strict_slashes" checking so endpoints with a trailing
        # slash resolve to the same endpoint as without
        app.app.url_map.strict_slashes = False

        # Feed the swagger definition to the connexion app, this informs the
        # app how to route URL's to endpoints in dois_controller.py
        app.add_api("swagger.yaml", arguments={"title": "Planetary Data System DOI Service API"}, pythonic_params=True)

        app.initialized = True

    return app


def main():
    """
    Main entry point for the DOI Service API

    The API connexion application is created using the swagger definition and
    fed to a waitress server instance.
    """
    logger = logging.getLogger(__name__)

    logger.info("Starting PDS DOI Service API")

    config = DOIConfigUtil().get_config()

    # Now that we've parsed config, we can fully set up logging
    logger = get_logger(__name__)
    logging_level = config.get("OTHER", "logging_level", fallback="info")

    logger.info(f"Logging system configured at level {logging_level}")

    # Initialize the Connexion (Flask) application
    app = init_app()

    # Set the log level of waitress to match the configured level
    get_logger("waitress")
    logger.info(f"Waitress logging configured at level {logging_level}")

    try:
        serve(
            app,
            host=config.get("OTHER", "api_host", fallback="0.0.0.0"),
            port=config.get("OTHER", "api_port", fallback=8080),
        )
    except KeyboardInterrupt:
        logger.info("Stopping PDS DOI Service API")


if __name__ == "__main__":
    main()
