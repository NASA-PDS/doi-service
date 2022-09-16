import logging
import time

from flask import current_app
from jose import jwt  # type: ignore
from jose import JWTError
from pds_doi_service.core.util.config_parser import DOIConfigUtil
from werkzeug.exceptions import Unauthorized

config = DOIConfigUtil().get_config()

JWT_ISSUER = config.get("API_AUTHENTICATION", "jwt_issuer")
JSON_WEB_KEY_SET = config.get("API_AUTHENTICATION", "json_web_key_set")
JWT_LIFETIME_SECONDS = config.get("API_AUTHENTICATION", "jwt_lifetime_seconds")
JWT_ALGORITHM = config.get("API_AUTHENTICATION", "jwt_algorithm")


def decode_token(token):
    try:
        current_app.logger.debug("try to decode/validate token %s", token)
        return jwt.decode(
            token,
            JSON_WEB_KEY_SET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"verify_signature": True, "verify_iss": True},
        )
    except JWTError as e:
        current_app.logger.error("authentication exception")
        raise Unauthorized from e
