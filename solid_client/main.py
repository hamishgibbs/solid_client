from fastapi import FastAPI, Request, Form, HTTPException, status, Cookie
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from solid_client import consent
from solid_client import token
import secrets
import urllib
from typing import Optional
import uuid
import datetime
import requests

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from authlib.jose import jwt, JsonWebKey

from pymongo import MongoClient

client = MongoClient('mongodb://0.0.0.0:27017')

db = client['client']

key = ec.generate_private_key(ec.SECP256R1(), backend=crypto_default_backend())

private_key = key.private_bytes(
    crypto_serialization.Encoding.PEM,
    crypto_serialization.PrivateFormat.PKCS8,
    crypto_serialization.NoEncryption())
public_key = key.public_key().public_bytes(
    crypto_serialization.Encoding.OpenSSH,
    crypto_serialization.PublicFormat.OpenSSH
)

CLIENT_PRIVATE_KEY = JsonWebKey.import_key(private_key, {'kty': 'EC'})
CLIENT_PUBLIC_KEY = JsonWebKey.import_key(public_key, {'kty': 'EC'})

templates = Jinja2Templates(directory="templates")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/consent")
async def get_consent(request: Request):
    return templates.TemplateResponse("consent.html", {"request": request})


@app.post("/consent")
async def post_consent(request: Request,
                       idp: str = Form(default=None),
                       webid: str = Form(default=None)):

    nonce = secrets.token_hex(10)

    if idp is not None:

        idp_config = consent.get_idp_config(idp)

    elif webid is not None:

        idp = consent.get_webid_idp(webid)

        print(idp)

        idp_config = consent.get_idp_config(idp)

    else:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide a Webid or Identity Provider.",
        )

    code_request = consent.prepare_code_request(nonce)

    code_params = urllib.parse.urlencode(code_request)

    auth_url = idp_config['authorization_endpoint'] + '?' + code_params

    response = RedirectResponse(auth_url,
                                status_code=303)

    response.set_cookie(key="challenge_secret",
                        value=nonce,
                        httponly=True)

    response.set_cookie(key="token_endpoint",
                        value=idp_config['token_endpoint'],
                        httponly=True)

    return response


@app.get("/callback")
async def callback(code: str,
                   challenge_secret: Optional[str] = Cookie(None),
                   token_endpoint: Optional[str] = Cookie(None)):

    dpop_token_header = {
        "alg": "ES256",
        "typ": "dpop+jwt"
    }

    dpop_token_payload = {
        "htu": "http://127.0.0.1:8001",
        "cnf": {"jwk": CLIENT_PUBLIC_KEY},
        "htm": "POST",
        "jti": uuid.uuid4().__str__(),
        "iat": int(datetime.datetime.timestamp(datetime.datetime.now()))
    }

    dpop_token = jwt.encode(dpop_token_header, dpop_token_payload, CLIENT_PRIVATE_KEY)

    auth_headers = {
        "DPoP": dpop_token,
        "content-type": "application/x-www-form-urlencoded"
    }

    auth_body = {
        'grant_type': 'authorization_code',
        'code_verifier': challenge_secret,
        'code': code,
        'redirect_uri': 'http://127.0.0.1:8001/callback',
        'client_id': 'http://127.0.0.1:8001/webid#this'
    }

    res = requests.post(token_endpoint, params=auth_body, headers=auth_headers)

    if res.status_code == 200:

        token_response = res.json()

        if 'access_token' in token_response.keys():

            access_token = token_response['access_token']

            print(access_token)

        else:

            access_token = None

        if 'id_token' in token_response.keys():

            id_token = token_response['id_token']

        else:

            id_token = None

        if 'refresh_token' in token_response.keys():

            refresh_token = token_response['refresh_token']

        else:

            refresh_token = None

    else:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to verify identity.",
        )

    response = RedirectResponse('/data', status_code=307)

    response.delete_cookie("challenge_secret")
    response.delete_cookie("token_endpoint")

    response.set_cookie(key="access_token", value=access_token)

    return response


@app.get("/data")
async def get_data_view(request: Request,
                        access_token: Optional[str] = Cookie(None)):

    print(access_token)

    if not access_token:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access token for protected resources.",
        )

    dpop_token = token.gen_access_request_dpop_token(CLIENT_PUBLIC_KEY,
                                                     CLIENT_PRIVATE_KEY,
                                                     'http://127.0.0.1:8002/protected/data.ttl')
    request_headers = {
        'authorization': 'DPoP ' + access_token,
        'dpop': dpop_token
    }

    res = requests.get('http://127.0.0.1:8002/protected/data.ttl',
                       headers=request_headers)

    return templates.TemplateResponse("data.html", {"request": request,
                                                    "message": res.json()})


@app.get("/success")
async def get_success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@app.get("/webid")
async def webid():
    return FileResponse('static/webid.ttl')
