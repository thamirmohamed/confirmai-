import os
import secrets
import requests
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/shopify", tags=["Shopify"])

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_SCOPES = os.getenv("SHOPIFY_SCOPES")
SHOPIFY_REDIRECT_URI = os.getenv("SHOPIFY_REDIRECT_URI")


@router.get("/install")
def install(shop: str):

    state = secrets.token_hex(16)

    params = {
        "client_id": SHOPIFY_API_KEY,
        "scope": SHOPIFY_SCOPES,
        "redirect_uri": SHOPIFY_REDIRECT_URI,
        "state": state,
    }

    url = (
        f"https://{shop}/admin/oauth/authorize?"
        + urlencode(params)
    )

    return {"install_url": url}


@router.get("/callback")
def callback(shop: str, code: str):

    response = requests.post(

        f"https://{shop}/admin/oauth/access_token",

        json={
            "client_id": SHOPIFY_API_KEY,
            "client_secret": SHOPIFY_API_SECRET,
            "code": code,
        },
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=response.text,
        )

    token = response.json()["access_token"]

    return {
        "shop": shop,
        "access_token": token,
    }