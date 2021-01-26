from fastapi import FastAPI, Request, Form, HTTPException, status, Cookie
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from solid_client import consent
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

    random_secret = secrets.token_hex(10)

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

    code_request = consent.prepare_code_request(random_secret)

    code_params = urllib.parse.urlencode(code_request)

    auth_url = idp_config['authorization_endpoint'] + '?' + code_params

    response = RedirectResponse(auth_url,
                                status_code=303)

    response.set_cookie(key="challenge_secret",
                        value=random_secret,
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

    print(res)
    print(res.status_code)
    print(res.text)
    print(res.json)

    if res.status_code == 200:

        print(res.json())

    else:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to verify identity.",
        )

    response = RedirectResponse('/success', status_code=307)

    response.delete_cookie("challenge_secret")
    response.delete_cookie("token_endpoint")

    return response


@app.get("/success")
async def get_success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@app.get("/webid")
async def webid():
    return FileResponse('static/webid.ttl')
