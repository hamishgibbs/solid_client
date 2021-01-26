from fastapi import HTTPException, status
import requests
from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery
import base64
import hashlib

def get_idp_config(idp: str):

    res = requests.get(idp + '/.well-known/openid_configuration')

    if res.status_code == 200:

        idp_config = res.json()

    else:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to confirm Identity Provider.",
        )

    return idp_config


def get_webid_idp(webid: str):

    try:

        g = Graph()

        g.parse('http://127.0.0.1:8000/jade/card', format='turtle')

        q = prepareQuery(
            '''
            SELECT ?o
            WHERE {
                ?s <http://www.w3.org/ns/solid/terms#oidcIssuer> ?o
            }
            '''
        )

        oidc_registration = []

        for row in g.query(q):
            oidc_registration.append(row)

    except Exception:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to confirm Identity Provider.",
        )

    return oidc_registration[0][0].value


def create_code_challenge(nonce: str):

    return base64.b64encode(hashlib.sha256(nonce.encode('ascii')).digest())


def prepare_code_request(nonce: str,
                         scope: str = 'open_id profile offline_access'):

    auth_params = {'response_type': 'code',
                   'redirect_uri': 'http://127.0.0.1:8001/callback',
                   'scope': scope,
                   'client_id': 'http://127.0.0.1:8001/webid#this',
                   'code_challenge_method': 'S256',
                   'code_challenge': create_code_challenge(nonce)}

    return auth_params
