import time
import logging
from jose import JWTError, jwt
from flask import current_app
from werkzeug.exceptions import Unauthorized
from pds_doi_service.core.util.config_parser import DOIConfigUtil

config = DOIConfigUtil().get_config()

JWT_ISSUER = config.get('API_AUTHENTICATION', 'jwt_issuer')
JWT_SECRET = config.get('API_AUTHENTICATION', 'jwt_secret')
JWT_LIFETIME_SECONDS = 3600
JWT_ALGORITHM = "RS256"


def decode_token(token):
    try:
        current_app.logger.debug("try to decode/validate token %s", token)
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={
                'verify_signature': False,
                'verify_iss': True
            }
        )
    except JWTError as e:
        current_app.logger.error("authentication exception")
        raise Unauthorized from e
