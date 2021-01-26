from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pickle
from solid_client import consent
import secrets
import urllib

SESSION_STORAGE = 'data/code_keystore.p'

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

    with open(SESSION_STORAGE, 'rb') as f:

        keystore = pickle.load(f)

    random_secret = secrets.token_hex(10)

    keystore.append(random_secret)

    if idp is not None:

        idp_config = consent.get_idp_config(idp)

    elif webid is not None:

        idp = consent.get_webid_idp(webid)

        print(idp)

        idp_config = consent.get_idp_config(idp)

    else:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide a Webid or Identity Proivder.",
        )

    code_request = consent.prepare_code_request(random_secret)

    code_params = urllib.parse.urlencode(code_request)

    auth_url = idp_config['authorization_endpoint'] + '?' + code_params

    return RedirectResponse(auth_url,
                            status_code=303)


@app.get("/callback")
async def callback(code: str):

    print(code)

    return {"message": "This is the callback endpoint."}


@app.get("/webid")
async def webid():
    return FileResponse('static/webid.ttl')
