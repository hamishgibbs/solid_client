import uuid
import datetime
from authlib.jose import jwt, JsonWebKey


def gen_access_request_dpop_token(CLIENT_PUBLIC_KEY: dict,
                                  CLIENT_PRIVATE_KEY: dict,
                                  resource_uri: str):

    dpop_token_header = {
        "alg": "ES256",
        "typ": "dpop+jwt"
    }

    dpop_token_payload = {
        "htu": resource_uri,
        "htm": "GET",
        "jti": uuid.uuid4().__str__(),
        "cnf": {"jwk": CLIENT_PUBLIC_KEY},
        "iat": int(datetime.datetime.timestamp(datetime.datetime.now()))
    }

    dpop_token = jwt.encode(dpop_token_header,
                            dpop_token_payload,
                            CLIENT_PRIVATE_KEY)

    return dpop_token
